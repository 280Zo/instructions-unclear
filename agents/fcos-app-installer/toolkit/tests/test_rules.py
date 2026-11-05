"""The toolkit's rules: the parts of the agent's instructions that don't depend
on the OS, loaded for every agent started in this folder.

The rule sources (rules/ in the repository) are written by rulesync into this folder's AGENTS.md,
which OpenCode loads from the folder it is started in. Nothing here needs the config's
`instructions` list.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_MD = ROOT / "AGENTS.md"
PROMPT = ROOT / ".opencode" / "agents" / "fcos-app-installer.md"


def flat(path: Path) -> str:
    return " ".join(path.read_text().split())


class RulesTests(unittest.TestCase):
    def test_the_rules_are_in_the_folders_agents_md_and_nothing_else_loads_them(self):
        self.assertTrue(AGENTS_MD.is_file())
        self.assertFalse((ROOT / "rules").exists())  # the sources stay in the repository
        self.assertFalse((ROOT / "opencode.json").exists())
        self.assertFalse((ROOT / ".opencode" / "opencode.json").exists())  # no instructions list to depend on

    def test_owner_steps_rule(self):
        text = flat(AGENTS_MD)
        for needle in ("# Owner steps", "one table", "one step per answer", "machine and shell",
                       "report back", "ends its turn", "fish", "bash", "bash equivalent",
                       "never touch", "root"):
            self.assertIn(needle.lower(), text.lower())

    def test_secret_handling_rule(self):
        text = flat(AGENTS_MD)
        for needle in ("# Secrets and private values", "never ask for, read, print or store",
                       "hidden prompt", "password manager", "names only", "rotate", "logs",
                       "[hidden]", "placeholders", "192.0.2.", "workspace"):
            self.assertIn(needle.lower(), text.lower())

    def test_rules_are_portable(self):
        text = AGENTS_MD.read_text()
        for word in ("Butane", "Ignition", "Quadlet", "Fedora CoreOS", "Proxmox", "Authentik"):
            with self.subTest(word=word):
                self.assertNotIn(word, text)

    def test_the_rules_have_no_frontmatter_left_in_agents_md(self):
        # rulesync turns each rule's frontmatter (root, targets, description) into nothing the model reads.
        self.assertFalse(AGENTS_MD.read_text().lstrip().startswith("---"))

    def test_prompt_points_to_the_rules_instead_of_repeating_them(self):
        prompt = PROMPT.read_text()
        self.assertIn("Owner steps", prompt)
        self.assertIn("Secrets and private values", prompt)
        self.assertNotIn("rules/owner-steps.md", prompt)  # that file is not in this folder
        self.assertNotIn("rules/secret-handling.md", prompt)
        for moved in ("**Several items of one kind are one table**", "Never ask for, read, print or store",
                      "Real values go only in the workspace"):
            with self.subTest(moved=moved):
                self.assertNotIn(moved, prompt)


if __name__ == "__main__":
    unittest.main()
