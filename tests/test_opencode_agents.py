"""Offline checks for the agents agents/generate.py writes and the agent map."""

import fnmatch
import json
import re
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

from test_security_re_context import ROOT, read_jsonc

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "agents"))
import generate  # noqa: E402

BUILTINS = {"build": "primary", "plan": "primary", "general": "subagent", "explore": "subagent"}
SPECIALISTS = ["design", "career", "ai-research", "security", "reverse-engineering", "3d-modeling"]
# Agents that have a folder of their own; security and reverse-engineering join their sets.
OWN_FOLDERS = [*BUILTINS, "design", "career", "ai-research", "3d-modeling"]
GLOBAL_ROOTS = {
    *(f"agents/{n}" for n in OWN_FOLDERS), "agents/security", "agents/reverse-engineering",
    "skills/designskills", "skills/resume-skills", "skills/interview-coach",
    "skills/career-workspace", "skills/ai-research", "skills/security-threat-model",
    "mcp-servers/reva", "mcp-servers/radare2", "mcp-servers/zap",
}


def agent_file(name):
    return ROOT / generate.agent_path(name)


def frontmatter(path):
    text = path.read_text()
    match = re.match(r"---\n(.*?)\n---\n(.*)\Z", text, re.S)
    if match is None:
        raise AssertionError(f"No frontmatter in {path}")
    return match[1], match[2]


def default_skill_ids():
    ids = {}
    for root in read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"]:
        for skill in (ROOT / root / "skills").glob("*/SKILL.md"):
            ids.setdefault(skill.parent.name, []).append(root)
    return ids


def rule_lines(head):
    return [l.strip() for l in head.splitlines() if l.strip().startswith("- {action")]


