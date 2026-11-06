import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from layout import SKILLS  # noqa: E402

SETUP = SKILLS / "adapter-proxmox" / "scripts" / "setup-agent-access.sh"
TEARDOWN = SKILLS / "adapter-proxmox" / "scripts" / "teardown-agent-access.sh"
LIB = SKILLS / "adapter-proxmox" / "scripts" / "lib.sh"
STUBS = ROOT / "tests" / "stubs"

PRIVS = ("VM.Allocate VM.Audit VM.PowerMgmt VM.Config.CPU VM.Config.Memory VM.Config.Disk "
         "VM.Config.Network VM.Config.HWType VM.Config.Options VM.Config.Cloudinit Pool.Audit")
USER = "fcos-agent@pve"
KEYID = "fcos-agent@pve!fcos-bootstrap"
FAKE_VALUE = "00000000-stub-0000-0000-000000000000"
HOST = subprocess.run(["uname", "-n"], capture_output=True, text=True, check=True).stdout.strip().split(".")[0]
WRITE_VERBS = {"add", "modify", "delete", "remove"}

HOST_FACTS = {"storages": ["local-lvm"], "bridges": ["vmbr0"]}
KEEP = object()  # run again on the state the previous run left behind


def acls_for(storage="local-lvm", bridge="vmbr0"):
    acls = []
    for path, role in (("/pool/fcos-agent", "FCOSAgentVM"), (f"/storage/{storage}", "PVEDatastoreUser"),
                       (f"/sdn/zones/localnetwork/{bridge}", "PVESDNUser")):
        acls += [[path, "user", USER, role], [path, "token", KEYID, role]]
    return acls


ISO_PRIVS = "Datastore.AllocateTemplate Datastore.Audit"


def iso_acls(storage="local"):
    return [[f"/storage/{storage}", "user", USER, "FCOSAgentISO"],
            [f"/storage/{storage}", "token", KEYID, "FCOSAgentISO"]]


def iso_host(content="snippets,backup,import,vztmpl,iso"):
    """A host with a directory storage `local` for config discs and images."""
    return dict(HOST_FACTS, storages=["local-lvm", "local"], storage_content={"local": content})


def partial_state():
    """The user's real half-finished state: everything but the ACLs."""
    state = dict(HOST_FACTS, pools={"fcos-agent": []}, roles={"FCOSAgentVM": ",".join(PRIVS.split())},
                 users=[USER])
    state["tokens"] = [KEYID]
    return state


def full_state(**overrides):
    state = dict(partial_state(), acls=acls_for())
    state.update(overrides)
    return state


class HostScriptCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.state_path = self.tmp / "state.json"
        self.log_path = self.tmp / "calls.log"

    def write_state(self, state):
        self.state_path.write_text(json.dumps(state))

    def read_state(self):
        return json.loads(self.state_path.read_text())

    def run_script(self, script, *args, state=None, nonroot_ok=True):
        if state is not KEEP:
            self.write_state(HOST_FACTS if state is None else state)
        env = dict(os.environ, PATH=f"{STUBS}:{os.environ['PATH']}",
                   STUB_STATE=str(self.state_path), STUB_LOG=str(self.log_path))
        env.pop("FCOS_ALLOW_NONROOT", None)
        if nonroot_ok:
            env["FCOS_ALLOW_NONROOT"] = "1"
        return subprocess.run(["bash", str(script), *args], capture_output=True, text=True, env=env, cwd=self.tmp)

    def setup(self, *args, state=None):
        return self.run_script(SETUP, "--storage", "local-lvm", "--bridge", "vmbr0", "--node", "testnode",
                               *args, state=state)

    def calls(self):
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text().splitlines()]

    def writes(self):
        return [c for c in self.calls() if WRITE_VERBS & set(c[:5])]

    def assertNoWrites(self):
        self.assertEqual([], self.writes())


