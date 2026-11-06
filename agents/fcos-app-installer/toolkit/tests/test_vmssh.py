"""tools/vmssh.py: the agent's own, revocable setup key for a VM.

The real ssh, ssh-keygen and ssh-keyscan are replaced by stubs on PATH that log
their arguments; nothing here reaches a real machine or the user's keys.
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "vmssh.py"
FP = "SHA256:abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"

STUB = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, sys
    from pathlib import Path
    name = Path(sys.argv[0]).name
    args = sys.argv[1:]
    stdin = "" if sys.stdin.isatty() else sys.stdin.read()
    with open(os.environ["STUB_LOG"], "a") as log:
        log.write(json.dumps({"cmd": name, "args": args, "stdin": stdin}) + "\\n")
    if name == "ssh-keygen" and "-f" in args and "-N" in args:
        key = Path(args[args.index("-f") + 1])
        comment = args[args.index("-C") + 1]
        key.write_text("PRIVATE-KEY-MATERIAL\\n")
        key.chmod(0o600)
        key.with_name(key.name + ".pub").write_text(f"ssh-ed25519 AAAAC3agentpub {comment}\\n")
    elif name == "ssh-keygen" and "-lf" in args:
        print(f"256 {os.environ['STUB_FP']} 192.0.2.20 (ED25519)")
    elif name == "ssh-keyscan":
        print("192.0.2.20 ssh-ed25519 AAAAC3hostkey")
    elif name == "ssh":
        counter = Path(os.environ["STUB_LOG"] + ".n")
        n = int(counter.read_text()) if counter.exists() else 0
        counter.write_text(str(n + 1))
        codes = os.environ.get("STUB_SSH_EXITS", "0").split(",")
        code = int(codes[min(n, len(codes) - 1)])
        if code == 0:
            print("remote ran: " + args[-1] + (" | stdin: " + stdin if stdin else ""))
        else:
            print(os.environ.get("STUB_SSH_STDERR", "admin@192.0.2.20: Permission denied (publickey)."), file=sys.stderr)
        sys.exit(code)
''')

SITE = textwrap.dedent('''\
    admin_user: admin
    vms:
      - name: edge
        ip: 192.0.2.20
''')


class VmSshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="vmssh-test-"))
        self.ws = self.tmp / "fcos-ws"
        (self.ws / "secrets").mkdir(parents=True)
        (self.ws / "secrets").chmod(0o700)
        (self.ws / "vms" / "edge").mkdir(parents=True)
        (self.ws / "site.yaml").write_text(SITE)
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name in ("ssh", "ssh-keygen", "ssh-keyscan"):
            (self.bin / name).write_text(STUB)
            (self.bin / name).chmod(0o755)
        self.log = self.tmp / "log.jsonl"
        self.key = self.ws / "secrets" / "agent-ssh" / "edge" / "id_ed25519"

    def tearDown(self):
        subprocess.run(["rm", "-rf", str(self.tmp)], check=False)

    def run_tool(self, *args, exits="0", fp=FP, stdin="", stderr=None):
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}", STUB_LOG=str(self.log),
                   STUB_FP=fp, STUB_SSH_EXITS=exits, SSH_AUTH_SOCK="/tmp/owner-agent.sock")
        if stderr is not None:
            env["STUB_SSH_STDERR"] = stderr
        env.pop("FCOS_WORKSPACE", None)
        r = subprocess.run([sys.executable, str(TOOL), *args, "--workspace", str(self.ws)] if "--" not in args
                           else [sys.executable, str(TOOL), *args[:args.index("--")], "--workspace", str(self.ws),
                                 *args[args.index("--"):]],
                           capture_output=True, text=True, env=env, input=stdin, timeout=60)
        return r.returncode, r.stdout, r.stderr

    def calls(self, cmd=None):
        if not self.log.exists():
            return []
        out = [json.loads(line) for line in self.log.read_text().splitlines()]
        return [c for c in out if cmd is None or c["cmd"] == cmd]

    def setup_key(self):
        self.assertEqual(self.run_tool("keygen", "edge")[0], 0)
        code, out, err = self.run_tool("trust", "edge", "--fingerprint", FP)
        self.assertEqual(code, 0, out + err)

    # keygen

    def test_keygen_makes_a_separate_key_in_secrets_and_prints_the_manual_step(self):
        code, out, err = self.run_tool("keygen", "edge")
        self.assertEqual(code, 0, err)
        self.assertTrue(self.key.is_file())
        self.assertEqual(stat.S_IMODE(self.key.parent.stat().st_mode), 0o700)
        gen = self.calls("ssh-keygen")[0]["args"]
        self.assertEqual(gen[:2], ["-q", "-t"])
        self.assertIn("ed25519", gen)
        self.assertEqual(gen[gen.index("-N") + 1], "")
        self.assertEqual(gen[gen.index("-C") + 1], "fcos-agent-setup-edge")
        # The manual step: the public key into its own file beside the user's, and the host fingerprint.
        self.assertIn("# vm edge (bash, admin)", out)
        self.assertIn("~/.ssh/authorized_keys.d/fcos-agent", out)
        self.assertIn("ssh-ed25519 AAAAC3agentpub fcos-agent-setup-edge", out)
        self.assertIn("ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub", out)
        self.assertNotIn("PRIVATE-KEY-MATERIAL", out + err)

    def run_manual_step(self, out, hostname):
        """Paste the printed manual block into a real bash on a machine whose hostname is `hostname`."""
        block = out.split("```bash\n", 1)[1].split("\n```", 1)[0]
        home = self.tmp / ("home-" + hostname)
        home.mkdir()
        stubs = self.tmp / ("ownerbin-" + hostname)
        stubs.mkdir()
        (stubs / "hostnamectl").write_text(f"#!/bin/sh\necho {hostname}\n")
        (stubs / "ssh-keygen").write_text('#!/bin/sh\necho "256 SHA256:stub no comment (ED25519)"\n')
        for name in ("hostnamectl", "ssh-keygen"):
            (stubs / name).chmod(0o755)
        env = {"PATH": f"{stubs}:/usr/bin:/bin", "HOME": str(home)}
        r = subprocess.run(["bash", "-c", block], env=env, capture_output=True, text=True, timeout=30)
        return r, home / ".ssh" / "authorized_keys.d" / "fcos-agent"

    def test_manual_step_adds_the_key_only_on_the_machine_it_is_for(self):
        # Seen twice on a real install: the block was pasted on the wrong machine,
        # once overwriting another VM's agent key and once landing on the hypervisor.
        code, out, err = self.run_tool("keygen", "edge")
        self.assertEqual(code, 0, err)
        right, keyfile = self.run_manual_step(out, "edge")
        self.assertEqual(right.returncode, 0, right.stderr)
        self.assertEqual(keyfile.read_text(), "ssh-ed25519 AAAAC3agentpub fcos-agent-setup-edge\n")
        self.assertIn("256 SHA256:stub", right.stdout)
        wrong, wrong_keyfile = self.run_manual_step(out, "hypervisor-1")
        self.assertFalse(wrong_keyfile.exists())
        self.assertFalse(wrong_keyfile.parent.exists(), "not even the folder is made on the wrong machine")
        self.assertIn("STOP: this is not edge", wrong.stdout)
        self.assertIn("hypervisor-1", wrong.stdout)
        self.assertNotIn("SHA256", wrong.stdout)

    def test_manual_step_says_which_machine_in_its_first_line(self):
        code, out, err = self.run_tool("keygen", "edge")
        block = out.split("```bash\n", 1)[1]
        self.assertEqual(block.splitlines()[0], "# vm edge (bash, admin): run this ONLY on edge")

    def test_keygen_never_overwrites(self):
        self.run_tool("keygen", "edge")
        code, out, err = self.run_tool("keygen", "edge")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)
        self.assertEqual(len(self.calls("ssh-keygen")), 1)

    def test_secrets_folder_must_be_private(self):
        (self.ws / "secrets").chmod(0o755)
        code, out, err = self.run_tool("keygen", "edge")
        self.assertEqual(code, 1)
        self.assertIn("0755", err)

    # trust

    def test_trust_pins_the_host_key_only_when_the_fingerprint_matches(self):
        self.run_tool("keygen", "edge")
        code, out, err = self.run_tool("trust", "edge", "--fingerprint", "SHA256:wrong")
        self.assertEqual(code, 1)
        self.assertIn("does not match", err)
        self.assertFalse(self.key.with_name("known_hosts").exists())
        code, out, err = self.run_tool("trust", "edge", "--fingerprint", FP)
        self.assertEqual(code, 0, err)
        kh = self.key.with_name("known_hosts")
        self.assertEqual(kh.read_text(), "192.0.2.20 ssh-ed25519 AAAAC3hostkey\n")
        scan = self.calls("ssh-keyscan")[-1]["args"]
        self.assertIn("ed25519", scan)
        self.assertEqual(scan[-1], "192.0.2.20")

    # run

    def test_run_uses_only_the_agent_key_never_the_users(self):
        self.setup_key()
        code, out, err = self.run_tool("run", "edge", "--", "sudo systemctl --user -M x@ is-active x.service")
        self.assertEqual(code, 0, err)
        self.assertIn("remote ran: sudo systemctl --user -M x@ is-active x.service", out)
        args = self.calls("ssh")[-1]["args"]
        joined = " ".join(args)
        for needle in ("-F none", "IdentitiesOnly=yes", "IdentityAgent=none", "BatchMode=yes",
                       "StrictHostKeyChecking=yes", "PasswordAuthentication=no",
                       f"UserKnownHostsFile={self.key.with_name('known_hosts')}", "GlobalKnownHostsFile=none", f"-i {self.key}",
                       "-l admin "):
            self.assertIn(needle, joined)
        self.assertEqual(args[-3:-1], ["192.0.2.20", "--"])

    def test_run_passes_stdin_and_the_exit_code(self):
        self.setup_key()
        code, out, err = self.run_tool("run", "edge", "--", "bash -s", stdin="echo hi\n")
        self.assertIn("stdin: echo hi", out)
        code, out, err = self.run_tool("run", "edge", "--", "false", exits="3")
        self.assertEqual(code, 3)

    def test_run_refuses_without_key_or_pinned_host(self):
        code, out, err = self.run_tool("run", "edge", "--", "true")
        self.assertEqual(code, 1)
        self.assertIn("keygen", err)
        self.run_tool("keygen", "edge")
        code, out, err = self.run_tool("run", "edge", "--", "true")
        self.assertEqual(code, 1)
        self.assertIn("trust", err)
        self.assertEqual(self.calls("ssh"), [])

    def test_refuses_root_unknown_vms_and_bad_names(self):
        (self.ws / "site.yaml").write_text(SITE.replace("admin_user: admin", "admin_user: root"))
        self.assertEqual(self.run_tool("keygen", "edge")[0], 1)
        (self.ws / "site.yaml").write_text(SITE)
        for vm in ("other", "../x", "-oProxyCommand=x"):
            with self.subTest(vm=vm):
                code, out, err = self.run_tool("keygen", vm)
                self.assertNotEqual(code, 0)  # 2 when the parser refuses an option-like name
        self.assertEqual(self.calls(), [])

    # secrets never reach the agent (an app printed a secret into its log)

    def test_run_output_is_redacted(self):
        self.setup_key()
        code, out, err = self.run_tool("run", "edge", "--", "echo Client secret" + ": N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM")
        self.assertEqual(code, 0, err)
        self.assertNotIn("N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM", out + err)
        self.assertIn("[hidden]", out)
        code, out, err = self.run_tool("run", "edge", "--", "false", exits="3",
                                       stderr="password" + "=hunter2 refused")
        self.assertEqual(code, 3)
        self.assertNotIn("hunter2", out + err)

    def test_run_refuses_direct_log_environment_and_secret_reads(self):
        self.setup_key()
        for command in ("sudo journalctl -u x", "sudo -u crm podman logs crm-app",
                        "podman --remote logs x", "docker logs x", "podman secret inspect --showsecret x",
                        "sudo podman secret inspect x", "printenv", "sudo -u x env", "env | grep KEY",
                        "cat /proc/1/environ", "sudo tail /var/lib/appdata/crm/storage/logs/laravel.log",
                        "cat /var/www/html/.env", "ls /run/secrets", "podman exec x cat /run/secrets/k",
                        "sudo systemctl status nftables", "sudo -u x systemctl --user status x.service",
                        "podman exec x sh -c 'echo $APP_KEY'",
                        "cat ~/.local/share/containers/storage/secrets/filedriver/secretsdata.json"):
            with self.subTest(command=command):
                code, out, err = self.run_tool("run", "edge", "--", command)
                self.assertEqual(code, 1, out)
                self.assertIn("vmssh.py logs", err)
        self.assertEqual([c for c in self.calls("ssh") if c["args"][-1] != "true"], [])
        # Ordinary commands still run.
        for command in ("sudo -u x XDG_RUNTIME_DIR=/run/user/3203 systemctl --user is-active x.service",
                        "sudo ls /var/lib/appdata/traefik/dynamic/", "id -u crm",
                        'for m in /var/mnt/*; do /usr/local/bin/require-mounts $m && echo "$m mounted"; done'):
            with self.subTest(command=command):
                self.assertEqual(self.run_tool("run", "edge", "--", command)[0], 0)

    def test_no_agent_command_in_the_guide_is_refused(self):
        sys.path.insert(0, str(ROOT / "tools"))
        from vmssh import DIRECT_READS
        for page in sorted((ROOT / "docs" / "guide").glob("*.md")):
            for line in page.read_text().splitlines():
                if line.strip().startswith("python3 tools/vmssh.py run"):
                    with self.subTest(page=page.name, line=line[:80]):
                        self.assertIsNone(DIRECT_READS.search(line))

    def test_logs_reads_one_unit_and_hides_secrets(self):
        self.setup_key()
        code, out, err = self.run_tool("logs", "edge", "crm-app.service", "-n", "40")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls("ssh")[-1]["args"][-1],
                         "sudo journalctl _SYSTEMD_USER_UNIT=crm-app.service -n 40 --no-pager -o short-iso")
        code, out, err = self.run_tool("logs", "edge", "nftables.service", "--system")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls("ssh")[-1]["args"][-1],
                         "sudo journalctl _SYSTEMD_UNIT=nftables.service -n 30 --no-pager -o short-iso")
        for bad in (["x; rm -rf /"], ["../x.service"], ["x"], ["crm-app.service", "-n", "0"],
                    ["crm-app.service", "-n", "501"]):
            with self.subTest(bad=bad):
                self.assertNotEqual(self.run_tool("logs", "edge", *bad)[0], 0)

    # revoke

    def test_revoke_removes_the_vm_file_proves_the_login_fails_then_deletes_the_key(self):
        self.setup_key()
        code, out, err = self.run_tool("revoke", "edge", exits="0,255")
        self.assertEqual(code, 0, out + err)
        ssh = self.calls("ssh")
        self.assertIn("rm -f ~/.ssh/authorized_keys.d/fcos-agent", ssh[0]["args"][-1])
        self.assertEqual(len(ssh), 2)  # the removal, then a login that must fail
        self.assertFalse(self.key.exists())
        self.assertFalse(self.key.with_name("id_ed25519.pub").exists())
        self.assertFalse((self.ws / "secrets" / "agent-ssh" / "edge").exists())
        self.assertIn("revoked", out)

    def test_revoke_keeps_the_key_when_the_check_login_fails_for_another_reason(self):
        # A network drop after the removal must not count as "revoked".
        self.setup_key()
        code, out, err = self.run_tool("revoke", "edge", exits="0,255",
                                       stderr="ssh: connect to host 192.0.2.20 port 22: Connection timed out")
        self.assertEqual(code, 1)
        self.assertIn("could not confirm", err)
        self.assertTrue(self.key.exists())

    def test_ssh_never_offers_the_agent_socket(self):
        self.setup_key()
        self.run_tool("run", "edge", "--", "true")
        self.assertNotIn("owner-agent.sock", json.dumps(self.calls("ssh")))

    def test_reinstall_after_a_rebuild_reprints_the_manual_step_for_the_same_key(self):
        # A rebuild wipes /var/home (the key file) and changes the host key; the local key stays.
        self.setup_key()
        pub = self.key.with_name("id_ed25519.pub").read_text().strip()
        code, out, err = self.run_tool("reinstall", "edge")
        self.assertEqual(code, 0, err)
        self.assertIn(pub, out)
        self.assertIn("~/.ssh/authorized_keys.d/fcos-agent", out)
        self.assertFalse(self.key.with_name("known_hosts").exists())  # trust again with the new fingerprint
        self.assertEqual(len(self.calls("ssh-keygen")), 2)  # keygen + trust's fingerprint only: no new key
        code, out, err = self.run_tool("run", "edge", "--", "true")
        self.assertIn("trust", err)

    def test_reinstall_needs_an_existing_key(self):
        code, out, err = self.run_tool("reinstall", "edge")
        self.assertEqual(code, 1)
        self.assertIn("keygen", err)

    def test_revoke_keeps_the_key_and_fails_when_the_login_still_works(self):
        self.setup_key()
        code, out, err = self.run_tool("revoke", "edge", exits="0,0")
        self.assertEqual(code, 1)
        self.assertIn("still logs in", err)
        self.assertTrue(self.key.exists())


class GuideTests(unittest.TestCase):
    def test_agent_steps_use_vmssh_never_the_users_ssh(self):
        guide = ROOT / "docs" / "guide"
        for page in sorted(guide.glob("0[2-7]-*.md")):
            with self.subTest(page=page.name):
                self.assertNotIn("ssh <admin>@", page.read_text())
        text = " ".join((guide / "02-build-a-vm.md").read_text().split())
        for needle in ("python3 tools/vmssh.py keygen", "python3 tools/vmssh.py trust",
                       "authorized_keys.d/fcos-agent", "python3 tools/vmssh.py run"):
            self.assertIn(needle, text)
        text3 = " ".join((guide / "03-add-a-service.md").read_text().split())
        self.assertIn("python3 tools/vmssh.py revoke", text3)
        text5 = " ".join((guide / "05-rebuild-a-vm.md").read_text().split())
        self.assertIn("python3 tools/vmssh.py reinstall", text5)
        prompt = " ".join((ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text().split())
        for needle in ("never use the user's SSH key", "tools/vmssh.py revoke"):
            self.assertIn(needle, prompt)


class UserManagerTests(unittest.TestCase):
    """From a non-interactive ssh session, 'systemctl --user -M <svc>@' hands sshd's
    stderr pipe to a bridge unit; SELinux forbids dbus-broker (system_dbusd_t) to pass an
    sshd_session_t fifo (a silenced denial) and the bus drops the call. The agent's commands use
    the service user's own bus instead."""

    def test_agent_commands_never_use_machine_connections(self):
        for page in sorted((ROOT / "docs" / "guide").glob("0[2-7]-*.md")):
            for n, line in enumerate(page.read_text().splitlines(), 1):
                if "vmssh.py run" in line:
                    with self.subTest(page=page.name, line=n):
                        self.assertNotRegex(line, r"systemctl --user -M")

    def test_no_agent_text_uses_machine_connections(self):
        # Pages 2-7 are the agent's procedure; -M stays only in the user's interactive
        # bash blocks on the VM ("# vm ... (bash" headings).
        for page in sorted((ROOT / "docs" / "guide").glob("0[2-7]-*.md")):
            manual_block, in_block = False, False
            for n, line in enumerate(page.read_text().splitlines(), 1):
                if line.startswith("```"):
                    in_block = not in_block
                    manual_block = False
                    continue
                if in_block and line.startswith("# vm ") and "(bash" in line:
                    manual_block = True
                if not manual_block:
                    with self.subTest(page=page.name, line=n):
                        self.assertNotRegex(line, r"systemctl --user -M")

    def test_push_waits_for_the_user_manager_after_linger(self):
        # enable-linger only queues user@<uid>; daemon-reload over its bus must wait for it.
        text = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        push = next(line for line in text.splitlines() if "enable-linger $svc" in line and "vmssh.py run" in line)
        start = push.index("sudo systemctl start user@\\$(id -u $svc).service")
        self.assertLess(push.index("enable-linger $svc"), start)
        self.assertLess(start, push.index("daemon-reload"))

    def test_direct_form_finds_the_uid_on_the_vm(self):
        text = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        start = next(line for line in text.splitlines() if "vmssh.py run" in line and "$svc-app.service $svc-cron" in line)
        # In fish double quotes the $( must be escaped, so id -u runs on the VM, not the desktop.
        self.assertIn('sudo -u $svc XDG_RUNTIME_DIR=/run/user/\\$(id -u $svc) systemctl --user start', start)


