"""Guide 11 (moving, updating, a service's new release line) and the README's safety notes
(owner and general review, 2026-11-04)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "guide" / "11-move-and-update.md"


def flat(text: str) -> str:
    return " ".join(text.split())


class GuidePageTests(unittest.TestCase):
    def test_moving_to_another_computer(self):
        text = flat(PAGE.read_text().split("## 11.1", 1)[1].split("## 11.2", 1)[0])
        for needle in ("~/.config/fcos-agent/workspace", "python3 tools/workspace.py init", "secrets/",
                       "store_api_token", "vmssh.py keygen", "python3 tools/check_requirements.py",
                       "10-trial-run.md", "password manager"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_updating_the_toolkit(self):
        text = flat(PAGE.read_text().split("## 11.2", 1)[1].split("## 11.3", 1)[0])
        for needle in ("python3 tools/check_updates.py", "checksum", "create_api_access", "README.md",
                       "previous folder", "host-scripts.sha256", "tampered download"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)
        self.assertNotIn("git tag", text)  # the toolkit needs no git: an update is a new copy, not a checkout

    def test_moving_a_service_to_a_new_release_line(self):
        text = flat(PAGE.read_text().split("## 11.3", 1)[1])
        for needle in ("[Owner]", "[Agent]", "official release notes", "research.md", "Check a backup",
                       "image:", "gen_service.py", "3.10", "AutoUpdate=registry", "one release line at a time",
                       "pg_dumpall", "Restore", "Report back"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_linked_from_the_guide_index(self):
        self.assertIn("11-move-and-update.md", (ROOT / "docs" / "guide" / "README.md").read_text())


class ReadmeNotesTests(unittest.TestCase):
    def test_safety_notes(self):
        readme = flat((ROOT / "README.md").read_text())
        for needle in ('contains "fcos-"', "Allow always", "Allow once", "`fcos-app-installer` agent",
                       "`build` agent"):
            with self.subTest(needle=needle):
                self.assertIn(needle, readme)


if __name__ == "__main__":
    unittest.main()
