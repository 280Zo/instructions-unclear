import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from gitfree import folder_outside_any_checkout, in_a_checkout, without_git_variables  # noqa: E402
from layout import SKILLS_DIR  # noqa: E402
from publish_check import check_text  # noqa: E402
from workspace import init_workspace  # noqa: E402


def j(*parts: str) -> str:
    """Join pieces at runtime, so this file never holds a real-looking value
    that publish_check would (rightly) flag."""
    return "".join(parts)


class GenericRuleTests(unittest.TestCase):
    def test_flags_environment_details(self):
        for line in (
            j("NFS_SERVER=10", ".0.30.1"),
            j("gateway: 192", ".168.1.1"),
            j("ip: 172", ".20.0.5"),
            j("domain: myhome.", "duckdns.org"),
            j("acme_email: someone@", "gmail.com"),
            j("ssh-ed25519 AAAA", "C3NzaC1lZDI1NTE5AAAAIGJx5n0realkeymaterialrealkeymaterialabcd user@laptop"),
            j('password_hash: "$', 'y$j9T$abcdefghijkl$abcdefghijklmnopqrstuvwxyzABCDEFG12"'),
            j("-----BEGIN OPENSSH PRIV", "ATE KEY-----"),
            j("token = ", "abcdefghijklmnop"),
        ):
            with self.subTest(line=line):
                self.assertTrue(check_text(line + "\n", set()), line)

    def test_allows_placeholders(self):
        for line in (
            "NFS_SERVER=192.0.2.1",
            "lan_cidr: 198.51.100.0/24",
            "listen 127.0.0.1:9000",
            "domain: example.duckdns.org",
            "host: opencode.example.duckdns.org",
            "acme_email: owner@example.com",
            "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIEXAMPLEEXAMPLEEXAMPLE owner@example.com",
            'password_hash: "$y$j9T$EXAMPLEONLY$NOTAREALHASH"',
            "image: docker.io/library/traefik:v3",
        ):
            with self.subTest(line=line):
                self.assertEqual(check_text(line + "\n", set()), [], line)

    def test_flags_config_values(self):
        self.assertTrue(check_text("pool is TankPool here\n", {"TankPool"}))
        self.assertEqual(check_text("nothing personal\n", {"TankPool"}), [])

    def test_hits_never_echo_the_value(self):
        hits = check_text(j("api_key: ", "supersecretvalue123\n"), set())
        self.assertTrue(hits)
        self.assertNotIn("supersecretvalue123", " ".join(hits))


