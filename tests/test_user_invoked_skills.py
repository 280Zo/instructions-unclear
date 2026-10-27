"""Checks for handoff, teach and wait-what, copied from mattpocock/skills."""

import re
import unittest

from test_security_re_context import ROOT, read_jsonc

SKILLS = {
    "handoff": ["agents/openai.yaml"],
    "teach": [
        "agents/openai.yaml",
        "GLOSSARY-FORMAT.md",
        "LEARNING-RECORD-FORMAT.md",
        "MISSION-FORMAT.md",
        "RESOURCES-FORMAT.md",
    ],
    "wait-what": ["agents/openai.yaml"],
}
COMMIT = "5beb35b040e3de97e54fa9e386d7e42d15c295c2"
GROUPS = ["default", "work", "writing_reporting"]


def frontmatter(name):
    text = (ROOT / f"skills/{name}/skills/{name}/SKILL.md").read_text()
    return text.split("---\n")[1]


class UserInvokedSkillTests(unittest.TestCase):
    def test_each_skill_is_its_own_folder_with_supporting_files(self):
        for name, files in SKILLS.items():
            root = ROOT / f"skills/{name}/skills/{name}"
            for relative in ["SKILL.md", *files]:
                self.assertTrue((root / relative).is_file(), f"{name}/{relative}")
            readme = (ROOT / f"skills/{name}/README.md").read_text()
            self.assertIn(COMMIT, readme, name)
            self.assertIn("## For agents: routing and updates", readme, name)
        self.assertFalse((ROOT / "skills/mattpocock").exists())

    def test_invocation_fields_live_in_tool_sections(self):
        for name in SKILLS:
            fm = frontmatter(name)
            self.assertRegex(fm, rf"(?m)^name: {name}$")
            self.assertNotRegex(fm, r"(?m)^(disable-model-invocation|argument-hint):", name)
            for tool in ["claudecode", "opencode"]:
                block = re.search(rf"(?ms)^{tool}:\n((?:  .*\n)+)", fm)
                self.assertIsNotNone(block, (name, tool))
                self.assertIn("disable-model-invocation: true", block.group(1), (name, tool))

    def test_groups_routing_and_license(self):
        for group in GROUPS:
            roots = read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]
            for name in SKILLS:
                self.assertIn(f"skills/{name}", roots, group)
        # User-invoked skills are never chosen by the model, so the
        # every-request routing rule leaves them out.
        routing = (ROOT / "rules/routing/rules/routing.md").read_text()
        for name in SKILLS:
            self.assertNotIn(f"`{name}`", routing)
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text()
        self.assertIn("## mattpocock/skills", licenses)
        self.assertIn("Copyright (c) 2026 Matt Pocock", licenses)


if __name__ == "__main__":
    unittest.main()