class SetupTests(HostScriptCase):
    def test_fresh_setup_calls(self):
        result = self.setup()
        self.assertEqual(0, result.returncode, result.stderr)
        acl = ["pveum", "acl", "modify"]
        expected_acls = [acl + [path, "--roles", role, flag, who]
                         for path, role in (("/pool/fcos-agent", "FCOSAgentVM"),
                                            ("/storage/local-lvm", "PVEDatastoreUser"),
                                            ("/sdn/zones/localnetwork/vmbr0", "PVESDNUser"))
                         for flag, who in (("--users", USER), ("--tokens", KEYID))]
        writes = self.writes()
        self.assertEqual(["pveum", "pool", "add", "fcos-agent"], writes[0][:4])
        self.assertEqual(["pveum", "role", "add", "FCOSAgentVM", "--privs", PRIVS], writes[1])
        self.assertEqual(["pveum", "user", "add", USER], writes[2][:4])
        self.assertNotIn("--password", writes[2])
        self.assertEqual(["pveum", "user", "token", "add", USER, "fcos-bootstrap", "--privsep", "1"], writes[3])
        self.assertEqual(expected_acls, writes[4:])
        self.assertEqual(10, len(writes))
        self.assertEqual(["pveum", "user", "token", "permissions", USER, "fcos-bootstrap"], self.calls()[-1])
        self.assertEqual(sorted(map(tuple, acls_for())), sorted(map(tuple, self.read_state()["acls"])))

    def test_resumes_partial_setup(self):
        result = self.setup(state=partial_state())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], [c for c in self.calls() if "add" in c[:5]])
        acl_calls = [c for c in self.calls() if c[1:3] == ["acl", "modify"]]
        self.assertEqual(6, len(acl_calls))
        self.assertEqual(sorted(map(tuple, acls_for())), sorted(map(tuple, self.read_state()["acls"])))
        self.assertNotIn(FAKE_VALUE, result.stdout + result.stderr)
        self.assertIn("token already exists; secret not shown (use --rotate to replace)", result.stdout)

    def test_rerun_after_full_setup_changes_nothing_new(self):
        self.assertEqual(0, self.setup().returncode)
        self.log_path.unlink()
        again = self.setup(state=KEEP)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual([], [c for c in self.calls() if "add" in c[:5]])
        self.assertNotIn(FAKE_VALUE, again.stdout + again.stderr)
        self.assertEqual(sorted(map(tuple, acls_for())), sorted(map(tuple, self.read_state()["acls"])))

    def test_reads_use_documented_pvesh_calls_and_never_pvesm(self):
        result = self.setup("--check")
        self.assertEqual(0, result.returncode, result.stderr)
        calls = self.calls()
        self.assertEqual([], [c for c in calls if c[0] == "pvesm"])
        self.assertIn(["pvesh", "get", "/nodes/testnode/storage", "--output-format", "json"], calls)
        self.assertIn(["pvesh", "get", "/nodes/testnode/network", "--type", "bridge", "--output-format", "json"],
                      calls)
        for call in calls:
            if call[0] == "pveum":
                self.assertNotIn("--output-format", call)
                self.assertNotIn("list", call[:4])

    def test_validates_storage_and_bridge(self):
        for args in (("--storage", "nope", "--bridge", "vmbr0"), ("--storage", "local-lvm", "--bridge", "nope")):
            with self.subTest(args=args):
                if self.log_path.exists():
                    self.log_path.unlink()
                result = self.run_script(SETUP, *args, "--node", "testnode")
                self.assertEqual(1, result.returncode)
                self.assertIn(args[1] if args[1] == "nope" else args[3], result.stderr)
                self.assertNoWrites()

    def test_rejects_placeholder_values(self):
        result = self.run_script(SETUP, "--storage", "<storage>", "--bridge", "<bridge>")
        self.assertEqual(1, result.returncode)
        self.assertIn("placeholder", result.stderr)
        self.assertEqual([], self.calls())

    def test_usage_errors_exit_2(self):
        for args in ((), ("--storage", "local-lvm"), ("--bridge", "vmbr0"),
                     ("--storage", "local-lvm", "--bridge", "vmbr0", "--bogus"),
                     ("--storage", "--bridge", "vmbr0")):
            with self.subTest(args=args):
                self.assertEqual(2, self.run_script(SETUP, *args).returncode)
        self.assertEqual([], self.calls())

    def test_refuses_non_root(self):
        if os.geteuid() == 0:
            self.skipTest("running as root")
        result = self.run_script(SETUP, "--storage", "local-lvm", "--bridge", "vmbr0", nonroot_ok=False)
        self.assertEqual(1, result.returncode)
        self.assertIn("root", result.stderr)
        self.assertEqual([], self.calls())

    def test_check_mode_changes_nothing(self):
        for state in (None, partial_state()):
            with self.subTest(state=state):
                if self.log_path.exists():
                    self.log_path.unlink()
                before = state or HOST_FACTS
                result = self.setup("--check", state=state)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertNoWrites()
                self.assertNotIn(FAKE_VALUE, result.stdout)
                self.assertEqual(before, self.read_state())
        self.assertIn("would", self.setup("--check").stdout)

    def test_rotate_replaces_token(self):
        result = self.setup("--rotate", state=full_state())
        self.assertEqual(0, result.returncode, result.stderr)
        writes = self.writes()
        self.assertEqual(["pveum", "user", "token", "remove", USER, "fcos-bootstrap"], writes[0])
        self.assertEqual(["pveum", "user", "token", "add", USER, "fcos-bootstrap", "--privsep", "1"], writes[1])
        self.assertEqual(6, len([c for c in writes[2:] if c[1:3] == ["acl", "modify"]]))
        self.assertIn(FAKE_VALUE, result.stdout)
        self.assertEqual(sorted(map(tuple, acls_for())), sorted(map(tuple, self.read_state()["acls"])))

    def test_secret_printed_once_and_nothing_else_to_run(self):
        # The script's output holds the secret and no command; storing it is
        # the agent's next step (adapter step store_api_token), shown on its own.
        result = self.setup()
        out = result.stdout
        self.assertEqual(1, out.count(FAKE_VALUE))
        self.assertNotIn(FAKE_VALUE, result.stderr)
        self.assertNotIn(FAKE_VALUE, json.dumps(self.calls()))
        for needle in ("read -s", "chmod", "<workspace>", ".token"):
            self.assertNotIn(needle, out)
        self.assertIn("next step", out)

    def test_bad_host_keys_refused(self):
        for bad in ("<host>", "a b", "../x", "x/y", ".", "..", "-x"):
            with self.subTest(bad=bad):
                self.assertNotEqual(0, self.setup("--host-key", bad).returncode)
                self.assertNotEqual(0, self.run_script(TEARDOWN, "--host-key", bad, state=teardown_state()).returncode)

    def test_rotate_check_reports_the_token_grants_it_would_redo(self):
        # Proxmox drops a removed token's ACL entries, so a replacement needs them again.
        result = self.setup("--rotate", "--check", state=full_state())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(f"ok: FCOSAgentVM on /pool/fcos-agent for token {KEYID}", result.stdout)
        self.assertIn(f"would: grant FCOSAgentVM on /pool/fcos-agent to token {KEYID}", result.stdout)
        self.assertNoWrites()

    def test_resets_role_with_wrong_privileges(self):
        state = partial_state()
        state["roles"]["FCOSAgentVM"] = "VM.Allocate,VM.Audit,VM.Console,Sys.Modify"
        result = self.setup(state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(["pveum", "role", "modify", "FCOSAgentVM", "--privs", PRIVS], self.calls())
        self.assertEqual(",".join(PRIVS.split()), self.read_state()["roles"]["FCOSAgentVM"])

    def test_refuses_token_without_privilege_separation(self):
        state = partial_state()
        state["tokens_no_privsep"] = [KEYID]
        result = self.setup(state=state)
        self.assertEqual(1, result.returncode)
        self.assertIn("--rotate", result.stderr)
        self.assertNoWrites()

    def test_iso_storage_grants_upload_role(self):
        result = self.setup("--iso-storage", "local", state=iso_host())
        self.assertEqual(0, result.returncode, result.stderr)
        calls = self.calls()
        self.assertIn(["pveum", "role", "add", "FCOSAgentISO", "--privs", ISO_PRIVS], calls)
        for flag, who in (("--users", USER), ("--tokens", KEYID)):
            self.assertIn(["pveum", "acl", "modify", "/storage/local", "--roles", "FCOSAgentISO", flag, who], calls)
        state = self.read_state()
        self.assertEqual(",".join(ISO_PRIVS.split()), state["roles"]["FCOSAgentISO"])
        self.assertEqual(sorted(map(tuple, acls_for() + iso_acls())), sorted(map(tuple, state["acls"])))
        # Re-run: nothing new is added.
        self.log_path.unlink()
        again = self.setup("--iso-storage", "local", state=KEEP)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertEqual([], [c for c in self.calls() if "add" in c[:5]])

    def test_iso_storage_must_exist_and_allow_iso_and_import(self):
        for content, missing in (("iso,vztmpl", "import"), ("import,snippets", "iso"), ("images", "iso")):
            with self.subTest(content=content):
                if self.log_path.exists():
                    self.log_path.unlink()
                result = self.setup("--iso-storage", "local", state=iso_host(content))
                self.assertEqual(1, result.returncode)
                self.assertIn(missing, result.stderr)
                self.assertIn("local", result.stderr)
                self.assertNoWrites()
        self.log_path.unlink(missing_ok=True)
        result = self.setup("--iso-storage", "nope", state=iso_host())
        self.assertEqual(1, result.returncode)
        self.assertIn("nope", result.stderr)
        self.assertNoWrites()

    def test_iso_storage_error_lists_allowed_content(self):
        result = self.setup("--iso-storage", "local", state=iso_host("iso,vztmpl"))
        self.assertIn("(it allows: iso,vztmpl)", result.stderr)
        result = self.setup("--iso-storage", "local", state=iso_host(""))
        self.assertIn("(it allows: nothing)", result.stderr)

    def test_iso_storage_name_validated(self):
        result = self.setup("--iso-storage", "<iso-storage>", state=iso_host())
        self.assertEqual(1, result.returncode)
        self.assertIn("placeholder", result.stderr)
        self.assertEqual(2, self.setup("--iso-storage", state=iso_host()).returncode)

    def test_without_iso_storage_no_upload_role_and_says_so(self):
        result = self.setup(state=iso_host())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("FCOSAgentISO", json.dumps(self.calls()))
        self.assertIn("--iso-storage", result.stdout)

    def test_iso_role_reset_when_privileges_drift(self):
        state = full_state(storages=["local-lvm", "local"], storage_content={"local": "iso,import"})
        state["roles"] = dict(state["roles"], FCOSAgentISO="Datastore.AllocateTemplate,Datastore.Allocate")
        result = self.setup("--iso-storage", "local", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(["pveum", "role", "modify", "FCOSAgentISO", "--privs", ISO_PRIVS], self.calls())
        self.assertEqual(",".join(ISO_PRIVS.split()), self.read_state()["roles"]["FCOSAgentISO"])

    def test_refuses_to_change_a_role_someone_else_holds(self):
        # A same-named role the user grants elsewhere is not the agent's to rewrite.
        for role, args, extra in (("FCOSAgentVM", (), {}),
                                  ("FCOSAgentISO", ("--iso-storage", "local"),
                                   dict(storages=["local-lvm", "local"], storage_content={"local": "iso,import"}))):
            with self.subTest(role=role):
                self.log_path.unlink(missing_ok=True)
                state = full_state(**extra)
                state["roles"] = dict(state["roles"], **{role: "Sys.Audit"})
                state["acls"] = state["acls"] + [["/vms/100", "user", "owner@pam", role],
                                                 ["/vms/101", "token", "owner@pam!ci", role]]
                for mode in ((), ("--check",)):
                    result = self.setup(*args, *mode, state=state)
                    self.assertEqual(1, result.returncode, result.stdout + result.stderr)
                    for needle in ("owner@pam on /vms/100", "owner@pam!ci on /vms/101", role):
                        self.assertIn(needle, result.stderr)
                    self.assertNotIn("Rename", result.stderr)  # Proxmox roles can't be renamed
                    self.assertNotIn("done:", result.stdout)
                    self.assertNoWrites()

    def test_shared_role_with_the_right_privileges_is_used_as_is(self):
        state = full_state()
        state["acls"] = state["acls"] + [["/vms/100", "group", "admins", "FCOSAgentVM"]]
        result = self.setup(state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], [w for w in self.writes() if w[1] == "role"])
        self.assertIn("group admins on /vms/100", result.stderr)
        self.assertIn("teardown will keep it", result.stderr)

    def test_without_iso_storage_reports_upload_grants_left_from_before(self):
        state = full_state(storages=["local-lvm", "local"], storage_content={"local": "iso,import"},
                           acls=acls_for() + iso_acls())
        state["roles"] = dict(state["roles"], FCOSAgentISO=",".join(ISO_PRIVS.split()))
        for mode in (("--check",), ()):
            result = self.setup(*mode, state=state)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("cannot upload", result.stdout)
            self.assertIn("still holds FCOSAgentISO on:", result.stdout)
            # The exact commands that remove just those grants.
            self.assertIn("pveum acl delete /storage/local --roles FCOSAgentISO --users " + USER, result.stdout)
            self.assertIn(f"pveum acl delete /storage/local --roles FCOSAgentISO --tokens '{KEYID}'", result.stdout)
        # Moving to another upload storage leaves the old grant: say so too.
        state["storages"] = ["local-lvm", "local", "isos"]
        state["storage_content"] = {"local": "iso,import", "isos": "iso,import"}
        result = self.setup("--iso-storage", "isos", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("still holds FCOSAgentISO on:", result.stdout)
        self.assertIn("pveum acl delete /storage/local --roles FCOSAgentISO", result.stdout)
        self.assertNotIn("pveum acl delete /storage/isos", result.stdout)

    def test_iso_check_mode_changes_nothing(self):
        state = iso_host()
        result = self.setup("--iso-storage", "local", "--check", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNoWrites()
        self.assertEqual(state, self.read_state())
        self.assertIn("FCOSAgentISO", result.stdout)

    def test_bash_strict_and_no_history_expansion(self):
        for path in (SETUP, TEARDOWN, DISCOVER):
            lines = path.read_text().splitlines()
            self.assertEqual("#!/usr/bin/env bash", lines[0], path.name)
            self.assertIn("set -euo pipefail", lines, path.name)
        for path in (SETUP, TEARDOWN, LIB, DISCOVER):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if line.lstrip().startswith("#"):
                    continue
                self.assertEqual([], double_quoted_bangs(line), f"{path.name}:{number}: {line}")
        lib = LIB.read_text()
        self.assertIn("KEY_ID='" + KEYID + "'", lib)
        for path in (SETUP, TEARDOWN, LIB):
            for number, line in enumerate(path.read_text().splitlines(), start=1):
                if "!fcos-bootstrap" in line and not line.lstrip().startswith("#"):
                    self.assertIn("'" + KEYID + "'", line, f"{path.name}:{number}")


def double_quoted_bangs(line):
    """Return `!` characters that sit inside double quotes (not single-quoted)."""
    found, quote, index = [], None, 0
    while index < len(line):
        char = line[index]
        if char == "\\" and quote != "'":
            index += 2
            continue
        if quote is None and char in "\"'":
            quote = char
        elif quote == char:
            quote = None
        elif quote == '"' and char == "!":
            found.append(index)
        index += 1
    return found


class StrictStubTests(HostScriptCase):
    """The stubs must refuse what the real tools refuse (per the Proxmox man pages)."""

    def stub(self, *argv):
        self.write_state(HOST_FACTS)
        env = dict(os.environ, STUB_STATE=str(self.state_path), STUB_LOG=str(self.log_path))
        return subprocess.run([str(STUBS / argv[0]), *argv[1:]], capture_output=True, text=True, env=env)

    def test_pvesm_status_rejects_output_format(self):
        # The exact call that failed on the user's host.
        result = self.stub("pvesm", "status", "--output-format", "json")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Unknown option: output-format", result.stderr)
        self.assertEqual(0, self.stub("pvesm", "status", "--storage", "local-lvm").returncode)

    def test_pvesh_get_accepts_format_options_and_path_parameters(self):
        for argv in (("get", "/nodes/n/storage", "--output-format", "json"),
                     ("get", "/nodes/n/network", "--type", "bridge", "--output-format", "json"),
                     ("get", "/pools/fcos-agent", "--output-format", "json")):
            with self.subTest(argv=argv):
                state = dict(HOST_FACTS, pools={"fcos-agent": []})
                self.state_path.write_text(json.dumps(state))
                env = dict(os.environ, STUB_STATE=str(self.state_path))
                result = subprocess.run([str(STUBS / "pvesh"), *argv], capture_output=True, text=True, env=env)
                self.assertEqual(0, result.returncode, result.stderr)
                json.loads(result.stdout)

    def test_pvesh_get_rejects_options_the_path_does_not_have(self):
        for argv in (("get", "/nodes/n/storage", "--type", "bridge"),
                     ("get", "/nodes/n/network", "--storage", "x"),
                     ("get", "/access/acl", "--output-format", "json", "--bogus", "1"),
                     ("get", "/access/roles", "--poolid", "x")):
            with self.subTest(argv=argv):
                result = self.stub("pvesh", *argv)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("Unknown option: ", result.stderr)

    def test_pvesh_get_without_output_format_is_not_json(self):
        result = self.stub("pvesh", "get", "/nodes/n/storage")
        self.assertEqual(0, result.returncode)
        with self.assertRaises(ValueError):
            json.loads(result.stdout)

    def test_pveum_rejects_options_the_man_page_does_not_list(self):
        for argv in (("pool", "list", "--output-format", "json"),
                     ("user", "add", USER, "--bogus", "1"),
                     ("pool", "add", "p", "--output-format", "json"),
                     ("acl", "modify", "/pool/p", "--role", "R", "--users", USER),
                     ("role", "add", "R", "--privilege", "VM.Audit"),
                     ("user", "token", "add", USER, "t", "--privsep", "1", "--bogus", "1")):
            with self.subTest(argv=argv):
                result = self.stub("pveum", *argv)
                self.assertNotEqual(0, result.returncode)
                self.assertTrue("Unknown option: " in result.stderr or "unsupported command" in result.stderr,
                                result.stderr)

    def test_pveum_requires_roles_for_acl_changes(self):
        result = self.stub("pveum", "acl", "modify", "/pool/p", "--users", USER)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("roles", result.stderr)


class HelperTests(unittest.TestCase):
    def test_double_quoted_bangs_detects_only_double_quotes(self):
        self.assertEqual([], double_quoted_bangs("x='a!b'"))
        self.assertEqual([], double_quoted_bangs('[[ -n "$a" && ! -n "$b" ]]'))
        self.assertEqual([4], double_quoted_bangs('x="a!b"'))


def teardown_state(**overrides):
    state = full_state(pools={"fcos-agent": [101, 102], "keep": []})
    state.update(overrides)
    return state


class TeardownTests(HostScriptCase):
    def teardown(self, *args, state=None):
        return self.run_script(TEARDOWN, *args, state=state)

    def test_teardown_refuses_with_members(self):
        result = self.teardown(state=teardown_state())
        self.assertEqual(1, result.returncode)
        self.assertIn("101", result.stderr)
        self.assertIn("102", result.stderr)
        self.assertIn("--move-to", result.stderr)
        self.assertNoWrites()

    def test_teardown_moves_then_removes(self):
        result = self.teardown("--move-to", "keep", state=teardown_state())
        self.assertEqual(0, result.returncode, result.stderr)
        writes = self.writes()
        self.assertEqual(["pveum", "pool", "modify", "keep", "--vms", "101,102", "--allow-move", "1"], writes[0])
        acl_deletes = [w for w in writes if w[1:3] == ["acl", "delete"]]
        self.assertEqual(6, len(acl_deletes))
        self.assertEqual({tuple(c) for c in acl_deletes if "--users" in c},
                         {("pveum", "acl", "delete", path, "--roles", role, "--users", USER)
                          for path, role in (("/pool/fcos-agent", "FCOSAgentVM"), ("/storage/local-lvm", "PVEDatastoreUser"),
                                             ("/sdn/zones/localnetwork/vmbr0", "PVESDNUser"))})
        self.assertEqual(3, len([c for c in acl_deletes if c[-2:] == ["--tokens", KEYID]]))
        tail = [w for w in writes if w[1:3] != ["acl", "delete"]]
        self.assertEqual([
            ["pveum", "pool", "modify", "keep", "--vms", "101,102", "--allow-move", "1"],
            ["pveum", "user", "token", "remove", USER, "fcos-bootstrap"],
            ["pveum", "user", "delete", USER],
            ["pveum", "role", "delete", "FCOSAgentVM"],
            ["pveum", "pool", "delete", "fcos-agent"],
        ], tail)
        self.assertEqual(writes[1:7], acl_deletes)
        self.assertEqual(["pveum", "pool", "delete", "fcos-agent"], writes[-1])
        state = self.read_state()
        self.assertEqual([101, 102], sorted(state["pools"]["keep"]))
        self.assertNotIn("fcos-agent", state["pools"])
        self.assertEqual([], state["acls"] + state["users"] + state["tokens"] + list(state["roles"]))
        self.assertIn(f"rm -f <workspace>/secrets/proxmox-{HOST}.token", result.stdout)

    def test_teardown_names_the_workspace_token_file(self):
        result = self.teardown("--move-to", "keep", "--host-key", "mini-1", state=teardown_state())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("rm -f <workspace>/secrets/proxmox-mini-1.token", result.stdout)

    def test_teardown_missing_target_pool(self):
        state = teardown_state(pools={"fcos-agent": [101]})
        result = self.teardown("--move-to", "keep", state=state)
        self.assertEqual(1, result.returncode)
        self.assertIn("--create-pool", result.stderr)
        self.assertNoWrites()
        self.log_path.unlink()
        result = self.teardown("--move-to", "keep", "--create-pool", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        writes = self.writes()
        self.assertEqual(["pveum", "pool", "add", "keep"], writes[0][:4])
        self.assertEqual(["pveum", "pool", "modify", "keep", "--vms", "101", "--allow-move", "1"], writes[1])

    def test_teardown_check_changes_nothing(self):
        state = teardown_state()
        result = self.teardown("--move-to", "keep", "--check", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNoWrites()
        self.assertEqual(state, self.read_state())
        self.assertIn("would", result.stdout)

    def test_teardown_idempotent(self):
        self.assertEqual(0, self.teardown("--move-to", "keep", state=teardown_state()).returncode)
        self.log_path.unlink()
        again = self.teardown("--move-to", "keep", state=KEEP)
        self.assertEqual(0, again.returncode, again.stderr)
        self.assertIn("nothing to remove", again.stdout)
        self.assertNoWrites()

    def test_teardown_finishes_a_partial_teardown(self):
        state = dict(HOST_FACTS, pools={"fcos-agent": []}, roles={"FCOSAgentVM": "VM.Audit"}, users=[USER])
        result = self.teardown(state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([["pveum", "user", "delete", USER], ["pveum", "role", "delete", "FCOSAgentVM"],
                          ["pveum", "pool", "delete", "fcos-agent"]], self.writes())

    def test_teardown_removes_iso_role(self):
        state = teardown_state(storages=["local-lvm", "local"], acls=acls_for() + iso_acls())
        state["roles"] = dict(state["roles"], FCOSAgentISO=",".join(ISO_PRIVS.split()))
        result = self.teardown("--move-to", "keep", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        writes = self.writes()
        acl_deletes = [w for w in writes if w[1:3] == ["acl", "delete"]]
        self.assertEqual(8, len(acl_deletes))
        role_deletes = [w for w in writes if w[1:3] == ["role", "delete"]]
        self.assertEqual([["pveum", "role", "delete", "FCOSAgentVM"], ["pveum", "role", "delete", "FCOSAgentISO"]],
                         role_deletes)
        self.assertGreater(writes.index(role_deletes[-1]), writes.index(acl_deletes[-1]))
        state = self.read_state()
        self.assertEqual({}, state["roles"])
        self.assertEqual([], state["acls"])

    def test_teardown_keeps_a_role_someone_else_holds(self):
        state = teardown_state(storages=["local-lvm", "local"],
                               acls=acls_for() + [["/vms/100", "user", "owner@pam", "FCOSAgentVM"]])
        result = self.teardown("--move-to", "keep", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(["pveum", "role", "delete", "FCOSAgentVM"], self.writes())
        self.assertIn("owner@pam", result.stderr)
        state = self.read_state()
        self.assertIn("FCOSAgentVM", state["roles"])
        self.assertEqual([["/vms/100", "user", "owner@pam", "FCOSAgentVM"]], state["acls"])

    def test_teardown_check_and_iso_role_with_shared_roles(self):
        state = teardown_state(storages=["local-lvm", "local"],
                               acls=acls_for() + iso_acls() + [["/vms/9", "group", "ops", "FCOSAgentISO"]])
        state["roles"] = dict(state["roles"], FCOSAgentISO=",".join(ISO_PRIVS.split()))
        result = self.teardown("--move-to", "keep", "--check", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("would: remove role FCOSAgentISO", result.stdout)
        self.assertIn("would: remove role FCOSAgentVM", result.stdout)
        self.assertNoWrites()
        result = self.teardown("--move-to", "keep", state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn(["pveum", "role", "delete", "FCOSAgentISO"], self.writes())

    def test_teardown_nothing_left_but_a_kept_role_says_so(self):
        state = dict(HOST_FACTS, pools={}, roles={"FCOSAgentVM": "Sys.Audit"}, users=[],
                     acls=[["/vms/1", "user", "owner@pam", "FCOSAgentVM"]])
        result = self.teardown(state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNoWrites()
        self.assertIn("nothing to remove", result.stdout)
        self.assertIn("kept", result.stdout)

    def test_teardown_removes_leftover_iso_role_alone(self):
        state = dict(HOST_FACTS, pools={}, roles={"FCOSAgentISO": "Datastore.Audit"}, users=[])
        result = self.teardown(state=state)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([["pveum", "role", "delete", "FCOSAgentISO"]], self.writes())
        self.assertNotIn("nothing to remove", result.stdout)

    def test_teardown_usage_errors(self):
        for args in (("--create-pool",), ("--move-to",), ("--move-to", "fcos-agent"), ("--bogus",)):
            with self.subTest(args=args):
                self.assertIn(self.teardown(*args, state=teardown_state()).returncode, (1, 2))
        self.assertNoWrites()
        self.assertEqual(2, self.teardown("--create-pool", state=teardown_state()).returncode)
        self.assertEqual(2, self.teardown("--bogus", state=teardown_state()).returncode)

    def test_teardown_refuses_non_root(self):
        if os.geteuid() == 0:
            self.skipTest("running as root")
        self.assertEqual(1, self.run_script(TEARDOWN, "--move-to", "keep", nonroot_ok=False).returncode)
        self.assertEqual([], self.calls())


DISCOVER = SKILLS / "adapter-proxmox" / "scripts" / "discover-host.sh"

DISCOVERY_STATE = {
    "storages": ["local", "local-lvm", "nas"],
    "storage_info": {"local": {"total": 100 * 2**30, "avail": 80 * 2**30, "content": "iso,import,backup"},
                     "local-lvm": {"type": "lvmthin", "total": 300 * 2**30, "avail": 250 * 2**30,
                                   "content": "images,rootdir"},
                     "nas": {"type": "cifs", "total": 2**40, "avail": 2**39, "content": "backup"}},
    "storage_config": {"local": {"type": "dir", "path": "/var/lib/vz", "content": "iso,import,backup",
                                 "content-dirs": "import=custom/import"},
                       "local-lvm": {"type": "lvmthin", "vgname": "pve", "thinpool": "data", "content": "images"},
                       "nas": {"type": "cifs", "server": "192.0.2.50", "share": "backup", "username": "svc-backup",
                               "password": "stub-not-a-secret", "content": "backup"}},
    "interfaces": [{"iface": "vmbr0", "type": "bridge", "active": 1, "comments": "WAN", "bridge_ports": "enp1s0",
                    "cidr": "198.51.100.2/24"},
                   {"iface": "vmbr9", "type": "bridge", "active": 1, "comments": "LAN", "bridge_ports": "enp2s0",
                    "bridge_vlan_aware": 1, "bridge_vids": "2-4094", "mtu": 9000}],
    "node_status": {"cpuinfo": {"model": "Example CPU N100", "sockets": 1, "cores": 4, "cpus": 4},
                    "memory": {"total": 16 * 2**30, "available": 12 * 2**30, "used": 4 * 2**30, "free": 11 * 2**30},
                    "pveversion": "pve-manager/9.2.21"},
    "guests": {"qemu": [{"vmid": 100, "name": "router", "status": "running", "maxmem": 2**31, "cpus": 2,
                         "config": {"name": "router", "net0": "virtio=BC:24:11:00:00:01,bridge=vmbr9,tag=30,mtu=9000",
                                    "net1": "virtio=BC:24:11:00:00:02,bridge=vmbr0", "cores": 2,
                                    "memory": "current=2048", "cipassword": "stub-not-a-secret",
                                    "onboot": 1, "startup": "order=1,up=60"}},
                        {"vmid": 102, "name": "tools", "status": "stopped",
                         "config": {"name": "tools", "net0": "virtio=BC:24:11:00:00:04,bridge=vmbr9,tag=15",
                                    "cores": 1, "sockets": 2, "memory": "4096"}},
                        # A template never runs: listed, not counted.
                        {"vmid": 900, "name": "tmpl", "status": "stopped", "template": 1,
                         "config": {"name": "tmpl", "cores": 4, "memory": "8192", "template": 1}}],
               "lxc": [{"vmid": 101, "name": "dns", "status": "stopped",
                        "config": {"hostname": "dns", "net0": "name=eth0,bridge=vmbr9,tag=30,hwaddr=BC:24:11:00:00:03"}},
                       {"vmid": 103, "name": "web", "status": "running",
                        "config": {"hostname": "web", "cores": 1, "memory": 256}},
                       {"vmid": 104, "status": "stopped", "config": {}}]},
}


class DiscoverTests(HostScriptCase):
    """discover-host.sh: read-only facts for the agent's recommendations."""

    def discover(self, *args, state=None, nonroot_ok=True):
        tools = self.tmp / "tools"
        tools.mkdir(exist_ok=True)
        # Read-only system tools the script also uses, as fixed-output fakes that log their calls.
        for name, output in (("lsblk", "NAME TYPE SIZE ROTA TRAN MODEL\nsda disk 476.9G 0 sata Example SSD\n"
                                       "└─sda3 part 475G 0\n  └─pve-data_tdata lvm 300G 0\n"),
                             ("pvs", "  /dev/sda3 pve lvm2 475.00g 16.00g\n"),
                             ("lvs", "  data pve twi-aotz-- 300.00g 12.50\n")):
            script = tools / name
            if script.exists():
                continue  # a test replaced it
            script.write_text("#!/bin/sh\nprintf '%s\\n' \"[\\\"" + name + "\\\"]\" >> \"$STUB_LOG\"\n"
                              f"cat <<'EOF'\n{output}EOF\n")
            script.chmod(0o755)
        sysfs = self.tmp / "sys" / "devices" / "system" / "node"
        (sysfs / "node0").mkdir(parents=True, exist_ok=True)
        proc = self.tmp / "proc"
        proc.mkdir(exist_ok=True)
        (proc / "cpuinfo").write_text("processor\t: 0\nflags\t\t: fpu sse4_2 aes avx2 pcid\n\n"
                                      "processor\t: 1\nflags\t\t: fpu sse4_2 aes avx2 pcid\n")
        self.write_state(DISCOVERY_STATE if state is None else state)
        env = dict(os.environ, PATH=f"{tools}:{STUBS}:{os.environ['PATH']}", STUB_STATE=str(self.state_path),
                   STUB_LOG=str(self.log_path), FCOS_TEST_SYSFS=str(self.tmp / "sys"),
                   FCOS_TEST_PROC=str(self.tmp / "proc"))
        env.pop("FCOS_ALLOW_NONROOT", None)
        if nonroot_ok:
            env["FCOS_ALLOW_NONROOT"] = "1"
        return subprocess.run(["bash", str(DISCOVER), "--node", "testnode", *args], capture_output=True,
                              text=True, env=env, cwd=self.tmp)

    def test_reports_the_facts_recommendations_need(self):
        result = self.discover()
        self.assertEqual(0, result.returncode, result.stderr)
        out = result.stdout
        for needle in ("9.2.21", "Example CPU N100", "sockets=1", "cores=4", "cpus=4", "numa_nodes=1",
                       "memory_total_mib=16384", "memory_available_mib=12288",
                       "sda disk 476.9G 0 sata", "/dev/sda3 pve", "data pve",
                       "storage=local-lvm", "type=lvmthin", "vgname=pve", "thinpool=data", "avail_gib=250",
                       "content=images,rootdir", "path=/var/lib/vz",
                       # a changed folder layout moves the import folder (wiki Storage: Directory)
                       "content-dirs=import=custom/import",
                       "iface=vmbr9", "bridge_vlan_aware=1", "bridge_vids=2-4094", "mtu=9000", "comments=LAN",
                       "vmid=100", "name=router", "net0=virtio=BC:24:11:00:00:01,bridge=vmbr9,tag=30,mtu=9000",
                       "vmid=101", "hostname=dns",
                       # VM settings need the host's CPU flags and other VMs' start order.
                       "cpu_flags=fpu sse4_2 aes avx2 pcid", "startup=order=1,up=60", "onboot=1"):
            self.assertIn(needle, out)
        self.assertEqual(out.count("cpu_flags="), 1)
        # Every guest counted as running, stopped ones too (API schema defaults: memory 512;
        # VM cores 1 x sockets 1; a container without a core limit may use all cores):
        # memory router 2048 + tools 4096 + dns 512 + web 256 + vmid 104 512 = 7424 MiB (template 900
        # not counted); cores router 2 + tools 1x2 + web 1 = 5; dns and vmid 104 have no core limit.
        self.assertIn("all_guests_memory_mib=7424", out)
        self.assertIn("free_memory_if_all_run_mib=8960", out)  # 16384 - 7424, before Proxmox's own share
        self.assertIn("assigned_cores=5 host_cpus=4", out)    # cores are shared, not used up
        self.assertIn("no_core_limit=dns,vmid 104", out)
        self.assertIn("templates_not_counted=tmpl", out)

    def test_only_reads(self):
        self.discover()
        for call in self.calls():
            if call[0] == "pvesh":
                self.assertEqual("get", call[1], call)
            else:
                self.assertIn(call[0], ("lsblk", "pvs", "lvs"), call)
        self.assertNoWrites()
        self.assertEqual([], [c for c in self.calls() if c[0] in ("pveum", "pvesm", "qm", "pct")])

    def test_never_prints_credentials(self):
        result = self.discover()
        out = result.stdout + result.stderr
        for secretish in ("stub-not-a-secret", "svc-backup", "password", "username", "cipassword"):
            self.assertNotIn(secretish, out)

    def test_needs_root_and_validates_the_node(self):
        result = self.discover(nonroot_ok=False)
        if os.geteuid() != 0:
            self.assertEqual(1, result.returncode)
            self.assertIn("root", result.stderr)
        result = self.run_script(DISCOVER, "--node", "<node>", state=DISCOVERY_STATE)
        self.assertEqual(1, result.returncode)
        self.assertIn("placeholder", result.stderr)
        self.assertEqual(2, self.run_script(DISCOVER, "--bogus", state=DISCOVERY_STATE).returncode)

    def test_says_where_to_put_the_output(self):
        self.assertIn("hosts/", self.discover().stdout)

    def test_a_failed_listing_never_ends_in_done(self):
        # An empty guest or storage list must not pass as "none there".
        for path in ("/nodes/testnode/qemu", "/nodes/testnode/lxc", "/nodes/testnode/storage"):
            with self.subTest(path=path):
                state = dict(DISCOVERY_STATE, fail_paths=[path])
                result = self.discover(state=state)
                self.assertNotEqual(0, result.returncode, result.stdout)
                self.assertNotIn("Nothing was changed", result.stdout)

    def test_lvm_report_failure_does_not_stop_the_rest(self):
        self.discover()  # creates the fake tools
        (self.tmp / "tools" / "pvs").write_text("#!/bin/sh\necho 'WARNING: duplicate PV' >&2\nexit 5\n")
        result = self.discover()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("(pvs failed", result.stdout)
        self.assertIn("iface=vmbr9", result.stdout)


if __name__ == "__main__":
    unittest.main()
