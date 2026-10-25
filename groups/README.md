# Install groups

Saved selections, so you don't have to name every folder. Run every command from the repo root. If you see `Rulesync source directory '.../.rulesync' does not exist`, you ran it from somewhere else: rulesync ignores a `--config` path it can't find instead of reporting it.

| Group | Installs into | What it is |
|---|---|---|
| [`default`](#default) | Your home folder, OpenCode | The repo's default selection |
| [`work`](#work) | Your home folder, OpenCode, Copilot and Copilot CLI | Rules, agents, MCP servers and writing skills for a work machine |
| [`writing_reporting`](#writing_reporting) | Your home folder, OpenCode | Rules plus writing, report and visual skills, without touching MCP settings |
| [`infosec`](#infosec) | A folder you choose | The security bundle (rule, 2 agents, 4 commands), 11 security and utility skills and disabled ZAP MCP; native security plugins install separately |
| [`ai_research`](#ai_research) | A folder you choose | 98 AI research skills |
| [`career`](#career) | A folder you choose | 22 career skills, the interview coach and 4 career-workspace skills, including the application starter; a career agent will be added |
| [`reverse_engineering`](#reverse_engineering) | A folder you choose | REA, RE agents and disabled ReVa/radare2 MCPs; IoTHackBot is native-owned |
| [`design`](#design) | A folder you choose | 28 design skills: graphics, UI, palettes, typography, brand and critique |

## How they behave

- **Home-folder groups** (`default`, `work`, `writing_reporting`) replace your tool's whole rules file with that group's rules. Skills, agents and commands are added or overwritten by name; nothing else is deleted, so switching to a smaller group leaves the extra skills in place.
- `default` and `work` also replace your tool's MCP server list. `writing_reporting` leaves it alone.
- `infosec` and `reverse_engineering` write their selected MCP sets into the chosen folder. Generate a combined selection in one run if you need both; sequential runs can replace the earlier MCP set. New ZAP/ReVa/radare2 connections are disabled, and generated configuration contains environment references rather than key values.
- **Folder groups** (`infosec`, `ai_research`, `career`, `reverse_engineering`, `design`) install into one folder and load only when you start your tool there. Never add `--global` to them.
- Add `--dry-run` to any command to list what it would write without writing anything.
- None of them installs the programs a skill or MCP server uses. See each folder's README for that.
- Codebase-memory's complete integration belongs to its upstream installer: apply it after rulesync, as its [verified ordering requirement](../mcp-servers/codebase-memory/README.md) explains. The repo ships no extracted skill.

The [security and reverse-engineering tooling assessment](../reference/security-re-tooling.md) lists the complete inventory, selected integrations and deferred alternatives. The [agent-knowledge investigation](../reference/agent-knowledge/README.md) separates objectives, concepts, technologies, experiments and decisions. `reference/`, including its subfolders, holds published material, not install roots; it changes no group selections or counts. Context generation does not install native analysis tools or authorize target operations.

## default

Everything in [`rulesync.jsonc`](../rulesync.jsonc), into OpenCode: all selected global rules (including `routing` and `preferences`), the second-opinion and local-model agents, the repo-owned [`agents/security`](../agents/security/) bundle, and the selected global MCP servers/skills. Folder-only integrations below do not change the global default.

`documents` is included, and so are `handoff`, `teach` and `wait-what` (user-invoked only), Docker's 4 core skills ([`skills/docker`](../skills/docker/)) and the [Podman MCP](../mcp-servers/podman/), switched off. Docker's Sandboxes and Docker Agent skills are in `work` only. `security-threat-model` is deliberately excluded from this selection; it remains in `infosec` and `work`. With `delete: false`, generation does not remove an already-installed global copy. Review and separately approve stale-copy cleanup if one exists; no live files were deleted by this repo change.

```bash
npx rulesync@38.0.0 generate --config groups/default.jsonc --global
```

`npx rulesync@38.0.0 generate --global` does the same thing. Before adopting 38.0.0, isolated generation of the original default selection with 33.0.0 and 38.0.0 produced 604 byte-identical files. The refreshed selections are verified separately.

## work

Use `--dry-run` first:

```bash
npx rulesync@38.0.0 generate --config groups/work.jsonc --global --dry-run
npx rulesync@38.0.0 generate --config groups/work.jsonc --global
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
skills/playwright
skills/report
skills/visual-explainer
skills/handoff
skills/teach
skills/wait-what
```

What each tool gets:

| Tool | Gets | Skipped |
|---|---|---|
| OpenCode | Rules, 6 agents, 37 skills, 4 commands, MCP servers | Nothing |
| Copilot CLI | Rules, 6 agents, 37 skills, MCP servers (`~/.copilot/`) | Commands: Copilot CLI has none |
| Copilot (VS Code) | Rules, agents and skills, written to the same `~/.copilot/` folder | MCP servers and commands: rulesync writes those for VS Code only inside a project, not globally |

Codebase-memory, Presenton, ZAP and Podman are written switched off. OpenCode gets `"enabled": false` on each; Copilot CLI gets them listed under `disabledMcpServers` in `~/.copilot/settings.json`. ZAP only becomes usable after you set up a local ZAP with its MCP add-on and turn it on yourself; enabling it still doesn't authorize scanning any target.

### Plugin installation prompt

> **Plugins installed by your agent**
>
> Install the Superpowers plugin and opencode-quota plugin by following their READMEs in the plugins folder.

## writing_reporting

Rules (including `routing` and `preferences`), `second-opinion`, the Docling, Exa and PMB rules and skills, and `eli5`, `report`, `humanizer`, `visual-explainer`, `diagram-design`, `frontend-slides`, `frontend-design`, `theme-factory`, Magnus's [`documents`](../skills/documents/), and Matt Pocock's [`handoff`](../skills/handoff/), [`teach`](../skills/teach/) and [`wait-what`](../skills/wait-what/). That's 15 skills. MCP servers you already have stay as they are. The document skill adds authoring and smoke validation; it does not replace Docling's OCR/extraction role.

```bash
npx rulesync@38.0.0 generate --config groups/writing_reporting.jsonc --global
```

## infosec

The repo-owned [security bundle](../agents/security/) (secure-coding rule, `security-auditor` and `threat-modeling-expert` agents, 6 skills including `security-best-practices`, and 4 commands), [`security-threat-model`](../skills/security-threat-model/), the four audio/capture/browser skills, and the [official ZAP connection](../mcp-servers/zap/). That's 11 skills, 2 agents, 4 commands and 1 disabled MCP connection. `security-threat-model` is excluded from `default`, not from this group. Installing skills authorizes none of their runtime operations. [Trail of Bits](../skills/trailofbits/) and [IoTHackBot](../skills/iothackbot/) use complete native plugins, installed separately rather than flattened by this group. No complete OpenCode equivalent is claimed. Each README lists prerequisites and ownership limits.

The rule lands in the folder's own `AGENTS.md`, which OpenCode reads along with your global one. If you also installed `default` or `work`, the security bundle is there globally too; the folder copies load only in that folder and are identical. Reverse engineering has its own group below.

```bash
mkdir -p ~/AI/infosec
npx rulesync@38.0.0 generate --config groups/infosec.jsonc --output-roots ~/AI/infosec
```

## ai_research

The 98 skills from [`skills/ai-research`](../skills/ai-research/).

```bash
mkdir -p ~/AI/ai_research
npx rulesync@38.0.0 generate --config groups/ai_research.jsonc --output-roots ~/AI/ai_research
```

## career

The 22 skills from [`skills/resume-skills`](../skills/resume-skills/), from [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), and [`interview-coach`](../skills/interview-coach/), from [noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill), and the 4 [`career-workspace`](../skills/career-workspace/) skills, written for this repo, that keep career records, build a master resume and official work history, and start a reviewed application. Say “Use career-start-application” to load the workflow and supply a job link when asked; no copied kickoff prompt is needed. The [career-workspace README](../skills/career-workspace/README.md#workflow) shows how all of these fit together. That's 27 skills. The group also takes agents, so a career agent can be added to it later, and writes the career routing rule (which skill owns each step) into the folder's own `AGENTS.md`. None of these skills are in `default`; they install only into the folder you choose. Document export also needs an installed document-authoring skill and its tools; the career group does not install them.

```bash
mkdir -p ~/AI/career
npx rulesync@38.0.0 generate --config groups/career.jsonc --output-roots ~/AI/career
```

## reverse_engineering

The [REA](../mcp-servers/rea/) MCP/skill, [reverse-engineering agents](../agents/reverse-engineering/), and optional [ReVa](../mcp-servers/reva/) and [radare2](../mcp-servers/radare2/) connections. That's 11 skills, 3 agents and 3 MCP definitions: REA retains its existing enabled state; ReVa/radare2 are disabled until explicitly configured. ReVa's 6 companion skills can be discovered before its backend is enabled; they do not start it. [IoTHackBot](../skills/iothackbot/) is now installed through its native plugin separately, not generated here.

All component READMEs list prerequisites. Prefer REA for broad analysis; enable ReVa for shared Ghidra projects or radare2 for r2-specific work. Don't install their native skill plugins again alongside these same skills.

```bash
mkdir -p ~/AI/reverse_engineering
npx rulesync@38.0.0 generate --config groups/reverse_engineering.jsonc --output-roots ~/AI/reverse_engineering
```

## design

The 28 skills from [`skills/designskills`](../skills/designskills/), including `color-palette` and `design-context`, which the others read brand settings from. Inside this folder they take over design work from `frontend-design`, `frontend-slides`, `diagram-design`, `visual-explainer` and `theme-factory`; the group writes that routing rule into the folder's own `AGENTS.md`, so it loads only there. None of them are in `default` or `work`, because the skills depend on each other. Image generation needs a Gemini key and Python packages, and the render and critique scripts need Playwright; the [folder README](../skills/designskills/README.md#what-the-skills-need) lists them. Writes no MCP settings.

```bash
mkdir -p ~/AI/design
npx rulesync@38.0.0 generate --config groups/design.jsonc --output-roots ~/AI/design
```

## Other tools

Every group targets OpenCode by default (`work` adds the two Copilots). For other tools, add `--targets`, for example `--targets opencode,claudecode,codexcli`.

The security groups can also be generated for Claude Code and Codex CLI. Folder-scoped command support depends on the target; heed generation warnings rather than adding `--global` to work around them. Native plugin ownership is separate from this target override; it does not restore the retired flattened Trail of Bits/IoTHackBot profiles.

## Origin

Written for this repo. [MIT](../LICENSE).