class DesktopRouteTests(unittest.TestCase):
    """The user's desktop had a leg on the VM's own network, reached the VM
    directly from an address the VM's firewall doesn't allow, and the temporary fix (a route via
    the router) was lost on restart. The install gives a permanent route as a manual step."""

    def test_guide_gives_the_permanent_route_step(self):
        text = " ".join((ROOT / "docs" / "guide" / "02-build-a-vm.md").read_text().split())
        for needle in ("ip -4 -br addr", "nmcli connection modify", "+ipv4.routes", "nmcli device reapply", "ip route get <vm-ip>"):
            self.assertIn(needle, text)

    def test_prompt_requires_it(self):
        prompt = " ".join((ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text().split())
        self.assertIn("permanent route", prompt)


class AgentRulesTests(unittest.TestCase):
    """The agent reaches VMs only through vmssh.py, never plain ssh with the user's key."""

    def test_plain_ssh_is_denied_and_vmssh_allowed(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_agent import AGENT, effect
        text = AGENT.read_text()
        for command in ("ssh admin@192.0.2.20 true", "ssh -i ~/.ssh/id_rsa x@192.0.2.20",
                        "scp x admin@192.0.2.20:", "ssh-add ~/.ssh/id_rsa"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "deny")
        ws = "/home/owner/fcos-workspace"
        for command in (f"python3 tools/vmssh.py run edge --workspace {ws} -- sudo systemctl is-active x",
                        "python3 tools/vmssh.py keygen edge", "python3 tools/vmssh.py revoke edge"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "allow")
        self.assertEqual(effect(text, "read", f"{ws}/secrets/agent-ssh/edge/id_ed25519"), "deny")

    def test_ssh_hidden_in_a_longer_command_is_denied(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_agent import AGENT, effect
        text = AGENT.read_text()
        for command in ("python3 tools/hypervisor.py list; ssh admin@192.0.2.30 true",
                        "bash tools/validate.sh x && ssh 192.0.2.30", "env ssh 192.0.2.30", "command ssh 192.0.2.30",
                        "/usr/bin/ssh 192.0.2.30", "git -c core.sshCommand='ssh -i k' fetch",
                        "GIT_SSH_COMMAND=x git fetch", "SSH_AUTH_SOCK=/x python3 tools/x.py",
                        "python3 tools/hypervisor.py list | scp a b:", "python3 tools/x.py; rsync a b:"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "deny")
        # The agent's own commands still run hands-off.
        for command in ("python3 tools/vmssh.py run edge -- 'ls ~/.ssh/authorized_keys.d/'",
                        "python3 tools/vmssh.py run edge -- 'sudo systemctl is-active sshd'",
                        "ssh-keygen -R 192.0.2.20"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "allow")

    def test_logs_only_through_vmssh_logs(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_agent import AGENT, effect
        text = AGENT.read_text()
        for command in ("python3 tools/vmssh.py run edge -- 'sudo journalctl -u x'",
                        "python3 tools/vmssh.py run edge -- 'podman logs x'",
                        "python3 tools/vmssh.py run edge -- 'podman secret inspect --showsecret x'",
                        "python3 tools/vmssh.py run edge -- printenv",
                        "python3 tools/vmssh.py run edge -- 'cat /proc/1/environ'"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "deny")
        self.assertEqual(effect(text, "shell", "python3 tools/vmssh.py logs edge crm-app.service -n 40"), "allow")
        prompt = " ".join(text.split())
        self.assertIn("vmssh.py logs", prompt)

    def test_the_agent_cannot_plant_its_own_tools(self):
        # "python3 tools/*" is allowed from any working directory, so no folder the
        # agent may write to freely can hold a tools/ script.
        sys.path.insert(0, str(ROOT / "tests"))
        from test_agent import AGENT, effect
        text = AGENT.read_text()
        for path in ("/tmp/opencode/tools/x.py", "/home/owner/fcos-ws/vms/edge/tools/x.py",
                     "/home/owner/fcos-ws/services/a/tools/x.sh"):
            with self.subTest(path=path):
                self.assertNotEqual(effect(text, "edit", path), "allow")
        # Nor through the shell: a redirect or tee from an allowed tool, or a generator's output folder.
        for command in ("python3 tools/render.py /tmp/opencode/t.tmpl /tmp/opencode/v.values > /tmp/opencode/tools/x.py",
                        "python3 tools/ign_to_script.py a.ign >tools/x.sh",
                        "python3 tools/ign_to_script.py a.ign >> /home/owner/fcos-ws/vms/e/tools/x.sh",
                        "python3 tools/render.py a b | tee /tmp/opencode/tools/x.py",
                        "python3 tools/gen_service.py s.yaml site.yaml /tmp/opencode/tools",
                        "python3 tools/login_frontend.py site.yaml tools"):
            with self.subTest(command=command):
                self.assertEqual(effect(text, "shell", command), "deny")
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        push = next(line for line in guide.splitlines() if line.startswith("python3 tools/ign_to_script.py")
                    and "apply-$svc.sh" in line)
        # The push chains a generated script into a root run on the VM, so it asks (and is not denied).
        self.assertEqual(effect(text, "shell", push), "ask")
        # The pinned host key lives with the agent key, out of the agent's reach.
        self.assertEqual(effect(text, "edit", "/home/owner/fcos-ws/secrets/agent-ssh/edge/known_hosts"), "deny")


if __name__ == "__main__":
    unittest.main()
