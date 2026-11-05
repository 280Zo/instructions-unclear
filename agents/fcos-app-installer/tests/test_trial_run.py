"""Guide 10: the trial run after installing the toolkit on a machine (owner, 2026-11-04).
The tests check files; these steps check what only a live OpenCode can show."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs" / "guide" / "10-trial-run.md"


class TrialRunTests(unittest.TestCase):
    def test_live_checks_are_listed(self):
        text = " ".join(PAGE.read_text().split())
        for needle in ("rules/owner-steps.md", "Commands in full, in the message", "adapter-drafter",
                       "adapter-proxmox", "researching-apps-for-self-hosting", "python3 -m unittest discover tests",
                       "store_api_token", "file-server.md", "secrets.md", "AGENTS.md", "backups.md",
                       "vmssh.py logs", "[hidden]", "backrooms", "revoke", "Report back"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_live_checks_are_actions_not_questions(self):
        # General review, 2026-11-04: a model can answer "which skills can you load?" from memory.
        # Each check makes it do something whose result the owner can see.
        section = PAGE.read_text().split("## 10.2", 1)[1].split("## 10.3", 1)[0]
        self.assertNotIn("Which skills can you load", section)
        text = " ".join(section.split())
        for needle in ("Load the skill `adapter-proxmox`", "Load the skill `eli5`", "refused by permission",
                       "Run `ssh localhost true`", "no file read", "Start the `adapter-drafter` subagent",
                       # Whole-branch review: the tests' rule matcher is a stand-in for OpenCode's,
                       # so the rules that depend on how OpenCode splits a command are checked live.
                       "> .agents/skills/x.md", "--workspace ~/.agents/skills"):
            with self.subTest(needle=needle):
                self.assertIn(needle.lower(), text.lower())

    def test_linked_from_both_readmes(self):
        self.assertIn("10-trial-run.md", (ROOT / "README.md").read_text())
        self.assertIn("10-trial-run.md", (ROOT / "docs" / "guide" / "README.md").read_text())

    def test_readme_layout_names_every_top_folder(self):
        readme = (ROOT / "README.md").read_text()
        layout = readme.split("## Layout", 1)[1]
        for folder in ("`.opencode/`", "`.agents/skills/`", "`rules/`", "`docs/guide/`", "`schemas/`",
                       "`specs/login-frontend/`", "`templates/`", "`tools/`", "`tests/`"):
            with self.subTest(folder=folder):
                self.assertIn(folder, layout)
        self.assertIn("adapter-drafter", layout)


if __name__ == "__main__":
    unittest.main()
