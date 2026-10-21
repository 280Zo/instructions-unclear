"""Offline packaging checks; these never operate analysis tools or targets."""

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
IOT = ROOT / "skills/iothackbot/upstream/skills"


def read_jsonc(path):
    text = Path(path).read_text()
    text = re.sub(
        r'"(?:\\.|[^"\\])*"|//[^\n]*',
        lambda match: "" if match[0].startswith("//") else match[0],
        text,
    )
    return json.loads(text)


class SecurityReContextTests(unittest.TestCase):
    def test_upstream_ownership_policy_requires_verified_handoff(self):
        guide = (ROOT / "AGENTS.md").read_text()
        self.assertIn("## Upstream installation ownership", guide)
        for required in [
            "Prefer the upstream installer",
            "Remove duplicated extracted-skill maintenance only after",
            "Test subsequent rulesync generation",
            "Show the actual conflict",
        ]:
            self.assertIn(required, guide)
        self.assertNotIn("Never run an upstream's own installer", guide)

    def test_reviewed_mcp_launch_versions(self):
        cases = {
            "pmb": ["--from", "pmb-ai==1.2.3", "pmb-mcp"],
            "docling": [
                "--from",
                "docling-mcp[local]==3.3.0",
                "docling-mcp-server",
                "conversion",
                "generation",
                "--transport",
                "stdio",
            ],
        }
        for name, args in cases.items():
            server = read_jsonc(ROOT / f"mcp-servers/{name}/mcp.jsonc")["mcpServers"][
                name
            ]
            self.assertEqual(server["command"], "uvx")
            self.assertEqual(server["args"], args)
        rea = read_jsonc(ROOT / "mcp-servers/rea/mcp.jsonc")["mcpServers"]["rea"]
        self.assertIn("rea-agents@6.7.0", rea["args"])

    def test_exa_uses_current_upstream_skill_names(self):
        root = ROOT / "mcp-servers/exa/skills"
        self.assertEqual(
            {p.name for p in root.iterdir() if p.is_dir()}, {"search", "exa-agent"}
        )
        self.assertIn("name: search", (root / "search/SKILL.md").read_text())
        self.assertIn("name: Exa Agent", (root / "exa-agent/SKILL.md").read_text())
        server = read_jsonc(ROOT / "mcp-servers/exa/mcp.jsonc")["mcpServers"]["exa"]
        self.assertIn("agent_run", server["url"])

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
        }
        self.assertEqual({p.parent.name for p in IOT.glob("*/SKILL.md")}, expected)
        runtime = IOT.parent
        for directory in ["bin", "tools", "config", "wordlists"]:
            self.assertTrue((runtime / directory).is_dir(), directory)
        for path in [
            "picocom/serial_helper.py",
            "telnetshell/telnet_helper.py",
            "logicmso/analyze_protocol.py",
        ]:
            self.assertTrue((IOT / path).is_file(), path)

    def test_native_plugin_resources_resolve_without_flattening(self):
        tob = ROOT / "skills/trailofbits/upstream"
        for plugin in ["regression-hunt", "patching-bugs", "zeroize-audit"]:
            path = tob / "plugins" / plugin
            self.assertTrue((path / ".claude-plugin/plugin.json").is_file())
        patch = tob / "plugins/patching-bugs/skills/implement-patch"
        for relative in ["../../scripts/records.py", "../../references/records.md"]:
            self.assertTrue((patch / relative).is_file(), relative)
        zeroize = tob / "plugins/zeroize-audit/skills/zeroize-audit"
        self.assertTrue((zeroize / "../../agents/0-preflight.md").is_file())
        self.assertTrue((IOT.parent / ".claude-plugin/plugin.json").is_file())
        self.assertEqual((IOT.parent / ".claude/skills").resolve(), IOT.resolve())
        # A rulesync extraction would reintroduce competing ownership.
        native = {"skills/trailofbits", "skills/iothackbot"}
        for group in (ROOT / "groups").glob("*.jsonc"):
            self.assertFalse(native & set(read_jsonc(group)["inputRoots"]), group)

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
            "infosec": {"mcp-servers/zap"},
            "reverse_engineering": {
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
            {
                "career-intake",
                "career-master-resume",
                "career-start-application",
                "career-work-history",
            },
        )
        master = (workspace / "career-master-resume/SKILL.md").read_text()
        self.assertRegex(master, r"(?m)^name: career-master-resume$")
        intake = (workspace / "career-intake/SKILL.md").read_text()
        self.assertIn("## Setup", intake)
        self.assertIn("`inbox/`", intake)
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

    def test_career_workflow_dependencies_are_discoverable(self):
        workspace = ROOT / "skills/career-workspace"
        # Catch missing/misnamed packaged dependencies, not changes to prose.
        required = {
            "career-start-application",
            "career-intake",
            "career-master-resume",
            "career-work-history",
            "resume-version-manager",
            "job-description-analyzer",
            "resume-tailor",
            "resume-quantifier",
            "resume-bullet-writer",
            "resume-section-builder",
            "tech-resume-optimizer",
            "executive-resume-writer",
            "resume-ats-optimizer",
            "resume-formatter",
            "cover-letter-generator",
            "application-form-filler",
            "interview-coach",
        }
        available = {}
        config = read_jsonc(ROOT / "groups/career.jsonc")
        for root in config["inputRoots"]:
            for path in (ROOT / root / "skills").glob("*/SKILL.md"):
                name = re.search(r"^name:\s*(.+)$", path.read_text(), re.MULTILINE)
                self.assertIsNotNone(name, str(path))
                available[name[1].strip().strip("\"'")] = path
        self.assertFalse(required - available.keys(), required - available.keys())
        for name in required:
            self.assertEqual(available[name].parent.name, name)

    def test_career_intake_retains_single_tracker_ownership(self):
        workspace = ROOT / "skills/career-workspace"
        intake = (workspace / "skills/career-intake/SKILL.md").read_text()
        self.assertIn("resume-version-manager", intake)
        self.assertNotIn("resumes/versions.md", intake)
        self.assertNotIn("resumes/archive/", intake)
        template = (
            workspace / "skills/career-intake/templates/application.md"
        ).read_text()
        self.assertNotIn("resumes/archive/", template)
        self.assertNotIn("**Status:**", template)
        self.assertNotIn("## Timeline", template)
        readme = (workspace / "README.md").read_text()
        self.assertNotIn("versions.md", readme)

    def test_publication_docs_match_payload_and_nested_licenses(self):
        diagram = ROOT / "skills/diagram-design/skills/diagram-design"
        count = len(list((diagram / "references").glob("type-*.md")))
        self.assertEqual(count, 45)
        for doc in [ROOT / "README.md", ROOT / "skills/diagram-design/README.md"]:
            self.assertIn(f"{count} types", doc.read_text())
        diagram_readme = (ROOT / "skills/diagram-design/README.md").read_text()
        self.assertIn("Google Fonts", diagram_readme)
        self.assertIn("JavaScript", diagram_readme)
        self.assertIn(
            "https://github.com/oleksiijko/pmb",
            (ROOT / "mcp-servers/pmb/README.md").read_text(),
        )
        licenses = (ROOT / "THIRD_PARTY_LICENSES.md").read_text()
        nested = licenses.split("### Nested ML paper-writing template assets", 1)[
            1
        ].split("## trailofbits/skills", 1)[0]
        templates = ROOT / "skills/ai-research/skills/ml-paper-writing/templates"
        for asset in templates.rglob("*"):
            if asset.is_file():
                self.assertIn(f"`{asset.relative_to(templates)}`", nested)
        self.assertIn("LPPL Version 1.3c 2008-05-04", nested)
        self.assertIn("not established", nested)
        self.assertIn(
            "not a blanket license", (ROOT / "skills/ai-research/README.md").read_text()
        )

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

    def test_published_status_and_upstream_deviations_are_current(self):
        path = ROOT / "reference/security-re-tooling.md"
        self.assertTrue(path.is_file())
        assessment = path.read_text()
        self.assertFalse("other candidates are not yet pinned" in assessment)
        self.assertFalse("needs a pinned-version check" in assessment)


if __name__ == "__main__":
    unittest.main()
