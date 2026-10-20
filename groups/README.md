# Install groups

Saved selections, so you don't have to name every folder. Run every command from the repo root. If you see `Rulesync source directory '.../.rulesync' does not exist`, you ran it from somewhere else: rulesync ignores a `--config` path it can't find instead of reporting it.

| Group | Installs into | What it is |
|---|---|---|
| [`default`](#default) | Your home folder, OpenCode | The repo's default selection |
| [`work`](#work) | Your home folder, OpenCode, Copilot and Copilot CLI | Rules, agents, MCP servers and writing skills for a work machine |
| [`writing_reporting`](#writing_reporting) | Your home folder, OpenCode | Rules plus writing, report and visual skills, without touching MCP settings |
| [`infosec`](#infosec) | A folder you choose | Security rule/agents, Trail of Bits, IoTHackBot and disabled ZAP MCP |
| [`ai_research`](#ai_research) | A folder you choose | 98 AI research skills |
| [`career`](#career) | A folder you choose | 22 career skills, the interview coach and 3 career-workspace skills; a career agent will be added |
| [`reverse_engineering`](#reverse_engineering) | A folder you choose | REA, RE agents, IoTHackBot and disabled ReVa/radare2 MCPs |

## How they behave

- **Home-folder groups** (`default`, `work`, `writing_reporting`) replace your tool's whole rules file with that group's rules. Skills, agents and commands are added or overwritten by name; nothing else is deleted, so switching to a smaller group leaves the extra skills in place.
- `default` and `work` also replace your tool's MCP server list. `writing_reporting` leaves it alone.
- `infosec` and `reverse_engineering` write their selected MCP sets into the chosen folder. Generate a combined selection in one run if you need both; sequential runs can replace the earlier MCP set. New ZAP/ReVa/radare2 connections are disabled, and generated configuration contains environment references rather than key values.
- **Folder groups** (`infosec`, `ai_research`, `career`, `reverse_engineering`) install into one folder and load only when you start your tool there. Never add `--global` to them.
- Add `--dry-run` to any command to list what it would write without writing anything.
- None of them installs the programs a skill or MCP server uses. See each folder's README for that.

The [security and reverse-engineering tooling assessment](../reference/security-re-tooling.md) lists the complete inventory, selected integrations and deferred alternatives. The [agent-knowledge investigation](../reference/agent-knowledge/README.md) separates objectives, concepts, technologies, experiments and decisions. `reference/`, including its subfolders, holds published material, not install roots; it changes no group selections or counts. Context generation does not install native analysis tools or authorize target operations.

## default

Everything in [`rulesync.jsonc`](../rulesync.jsonc), into OpenCode: all selected global rules, the second-opinion, local-model and both security agent sets, and the selected global MCP servers/skills. Folder-only integrations below do not change the global default.

```bash
npx rulesync@33.0.0 generate --config groups/default.jsonc --global
```

`npx rulesync@33.0.0 generate --global` does the same thing.

## work

Use `--dry-run` first:

```bash
npx rulesync@33.0.0 generate --config groups/work.jsonc --global --dry-run
npx rulesync@33.0.0 generate --config groups/work.jsonc --global
```

The config installs these folders into OpenCode, GitHub Copilot (VS Code) and Copilot CLI, with rules, skills, agents, commands and MCP servers:

```text
rules/shell-preamble                 skills/package-management
rules/scope-secrets-approvals        agents/local-model
rules/engineering                    agents/second-opinion
rules/secure-coding                  agents/security-compliance
rules/communication                  agents/security-scanning
rules/shell-preamble-reminder        mcp-servers/codebase-memory
skills/anthropic-design              mcp-servers/docling
skills/diagram-design                mcp-servers/exa
skills/eli5                          mcp-servers/pmb
skills/frontend-slides               mcp-servers/presenton
skills/humanizer
skills/report
skills/visual-explainer
```

What each tool gets:

| Tool | Gets | Skipped |
|---|---|---|
| OpenCode | Rules, 7 agents, 17 skills, 4 commands, MCP servers | Nothing |
| Copilot CLI | Rules, 7 agents, 17 skills, MCP servers (`~/.copilot/`) | Commands: Copilot CLI has none |
| Copilot (VS Code) | Rules, agents and skills, written to the same `~/.copilot/` folder | MCP servers and commands: rulesync writes those for VS Code only inside a project, not globally |

### Plugin installation prompt

> **Plugins installed by your agent**
>
> Install the Superpowers plugin and opencode-quota plugin by following their READMEs in the plugins folder.

## writing_reporting

Rules, `second-opinion`, the Docling, Exa and PMB rules and skills, and `eli5`, `report`, `humanizer`, `visual-explainer`, `diagram-design`, `frontend-slides`, `frontend-design` and `theme-factory`. MCP servers you already have stay as they are.

```bash
npx rulesync@33.0.0 generate --config groups/writing_reporting.jsonc --global
```

## infosec

The [`secure-coding`](../rules/secure-coding/) rule, the [compliance](../agents/security-compliance/) and [scanning](../agents/security-scanning/) agent sets, [Trail of Bits](../skills/trailofbits/), [IoTHackBot](../skills/iothackbot/) and the [official ZAP connection](../mcp-servers/zap/). That's 102 skills, 33 agents, 4 commands and 1 disabled MCP connection. Each README lists separate runtime tools and activation steps.

The rule lands in the folder's own `AGENTS.md`, which OpenCode reads along with your global one. If you also installed `default` or `work`, the secure-coding rule and the two agent sets are there globally too; the folder copies load only in that folder and are identical. Reverse engineering has its own group below.

```bash
mkdir -p ~/AI/infosec
npx rulesync@33.0.0 generate --config groups/infosec.jsonc --output-roots ~/AI/infosec
```

## ai_research

The 98 skills from [`skills/ai-research`](../skills/ai-research/).

```bash
mkdir -p ~/AI/ai_research
npx rulesync@33.0.0 generate --config groups/ai_research.jsonc --output-roots ~/AI/ai_research
```

## career

The 22 skills from [`skills/resume-skills`](../skills/resume-skills/), from [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), and [`interview-coach`](../skills/interview-coach/), from [noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill), and the 3 [`career-workspace`](../skills/career-workspace/) skills, written for this repo, that keep career records in the folder and build a master resume and official work history from them. The [career-workspace README](../skills/career-workspace/README.md#workflow) shows how all of these fit together for an application. That's 26 skills. The group also takes agents, so a career agent can be added to it later. None of these skills are in `default`; they install only into the folder you choose.

```bash
mkdir -p ~/AI/career
npx rulesync@33.0.0 generate --config groups/career.jsonc --output-roots ~/AI/career
```

## reverse_engineering

The [REA](../mcp-servers/rea/) MCP/skill, [reverse-engineering agents](../agents/reverse-engineering/), [IoTHackBot](../skills/iothackbot/), and optional [ReVa](../mcp-servers/reva/) and [radare2](../mcp-servers/radare2/) connections. That's 25 skills, 3 agents and 3 MCP definitions: REA retains its existing enabled state; ReVa/radare2 are disabled until explicitly configured. ReVa's 6 companion skills can be discovered before its backend is enabled; they do not start it.

All component READMEs list prerequisites. Prefer REA for broad analysis; enable ReVa for shared Ghidra projects or radare2 for r2-specific work. Don't install their native skill plugins again alongside these same skills.

```bash
mkdir -p ~/AI/reverse_engineering
npx rulesync@33.0.0 generate --config groups/reverse_engineering.jsonc --output-roots ~/AI/reverse_engineering
```

## Other tools

Every group targets OpenCode by default (`work` adds the two Copilots). For other tools, add `--targets`, for example `--targets opencode,claudecode,codexcli`.

The two security groups were also generated for Claude Code and Codex CLI. Codex skips infosec's 4 commands in folder scope (rulesync 33.0.0 supports Codex commands only globally); it still receives the skills, agents, rule and MCP config. Do not add `--global` to work around this limitation.

## Origin

Written for this repo. [MIT](../LICENSE).