class AgentTests(unittest.TestCase):
    def test_generated_files_are_current(self):
        run = subprocess.run(
            [sys.executable, "-B", str(ROOT / "agents/generate.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_one_file_per_agent_in_its_folder(self):
        self.assertEqual(set(generate.SPECIALISTS), set(SPECIALISTS))
        self.assertEqual(generate.OVERRIDES, BUILTINS)
        for name in OWN_FOLDERS:
            files = sorted(p.name for p in (ROOT / f"agents/{name}/subagents").glob("*.md"))
            self.assertEqual(files, [f"{name}.md"], name)
            self.assertTrue((ROOT / f"agents/{name}/README.md").is_file(), name)
        for name in ["security", "reverse-engineering"]:
            self.assertTrue(agent_file(name).is_file(), name)
        self.assertEqual(list(ROOT.glob("agents/**/*.portable.md")), [])
        # Replaced on 2026-10-26 by the per-agent folders.
        for old in ["agents/specialists", "agents/opencode-overrides"]:
            self.assertFalse((ROOT / old).exists(), f"delete {old}")

    def test_default_agent_file_names_are_unique(self):
        # rulesync merges input roots by file path: a later root's file with the
        # same name replaces an earlier one, even when its targets differ.
        seen = {}
        for root in read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"]:
            for path in (ROOT / root / "subagents").glob("*.md"):
                self.assertNotIn(path.name, seen, f"{root} and {seen.get(path.name)}")
                seen[path.name] = root

    def test_builtins_add_only_denies_for_opencode(self):
        for name, mode in BUILTINS.items():
            head, body = frontmatter(agent_file(name))
            self.assertEqual(body.strip(), "", name)  # a body would replace OpenCode's prompt
            self.assertIn('targets: ["opencode"]', head, name)
            self.assertIn(f"\n  mode: {mode}\n", head, name)
            self.assertNotIn("description:", head, name)
            self.assertNotIn("effect: allow", head, name)
            for skill in ["anatomy", "humanizer", "security-best-practices"]:
                self.assertNotIn(f'"{skill}"', head, name)
            for skill in ["typography", "resume-tailor", "geo-sleuth", "binary-triage"]:
                self.assertIn(f'{{action: "skill", resource: "{skill}", effect: deny}}', head, name)
            self.assertIn('{action: "freecad_*", resource: "*", effect: deny}', head, name)

    def test_specialists_are_one_file_for_every_tool(self):
        for name in SPECIALISTS:
            head, body = frontmatter(agent_file(name))
            spec = generate.SPECIALISTS[name]
            self.assertIn('targets: ["*"]', head, name)
            self.assertIn("\n  mode: all\n", head, name)
            self.assertEqual(body.strip(), generate.agent_body(spec), name)
            self.assertIn("## How to work", body, name)  # stands in for OpenCode's base prompt
            self.assertNotIn("OpenCode", body, name)  # the body goes to every tool
            denied = [l.strip()[2:] for l in head.splitlines() if l.strip().startswith("- mcp__")]
            self.assertEqual(denied, [f"mcp__{m}" for m in generate.MCP if m not in spec["mcp"]], name)
            lines = rule_lines(head)
            self.assertEqual(lines[0], '- {action: "skill", resource: "*", effect: deny}', name)
            self.assertIn('- {action: "skill", resource: "humanizer", effect: allow}', lines, name)
            self.assertNotIn('- {action: "skill", resource: "eli5", effect: allow}', lines, name)
            self.assertIn('- {action: "subagent", resource: "*", effect: deny}', lines, name)
        design, _ = frontmatter(agent_file("design"))
        self.assertIn('resource: "typography", effect: allow', design)
        self.assertNotIn('resource: "resume-tailor"', design)
        modeling, _ = frontmatter(agent_file("3d-modeling"))
        self.assertNotIn('"freecad_*"', modeling)
        self.assertIn('{action: "zap_*", resource: "*", effect: deny}', modeling)

    def test_specialist_skills_exist(self):
        available = set(default_skill_ids()) | set(generate.SHARED)
        # REA stays folder-only (user decision, 2026-10-25), so its skill may be absent.
        available.add("reverse-engineer-anything")
        for spec in generate.agent_specs().values():
            for bundle in spec.get("bundles", []):
                for skill in generate.BUNDLES[bundle]:
                    self.assertIn(skill, available, bundle)

    def test_local_model_keeps_unrestricted_delegation(self):
        head, _ = frontmatter(ROOT / "agents/local-model/subagents/local-model.md")
        self.assertNotIn('action: "subagent"', head)
        self.assertIn('{action: "skill", resource: "*", effect: deny}', head)

    def test_routing_hands_denied_skills_to_their_agent(self):
        routing = (ROOT / "rules/routing/rules/routing.md").read_text()
        self.assertIn("denied to the current agent", routing)
        for name in SPECIALISTS:
            self.assertIn(f"`{name}`", routing)

    def test_mcp_rules_name_known_servers_only(self):
        for path in [*(agent_file(n) for n in [*SPECIALISTS, *BUILTINS]), *(ROOT / p for p in generate.MARKED)]:
            head, _ = frontmatter(path)
            for action in re.findall(r'action: "([^"]+)"', head):
                if action in {"skill", "subagent"}:
                    continue
                self.assertIn(action, generate.MCP.values(), path)

    def test_every_repo_mcp_server_has_a_permission_pattern(self):
        # Specialists only deny servers listed in generate.MCP, so a new server
        # missing from it would be open to every agent.
        for config in ROOT.glob("mcp-servers/*/mcp.jsonc"):
            for name in read_jsonc(config)["mcpServers"]:
                self.assertIn(name, generate.MCP, f"{config.parent.name}: add {name} to MCP")
                action = f"{re.sub(r'[^A-Za-z0-9_]', '_', name)}_tool"
                self.assertTrue(fnmatch.fnmatchcase(action, generate.MCP[name]), name)

    def test_default_installs_every_agent_bundle_once(self):
        default = read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"]
        self.assertEqual(default, read_jsonc(ROOT / "rulesync.jsonc")["inputRoots"])
        self.assertTrue(GLOBAL_ROOTS <= set(default), GLOBAL_ROOTS - set(default))
        self.assertNotIn("mcp-servers/rea", default)
        self.assertEqual(default[0], "rules/shell-preamble")
        self.assertEqual(default[-1], "rules/shell-preamble-reminder")
        duplicates = {k: v for k, v in default_skill_ids().items() if len(v) > 1}
        self.assertEqual(duplicates, {})

    def test_other_groups_keep_their_agents(self):
        # Only default gets the per-agent folders (user decision, 2026-10-25).
        # The security and reverse-engineering agents travel with their sets.
        for group in ROOT.glob("groups/*.jsonc"):
            if group.stem == "default":
                continue
            roots = read_jsonc(group)["inputRoots"]
            for name in OWN_FOLDERS:
                self.assertNotIn(f"agents/{name}", roots, group.stem)
        for group, folder in [("work", "security"), ("infosec", "security"),
                              ("reverse_engineering", "reverse-engineering")]:
            self.assertIn(f"agents/{folder}", read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"])

    def test_agent_map_is_in_readme_and_pages_file(self):
        readme = (ROOT / "README.md").read_text()
        self.assertIn(generate.MAP_BEGIN, readme)
        self.assertIn(generate.PAGES_URL, readme)
        block = readme.split(generate.MAP_BEGIN, 1)[1].split(generate.MAP_END, 1)[0]
        # The hero sits at the top, before the install instructions.
        self.assertLess(readme.index(generate.MAP_BEGIN), readme.index("## Let your agent install it"))
        for path in generate.HERO_FILES.values():
            self.assertIn(path, block)
            svg = ET.parse(ROOT / path).getroot()
            self.assertEqual(svg.get("role"), "img")
            labels = " ".join(t.text or "" for t in svg.iter("{http://www.w3.org/2000/svg}text"))
            for name in SPECIALISTS:
                self.assertIn(name.split("-")[0], labels, path)
            raw = (ROOT / path).read_text().replace('xmlns="http://www.w3.org/2000/svg"', "")
            self.assertNotIn("http", raw, path)  # GitHub can't load external fonts or images in an SVG
        page = (ROOT / "docs/agents-map.html").read_text()
        data = json.loads(re.search(r"const DATA = (.*?);\nconst map", page, re.S)[1])
        self.assertEqual(data["agents"], generate.MAP_AGENTS)
        superpowers = next(g for g in data["skills"] if g["title"].startswith("Superpowers"))
        self.assertEqual(len(superpowers["agents"]), len(generate.MAP_AGENTS) - 1)  # all but explore
        zap = next(g for g in data["mcp"] if g["title"] == "zap")
        self.assertEqual(zap["agents"], ["security"])


if __name__ == "__main__":
    unittest.main()
