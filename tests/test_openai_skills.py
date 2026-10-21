"""Offline checks for the pinned OpenAI skills, standalone and bundled."""

import unittest

from test_security_re_context import ROOT, read_jsonc

STANDALONE = [
    "transcribe",
    "speech",
    "security-threat-model",
    "screenshot",
    "playwright",
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
            "skills/playwright/skills/playwright": [
                "scripts/playwright_cli.sh",
                "NOTICE.txt",
            ],
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
        for group in ["default", "work", "infosec"]:
            roots = read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]
            for name in STANDALONE:
                expected = not (group == "default" and name == "security-threat-model")
                self.assertEqual(f"skills/{name}" in roots, expected, (group, name))
            self.assertIn("agents/security", roots)
            names = []
            for source in roots:
                names.extend(
                    p.parent.name for p in (ROOT / source / "skills").glob("*/SKILL.md")
                )
            self.assertEqual(len(names), len(set(names)), group)
            self.assertIn("security-best-practices", names)
            self.assertEqual("security-threat-model" in names, group != "default")
        self.assertEqual(
            read_jsonc(ROOT / "rulesync.jsonc")["inputRoots"],
            read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"],
        )

    def test_yeet_is_removed_from_repo_and_every_selection(self):
        self.assertFalse((ROOT / "skills/yeet").exists())
        configs = [ROOT / "rulesync.jsonc", *(ROOT / "groups").glob("*.jsonc")]
        for config in configs:
            self.assertNotIn("skills/yeet", read_jsonc(config)["inputRoots"], config)


if __name__ == "__main__":
    unittest.main()
