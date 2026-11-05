import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

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
        patcher = mock.patch.dict(os.environ, {"HOME": str(self.tmp / "home")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.secret = j("PVE-", "BIGBOX")
        (self.repo / "notes.md").write_text(f"runs on {self.secret} today\n")

    def run_check(self, *args: str, workspace: Path | None = None):
        env = {k: v for k, v in os.environ.items() if k != "FCOS_WORKSPACE"}
        env["HOME"] = str(self.tmp / "home")
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

    def test_bad_folder_refused(self):
        self.assertEqual(self.run_check(str(self.tmp / "missing")).returncode, 2)
        self.assertEqual(self.run_check(str(self.tmp)).returncode, 2)  # not inside a git checkout

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
        for path in ("config.yaml", "vms/edge/base-config.bu", "notes/x.md",
                     "docs/design/x.md", "docs/superpowers/plans/x.md"):
            with self.subTest(path=path):
                rc = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode
                self.assertEqual(rc, 0, f"{path} is not git-ignored")


if __name__ == "__main__":
    unittest.main()
