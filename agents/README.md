# Agents

One folder per agent or agent set, each with the skills, rules and commands that go with it. Each README has its install command. Installing copies every agent file into one flat folder per tool (for OpenCode, `~/.config/opencode/agents/`), so these folders only organize the repo.

| Folder | Adds |
| --- | --- |
| [`design`](design/) | Graphic, brand and visual design. Installed by default |
| [`career`](career/) | Career records, resumes, applications and interview coaching. Installed by default |
| [`ai-research`](ai-research/) | AI and machine-learning research and engineering. Installed by default |
| [`3d-modeling`](3d-modeling/) | CAD work in FreeCAD. Installed by default |
| [`security`](security/) | The `security` agent plus one repo-owned security bundle: secure-coding rule, security auditor and threat-modeling agents, 6 skills, 4 commands. Installed by default |
| [`reverse-engineering`](reverse-engineering/) | The `reverse-engineering` agent plus reverse-engineer, firmware and malware agents and 4 skills. Profile; also installed by default |
| [`second-opinion`](second-opinion/) | `second-opinion`, `evaluator` and `metacognitive`: a second check on the main agent's work. Installed by default |
| [`local-model`](local-model/) | Small working increments, scoped delegation and fast safe pause/resume handoffs. Installed by default; use as primary or delegated worker |
| [`build`](build/), [`plan`](plan/), [`general`](general/), [`explore`](explore/) | Restrictions for OpenCode's own agents of these names, so they don't see the specialist skills. Installed by default, for OpenCode only |

A profile installs into one folder you choose, not your home folder. To install several profiles into the same folder, run each one's command with the same `--output-roots`.

## How agents keep skills out of each other's requests

Every installed skill's description is sent with every request, unless the agent can't use it. The `default` group installs about 200 skills; the AI research skills alone add about 7,000 tokens. In OpenCode, each agent therefore lists the skills, MCP servers and subagents it may use, and OpenCode leaves the rest out of what the model sees and blocks calls to them (checked on OpenCode 2.1.3). The [root README](../README.md)'s hero image shows how many skills each agent sees; the [interactive map](https://280zo.github.io/instructions-unclear/agents-map.html) ([source](../docs/agents-map.html)) lists every skill, server and subagent.

Every agent gets the Superpowers skills, `package-management`, Exa's `search` and `exa-agent`, OpenCode's built-in `opencode` skill, the user-invoked `handoff`, `teach` and `wait-what`, and the Exa and PMB servers; all but `second-opinion` also get Docling.

| Agent | Own skills | Extra MCP | Can start |
|---|---|---|---|
| `build`, `plan` | Everything except the specialist skills below | Presenton, Podman, codebase-memory | any agent |
| `design` | Design skills, UI, slides, visuals, browser, documents | Presenton | `general`, `explore` |
| `career` | Resume skills, career workspace, interview coach, report, documents | | `general`, `explore` |
| `ai-research` | AI research skills, report, documents, visuals | | `general`, `explore` |
| `security` | Secure coding, SAST, threat modeling, geo-sleuth, browser, report, documents, and the Trail of Bits plugin when installed | ZAP | `general`, `explore`, `security-auditor`, `threat-modeling-expert` |
| `reverse-engineering` | Reverse-engineering, ReVa and REA skills, report, and the IoTHackBot plugin when installed | REA, ReVa, radare2 | `general`, `explore`, the three RE agents |
| `3d-modeling` | Report, documents, visuals, browser | FreeCAD | `general`, `explore` |
| `second-opinion` | Shared skills only | | `evaluator`, `metacognitive`, `general`, `explore` |
| `local-model` | Humanizer, report | | any agent |

`build`, `plan`, `general` and `explore` are OpenCode's own agents. Their files only add deny rules, so OpenCode keeps each built-in agent's prompt and policy. OpenCode's `explore` already denies skills and MCP tools; its file repeats those denials in case a later release loosens the built-in policy. They install only for OpenCode, the one tool that has these agents and can filter skills.

The six specialists are one file each for every tool. An agent file's body is the agent's whole system prompt in Claude Code and the other tools, and in OpenCode it replaces OpenCode's base prompt, as it does for `second-opinion` and `local-model`; your rules files and skills still load. So each specialist's body ends with a shared "How to work" section, adapted and made tool-neutral from OpenCode 2.1.3's default prompt ([license](../THIRD_PARTY_LICENSES.md#anomalycoopencode)). It is `BASE_INSTRUCTIONS` in `generate.py`; compare it with OpenCode's `packages/core/src/session/runner/prompt/system.txt` when you upgrade OpenCode.

## What each assistant enforces

| Assistant | Skills | MCP servers | Subagents | Pick as main agent |
|---|---|---|---|---|
| OpenCode | Hidden from the model and blocked | Hidden and blocked | Hidden and blocked | Yes (`mode: all`) |
| Claude Code | Not filtered | Denied servers removed (`disallowedTools: mcp__<server>`) | Not filtered | Through `claude --agent <name>` |
| Codex | Not filtered | Not filtered | Not filtered | No; spawned only |
| Copilot, Copilot CLI | Not filtered | Not filtered | Not filtered | Yes (agent picker) |
| Cursor | Not filtered | Not filtered | Not filtered | Depends on Cursor |

