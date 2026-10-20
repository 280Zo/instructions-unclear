"""Offline packaging checks; these never operate analysis tools or targets."""

import ast
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
IOT = ROOT / "skills/iothackbot/skills"


def read_jsonc(path):
    text = Path(path).read_text()
    text = re.sub(
        r'"(?:\\.|[^"\\])*"|//[^\n]*',
        lambda match: "" if match[0].startswith("//") else match[0],
        text,
    )
    return json.loads(text)


class SecurityReContextTests(unittest.TestCase):
    def test_published_assessment_excludes_removed_candidate(self):
        assessment = ROOT / "reference/security-re-tooling.md"
        self.assertTrue(assessment.is_file())
        self.assertNotIn("pentagi", assessment.read_text().lower())

    def test_complete_iot_collection_and_shared_assets(self):
        expected = {
            "apktool",
            "chipsec",
            "ffind",
            "iotnet",
            "jadx",
            "jtagprobe",
            "logicmso",
            "netflows",
            "nmap",
            "onvifscan",
            "picocom",
            "telnetshell",
            "wsdiscovery",
            "iothackbot-tools",
        }
        self.assertEqual({p.parent.name for p in IOT.glob("*/SKILL.md")}, expected)
        runtime = IOT / "iothackbot-tools"
        for directory in ["bin", "tools", "config", "wordlists"]:
            self.assertTrue((runtime / directory).is_dir(), directory)
        for path in [
            "picocom/serial_helper.py",
            "telnetshell/telnet_helper.py",
            "logicmso/analyze_protocol.py",
        ]:
            self.assertTrue((IOT / path).is_file(), path)

    def test_iot_portability_and_permission_fixes(self):
        self.assertTrue(IOT.is_dir())
        for path in IOT.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py"}:
                text = path.read_text()
                self.assertNotIn(".claude/skills/", text, str(path))
                self.assertNotRegex(text, r"chmod\s+(?:-\w+\s+)*777")
                if path.suffix == ".py":
                    ast.parse(text, filename=str(path))
        chipsec = (IOT / "chipsec/SKILL.md").read_text()
        self.assertIn("-nl", chipsec)
        self.assertIn("user-writable", chipsec)
        logic = (IOT / "logicmso/SKILL.md").read_text()
        self.assertNotIn("pip install saleae-mso-api", logic)
        self.assertIn("downloads.saleae.com", logic)

    def test_new_mcp_templates_are_disabled(self):
        for name in ["zap", "reva", "radare2"]:
            config = ROOT / f"mcp-servers/{name}/mcp.jsonc"
            self.assertTrue(config.is_file(), str(config))
            entry = read_jsonc(config)["mcpServers"][name]
            self.assertIs(entry["disabled"], True)
        r2 = read_jsonc(ROOT / "mcp-servers/radare2/mcp.jsonc")["mcpServers"]["radare2"]
        self.assertIn("-R", r2["args"])

    def test_group_roots_and_features(self):
        expected = {
            "infosec": {"skills/iothackbot", "mcp-servers/zap"},
            "reverse_engineering": {
                "skills/iothackbot",
                "mcp-servers/reva",
                "mcp-servers/radare2",
            },
        }
        for group, roots in expected.items():
            config = read_jsonc(ROOT / f"groups/{group}.jsonc")
            self.assertTrue(roots <= set(config["inputRoots"]))
            self.assertIn("mcp", config["features"])
            self.assertFalse(config["delete"])
            for root in config["inputRoots"]:
                self.assertTrue((ROOT / root).is_dir(), root)

    def test_career_group_is_folder_scoped(self):
        config = read_jsonc(ROOT / "groups/career.jsonc")
        self.assertEqual(
            config["inputRoots"],
            [
                "skills/resume-skills",
                "skills/interview-coach",
                "skills/career-workspace",
            ],
        )
        workspace = ROOT / "skills/career-workspace/skills"
        self.assertEqual(
            {p.parent.name for p in workspace.glob("*/SKILL.md")},
            {"career-intake", "career-master-resume", "career-work-history"},
        )
        master = (workspace / "career-master-resume/SKILL.md").read_text()
        self.assertRegex(master, r"(?m)^name: career-master-resume$")
        self.assertIn("Hand-off prompt", master)
        self.assertIn("<WORKSPACE>/resumes/master-resume.md", master)
        intake = (workspace / "career-intake/SKILL.md").read_text()
        for template in re.findall(r"`templates/([a-z-]+\.md)`", intake):
            self.assertTrue(
                (workspace / "career-intake/templates" / template).is_file()
            )
        self.assertEqual(set(config["features"]), {"skills", "subagents"})
        self.assertFalse(config["delete"])
        skills = list((ROOT / "skills/resume-skills/skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 22)
        coach_root = ROOT / "skills/interview-coach/skills"
        coach_skills = list(coach_root.glob("*/SKILL.md"))
        self.assertEqual(len(coach_skills), 1)
        coach = coach_root / "interview-coach"
        self.assertEqual(coach_skills, [coach / "SKILL.md"])
        coach_text = (coach / "SKILL.md").read_text()
        self.assertRegex(coach_text, r"(?m)^name: interview-coach$")
        commands = re.findall(r"^\| `([a-z]+)(?:[^`]*)` \|", coach_text, re.MULTILINE)
        self.assertEqual(len(commands), 25)
        for command in commands:
            self.assertTrue((coach / f"references/commands/{command}.md").is_file())
        for doc in ["groups/README.md", "README.md"]:
            self.assertIn("career", (ROOT / doc).read_text())

    def test_skill_names_are_unique_in_each_group(self):
        for group in ["infosec", "reverse_engineering", "career"]:
            names = []
            for root in read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]:
                for skill in (ROOT / root / "skills").glob("*/SKILL.md"):
                    match = re.search(
                        r"^name:\s*(.+)$", skill.read_text(), re.MULTILINE
                    )
                    self.assertIsNotNone(match, str(skill))
                    names.append(match[1].strip().strip("\"'"))
            self.assertEqual(len(names), len(set(names)), group)

    def test_specialist_roots_do_not_change_global_default(self):
        default = read_jsonc(ROOT / "rulesync.jsonc")
        mirror = read_jsonc(ROOT / "groups/default.jsonc")
        self.assertEqual(default["inputRoots"], mirror["inputRoots"])
        specialists = {
            "skills/iothackbot",
            "mcp-servers/reva",
            "mcp-servers/zap",
            "mcp-servers/radare2",
        }
        self.assertFalse(specialists & set(default["inputRoots"]))

    def test_bundled_helper_examples_use_installed_paths(self):
        for path in IOT.rglob("*"):
            if path.is_file() and path.suffix in {".md", ".py", ".txt"}:
                unresolved = re.search(
                    r"python3?\s+(?:skills/logicmso/)?analyze_protocol\.py|"
                    r"--script\s+enum_(?:system|network|files|security)\.txt",
                    path.read_text(),
                )
                self.assertIsNone(unresolved, str(path))

    def test_published_status_and_upstream_deviations_are_current(self):
        path = ROOT / "reference/security-re-tooling.md"
        self.assertTrue(path.is_file())
        assessment = path.read_text()
        self.assertFalse("other candidates are not yet pinned" in assessment)
        self.assertFalse("needs a pinned-version check" in assessment)
        self.assertIn(
            "formatting",
            (ROOT / "skills/iothackbot/README.md").read_text().lower(),
        )


if __name__ == "__main__":
    unittest.main()
