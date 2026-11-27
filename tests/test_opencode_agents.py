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
# Specialist sets that install whole from their folder group, agent included, not with default.
HERO_PICKABLE = ["build", "plan", *SPECIALISTS, "second-opinion", "local-model", "fcos-app-installer"]
FOLDER_AGENTS = {"ai_research": "ai-research", "career": "career", "reverse_engineering": "reverse-engineering"}
MOVED_ROOTS = {
    "agents/ai-research", "skills/ai-research",
    "agents/career", "skills/career-workspace", "skills/resume-skills", "skills/interview-coach",
    "agents/reverse-engineering", "mcp-servers/reva", "mcp-servers/radare2",
}
GLOBAL_ROOTS = {
    *(f"agents/{n}" for n in OWN_FOLDERS if n not in FOLDER_AGENTS.values()), "agents/security",
    "skills/designskills", "skills/security-threat-model", "skills/security-audit", "mcp-servers/zap",
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
        for key in generate.NATIVE_PLUGINS:
            available |= set(generate.BUNDLES[key])
        # REA is folder-only, so its skill may be absent.
        available.add("reverse-engineer-anything")
        # permission-tuning and the moved specialist sets install only with their folder groups.
        for bundle in ["permission-tuning", "ai-research", "career", "reverse-engineering"]:
            available |= set(generate.BUNDLES[bundle])
        for spec in generate.agent_specs().values():
            for bundle in spec.get("bundles", []):
                for skill in generate.BUNDLES[bundle]:
                    self.assertIn(skill, available, bundle)

    def test_native_plugin_skills_go_to_one_agent(self):
        # Plugins installed outside rulesync: only their owning agent may load them,
        # and build-family agents deny them so they never reach everyday requests.
        owners = {"trailofbits": "security", "iothackbot": "reverse-engineering"}
        self.assertEqual(set(generate.NATIVE_PLUGINS), set(owners))
        installed = set(default_skill_ids())
        samples = {}
        for key, owner in owners.items():
            skills = generate.BUNDLES[key]
            self.assertFalse(set(skills) & installed, key)  # IDs must not shadow repo skills
            self.assertFalse([s for s in skills if s in {"tests", "evals", "fixtures"}], key)
            samples[key] = skills[0]
            for name in SPECIALISTS:
                head, _ = frontmatter(agent_file(name))
                allowed = f'{{action: "skill", resource: "{skills[0]}", effect: allow}}' in head
                self.assertEqual(allowed, name == owner, (key, name))
        for name in BUILTINS:
            head, _ = frontmatter(agent_file(name))
            for skill in samples.values():
                self.assertIn(f'{{action: "skill", resource: "{skill}", effect: deny}}', head, name)
        self.assertEqual(len(generate.BUNDLES["trailofbits"]), 97)
        self.assertEqual(len(generate.BUNDLES["iothackbot"]), 14)
        data = generate.map_data()
        for key, owner in owners.items():
            group = next(g for g in data["skills"] if g["title"].startswith(generate.NATIVE_PLUGINS[key]["title"]))
            self.assertIn("installed separately", group["title"])
            self.assertEqual(group["agents"], [owner])
        hero = (ROOT / generate.HERO_FILES["light"]).read_text()
        self.assertIn("Trail of Bits 97 (security)", hero)

    def test_security_audit_belongs_to_the_security_agent(self):
        self.assertEqual(generate.BUNDLES["audit"], ["security-audit"])
        allow = '{action: "skill", resource: "security-audit", effect: allow}'
        for name in SPECIALISTS:
            head, _ = frontmatter(agent_file(name))
            self.assertEqual(allow in head, name == "security", name)
        for name in BUILTINS:
            head, _ = frontmatter(agent_file(name))
            self.assertIn('{action: "skill", resource: "security-audit", effect: deny}', head, name)
        for group in ["default", "work"]:
            self.assertIn("skills/security-audit", read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"], group)

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

    def test_folder_sets_leave_default(self):
        default = set(read_jsonc(ROOT / "groups/default.jsonc")["inputRoots"])
        self.assertFalse(MOVED_ROOTS & default, MOVED_ROOTS & default)
        installed = set(default_skill_ids())
        for group, agent in FOLDER_AGENTS.items():
            config = read_jsonc(ROOT / f"groups/{group}.jsonc")
            self.assertEqual(config["inputRoots"][0], f"agents/{agent}", group)
            self.assertIn("subagents", config["features"], group)
            # The agent's shared bundles (report, documents, humanizer, visuals) still come from default.
            for bundle in generate.SPECIALISTS[agent]["bundles"]:
                if bundle in generate.FOLDER_ONLY_BUNDLES or bundle in generate.NATIVE_PLUGINS:
                    continue
                self.assertTrue(set(generate.BUNDLES[bundle]) <= installed, (agent, bundle))
        moved = {r for r in MOVED_ROOTS if not r.startswith("agents/")}
        grouped = {r for g in FOLDER_AGENTS for r in read_jsonc(ROOT / f"groups/{g}.jsonc")["inputRoots"]}
        self.assertTrue(moved <= grouped, moved - grouped)

    def test_moved_bundles_show_as_folder_groups(self):
        data = generate.map_data()
        for group, agent in FOLDER_AGENTS.items():
            bundle = generate.BUNDLES[agent]
            entry = next(g for g in data["skills"] if g["title"].startswith(generate.BUNDLE_TITLES[agent]))
            self.assertIn(f"folder group {group}, not default", entry["title"])
            self.assertEqual(sorted(entry["items"]), sorted(bundle))
            self.assertEqual(entry["agents"], [agent])
        for name in BUILTINS:
            head, _ = frontmatter(agent_file(name))
            for skill in ["vllm", "resume-tailor", "binary-triage"]:
                self.assertIn(f'{{action: "skill", resource: "{skill}", effect: deny}}', head, name)

    def hero_texts(self):
        svg = ET.parse(ROOT / generate.HERO_FILES["light"]).getroot()
        return [t.text or "" for t in svg.iter("{http://www.w3.org/2000/svg}text")]

    def test_hero_shows_repo_totals(self):
        comps = [p for top in ("skills", "agents", "mcp-servers") for p in (ROOT / top).iterdir() if p.is_dir()]
        skills = {s.parent.name for c in comps for s in c.glob("skills/*/SKILL.md")}
        files = {p.stem for p in ROOT.glob("agents/*/subagents/*.md")}
        pick = set(HERO_PICKABLE)
        servers = {n for p in ROOT.glob("mcp-servers/*/mcp.jsonc") for n in read_jsonc(p)["mcpServers"]}
        plugins = len(generate.SUPERPOWERS) + sum(len(generate.BUNDLES[k]) for k in generate.NATIVE_PLUGINS)
        texts = self.hero_texts()
        for number, label in [(len(skills), "skills"), (len(pick), "agents you pick"),
                              (len(files - pick), "helper agents"), (len(servers), "MCP servers"),
                              (plugins, "plugin skills")]:
            i = texts.index(label)
            self.assertEqual(texts[i - 1], str(number), label)

    def test_hero_lists_every_group_with_its_agents(self):
        texts = self.hero_texts()
        groups = sorted(p.stem for p in ROOT.glob("groups/*.jsonc"))
        self.assertEqual(sorted(g for g, _scope in generate.hero_groups()), groups)
        for group in groups:
            roots = read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]
            skills = {p.parent.name for r in roots for p in (ROOT / r / "skills").glob("*/SKILL.md")}
            servers = {n for r in roots if (ROOT / r / "mcp.jsonc").is_file()
                       for n in read_jsonc(ROOT / r / "mcp.jsonc")["mcpServers"]}
            # A group's row is its name followed by its summary; an agent chip may share the name (career).
            row_start = lambda j: texts[j] in groups and j + 1 < len(texts) and re.fullmatch(r"\d+ skills.*", texts[j + 1])
            i = next(j for j in range(len(texts)) if texts[j] == group and row_start(j))
            summary = f"{len(skills)} skills" + (f" \u00b7 {len(servers)} MCP" if servers else "")
            self.assertEqual(texts[i + 1], summary, group)
            agents = {p.stem for r in roots for p in (ROOT / r / "subagents").glob("*.md")} & set(HERO_PICKABLE)
            end = next((j for j in range(i + 2, len(texts)) if row_start(j) or texts[j].isupper()), len(texts))
            row = [a for a in texts[i + 2:end] if a in HERO_PICKABLE]
            self.assertEqual(sorted(row), sorted(agents), group)
        self.assertEqual([g for g, scope in generate.hero_groups() if scope == "global"], ["default", "work"])

    def test_hero_chips_count_only_skills_the_agent_alone_loads(self):
        own = {"design": len(generate.BUNDLES["design"]), "career": len(generate.BUNDLES["career"]),
               "ai-research": len(generate.BUNDLES["ai-research"]),
               "reverse-engineering": len(generate.BUNDLES["reverse-engineering"]),
               "security": len(generate.BUNDLES["threat"]) + len(generate.BUNDLES["audit"]),
               "fcos-app-installer": len(generate.BUNDLES["fcos"])}
        texts = self.hero_texts()
        for agent in HERO_PICKABLE:
            # The chip, not a group row of the same name (a row's next text is its skill summary).
            i = next(j for j, s in enumerate(texts) if s == agent and not texts[j + 1].endswith(("skills", "MCP")))
            following = texts[i + 1] if i + 1 < len(texts) else ""
            if agent in own:
                self.assertEqual(following, str(own[agent]), agent)
            else:
                self.assertFalse(following.isdigit(), agent)

    def test_other_groups_keep_their_agents(self):
        # Only default gets the per-agent folders, except the sets that install with their folder group.
        # The security and reverse-engineering agents travel with their sets.
        for group in ROOT.glob("groups/*.jsonc"):
            if group.stem == "default":
                continue
            roots = read_jsonc(group)["inputRoots"]
            for name in OWN_FOLDERS:
                if FOLDER_AGENTS.get(group.stem) == name:
                    continue
                self.assertNotIn(f"agents/{name}", roots, group.stem)
        for group, folder in [("work", "security"),
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
        # All but explore, and the FCOS app installer, which loads two of the fifteen.
        self.assertEqual(len(superpowers["agents"]), len(generate.MAP_AGENTS) - 2)
        zap = next(g for g in data["mcp"] if g["title"] == "zap")
        self.assertEqual(zap["agents"], ["security"])


class FcosAppInstallerMapTests(unittest.TestCase):
    """The FCOS app installer is on the map (not in the hero) with the lists its own source declares.

    Its permission lists are hand-written in agents/fcos-app-installer/subagents/fcos-app-installer.md;
    generate.py reads them from there (generate.DECLARED), so the map cannot drift from the agent."""

    NAME = "fcos-app-installer"
    SKILLS = ["adapter-generic", "authgw-authentik", "dns-duckdns", "fileserver-truenas", "hypervisor-proxmox",
              "ingress-traefik", "researching-apps-for-self-hosting", "router-opnsense"]

    def test_it_is_declared_and_on_the_map_but_not_generated(self):
        self.assertEqual(generate.DECLARED, {self.NAME: "agents/fcos-app-installer/subagents/fcos-app-installer.md"})
        self.assertIn(self.NAME, generate.MAP_AGENTS)
        self.assertNotIn(self.NAME, generate.SPECIALISTS)
        self.assertNotIn(generate.DECLARED[self.NAME], generate.MARKED)
        self.assertNotIn(generate.DECLARED[self.NAME], generate.outputs())  # its file is the source of truth
        self.assertIn(self.NAME, generate.HERO_ORDER)  # a chip in its folder group's row

    def test_the_map_reads_the_skills_it_may_load_from_its_rules(self):
        allowed = generate.allowed_skills(generate.spec_of(self.NAME), set(default_skill_ids()))
        self.assertTrue(set(self.SKILLS) <= allowed)
        for skill in ("opencode", "package-management", "search", "exa-agent", "systematic-debugging",
                      "verification-before-completion", "docker-compose-patterns", "docker-destructive-guardrails"):
            self.assertIn(skill, allowed)
        for skill in ("eli5", "brainstorming", "frontend-design", "humanizer", "resume-tailor"):
            self.assertNotIn(skill, allowed)

    def test_the_map_reads_the_servers_and_subagents_too(self):
        spec = generate.spec_of(self.NAME)
        self.assertEqual(generate.allowed_mcp(spec), ["exa"])  # a deny list; Exa stays for research
        # Only the locked-down helper: any other agent runs with its own, wider permissions.
        self.assertEqual(spec["subagents"], ["adapter-drafter"])

    def test_its_skills_are_a_folder_group_bundle_only_it_may_load(self):
        data = generate.map_data()
        group = next(g for g in data["skills"] if g["title"].startswith("FCOS app installer skills"))
        self.assertIn("fcos_app_installer", group["title"])
        self.assertIn("not default", group["title"])
        self.assertEqual(sorted(group["items"]), self.SKILLS)
        self.assertEqual(group["agents"], [self.NAME])
        # The everyday agents never offer them, even where the default install and this folder meet.
        for name in BUILTINS:
            head, _ = frontmatter(agent_file(name))
            for skill in self.SKILLS:
                self.assertIn(f'{{action: "skill", resource: "{skill}", effect: deny}}', head, name)

    def test_the_helper_appears_as_a_subagent_only_it_starts(self):
        data = generate.map_data()
        by_title = {g["title"]: g for g in data["subagents"]}
        self.assertEqual(by_title["adapter-drafter"]["agents"], [self.NAME])
        for other in ("second-opinion", "security", "plan", "explore", "general"):
            if other in by_title:
                self.assertNotIn(self.NAME, by_title[other]["agents"], other)

    def declared(self, rules: str):
        import tempfile
        from pathlib import Path
        scratch = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            path = Path(tmp) / "agent.md"
            path.write_text(f"---\nname: x\nopencode:\n  mode: primary\n  permissions:\n{rules}---\n\nbody\n")
            return generate.declared_rules(str(path))

    def test_the_rule_reader_takes_the_forms_the_file_uses(self):
        good = ('    - action: skill\n      resource: "adapter-*"\n      effect: allow\n'
                '    # a comment between rules\n'
                '    - action: "pmb_*"\n      resource: "*"\n      effect: deny\n'
                '    - action: shell\n      resource: "rm -f *\\t*"\n      effect: deny\n')
        self.assertEqual(self.declared(good), [("skill", "adapter-*", "allow"), ("pmb_*", "*", "deny"),
                                               ("shell", "rm -f *\t*", "deny")])

    def test_the_rule_reader_refuses_any_form_it_could_misread_or_skip(self):
        # A rule it cannot read would drop out of the map without a word; refuse instead.
        for name, rules in {
            "flow style": '    - {action: skill, resource: "eli5", effect: allow}\n',
            "resource first": '    - resource: "eli5"\n      action: skill\n      effect: allow\n',
            "bare dash": '    -\n      action: skill\n      resource: "eli5"\n      effect: allow\n',
            "comment after the action": '    - action: skill # note\n      resource: "eli5"\n      effect: allow\n',
            "trailing space": '    - action: skill \n      resource: "eli5"\n      effect: allow\n',
            "single quotes": "    - action: 'skill'\n      resource: \"eli5\"\n      effect: allow\n",
            "unquoted resource": '    - action: skill\n      resource: eli5\n      effect: allow\n',
            "comment after the effect": '    - action: skill\n      resource: "eli5"\n      effect: allow # x\n',
            "extra key": '    - action: skill\n      resource: "eli5"\n      effect: allow\n      note: x\n',
            "escape in the resource": '    - action: skill\n      resource: "\\u0065li5"\n      effect: allow\n',
            "unknown effect": '    - action: skill\n      resource: "eli5"\n      effect: maybe\n',
        }.items():
            with self.subTest(form=name):
                with self.assertRaises(ValueError):
                    self.declared(rules)

    def test_it_alone_among_agents_reaches_exa_and_nothing_else_beyond_the_shared_tools(self):
        data = generate.map_data()
        exa = next(g for g in data["mcp"] if g["title"] == "exa")
        self.assertIn(self.NAME, exa["agents"])
        for server in ("docling", "pmb", "podman", "zap", "freecad", "presenton"):
            group = next(g for g in data["mcp"] if g["title"] == server)
            self.assertNotIn(self.NAME, group["agents"], server)


if __name__ == "__main__":
    unittest.main()