The OpenCode row was tested on OpenCode 2.1.3. The others follow each vendor's documentation and weren't run here. Why the gaps:

- **Claude Code** has no skill filter. Its `skills` field preloads skills; it doesn't hide the rest.
- **Codex** can disable individual skills with `skills.config`, but rulesync 41 writes that table before `developer_instructions`, so TOML reads the instructions as part of the table. Its agents can't change MCP servers.
- **Copilot**'s `tools` field is an allowlist. Leaving out a built-in tool alias removes that tool, and this couldn't be tested without Copilot, so it isn't set.

Outside OpenCode every installed skill stays visible, so install specialist skills there with their folder groups (`design`, `career`, `ai_research`, `infosec`, `reverse_engineering`) rather than globally. Installing just the agents (`--features subagents`) gives other tools their instructions without the skills.

## Install

The [`default` group](../groups/README.md#default) installs every agent folder above and every skill folder the agents filter:

```bash
npx rulesync@41.0.0 generate --config groups/default.jsonc --global
```

It needs rulesync 41 or later. Older releases add a `name:` field that makes OpenCode 2.1.3 drop every agent permission without warning. ZAP, ReVa, radare2, FreeCAD, Presenton, Podman and codebase-memory are written switched off. REA isn't installed globally because it starts switched on; use it in a folder made with the [`reverse_engineering` group](../groups/README.md#reverse_engineering).

Other groups install agents with their sets: `infosec` and `work` include `agents/security`, so they also get the `security` agent; `reverse_engineering` gets the `reverse-engineering` agent. `work` and `writing_reporting` also include `second-opinion`, and `work` includes `local-model`. The `design`, `career`, `ai-research`, `3d-modeling`, `build`, `plan`, `general` and `explore` folders are in `default` only.

## Use

- OpenCode: pick an agent with `/agents`, or ask `build` to hand a task to one: "have the career agent tailor my resume for this posting". `general`, `explore` and the helper agents are subagents: other agents start them, and they don't appear in the picker. Claude Code: `claude --agent design`, or ask for the agent by name. Codex, Copilot and Cursor: use each tool's agent picker or ask for it by name.
- Start your tool in the folder whose files you want used. The career skills keep records relative to it, and the design skills read `.agents/design-context.md` from it.
- In OpenCode an agent can't load a skill it doesn't list. The global routing rule tells it to hand the task to the owning agent instead of substituting another skill.

## Limits

- **Delegated work uses the child's permissions.** A specialist that hands work to `general` gets build's skills and tools in that child. The custom subagents `security-auditor`, `threat-modeling-expert`, `reverse-engineer`, `malware-analyst`, `firmware-analyst`, `evaluator` and `metacognitive` have no skill or MCP filter. Hand specialist work to the specialist itself.
- **Agent allows win over your global denies** in OpenCode, because agent rules come after global rules. To block something everywhere, use an OpenCode [policy](https://opencode.ai/v2/docs/permissions/), which runs after these rules.
- **Only listed MCP servers are filtered.** A server you add outside this repo is open to every agent until you add it to `MCP` in `generate.py`.
- **Only listed plugins are filtered.** Skills from a plugin not in `NATIVE_PLUGINS` (or, for Superpowers, `SUPERPOWERS`) reach `build`, `plan` and `general` in every request, and no specialist can load them.
- A real model can still ask for a skill by name; OpenCode then denies the call.

## Keeping the README image and agent map current

The image at the top of the [root README](../README.md) (`docs/hero-light.svg` and `docs/hero-dark.svg`) and the [interactive map](https://280zo.github.io/instructions-unclear/agents-map.html) are drawn from the agent definitions in `generate.py` and the folders `default` installs, so their skill and server counts follow those files. Never edit the SVGs by hand. Regenerate them, with the rest of the generated agent files, after any of these:

- adding, removing or renaming a skill folder, or adding or removing skills inside one;
- adding or removing a folder in `groups/default.jsonc` (and its mirror `rulesync.jsonc`);
- adding, removing or renaming an MCP server;
- adding, removing or renaming an agent, or changing its skills, servers or description;
- a new Superpowers release that adds or renames skills (update `SUPERPOWERS` in `generate.py` first);
- adding, removing or updating a plugin that brings skills, such as Trail of Bits (see [Adding a plugin that brings skills](#adding-a-plugin-that-brings-skills));
- changing the agent cards (`HERO_AGENTS` in `generate.py`) or the look (`agents/hero.py`).

From the repo root:

```bash
python3 agents/generate.py
python3 -m unittest discover -s tests
```

The tests fail when the image is out of date, so forgetting shows up there. To preview it, open `docs/hero-light.svg` in a browser. The image uses system fonts, because GitHub can't load web fonts inside README images. Its accent is deep teal, set in `hero.py`, instead of the diagram style guide's default orange.

## For agents: install, remove and update

### Install

Use the `default` group as above. Don't add the per-agent folders (`build`, `plan`, `general`, `explore`, `design`, `career`, `ai-research`, `3d-modeling`) to other groups: `work` also targets Copilot, which can't filter skills. To verify in OpenCode, ask the user to open `/agents` in a new session and check that the six specialists, `build`, `plan`, `second-opinion` and `local-model` appear, then run [the runtime check](../tests/README.md#opencode-permission-regression) instead of asking a model which skills it has. For other tools, the runtime check only confirms the generated files.

### Remove

Follow [Removing or replacing a component](../AGENTS.md#removing-or-replacing-a-component). Each agent's files are `~/.config/opencode/agents/<name>.md`, `~/.claude/agents/<name>.md`, `~/.codex/agents/<name>.toml` and `~/.copilot/agents/<name>.agent.md`; Cursor's is `<name>.md` in its agents folder. Deleting the OpenCode `build`, `plan`, `general` or `explore` file restores the unrestricted built-in agent. Skill folders installed by `default` stay until removed separately.

### Update

[`generate.py`](generate.py) writes the six specialists, the four OpenCode files, the marked blocks in `second-opinion` and `local-model`, the root README hero (`docs/hero-light.svg`, `docs/hero-dark.svg`, drawn by [`hero.py`](hero.py)) and `docs/agents-map.html`. `SPECIALISTS` holds each agent's description, instructions, skill bundles, MCP servers and subagents; `BUNDLES` lists skill groups, and the specialist bundles are read from their skill folders. After changing the manifest, adding or removing a skill folder, or adding an MCP server:

```bash
python3 agents/generate.py
python3 -m unittest discover -s tests
```

Run it after every event listed in [Keeping the README image and agent map current](#keeping-the-readme-image-and-agent-map-current), in the same change, and include the regenerated `docs/hero-*.svg` and `docs/agents-map.html` in it. When an image change is visible (new card, new counts, new look), render a preview (for example `rsvg-convert -w 1800 docs/hero-light.svg -o /tmp/opencode/hero.png`) and look at both themes before reporting it done; check that long agent names and tags still fit their cards. Card labels and tags are in `HERO_AGENTS`; a new user-selectable agent needs a card there (the layout fits nine, so ask the user which to merge or drop beyond that). Colors, fonts and layout are in `hero.py`; keep its 4 px grid, accessible `<title>`/`<desc>`, and no external fonts, images or links.

`tests/test_opencode_agents.py` fails until every generated file matches. Don't edit generated files or the lines between `BEGIN generated` and `END generated` markers by hand. Superpowers is a plugin, so its skill IDs are listed in the script; update them when Superpowers adds or renames a skill.

#### Adding a plugin that brings skills

rulesync doesn't install plugins, so their skills never appear in the `default` group, yet OpenCode still sends them to every agent that doesn't deny them. Whenever you add a plugin that ships skills (in `plugins/` or as a native tree such as `skills/trailofbits/upstream/`):

1. Decide which agent owns it. If every agent should have it, as with Superpowers, list its skill IDs in `SHARED` and skip the next two steps.
2. Otherwise add it to `NATIVE_PLUGINS` in `generate.py` with a title and the folder holding its complete tree. The script reads skill IDs from every `SKILL.md` there, skipping test and eval fixtures. If the repo holds no copy, list the IDs explicitly, as `SUPERPOWERS` does.
3. Add its key to the owning agent's `bundles` in `SPECIALISTS`, and mention it in that agent's `instructions`.
4. Run `python3 agents/generate.py` and the tests. Build-family agents now deny the skills, the owner allows them, the map lists the plugin as installed separately, and the hero footnote names it.
5. Check that no new skill ID matches an existing repo skill; `test_native_plugin_skills_go_to_one_agent` fails if one does, because denying it would also block the repo skill. Update that test's owner list, and the plugin's wrapper README and this README's agent table.
6. Run the runtime check: it plants one skill from each listed plugin and confirms only the owner can load it.

Permission resources are skill directory IDs, not display names: `0-autoresearch-skill`, not `autoresearch`. MCP rules name each known server. Never use a blanket `*_*` rule, because built-in actions such as `external_directory` also contain underscores. Agent files must have unique names across a group's folders: rulesync merges folders by file path, so a later file with the same name replaces an earlier one without warning.

The interactive map works on GitHub Pages only after the repo owner sets **Settings → Pages → Build and deployment** to deploy from the default branch's `/docs` folder; `docs/.nojekyll` makes Pages serve it unchanged. Until then the link returns 404; open the file locally with `firefox docs/agents-map.html`.

## Origin

This README, `generate.py` and the generated agents are written for this repo by 280Zo. [MIT](../LICENSE). The specialists' "How to work" section is adapted from [OpenCode](https://github.com/anomalyco/opencode) v2.1.3, MIT, © 2025 opencode; see [THIRD_PARTY_LICENSES.md](../THIRD_PARTY_LICENSES.md#anomalycoopencode). Each set's own README covers its origin.