class WorkspaceSourceTests(unittest.TestCase):
    """Private values come from the workspace, never from a file in the repo."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        (self.tmp / "home").mkdir()
        # No GIT_* variable from the caller (a git hook sets GIT_DIR): the test's own git calls and
        # the tool's must all see the repositories the test builds.
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env["HOME"] = str(self.tmp / "home")
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.secret = j("PVE-", "BIGBOX")
        (self.repo / "notes.md").write_text(f"runs on {self.secret} today\n")

    def run_check(self, *args: str, workspace: Path | None = None, **extra_env: str):
        env = {k: v for k, v in os.environ.items() if k != "FCOS_WORKSPACE"}
        env["HOME"] = str(self.tmp / "home")
        env.update(extra_env)
        if workspace is not None:
            env["FCOS_WORKSPACE"] = str(workspace)
        return subprocess.run([sys.executable, str(ROOT / "tools/publish_check.py"), *(args or (str(self.repo),))],
                              cwd=self.repo, env=env, capture_output=True, text=True)

    def test_only_the_named_folder_is_scanned(self):
        # Owner, 2026-11-04: inside instructions-unclear the toolkit is one folder of a larger
        # repo; files outside it are that repo's own business.
        sub = self.repo / "agents" / "toolkit"
        sub.mkdir(parents=True)
        (sub / "ok.md").write_text("nothing private\n")
        result = self.run_check(str(sub), workspace=self.make_workspace())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("notes.md", result.stdout)
        self.assertEqual(self.run_check(str(self.repo), workspace=self.make_workspace()).returncode, 1)

    def test_missing_folder_refused(self):
        self.assertEqual(self.run_check(str(self.tmp / "missing")).returncode, 2)

    def put(self, folder: Path, relative: str, text: str) -> None:
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def test_every_installed_file_gets_the_full_scan_with_no_exemptions(self):
        # Owner, 2026-11-05: no companion agents live in this folder, so nothing is exempt. A file
        # under the agent folders, a skill, or one named like an upstream agent is scanned like any other.
        folder = self.plain_folder()
        example = j("gateway: 10", ".1.2.3\n")
        for path in (".opencode/commands/security-sast.md", ".opencode/agents/security-auditor.md",
                     ".opencode/commands/add-service.md", ".opencode/agents/fcos-app-installer.md",
                     ".opencode/agents/Fcos-app-installer.md", ".opencode/agents/adapter-drafter.md ",
                     ".opencode/agents/new-agent.md", f"{SKILLS_DIR}/adapter-proxmox/SKILL.md",
                     f"{SKILLS_DIR}/security-best-practices/SKILL.md", f"{SKILLS_DIR}/zzz-new/scripts/run.sh",
                     "tools/x.py", "AGENTS.md"):
            with self.subTest(path=path):
                self.put(folder, path, example)
                result = self.run_check(str(folder))
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(path, result.stdout)
                (folder / path).unlink()

    def plain_folder(self, name="plain") -> Path:
        # Needs a folder with no git checkout around it, and TMPDIR may be inside one: look elsewhere.
        base = folder_outside_any_checkout("publish-plain-")
        if base is None:
            self.skipTest("no place on this machine is outside every git checkout")
        self.addCleanup(shutil.rmtree, base, True)
        folder = base / name
        folder.mkdir()
        return folder

    def test_an_unreadable_folder_is_a_hit_in_both_modes_not_a_pass(self):
        # A folder the tool cannot open could hold anything: it must not read as clean.
        if os.geteuid() == 0:
            self.skipTest("root can open any folder")
        for kind in ("walked", "git list"):
            with self.subTest(mode=kind):
                folder = self.plain_folder() if kind == "walked" else self.repo
                (folder / "ok.md").write_text("nothing private\n")
                locked = folder / "locked"
                locked.mkdir()
                (locked / "leak.md").write_text(j("gateway: 192", ".168.1.1\n"))
                locked.chmod(0)
                self.addCleanup(locked.chmod, 0o700)
                result = self.run_check(str(folder))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("locked: unreadable folder (not checked)", result.stdout)
                locked.chmod(0o700)

    def test_a_folder_that_lists_but_cannot_be_searched_is_a_hit_not_a_silent_pass(self):
        # Mode 0o444: the names can be read, the files inside cannot be opened or even stat-ed.
        if os.geteuid() == 0:
            self.skipTest("root can open any folder")
        for kind in ("walked", "git list"):
            with self.subTest(mode=kind):
                folder = self.plain_folder() if kind == "walked" else self.repo
                (folder / "ok.md").write_text("nothing private\n")
                closed = folder / "closed"
                closed.mkdir()
                (closed / "leak.md").write_text(j("gateway: 192", ".168.1.1\n"))
                closed.chmod(0o444)
                self.addCleanup(closed.chmod, 0o700)
                result = self.run_check(str(folder))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("closed", result.stdout)
                closed.chmod(0o700)

    def test_a_file_name_cannot_forge_output_lines(self):
        plain = self.plain_folder()
        name = "x.md\nforged.md:1: all clear"
        try:
            (plain / name).write_text(j("gateway: 192", ".168.1.1\n"))
        except OSError:
            self.skipTest("this file system refuses newlines in names")
        result = self.run_check(str(plain))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(len(result.stdout.splitlines()), 1, result.stdout)
        self.assertIn("\\n", result.stdout)

    def test_a_copy_that_is_not_a_checkout_is_walked(self):
        # An installed toolkit is a plain folder, not a git checkout: every file in it is checked.
        plain = self.plain_folder()
        (plain / "ok.md").write_text("nothing private\n")
        result = self.run_check(str(plain))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("(1 file, walked)", result.stderr)
        (plain / "sub").mkdir()
        (plain / "sub" / "bad.md").write_text(j("gateway: 192", ".168.1.1\n"))
        result = self.run_check(str(plain))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("sub/bad.md:1: private IPv4 address", result.stdout)

    def test_a_walked_copy_is_checked_against_the_workspace_too(self):
        plain = self.plain_folder()
        (plain / "notes.md").write_text(f"runs on {self.secret} today\n")
        result = self.run_check(str(plain), workspace=self.make_workspace())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("notes.md:1: value from workspace", result.stdout)
        self.assertNotIn(self.secret, result.stdout + result.stderr)

    def test_the_walk_skips_git_internals_caches_and_symlinks(self):
        plain = self.plain_folder()
        (plain / "ok.md").write_text("nothing private\n")
        for skipped in (".git", "__pycache__"):
            (plain / skipped).mkdir()
            (plain / skipped / "x").write_text(j("gateway: 192", ".168.1.1\n"))
        outside = self.tmp / "outside.md"
        outside.write_text(j("gateway: 192", ".168.1.1\n"))
        (plain / "link.md").symlink_to(outside)
        (plain / "linked").symlink_to(self.tmp, target_is_directory=True)
        result = self.run_check(str(plain))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("(1 file, walked)", result.stderr)

    def test_a_checkout_is_scanned_from_gits_list_and_says_so(self):
        result = self.run_check()
        self.assertIn("git list)", result.stderr)

    def test_the_callers_git_variables_do_not_switch_the_mode(self):
        # A git hook runs with GIT_DIR pointing at its own repository.
        elsewhere = {"GIT_DIR": str(self.tmp / "nowhere" / ".git"), "GIT_WORK_TREE": str(self.tmp / "nowhere")}
        in_repo = self.run_check(**elsewhere)
        self.assertIn("git list)", in_repo.stderr)
        self.assertNotIn("walked", in_repo.stderr)
        plain = self.plain_folder()
        (plain / "ok.md").write_text("nothing private\n")
        self.assertIn("walked)", self.run_check(str(plain), **elsewhere).stderr)

    def test_an_unreadable_file_is_a_hit_not_a_crash(self):
        if os.geteuid() == 0:
            self.skipTest("root can read any file")
        plain = self.plain_folder()
        locked = plain / "locked.md"
        locked.write_text("nothing private\n")
        locked.chmod(0)
        self.addCleanup(locked.chmod, 0o600)
        result = self.run_check(str(plain))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("locked.md: unreadable", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_a_file_name_that_is_not_utf8_does_not_crash_either_mode(self):
        name = b"bad\xff.md"
        plain = self.plain_folder()
        try:
            (Path(os.fsdecode(bytes(plain))) / os.fsdecode(name)).write_text(j("gateway: 192", ".168.1.1\n"))
            (self.repo / os.fsdecode(name)).write_text(j("gateway: 192", ".168.1.1\n"))
        except OSError:
            self.skipTest("this file system refuses non-UTF-8 names")
        for folder in (plain, self.repo):
            with self.subTest(folder=folder.name):
                result = self.run_check(str(folder))
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("private IPv4 address", result.stdout)
                self.assertIn("bad", result.stdout)

    def test_nothing_to_scan_is_an_error_not_a_pass(self):
        self.assertEqual(self.run_check(str(self.plain_folder("empty"))).returncode, 2)
        (self.repo / ".gitignore").write_text("ignored/\n")
        ignored = self.repo / "ignored"
        ignored.mkdir()
        (ignored / "x.md").write_text("nothing\n")
        result = self.run_check(str(ignored))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("nothing to scan", result.stderr)

    def make_workspace(self) -> Path:
        ws = self.tmp / "ws"
        init_workspace(ws)
        (ws / "site.yaml").write_text(f"hosts:\n  big:\n    node: {self.secret}\n")
        return ws

    def test_flags_value_from_workspace(self):
        result = self.run_check(workspace=self.make_workspace())
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("notes.md:1: value from workspace", result.stdout)
        self.assertNotIn(self.secret, result.stdout + result.stderr)

    def test_generic_rules_only_without_workspace(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("generic rules only", result.stderr)

    def test_generic_rules_still_apply_without_workspace(self):
        (self.repo / "notes.md").write_text(j("gateway: 192", ".168.1.1\n"))
        self.assertEqual(self.run_check().returncode, 1)

    def test_config_flag_removed(self):
        result = self.run_check("--config", "config.yaml")
        self.assertEqual(result.returncode, 2)

    def test_workspace_without_site_yaml_is_an_error(self):
        missing = self.tmp / "no-such-folder"
        result = self.run_check(workspace=missing)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(f"publish_check: workspace {missing} has no site.yaml", result.stderr)
        self.assertIn("wrong FCOS_WORKSPACE or moved folder?", result.stderr)

    def test_stale_remembered_workspace_is_an_error(self):
        remembered = self.tmp / "home" / ".config" / "fcos-agent" / "workspace"
        remembered.parent.mkdir(parents=True)
        remembered.write_text(f"{self.tmp / 'deleted-ws'}\n")
        result = self.run_check()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("has no site.yaml", result.stderr)

    def test_empty_workspace_folder_is_an_error(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        self.assertEqual(self.run_check(workspace=empty).returncode, 2)

    def test_workspace_inside_repo_is_an_error(self):
        result = self.run_check(workspace=ROOT / "ws-inside")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("inside", result.stderr)


class RepoTests(unittest.TestCase):
    def test_repo_is_publishable(self):
        with tempfile.TemporaryDirectory() as home:
            env = {k: v for k, v in os.environ.items() if k != "FCOS_WORKSPACE"}
            env["HOME"] = home
            result = subprocess.run([sys.executable, str(ROOT / "tools/publish_check.py")],
                                    cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_default_is_the_toolkit_folder_wherever_it_runs(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            env = {k: v for k, v in os.environ.items() if k != "FCOS_WORKSPACE"}
            env["HOME"] = elsewhere
            result = subprocess.run([sys.executable, str(ROOT / "tools/publish_check.py")],
                                    cwd=elsewhere, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"scanned {ROOT}", result.stderr)

    def test_private_paths_ignored(self):
        # The folder's .gitignore keeps these out of any checkout it is committed to. An installed
        # copy that is not in a checkout has nothing to ask, and a git hook's GIT_DIR must not decide.
        if not in_a_checkout(ROOT):
            self.skipTest("this copy of the toolkit is not in a git checkout")
        env = without_git_variables(os.environ)
        for path in ("config.yaml", "vms/edge/base-config.bu", "notes/x.md",
                     "docs/design/x.md", "docs/superpowers/plans/x.md"):
            with self.subTest(path=path):
                rc = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT, env=env).returncode
                self.assertEqual(rc, 0, f"{path} is not git-ignored")


if __name__ == "__main__":
    unittest.main()
