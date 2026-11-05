"""The toolkit's rule files (rules/*.md, owner 2026-11-04): the parts of the agent's
instructions that don't depend on the OS, loaded for every agent started in this folder
through opencode.json `instructions` (opencode.ai/v2/docs/config, Instructions). A root
AGENTS.md can't be used: it is in the owner's global git-ignore."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "rules"
PROMPT = ROOT / ".opencode" / "agents" / "fcos-app-installer.md"


class RulesTests(unittest.TestCase):
    def test_opencode_json_loads_the_rules(self):
        # .opencode/opencode.json: the owner's global gitignore excludes a root opencode.json.
        config = json.loads((ROOT / ".opencode" / "opencode.json").read_text())
        self.assertFalse((ROOT / "opencode.json").exists())
        self.assertEqual(config["$schema"], "https://opencode.ai/config.json")
        self.assertIn("rules/*.md", config["instructions"])

    def test_owner_steps_rule(self):
        text = " ".join((RULES / "owner-steps.md").read_text().split())
        for needle in ("# Owner steps", "one table", "one step per answer", "machine and shell",
                       "report back", "ends its turn", "fish", "bash", "bash equivalent",
                       "never touch", "root"):
            self.assertIn(needle.lower(), text.lower())

    def test_secret_handling_rule(self):
        text = " ".join((RULES / "secret-handling.md").read_text().split())
        for needle in ("# Secrets and private values", "never ask for, read, print or store",
                       "hidden prompt", "password manager", "names only", "rotate", "logs",
                       "[hidden]", "placeholders", "192.0.2.", "workspace"):
            self.assertIn(needle.lower(), text.lower())

    def test_rules_are_portable(self):
        for path in RULES.glob("*.md"):
            text = path.read_text()
            for word in ("Butane", "Ignition", "Quadlet", "Fedora CoreOS", "Proxmox", "Authentik"):
                with self.subTest(rule=path.name, word=word):
                    self.assertNotIn(word, text)

    def test_prompt_points_to_the_rules_instead_of_repeating_them(self):
        prompt = PROMPT.read_text()
        self.assertIn("rules/owner-steps.md", prompt)
        self.assertIn("rules/secret-handling.md", prompt)
        for moved in ("**Several items of one kind are one table**", "Never ask for, read, print or store",
                      "Real values go only in the workspace"):
            with self.subTest(moved=moved):
                self.assertNotIn(moved, prompt)


if __name__ == "__main__":
    unittest.main()
