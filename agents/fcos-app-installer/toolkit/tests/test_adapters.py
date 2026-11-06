"""Provider adapters: the owner's steps for systems the agent doesn't touch."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from adapters import (ROLE_STEPS, AdapterError, draft_adapter, load_adapter,  # noqa: E402
                      render_step)
from layout import SKILLS, SKILLS_DIR  # noqa: E402

ADAPTERS = SKILLS
PROXMOX = ADAPTERS / "adapter-proxmox"
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None
KNOWN = {"virtualization": "proxmox", "router_firewall": "opnsense", "file_server": "truenas",
         "dns_certificates": "duckdns"}


def every_value(adapter, step_id) -> dict:
    """Example values for every placeholder the step uses (the tool fills in the derived ones)."""
    from adapters import derived_keys, example_value
    skip = derived_keys(adapter)
    return {key: example_value(key) for key in adapter["owner_steps"][step_id].get("uses", []) if key not in skip}


class AcmeDataTests(unittest.TestCase):
    """The DNS adapter says how a certificate client proves the domain through that provider; the
    ingress module reads it, so no provider is written into any proxy template."""

    def site(self, provider):
        return {"roles": {"dns_certificates": {"provider": provider}}}

    def test_the_dns_adapter_carries_the_certificate_provider_data(self):
        acme = load_adapter("dns_certificates", "duckdns")["acme"]
        self.assertEqual(acme["provider"], "duckdns")
        self.assertEqual(acme["env"], "DUCKDNS_TOKEN")
        self.assertEqual(acme["store_as"], "duckdns_token")
        self.assertTrue(acme["notes"])

    def test_acme_data_is_read_for_the_provider_the_site_names(self):
        from adapters import acme_data
        self.assertEqual(acme_data(self.site("duckdns")), load_adapter("dns_certificates", "duckdns")["acme"])

    def test_no_provider_chosen_is_an_error_that_says_what_to_do(self):
        from adapters import acme_data
        for site in ({}, {"roles": {}}, self.site("ASK"), self.site(None)):
            with self.subTest(site=site), self.assertRaises(AdapterError) as caught:
                acme_data(site)
            self.assertIn("roles.dns_certificates.provider", str(caught.exception))

    def test_an_adapter_without_acme_data_is_named(self):
        from adapters import acme_data
        with self.assertRaises(AdapterError) as caught:
            acme_data(self.site("generic"))
        self.assertIn("acme", str(caught.exception))

    def test_notes_with_a_placeholder_and_system_variables_are_refused(self):
        from adapters import _check_adapter
        base = load_adapter("dns_certificates", "duckdns")
        base = {k: v for k, v in base.items() if k not in ("generic", "skill_dir")}
        for bad in (dict(base["acme"], notes="x {{DOMAIN}} y"), dict(base["acme"], env="LD_PRELOAD"),
                    dict(base["acme"], env="PATH"), dict(base["acme"], env="HOME")):
            with self.subTest(acme=bad), self.assertRaises(AdapterError):
                _check_adapter(dict(base, acme=bad), "dns_certificates", "duckdns")

    def test_acme_is_checked_and_only_for_the_dns_role(self):
        from adapters import _check_adapter
        base = load_adapter("dns_certificates", "duckdns")
        base = {k: v for k, v in base.items() if k not in ("generic", "skill_dir")}
        for bad in ({"provider": "x"}, {"provider": "x y", "env": "T", "store_as": "s"},
                    {"provider": "x", "env": "lower", "store_as": "s"},
                    {"provider": "x", "env": "T", "store_as": "Bad Name"}, "text"):
            with self.subTest(acme=bad), self.assertRaises(AdapterError):
                _check_adapter(dict(base, acme=bad), "dns_certificates", "duckdns")
        file_server = load_adapter("file_server", "truenas")
        file_server = {k: v for k, v in file_server.items() if k not in ("generic", "skill_dir")}
        with self.assertRaises(AdapterError):
            _check_adapter(dict(file_server, acme=base["acme"]), "file_server", "truenas")


class AdapterTests(unittest.TestCase):
    def test_role_steps_are_the_planned_ones(self):
        self.assertEqual(ROLE_STEPS, {
            "virtualization": ["download_image", "copy_ignition_snippet", "rebuild_os_disk", "create_api_access"],
            "router_firewall": ["reserve_ip", "dns_wildcard", "allow_flows"],
            "file_server": ["nfs_export", "service_user", "backup_folder"],
            "dns_certificates": ["api_token", "acme_provider"],
        })

    def test_every_adapter_has_role_steps(self):
        for role, provider in KNOWN.items():
            with self.subTest(role=role):
                adapter = load_adapter(role, provider)
                self.assertEqual((adapter["role"], adapter["provider"]), (role, provider))
                self.assertFalse(adapter.get("generic"))
                for step in ROLE_STEPS[role]:
                    self.assertIn(step, adapter["owner_steps"])
                    self.assertTrue(render_step(adapter, step, every_value(adapter, step)))
                self.assertTrue(adapter["docs"], "official doc links")
        for role in ROLE_STEPS:
            with self.subTest(generic=role):
                adapter = load_adapter(role, None)
                for step in ROLE_STEPS[role]:
                    self.assertTrue(render_step(adapter, step, every_value(adapter, step)))

    def test_unknown_provider_falls_back_to_generic(self):
        adapter = load_adapter("router_firewall", "pfsense")
        self.assertTrue(adapter["generic"])
        self.assertEqual(adapter["provider"], "pfsense")
        self.assertEqual(sorted(adapter["owner_steps"]), sorted(ROLE_STEPS["router_firewall"]))
        text = render_step(adapter, "reserve_ip", every_value(adapter, "reserve_ip"))
        self.assertNotIn("OPNsense", text)

    def test_agent_folder_and_checksums_come_from_where_the_agent_is(self):
        # Never typed in by hand: the step tool knows where it is installed, and
        # hashes the scripts it ships, so moving the agent keeps the steps right.
        import hashlib
        adapter = load_adapter("virtualization", "proxmox")
        for step, scripts in (("discover_host", ("lib.sh", "discover-host.sh")),
                              ("create_api_access", ("lib.sh", "setup-agent-access.sh", "teardown-agent-access.sh"))):
            with self.subTest(step=step):
                text = render_step(adapter, step, every_value(adapter, step))
                self.assertIn(f"{PROXMOX}/scripts/", text)
                for name in scripts:
                    digest = hashlib.sha256((PROXMOX / "scripts" / name).read_bytes()).hexdigest()
                    self.assertIn(f"{digest} {name}", text)

    def test_copied_files_are_the_hashed_files(self):
        # Every file a step copies from the agent's folder is a listed script, and
        # every "<checksum> <name>" pair names the script that checksum is taken from.
        import re as _re
        from adapters import _checksum_key
        for role, provider in list(KNOWN.items()) + [(r, None) for r in ROLE_STEPS]:
            adapter = load_adapter(role, provider)
            listed = set(adapter.get("scripts", []))
            for step_id, step in adapter["owner_steps"].items():
                for block in step.get("blocks", []):
                    with self.subTest(role=role, step=step_id):
                        self.assertNotIn("{{AGENT_REPO}}/", block["code"])  # scripts come from the skill
                        for path in _re.findall(r"\{\{SKILL_DIR\}\}/(\S+)", block["code"]):
                            self.assertIn(path, listed)
                        pairs = _re.findall(r"\{\{([A-Z][A-Z0-9]*_SHA256)\}\}\s+(\S+)", block["code"])
                        # Every checksum placeholder is in a pair this test checks.
                        self.assertEqual(len(pairs), len(_re.findall(r"\{\{[A-Z0-9_]*_SHA256\}\}", block["code"])))
                        for key, name in pairs:
                            self.assertEqual(_checksum_key(name), key)
                            self.assertIn(name, {Path(p).name for p in listed})

    def test_hand_typed_checksums_refused_everywhere(self):
        # A drafted adapter ships no scripts, so a *_SHA256 it uses can't be filled in.
        draft = {"role": "virtualization", "provider": "x", "name": "X", "scripts": [], "owner_steps": {
            "s": {"title": "t", "steps": ["a"], "uses": ["X_SHA256"],
                  "blocks": [{"machine": "x (bash, root)", "code": "echo {{X_SHA256}}"}]}}}
        with self.assertRaises(AdapterError) as caught:
            render_step(draft, "s", {"X_SHA256": "deadbeef"})
        self.assertIn("checksum", str(caught.exception))

    def test_script_names_checked_when_the_adapter_loads(self):
        from adapters import _check_scripts
        for scripts, needle in ((["scripts/lib.sh", "scripts/lib-extra.sh"], "two scripts"),
                                (["scripts/2fa.sh"], "name")):
            with self.subTest(scripts=scripts), self.assertRaises(AdapterError) as caught:
                _check_scripts(scripts, "test")
            self.assertIn(needle, str(caught.exception))

    def test_token_steps_name_the_workspace_token_file_and_can_replace_it(self):
        adapter = load_adapter("virtualization", "proxmox")
        values = every_value(adapter, "create_api_access")
        text = render_step(adapter, "create_api_access", values)
        runs = [line for line in text.splitlines() if "bash setup-agent-access.sh" in line]
        self.assertEqual(len(runs), 4, runs)  # check, apply, check a replacement, replace
        for line in runs:
            self.assertIn(f"--host-key {values['HOST']}", line)
        self.assertEqual(sum("--rotate" in line for line in runs), 2)
        self.assertTrue(any("--rotate" in l and "--check" in l for l in runs))
        teardown = render_step(adapter, "teardown_api_access", every_value(adapter, "teardown_api_access"))
        lines = [line for line in teardown.splitlines() if line.startswith("bash teardown-agent-access.sh")]
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertIn("--host-key", line)

    def test_token_is_stored_in_a_step_of_its_own(self):
        # The store command is its own step in the agent's answer, not
        # part of the setup script's output.
        adapter = load_adapter("virtualization", "proxmox")
        setup = render_step(adapter, "create_api_access", every_value(adapter, "create_api_access"))
        self.assertNotIn("together with a command", setup)
        self.assertNotIn("read -s", setup)
        values = every_value(adapter, "store_api_token")
        text = render_step(adapter, "store_api_token", values)
        self.assertIn("# desktop (fish)", text)
        token_file = f"{values['WORKSPACE']}/secrets/proxmox-{values['HOST']}.token"
        self.assertIn(f"> {token_file}", text)
        self.assertIn(f"chmod 600 {token_file}", text)
        self.assertIn("read -s", text)
        key_id = re.search(r"^KEY_ID='([^']+)'", (PROXMOX / "scripts" / "lib.sh").read_text(), re.M).group(1)
        self.assertIn(f"'{key_id}='", text)  # pve.py reads one line <token id>=<secret>
        self.assertIn("set -e t", text)
        block = text.split("```fish", 1)[1].split("```", 1)[0]
        # Review: no file readable by others for a moment, and no empty token file.
        self.assertLess(block.index('test -n "$t"'), block.index("install -m 600 /dev/null"))
        self.assertLess(block.index("install -m 600 /dev/null"), block.index("printf"))
        self.assertNotIn("umask", block)  # it would stay set in the owner's shell
        self.assertNotIn("pve.py", block)  # the agent checks the token itself (guide 1.4)

    def test_host_must_be_a_workspace_key_for_the_server(self):
        # HOST names the token file and hosts/<HOST>/: it is the site file's hosts key,
        # never the server's display or node name.
        ws = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "site.yaml").write_text("hosts:\n  mini-1:\n    name: Mini One\n    node: pve-mini\n")
        values = ws / "values.json"
        tool = [sys.executable, str(ROOT / "tools" / "adapters.py"), "render", "--role", "virtualization",
                "--provider", "proxmox", "--step", "discover_host", "--values", str(values)]
        env = dict(os.environ, FCOS_WORKSPACE=str(ws))
        for host, ok in (("mini-1", True), ("pve-mini", False), ("Mini-One", False)):
            with self.subTest(host=host):
                values.write_text(json.dumps({"HOST": host, "HOST_ADDRESS": "192.0.2.21", "WORKSPACE": str(ws)}))
                result = subprocess.run(tool, capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
                if not ok:
                    self.assertIn("mini-1", result.stderr)
        # The step's own WORKSPACE wins over the remembered one.
        other = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, other, True)
        (other / "site.yaml").write_text("hosts:\n  big:\n    name: Big\n")
        values.write_text(json.dumps({"HOST": "big", "HOST_ADDRESS": "192.0.2.21", "WORKSPACE": str(other)}))
        self.assertEqual(subprocess.run(tool, capture_output=True, text=True, env=env).returncode, 0)
        # A broken or missing site file is an error message, not a crash or a silent pass.
        for text in ("hosts: [unclosed\n", None):
            with self.subTest(site=text):
                if text is None:
                    (other / "site.yaml").unlink()
                else:
                    (other / "site.yaml").write_text(text)
                result = subprocess.run(tool, capture_output=True, text=True, env=env)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("site file", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_router_flows_take_network_lists_and_cover_the_web_ports(self):
        for provider in ("opnsense", None):
            with self.subTest(provider=provider):
                router = load_adapter("router_firewall", provider)
                values = dict(every_value(router, "allow_flows"), ADMIN_LAN_CIDR="192.0.2.0/24",
                              LAN_CIDR="192.0.2.0/24,198.51.100.0/24")
                text = render_step(router, "allow_flows", values)
                self.assertIn("192.0.2.0/24, 198.51.100.0/24", text)
                self.assertIn("443", text)  # web networks to the login front end
                with self.assertRaises(AdapterError):
                    render_step(router, "allow_flows", dict(values, LAN_CIDR="0.0.0.0/0"))

    def test_network_list_never_lands_in_a_command(self):
        # Unquoted, "a, b" would split into separate arguments of the owner's command.
        step = {"role": "router_firewall", "provider": "x", "name": "X", "scripts": [], "owner_steps": {
            "s": {"title": "t", "steps": ["Allow {{LAN_CIDR}}."], "uses": ["LAN_CIDR"],
                  "blocks": [{"machine": "x (bash, root)", "code": "allow {{LAN_CIDR}}"}]}}}
        with self.assertRaises(AdapterError):
            render_step(step, "s", {"LAN_CIDR": "192.0.2.0/24, 198.51.100.0/24"})
        self.assertIn("allow 192.0.2.0/24", render_step(step, "s", {"LAN_CIDR": "192.0.2.0/24"}))

    # Review of ff605b1: the owner runs the host scripts as root, and the step shows the checksum of
    # the file as it is. The pinned list, a file the agent's rules keep it from editing, says what the file must be.
    def pinned(self, text):
        path = Path(tempfile.mkdtemp(dir=SCRATCH)) / "host-scripts.sha256"
        self.addCleanup(shutil.rmtree, path.parent, True)
        path.write_text(text)
        return path

    def render_discover(self, checksums):
        import adapters as mod
        adapter = load_adapter("virtualization", "proxmox")
        saved = mod.CHECKSUMS
        mod.CHECKSUMS = checksums
        try:
            return render_step(adapter, "discover_host", every_value(adapter, "discover_host"))
        finally:
            mod.CHECKSUMS = saved

    def real_list(self):
        import layout
        return layout.CHECKSUMS.read_text()

    def test_a_script_that_matches_the_pinned_list_renders(self):
        self.assertIn("discover-host.sh", self.render_discover(self.pinned(self.real_list())))

    def test_a_changed_host_script_is_refused(self):
        import hashlib
        wrong = hashlib.sha256(b"not the script").hexdigest()
        lines = [l.replace(l.split("  ")[0], wrong) if l.endswith("scripts/lib.sh") else l
                 for l in self.real_list().splitlines()]
        with self.assertRaisesRegex(AdapterError, "differs from the pinned checksum"):
            self.render_discover(self.pinned("\n".join(lines) + "\n"))

    def test_a_script_missing_from_the_list_is_refused_with_its_own_message(self):
        lines = [l for l in self.real_list().splitlines() if not l.endswith("scripts/lib.sh")]
        with self.assertRaises(AdapterError) as caught:
            self.render_discover(self.pinned("\n".join(lines) + "\n"))
        self.assertIn("isn't listed", str(caught.exception))
        self.assertNotIn("differs", str(caught.exception))  # not the same news as a changed script

    def test_a_changed_script_says_it_differs_not_that_it_is_unlisted(self):
        import hashlib
        wrong = hashlib.sha256(b"not the script").hexdigest()
        lines = [l.replace(l.split("  ")[0], wrong) if l.endswith("scripts/lib.sh") else l
                 for l in self.real_list().splitlines()]
        with self.assertRaises(AdapterError) as caught:
            self.render_discover(self.pinned("\n".join(lines) + "\n"))
        self.assertIn("differs", str(caught.exception))
        self.assertNotIn("isn't listed", str(caught.exception))

    def test_an_unreadable_or_malformed_list_refuses_plainly(self):
        with self.assertRaisesRegex(AdapterError, "checksum list.*can't be read"):
            self.render_discover(Path(tempfile.gettempdir()) / "no-such-list.sha256")
        with self.assertRaisesRegex(AdapterError, r"host-scripts\.sha256:1: not a sha256sum line"):
            self.render_discover(self.pinned("this is not a checksum\n"))
        # Blank lines and comments are not allowed either, and the message says so.
        with self.assertRaisesRegex(AdapterError, "no blank lines or comments"):
            self.render_discover(self.pinned("\n"))

    def test_the_list_splits_on_newlines_only_and_wants_lowercase_hex(self):
        # sha256sum -c ends a line at a newline only; a lone CR (or U+2028) joins two entries into
        # one bad line, so this tool must not split there and accept what sha256sum would not.
        lines = self.real_list().splitlines()
        joined = lines[0] + "\r" + lines[1] + "\n" + "\n".join(lines[2:]) + "\n"
        with self.assertRaisesRegex(AdapterError, r"host-scripts\.sha256:1: not a sha256sum line"):
            self.render_discover(self.pinned(joined))
        upper = lines[0].split("  ")[0].upper() + "  " + lines[0].split("  ")[1]
        with self.assertRaisesRegex(AdapterError, "lowercase hex"):
            self.render_discover(self.pinned("\n".join([upper] + lines[1:]) + "\n"))

    def odd_root(self):
        """A copy of the Proxmox skill outside the real skills folder, as a loaded root."""
        root = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, root, True)
        shutil.copytree(PROXMOX, root / "adapter-proxmox")
        return root

    def test_a_skill_outside_the_skills_folder_is_never_pinned(self):
        # A copy of an adapter loaded from some other root has no entry in the list, however
        # identical its scripts are.
        from adapters import derived_values
        root = self.odd_root()
        adapter = load_adapter("virtualization", "proxmox", root=root)
        with self.assertRaisesRegex(AdapterError, "isn't listed"):
            derived_values(adapter)

    def test_a_script_that_is_a_link_out_of_its_skill_is_refused(self):
        from adapters import derived_values
        root = self.odd_root()
        adapter = load_adapter("virtualization", "proxmox", root=root)
        script = root / "adapter-proxmox" / adapter["scripts"][0]  # the first one the check looks at
        outside = root / "elsewhere.sh"
        outside.write_text(script.read_text())
        script.unlink()
        script.symlink_to(outside)
        with self.assertRaisesRegex(AdapterError, "not a file in its skill folder"):
            derived_values(adapter)

    def test_a_list_that_is_not_text_is_refused_plainly(self):
        path = Path(tempfile.mkdtemp(dir=SCRATCH)) / "host-scripts.sha256"
        self.addCleanup(shutil.rmtree, path.parent, True)
        path.write_bytes(b"\xff\xfe\x00 not utf-8\n")
        with self.assertRaisesRegex(AdapterError, "checksum list.*can't be read"):
            self.render_discover(path)

    def test_a_line_listed_twice_is_refused_as_sha256sum_would_complain(self):
        lines = self.real_list().splitlines()
        with self.assertRaisesRegex(AdapterError, r"host-scripts\.sha256:\d+: .* is listed twice"):
            self.render_discover(self.pinned("\n".join(lines + lines[:1]) + "\n"))

    def test_the_script_check_needs_no_git(self):
        # The agent compares each script with the pinned checksum list, never with a committed copy, so it needs no git or clone.
        source = (ROOT / "tools" / "adapters.py").read_text()
        for gone in ("_git", "_committed", "_blob_hash", "rev-parse"):
            self.assertNotIn(gone, source)
        elsewhere = Path(tempfile.mkdtemp(dir=SCRATCH))  # not a checkout, and a PATH without git
        self.addCleanup(shutil.rmtree, elsewhere, True)
        code = ("import sys; sys.path.insert(0, sys.argv[1]); "
                "from adapters import derived_values, load_adapter; "
                "print(sorted(derived_values(load_adapter('virtualization', 'proxmox'))))")
        env = dict(os.environ, PATH=str(elsewhere), HOME=str(elsewhere))  # everything else as it is, git gone
        result = subprocess.run([sys.executable, "-c", code, str(ROOT / "tools")], cwd=elsewhere,
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DISCOVER_SHA256", result.stdout)

    def test_draft_needs_a_real_workspace_outside_any_skill_folder(self):
        # A draft written into a skill folder would become a
        # live skill before anyone reviewed it.
        tool = [sys.executable, str(ROOT / "tools" / "adapters.py")]
        recorded = Path(tempfile.mkdtemp(dir=SCRATCH)) / "r.json"
        self.addCleanup(shutil.rmtree, recorded.parent, True)
        recorded.write_text('[{"id": "nfs_export", "title": "Share", "steps": ["Allow {{VM_IP}}."], '
                            '"uses": ["VM_IP"]}]')
        base = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, base, True)
        for ws, needle in ((base / "no-site", "site.yaml"), (base / SKILLS_DIR, "skill"),
                           (base / ".config" / "opencode" / "skills", "skill")):
            ws.mkdir(parents=True)
            if needle == "skill":
                (ws / "site.yaml").write_text("{}\n")
            with self.subTest(ws=str(ws)):
                result = subprocess.run(tool + ["draft", "--role", "file_server", "--provider", "synology",
                                                "--from", str(recorded), "--workspace", str(ws)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(needle, result.stderr)
                self.assertFalse((ws / "adapters-draft").exists())

    def test_skill_tables_show_no_raw_placeholders(self):
        for skill in ADAPTERS.glob("adapter-*/SKILL.md"):
            with self.subTest(skill=skill.parent.name):
                self.assertNotIn("{{", skill.read_text())

    def test_skill_dir_is_derived_from_where_the_skill_is(self):
        adapter = load_adapter("virtualization", "proxmox")
        from adapters import derived_keys, derived_values
        self.assertIn("SKILL_DIR", derived_keys(adapter))
        self.assertEqual(derived_values(adapter)["SKILL_DIR"], str(PROXMOX))
        with self.assertRaises(AdapterError):
            render_step(adapter, "discover_host", dict(every_value(adapter, "discover_host"), SKILL_DIR="/x"))

    def test_derived_values_cannot_be_passed_in(self):
        adapter = load_adapter("virtualization", "proxmox")
        for key, value in (("AGENT_REPO", "/home/owner/elsewhere"), ("LIB_SHA256", "0" * 64)):
            with self.subTest(key=key), self.assertRaises(AdapterError) as caught:
                render_step(adapter, "discover_host", dict(every_value(adapter, "discover_host"), **{key: value}))
            self.assertIn("filled in by the tool", str(caught.exception))

    def test_every_checksum_a_step_uses_names_a_shipped_script(self):
        for role, provider in list(KNOWN.items()) + [(r, None) for r in ROLE_STEPS]:
            adapter = load_adapter(role, provider)
            for path in adapter.get("scripts", []):
                with self.subTest(role=role, script=path):
                    self.assertTrue((Path(adapter["skill_dir"]) / path).is_file())
            for step_id, step in adapter["owner_steps"].items():
                for key in step.get("uses", []):
                    if key.endswith("_SHA256"):
                        with self.subTest(role=role, step=step_id, key=key):
                            from adapters import derived_keys
                            self.assertIn(key, derived_keys(adapter))

    def test_discover_host_checks_then_only_reads(self):
        adapter = load_adapter("virtualization", "proxmox")
        text = render_step(adapter, "discover_host", every_value(adapter, "discover_host"))
        self.assertIn("discover-host.sh", text)
        node = text.split("(bash, root)", 1)[1]
        # The checksums are checked before the script runs, in the same command.
        self.assertLess(node.index("sha256sum -c -"), node.index("bash discover-host.sh"))
        self.assertIn("sha256sum -c - && bash discover-host.sh", node)
        for change in ("setup-agent-access", "pveum", "qm ", "pct ", "rm "):
            self.assertNotIn(change, text)
        self.assertIn("/hosts/", text)

    def test_bad_role_or_provider_name_refused(self):
        for role, provider in (("nope", None), ("virtualization", "../generic"), ("virtualization", "Prox mox")):
            with self.subTest(role=role, provider=provider), self.assertRaises(AdapterError):
                load_adapter(role, provider)

    def test_render_step_fails_on_missing_value(self):
        adapter = load_adapter("virtualization", "proxmox")
        values = every_value(adapter, "create_api_access")
        values.pop(sorted(values)[0])
        with self.assertRaises(AdapterError) as caught:
            render_step(adapter, "create_api_access", values)
        self.assertIn("missing", str(caught.exception))
        with self.assertRaises(AdapterError):
            render_step(adapter, "no_such_step", {})

    def test_render_step_refuses_values_that_could_change_a_command(self):
        adapter = load_adapter("virtualization", "proxmox")
        for bad in ("local; rm -rf /", "$(id)", "a b", "`x`", "a'b", 'a"b', "a\nb", "a|b", "a&b", "a>b",
                    "*", "/var/*", "a%s", "", "a\\b", "~root", "a?b", "[ab]", "{a,b}", "-rf", "--purge"):
            with self.subTest(bad=bad):
                values = every_value(adapter, "create_api_access")
                values[sorted(values)[0]] = bad
                with self.assertRaises(AdapterError):
                    render_step(adapter, "create_api_access", values)

    def test_every_command_block_names_its_machine_and_shell(self):
        for role, provider in list(KNOWN.items()) + [(r, None) for r in ROLE_STEPS]:
            adapter = load_adapter(role, provider)
            for step_id, step in adapter["owner_steps"].items():
                for block in step.get("blocks", []):
                    with self.subTest(role=role, provider=provider, step=step_id):
                        self.assertRegex(block["machine"], r"\((bash|fish)(, [^)]+)?\)$")
                        if block["machine"].startswith("desktop"):
                            self.assertIn("(fish", block["machine"])
                lines = render_step(adapter, step_id, every_value(adapter, step_id)).splitlines()
                for index, line in enumerate(lines):
                    if line.startswith("```") and line != "```":
                        self.assertTrue(lines[index + 1].startswith("# "), (step_id, lines[index + 1]))

    def test_proxmox_adapter_uses_setup_script(self):
        adapter = load_adapter("virtualization", "proxmox")
        setup = render_step(adapter, "create_api_access", every_value(adapter, "create_api_access"))
        self.assertIn("setup-agent-access.sh", setup)
        for flag in ("--storage", "--bridge", "--iso-storage", "--check"):
            self.assertIn(flag, setup)
        self.assertIn("sha256sum -c", setup)
        teardown = render_step(adapter, "teardown_api_access", every_value(adapter, "teardown_api_access"))
        self.assertIn("teardown-agent-access.sh --move-to", teardown)

    def test_teardown_creates_the_pool_the_vms_move_into(self):
        # An owner with no pool of their own has nowhere to move the VMs to. The script creates it with --create-pool, so the check and the
        # real run must both pass it; without it the script stops: "create it first".
        adapter = load_adapter("virtualization", "proxmox")
        teardown = render_step(adapter, "teardown_api_access", every_value(adapter, "teardown_api_access"))
        runs = [line for line in teardown.splitlines() if line.startswith("bash teardown-agent-access.sh")]
        self.assertEqual(len(runs), 2, runs)
        for line in runs:
            self.assertIn("--create-pool", line)
        self.assertIn("created if it doesn't exist", teardown)
        # The installs always move to pool backrooms, so nothing is asked.
        for line in runs:
            self.assertIn("--move-to backrooms --create-pool", line)
        self.assertNotIn("KEEP_POOL", adapter["owner_steps"]["teardown_api_access"]["uses"])

    def test_truenas_backup_folder_does_not_make_the_vm_folder_group_writable(self):
        # The VM's folder must not be group-writable ("mode 2775" for "the group of the services that
        # back up there"). Each service has its own group, so that group means nothing, and group
        # write without a sticky bit lets a member delete another service's backup folder.
        adapter = load_adapter("file_server", "truenas")
        text = render_step(adapter, "backup_folder", every_value(adapter, "backup_folder"))
        self.assertNotIn("2775", text)
        self.assertNotIn("group of the services", text)
        self.assertIn("0755", text)
        self.assertIn("not group-writable", text)
        # The service's own folder is what it writes in; the number counts, not the group's name.
        self.assertIn("UID", text)
        self.assertIn("create", text.lower())
        self.assertIn("can't create", text)

    def test_proxmox_capabilities(self):
        adapter = load_adapter("virtualization", "proxmox")
        self.assertTrue(adapter["capabilities"]["api_create_vm"])
        self.assertTrue(adapter["capabilities"]["api_upload_ignition"])
        self.assertEqual(adapter["defaults"]["ignition_method"], "nocloud-iso")
        self.assertIn("scripts/setup-agent-access.sh", adapter["scripts"])
        for path in adapter["scripts"]:
            self.assertTrue((PROXMOX / path).is_file(), path)

    def test_reserve_ip_comes_after_create_and_before_start(self):
        adapter = load_adapter("router_firewall", "opnsense")
        text = render_step(adapter, "reserve_ip", every_value(adapter, "reserve_ip")).lower()
        self.assertIn("before", text)
        self.assertIn("first start", text)
        for service in ("dnsmasq", "kea"):
            self.assertIn(service, text)

    def test_values_are_checked_by_kind(self):
        adapter = load_adapter("virtualization", "proxmox")
        base = every_value(adapter, "rebuild_os_disk")
        good = dict(base, VMID="901", VM_NAME="apps", QCOW2="fedora-coreos-44.1-proxmoxve.x86_64.qcow2",
                    STORAGE="local-lvm", ISO_STORAGE="local", SCSI0_OPTIONS="iothread=1,discard=on,ssd=1",
                    IGN_ISO_VOLUME="local:iso/fcos-apps-ign.iso", OS_DISK_GIB="20")
        self.assertIn("ssd=1", render_step(adapter, "rebuild_os_disk", good))
        for key, bad in (("QCOW2", "x.qcow2,backup=1"), ("STORAGE", "local-lvm,ssd=0"), ("VMID", "1=2")):
            with self.subTest(key=key), self.assertRaises(AdapterError):
                render_step(adapter, "rebuild_os_disk", dict(good, **{key: bad}))
        from adapters import _value_ok
        for bad in ("relative/path", "/", "/a/../etc", "/home/x:/y", "otherhost:/tmp"):
            with self.subTest(path=bad):
                self.assertFalse(_value_ok("AGENT_REPO", bad))
        self.assertTrue(_value_ok("AGENT_REPO", "/home/owner/agent"))
        router = load_adapter("router_firewall", "opnsense")
        text = render_step(router, "allow_flows", dict(every_value(router, "allow_flows"),
                                                       ADMIN_LAN_CIDR="192.0.2.0/24", VM_IP="192.0.2.40"))
        self.assertIn("192.0.2.0/24", text)
        self.assertNotIn("{{", text)

    def test_iso_volume_and_address_kinds(self):
        adapter = load_adapter("virtualization", "proxmox")
        values = every_value(adapter, "remove_vm")
        self.assertIn("pvesm free local:iso/fcos-apps-ign.iso",
                      render_step(adapter, "remove_vm", dict(values, IGN_ISO_VOLUME="local:iso/fcos-apps-ign.iso")))
        for bad in ("local-lvm:vm-100-disk-0", "local:iso/x", "local:import/x.iso", "local:iso/../x.iso"):
            with self.subTest(volume=bad), self.assertRaises(AdapterError):
                render_step(adapter, "remove_vm", dict(values, IGN_ISO_VOLUME=bad))
        values = every_value(adapter, "create_api_access")
        for bad in ("root@host", "a@b", "host:22"):
            with self.subTest(address=bad), self.assertRaises(AdapterError):
                render_step(adapter, "create_api_access", dict(values, HOST_ADDRESS=bad))
        self.assertIn("root@pve-a.example.org:", render_step(adapter, "create_api_access",
                                                            dict(values, HOST_ADDRESS="pve-a.example.org")))

    def test_remove_vm_checks_the_disc_belongs_to_the_vm(self):
        code = load_adapter("virtualization", "proxmox")["owner_steps"]["remove_vm"]["blocks"][0]["code"]
        guard = code.index('= "{{IGN_ISO_VOLUME}}" ]')
        self.assertLess(guard, code.index("--protection 0"))

    def test_scripts_report_any_failure_and_check_the_image_first(self):
        steps = load_adapter("virtualization", "proxmox")["owner_steps"]
        for step_id in ("rebuild_os_disk", "remove_vm", "download_image"):
            with self.subTest(step=step_id):
                self.assertIn("trap 'echo \"STOP: failed at line $LINENO", steps[step_id]["blocks"][0]["code"])
        rebuild = steps["rebuild_os_disk"]["blocks"][0]["code"]
        self.assertLess(rebuild.index("pvesm path {{ISO_STORAGE}}:import/$QCOW"), rebuild.index("qm shutdown"))
        self.assertLess(rebuild.index("pvesm path {{IGN_ISO_VOLUME}}"), rebuild.index("qm shutdown"))
        self.assertLess(rebuild.index('[ "$cur" != "{{IGN_ISO_VOLUME}}" ]'), rebuild.index("qm shutdown"))
        self.assertIn("xz -df", steps["download_image"]["blocks"][0]["code"])

    def test_teardown_check_and_run_are_separate_blocks(self):
        adapter = load_adapter("virtualization", "proxmox")
        for step_id in ("create_api_access", "teardown_api_access"):
            for block in adapter["owner_steps"][step_id]["blocks"]:
                runs = [line for line in block["code"].splitlines()
                        if line.startswith("bash ") and "-agent-access.sh" in line]
                with self.subTest(step=step_id, block=block["code"][:40]):
                    self.assertLessEqual(len(runs), 1, "a check and a real run must not share a block")

    def test_destructive_blocks_stop_on_every_check(self):
        adapter = load_adapter("virtualization", "proxmox")
        for step_id in ("rebuild_os_disk", "remove_vm", "download_image"):
            with self.subTest(step=step_id):
                for block in adapter["owner_steps"][step_id]["blocks"]:
                    self.assertTrue(block["code"].startswith("bash -euo pipefail <<'EOF'\n"), block["code"][:40])
                    self.assertTrue(block["code"].rstrip().endswith("EOF"))
        for step_id in ("rebuild_os_disk", "remove_vm"):
            with self.subTest(guard=step_id):
                code = adapter["owner_steps"][step_id]["blocks"][0]["code"]
                guard = code.index('= "{{VM_NAME}}" ]')
                self.assertLess(guard, code.index("--protection 0"))
        rebuild = adapter["owner_steps"]["rebuild_os_disk"]["blocks"][0]["code"]
        self.assertNotIn("sed -n \"s/^\\(unused", rebuild)  # no volume id inside a regex
        self.assertLess(rebuild.index('[ -n "$SLOT" ] ||'), rebuild.index("qm disk unlink"))
        self.assertLess(rebuild.index("grep -q '^scsi1:'"), rebuild.index("qm disk unlink"))
        download = adapter["owner_steps"]["download_image"]["blocks"][0]["code"]
        self.assertLess(download.index("sha256sum -c"), download.index("xz -d"))
        self.assertIn("rm -f", download)

    def test_bash_blocks_parse(self):
        # bash -n only parses; nothing runs. The script inside a heredoc is checked too.
        for role, provider in list(KNOWN.items()) + [(r, None) for r in ROLE_STEPS]:
            adapter = load_adapter(role, provider)
            for step_id, step in adapter["owner_steps"].items():
                from adapters import derived_values
                values = dict(every_value(adapter, step_id), **derived_values(adapter))
                for block in step.get("blocks", []):
                    if "(bash" not in block["machine"]:
                        continue
                    from render import render
                    code = render(block["code"], values)
                    parts = [code]
                    if code.startswith("bash -euo pipefail <<'EOF'\n"):
                        parts.append(code.split("\n", 1)[1].rsplit("EOF", 1)[0])
                    for part in parts:
                        with self.subTest(provider=provider, step=step_id):
                            result = subprocess.run(["bash", "-n"], input=part, capture_output=True, text=True)
                            self.assertEqual(result.returncode, 0, result.stderr)

    def test_snippet_fallback_follows_fedora_docs(self):
        adapter = load_adapter("virtualization", "proxmox")
        text = render_step(adapter, "copy_ignition_snippet", every_value(adapter, "copy_ignition_snippet"))
        self.assertIn("--ciupgrade 0", text)
        self.assertIn("hostname", text.lower())

    def test_invalid_provider_file_is_an_error_not_a_fallback(self):
        root = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "adapter-pfsense").mkdir()
        for text in ("role: [unclosed", "role: router_firewall\nprovider: pfsense\n", "\xff"):
            with self.subTest(text=text[:20]):
                (root / "adapter-pfsense" / "adapter.yaml").write_bytes(text.encode("latin-1"))
                with self.assertRaises(AdapterError):
                    load_adapter("router_firewall", "pfsense", root=root)

    def test_bad_steps_refused(self):
        for step in ({"title": "t", "steps": ["{{VM_IP}}"]},  # placeholder not in uses
                     {"title": "t", "steps": ["s"], "blocks": [{"machine": "desktop (bash)", "code": "ls"}]},
                     {"title": "t", "steps": ["s"], "blocks": [{"machine": "somewhere", "code": "ls"}]},
                     {"title": "t", "steps": ["s"], "extra": 1}):
            with self.subTest(step=step), self.assertRaises(AdapterError):
                draft_adapter("router_firewall", "pfsense", [dict(step, id="reserve_ip")])

    def test_destructive_steps_say_so(self):
        adapter = load_adapter("virtualization", "proxmox")
        for step in ("rebuild_os_disk", "remove_vm"):
            with self.subTest(step=step):
                blocks = adapter["owner_steps"][step]["blocks"]
                self.assertTrue(any("destructive" in b["machine"] for b in blocks))

    def test_draft_round_trips(self):
        recorded = [{"id": "reserve_ip", "title": "Reserve the address",
                     "steps": ["In the router's DHCP page add a reservation for {{VM_MAC}} with {{VM_IP}}."],
                     "uses": ["VM_MAC", "VM_IP"], "report_back": ["done"]}]
        text = draft_adapter("router_firewall", "pfsense", recorded)
        data = yaml.safe_load(text)
        self.assertEqual((data["role"], data["provider"]), ("router_firewall", "pfsense"))
        self.assertTrue(data["draft"])
        for step in ROLE_STEPS["router_firewall"]:
            self.assertIn(step, data["owner_steps"])
        self.assertIn("{{VM_MAC}}", data["owner_steps"]["reserve_ip"]["steps"][0])
        tmp = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "adapter-pfsense").mkdir()
        (tmp / "adapter-pfsense" / "adapter.yaml").write_text(text)
        adapter = load_adapter("router_firewall", "pfsense", root=tmp)
        self.assertFalse(adapter.get("generic"))
        self.assertIn("reservation", render_step(adapter, "reserve_ip", {"VM_MAC": "bc:24:11:00:00:01",
                                                                          "VM_IP": "192.0.2.40"}))

    def test_draft_refuses_bad_recorded_steps(self):
        for recorded in ([{"id": "Bad Id", "title": "x", "steps": ["y"]}],
                         [{"id": "reserve_ip", "title": "x", "steps": "not a list"}],
                         [{"id": "reserve_ip", "title": "x", "steps": ["{{lower}}"], "uses": ["lower"]}]):
            with self.subTest(recorded=recorded), self.assertRaises(AdapterError):
                draft_adapter("router_firewall", "pfsense", recorded)

    def test_draft_cli_writes_into_the_workspace(self):
        ws = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "site.yaml").write_text("{}\n")
        recorded = ws / "recorded.json"
        # AGENT_REPO is filled in by the tool; the drafted test must not pass it.
        recorded.write_text('[{"id": "nfs_export", "title": "Share", "steps": ["Allow {{VM_IP}} ({{AGENT_REPO}})."], '
                            '"uses": ["VM_IP", "AGENT_REPO"], "report_back": ["done"]}]')
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "adapters.py"), "draft", "--role",
                                 "file_server", "--provider", "synology", "--from", str(recorded),
                                 "--workspace", str(ws)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        folder = ws / "adapters-draft" / "adapter-synology"
        self.assertTrue((folder / "adapter.yaml").is_file())
        skill = (folder / "SKILL.md").read_text()  # a draft is a skill, ready to review and move
        self.assertTrue(skill.startswith("---\nname: adapter-synology\n"))
        self.assertIn("draft", skill.lower())
        test = folder / "test_synology.py"
        self.assertTrue(test.is_file())
        check = subprocess.run([sys.executable, str(test)], capture_output=True, text=True,
                               env=dict(os.environ, FCOS_AGENT_ROOT=str(ROOT)))
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)

    def test_show_and_render_from_the_command_line(self):
        tool = [sys.executable, str(ROOT / "tools" / "adapters.py")]
        shown = subprocess.run(tool + ["show", "--role", "router_firewall", "--provider", "opnsense"],
                               capture_output=True, text=True)
        self.assertEqual(shown.returncode, 0, shown.stderr)
        data = yaml.safe_load(shown.stdout)
        self.assertEqual(data["provider"], "opnsense")
        self.assertFalse(data["generic"])
        self.assertEqual(data["steps"]["reserve_ip"], ["VM_IP", "VM_NAME", "VM_MAC"])
        generic = subprocess.run(tool + ["show", "--role", "router_firewall", "--provider", "pfsense"],
                                 capture_output=True, text=True)
        self.assertTrue(yaml.safe_load(generic.stdout)["generic"])

        tmp = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, tmp, True)
        values = tmp / "values.json"
        values.write_text('{"VM_IP": "192.0.2.40", "VM_NAME": "apps", "VM_MAC": "bc:24:11:00:00:01"}')
        rendered = subprocess.run(tool + ["render", "--role", "router_firewall", "--provider", "opnsense",
                                          "--step", "reserve_ip", "--values", str(values)],
                                  capture_output=True, text=True)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertIn("bc:24:11:00:00:01", rendered.stdout)
        values.write_text('{"VM_IP": "192.0.2.40; rm -rf /", "VM_NAME": "apps", "VM_MAC": "x"}')
        bad = subprocess.run(tool + ["render", "--role", "router_firewall", "--provider", "opnsense",
                                     "--step", "reserve_ip", "--values", str(values)],
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(bad.stdout, "")

    def test_adapters_publishable(self):
        from publish_check import check_text
        files = sorted(ADAPTERS.glob("adapter-*/adapter.yaml"))
        self.assertGreaterEqual(len(files), 5)
        for path in files:
            with self.subTest(path=path.name):
                self.assertEqual(check_text(path.read_text(), set()), [])


if __name__ == "__main__":
    unittest.main()
