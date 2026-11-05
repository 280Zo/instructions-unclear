"""The agent's name (owner, 2026-11-04): fcos-app-installer, everywhere."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "fcos-" + "service"  # split so this file doesn't match itself


class NamingTests(unittest.TestCase):
    def test_agent_file_and_command_use_the_name(self):
        self.assertTrue((ROOT / ".opencode" / "agents" / "fcos-app-installer.md").is_file())
        self.assertFalse((ROOT / ".opencode" / "agents" / f"{OLD}.md").exists())
        self.assertIn("agent: fcos-app-installer", (ROOT / ".opencode" / "commands" / "add-service.md").read_text())

    def test_old_name_is_gone_from_published_files(self):
        files = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
                               capture_output=True, text=True, check=True).stdout.split()
        hits = [f for f in files if (ROOT / f).is_file() and OLD in (ROOT / f).read_text(errors="ignore")]
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
