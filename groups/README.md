# Install groups

Saved selections, so you don't have to name every folder. Run every command from the repo root. If you see `Rulesync source directory '.../.rulesync' does not exist`, you ran it from somewhere else: rulesync ignores a `--config` path it can't find instead of reporting it.

| Group | Installs into | What it is |
|---|---|---|
| [`default`](#default) | Your home folder, OpenCode | The repo's default selection, with OpenCode agents that each see only their own skills |
| [`work`](#work) | Your home folder, OpenCode, Copilot and Copilot CLI | Rules, agents, MCP servers and writing skills for a work machine |
| [`writing_reporting`](#writing_reporting) | Your home folder, OpenCode | Rules plus writing, report and visual skills, without touching MCP settings |
| [`infosec`](#infosec) | A folder you choose | The security bundle (rule, 3 agents, 4 commands), 11 security and utility skills and disabled ZAP MCP; native security plugins install separately |
| [`ai_research`](#ai_research) | A folder you choose | 98 AI research skills |
| [`career`](#career) | A folder you choose | 22 career skills, the interview coach and 4 career-workspace skills, including the application starter. The `career` agent comes with `default` |
| [`reverse_engineering`](#reverse_engineering) | A folder you choose | REA, RE agents and disabled ReVa/radare2 MCPs; IoTHackBot is native-owned |
| [`design`](#design) | A folder you choose | 19 design skills (graphics, brand, palettes, typography, design systems, critique) plus `anatomy` |

## How they behave

- **Home-folder groups** (`default`, `work`, `writing_reporting`) replace your tool's whole rules file with that group's rules. Skills, agents and commands are added or overwritten by name; nothing else is deleted, so switching to a smaller group leaves the extra skills in place.
- `default` and `work` also replace your tool's MCP server list. `writing_reporting` leaves it alone.
- `infosec` and `reverse_engineering` write their selected MCP sets into the chosen folder. Generate a combined selection in one run if you need both; sequential runs can replace the earlier MCP set. New ZAP/ReVa/radare2 connections are disabled, and generated configuration contains environment references rather than key values.
- **Folder groups** (`infosec`, `ai_research`, `career`, `reverse_engineering`, `design`) install into one folder and load only when you start your tool there. Never add `--global` to them.
- Add `--dry-run` to any command to list what it would write without writing anything.
- None of them installs the programs a skill or MCP server uses. See each folder's README for that.
- Codebase-memory's complete integration belongs to its upstream installer: apply it after rulesync, as its [verified ordering requirement](../mcp-servers/codebase-memory/README.md) explains. The repo ships no extracted skill.

Context generation does not install native analysis tools or authorize target operations.

## default

Everything in [`rulesync.jsonc`](../rulesync.jsonc), into OpenCode: all selected global rules (including `routing`, the career routing rule and `preferences`), every [agent folder](../agents/README.md) (`design`, `career`, `ai-research`, `3d-modeling`, `second-opinion`, `local-model`, the `security` and `reverse-engineering` sets, and restrictions for OpenCode's `build`, `plan`, `general` and `explore`), the repo-owned [`agents/security`](../agents/security/) bundle, and the selected global MCP servers/skills.

Since 2026-10-25 `default` also installs the design, career, AI research, threat-model and reverse-engineering skills, plus switched-off ZAP, ReVa and radare2 connections. Each OpenCode agent loads only its own skills and tools, so these add nothing to the other agents' requests. REA stays in the `reverse_engineering` folder group because it starts switched on. The folder groups below still work for other tools and workspaces.

`documents` is included, and so are `handoff`, `teach` and `wait-what` (user-invoked only), Docker's 4 core skills ([`skills/docker`](../skills/docker/)) and the [Podman MCP](../mcp-servers/podman/), switched off. Docker's Sandboxes and Docker Agent skills are in `work` only. `security-threat-model` is included, and only the `security` agent can load it.

```bash
npx rulesync@41.0.0 generate --config groups/default.jsonc --global
```

`npx rulesync@41.0.0 generate --global` does the same thing. Isolated generation of all eight groups with 38.0.0 and 41.0.0 changed only OpenCode agent frontmatter and MCP configuration; file counts and all other output bytes were unchanged. Native skill permission enforcement was tested with the installed OpenCode 2.1.3. See [the regression check](../tests/README.md#opencode-permission-regression).

## work

Use `--dry-run` first:

```bash
npx rulesync@41.0.0 generate --config groups/work.jsonc --global --dry-run
npx rulesync@41.0.0 generate --config groups/work.jsonc --global
```

The config installs these folders into OpenCode, GitHub Copilot (VS Code) and Copilot CLI, with rules, skills, agents, commands and MCP servers:

```text
rules/shell-preamble                 skills/package-management
rules/scope-secrets-approvals        agents/local-model
rules/engineering                    agents/second-opinion
agents/security                      mcp-servers/codebase-memory
rules/communication                  mcp-servers/docling
rules/routing                        mcp-servers/exa
rules/preferences                    mcp-servers/pmb
rules/shell-preamble-reminder        mcp-servers/presenton
skills/anthropic-design              mcp-servers/zap
skills/diagram-design                mcp-servers/podman
skills/anatomy
skills/docker
skills/docker-sandboxes-agent
skills/eli5
skills/frontend-slides
skills/humanizer
skills/documents
skills/transcribe
skills/speech
skills/security-threat-model
skills/screenshot
skills/playwright-cli
skills/report
skills/visual-explainer
skills/handoff
skills/teach
skills/wait-what
```

What each tool gets:

| Tool | Gets | Skipped |
|---|---|---|
| OpenCode | Rules, 7 agents, 38 skills, 4 commands, MCP servers | Nothing |
| Copilot CLI | Rules, 7 agents, 38 skills, MCP servers (`~/.copilot/`) | Commands: Copilot CLI has none |
| Copilot (VS Code) | Rules, agents and skills, written to the same `~/.copilot/` folder | MCP servers and commands: rulesync writes those for VS Code only inside a project, not globally |

The seventh agent, `security`, comes with `agents/security` (added 2026-10-26). In OpenCode it loads only its own skills; Copilot gets its instructions without that filter. The other specialist agents aren't in `work`.

Codebase-memory, Presenton, ZAP and Podman are written switched off. OpenCode V2 gets `"disabled": true` on each; Copilot CLI gets them listed under `disabledMcpServers` in `~/.copilot/settings.json`. ZAP only becomes usable after you set up a local ZAP with its MCP add-on and turn it on yourself; enabling it still doesn't authorize scanning any target.

### Plugin installation prompt

> **Plugins installed by your agent**
>
> Install the Superpowers plugin and opencode-quota plugin by following their READMEs in the plugins folder.

## writing_reporting

Rules (including `routing` and `preferences`), `second-opinion`, the Docling, Exa and PMB rules and skills, and `eli5`, `report`, `humanizer`, `visual-explainer`, `diagram-design`, `frontend-slides`, `frontend-design`, `theme-factory`, Magnus's [`documents`](../skills/documents/), and Matt Pocock's [`handoff`](../skills/handoff/), [`teach`](../skills/teach/) and [`wait-what`](../skills/wait-what/). That's 15 skills. MCP servers you already have stay as they are. The document skill adds authoring and smoke validation; it does not replace Docling's OCR/extraction role.

```bash
npx rulesync@41.0.0 generate --config groups/writing_reporting.jsonc --global
```

## infosec

The repo-owned [security bundle](../agents/security/) (secure-coding rule, the `security`, `security-auditor` and `threat-modeling-expert` agents, 6 skills including `security-best-practices`, and 4 commands), [`security-threat-model`](../skills/security-threat-model/), the four audio/capture/browser skills, and the [official ZAP connection](../mcp-servers/zap/). That's 11 skills, 3 agents, 4 commands and 1 disabled MCP connection. In OpenCode, pick the `security` agent: it can't load the audio skills, so use another agent for those. Installing skills authorizes none of their runtime operations. [Trail of Bits](../skills/trailofbits/) and [IoTHackBot](../skills/iothackbot/) use complete native plugins, installed separately rather than flattened by this group. No complete OpenCode equivalent is claimed. Each README lists prerequisites and ownership limits.

The rule lands in the folder's own `AGENTS.md`, which OpenCode reads along with your global one. If you also installed `default` or `work`, the security bundle is there globally too; the folder copies load only in that folder and are identical. Reverse engineering has its own group below.

```bash
mkdir -p ~/AI/infosec
npx rulesync@41.0.0 generate --config groups/infosec.jsonc --output-roots ~/AI/infosec
```

## ai_research

The 98 skills from [`skills/ai-research`](../skills/ai-research/). `default` also installs them for the OpenCode [`ai-research` agent](../agents/ai-research/), the only agent that sees them; use this group for other tools.

```bash
mkdir -p ~/AI/ai_research
npx rulesync@41.0.0 generate --config groups/ai_research.jsonc --output-roots ~/AI/ai_research
```

## career

The 22 skills from [`skills/resume-skills`](../skills/resume-skills/), from [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), and [`interview-coach`](../skills/interview-coach/), from [noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill), and the 4 [`career-workspace`](../skills/career-workspace/) skills, written for this repo, that keep career records, build a master resume and official work history, and start a reviewed application. Say “Use career-start-application” to load the workflow and supply a job link when asked; no copied kickoff prompt is needed. The [career-workspace README](../skills/career-workspace/README.md#workflow) shows how all of these fit together. That's 27 skills. The group also writes the career routing rule (which skill owns each step) into the folder's own `AGENTS.md`. In OpenCode, `default` installs these skills globally for the [`career` agent](../agents/career/); use this group for other tools, or start OpenCode in a career folder either way, because the skills keep records relative to it. Document export also needs an installed document-authoring skill and its tools; the career group does not install them.

```bash
mkdir -p ~/AI/career
npx rulesync@41.0.0 generate --config groups/career.jsonc --output-roots ~/AI/career
```

## reverse_engineering

The [REA](../mcp-servers/rea/) MCP/skill, [reverse-engineering agents](../agents/reverse-engineering/), and optional [ReVa](../mcp-servers/reva/) and [radare2](../mcp-servers/radare2/) connections. That's 11 skills, 4 agents (pick `reverse-engineering`; the other three are its helpers) and 3 MCP definitions: REA retains its existing enabled state; ReVa/radare2 are disabled until explicitly configured. ReVa's 6 companion skills can be discovered before its backend is enabled; they do not start it. [IoTHackBot](../skills/iothackbot/) is now installed through its native plugin separately, not generated here.

`default` installs everything here except REA for the OpenCode [`reverse-engineering` agent](../agents/reverse-engineering/). REA's connection starts switched on, so it stays in this group; start OpenCode in the group's folder to use it. All component READMEs list prerequisites. Prefer REA for broad analysis; enable ReVa for shared Ghidra projects or radare2 for r2-specific work. Don't install their native skill plugins again alongside these same skills.

```bash
mkdir -p ~/AI/reverse_engineering
npx rulesync@41.0.0 generate --config groups/reverse_engineering.jsonc --output-roots ~/AI/reverse_engineering
```

## design

The 19 skills from [`skills/designskills`](../skills/designskills/), including `color-palette` and `design-context`, which the others read brand settings from. Nine upstream skills that overlapped `frontend-design`, `frontend-slides` and `diagram-design` were removed on 2026-10-25, so the folder needs no routing rule. `default` installs them for the OpenCode [`design` agent](../agents/design/); `work` doesn't include them. The group also installs [`anatomy`](../skills/anatomy/), the isometric explainer, which `default` and `work` include too. Image generation needs a Gemini key and Python packages, and the render and critique scripts need Playwright; the [folder README](../skills/designskills/README.md#what-the-skills-need) lists them. Writes no MCP settings.

```bash
mkdir -p ~/AI/design
npx rulesync@41.0.0 generate --config groups/design.jsonc --output-roots ~/AI/design
```

## Other tools

Every group targets OpenCode by default (`work` adds the two Copilots). For other tools, add `--targets`, for example `--targets opencode,claudecode,codexcli`.

The security groups can also be generated for Claude Code and Codex CLI. Folder-scoped command support depends on the target; heed generation warnings rather than adding `--global` to work around them. Native plugin ownership is separate from this target override; it does not restore the retired flattened Trail of Bits/IoTHackBot profiles.

## For agents: install, remove and update

Install. Follow [Installing on a machine](../AGENTS.md#installing-on-a-machine): read every `groups/*.jsonc` live, preview in a throwaway home, and get approval before the live run. Each folder in a group has its own README with prerequisites and verify steps.

Remove. Follow [Removing or replacing a component](../AGENTS.md#removing-or-replacing-a-component) for each folder in the group.

- Home-folder groups: switching to a smaller group replaces the rules file, and `default` and `work` also replace the MCP list. `writing_reporting` leaves the MCP list alone, so switching to it from `default` or `work` keeps their MCP servers. Because of `delete: false`, skills, agents and commands from the larger group stay installed. Compare the two groups' `inputRoots`, list the names that only the old group provided, and delete them only with approval.
- Folder groups: nothing outside the chosen folder changes. Delete the files the group generated there (the tool directories such as `.opencode/` or `.claude/`, plus the folder's own `AGENTS.md` and MCP settings where the group writes them), or the whole folder if nothing else lives there. Never delete the user's own work in that folder.

Programs, containers and plugins a group's folders used stay installed unless the user asks.

Update. A group changes when a folder is added, renamed or removed; update `groups/*.jsonc`, this README's counts and the root README together, and keep `default.jsonc` in step with `rulesync.jsonc`. Folder pins and the rulesync version are covered by [Check for updates](../AGENTS.md#check-for-updates).

## Origin

Written for this repo. [MIT](../LICENSE).
