"""Offline checks for the pinned OpenAI skills, standalone and bundled."""

import unittest

from test_security_re_context import ROOT, read_jsonc

STANDALONE = [
    "transcribe",
    "speech",
    "security-threat-model",
    "screenshot",
]


class OpenAISkillsTests(unittest.TestCase):
    def test_selected_skills_keep_required_runtime_resources(self):
        required = {
            "skills/transcribe/skills/transcribe": [
                "scripts/transcribe_diarize.py",
                "references/api.md",
            ],
            "skills/speech/skills/speech": [
                "scripts/text_to_speech.py",
                "references/cli.md",
            ],
            "skills/security-threat-model/skills/security-threat-model": [
                "references/prompt-template.md"
            ],
            "agents/security/skills/security-best-practices": [
                "references/python-fastapi-web-server-security.md"
            ],
            "skills/screenshot/skills/screenshot": ["scripts/take_screenshot.py"],
        }
        for path, resources in required.items():
            root = ROOT / path
            for relative in [
                "SKILL.md",
                "LICENSE.txt",
                "agents/openai.yaml",
                *resources,
            ]:
                self.assertTrue((root / relative).is_file(), f"{path}/{relative}")

    def test_groups_select_skills_without_default_threat_model(self):
        # Since 2026-10-25 default installs security-threat-model too: only the
        # OpenCode security agent may load it (agents/generate.py).
        for group in ["default", "work", "infosec"]:
            roots = read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]
            for name in STANDALONE:
                self.assertIn(f"skills/{name}", roots, (group, name))
            self.assertIn("agents/security", roots)
            names = []
            for source in roots:
                names.extend(
                    p.parent.name for p in (ROOT / source / "skills").glob("*/SKILL.md")
                )
            self.assertEqual(len(names), len(set(names)), group)
            self.assertIn("security-best-practices", names)
            self.assertIn("security-threat-model", names)
        self.assertEqual(
            read_jsonc(ROOT / "rulesync.jsonc")["inputRoots"],
            read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"],
        )

    def test_microsoft_playwright_cli_replaces_openai_copy(self):
        # OpenAI's deprecated playwright copy was replaced on 2026-10-24.
        self.assertFalse((ROOT / "skills/playwright").exists())
        skill = ROOT / "skills/playwright-cli/skills/playwright-cli"
        self.assertTrue((skill / "SKILL.md").is_file())
        self.assertTrue((skill / "references").is_dir())
        fm = (skill / "SKILL.md").read_text().split("---\n")[1]
        self.assertRegex(fm, r"(?m)^name: playwright-cli$")
        self.assertNotRegex(fm, r"(?m)^allowed-tools:")
        self.assertRegex(fm, r"(?m)^claudecode:\n  allowed-tools: ")
        for config in ["rulesync.jsonc", "groups/default.jsonc", "groups/work.jsonc", "groups/infosec.jsonc"]:
            roots = read_jsonc(ROOT / config)["inputRoots"]
            self.assertIn("skills/playwright-cli", roots, config)
            self.assertNotIn("skills/playwright", roots, config)
        readme = (ROOT / "skills/playwright-cli/README.md").read_text()
        self.assertIn("b85c7a736bb473bf55b584e54a09ffa698d6d871", readme)

    def test_yeet_is_removed_from_repo_and_every_selection(self):
        self.assertFalse((ROOT / "skills/yeet").exists())
        configs = [ROOT / "rulesync.jsonc", *(ROOT / "groups").glob("*.jsonc")]
        for config in configs:
            self.assertNotIn("skills/yeet", read_jsonc(config)["inputRoots"], config)


if __name__ == "__main__":
    unittest.main()
