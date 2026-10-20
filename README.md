# instructions-unclear

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Installs with rulesync](https://img.shields.io/badge/installs%20with-rulesync-8A2BE2)](https://github.com/dyoshikawa/rulesync)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-standard-green)](https://agentskills.io)
[![AGENTS.md](https://img.shields.io/badge/AGENTS.md-ready-orange)](https://agents.md)

Rules, agents, skills, MCP servers, and plugins for AI coding tools. Pick the pieces you want and [rulesync](https://github.com/dyoshikawa/rulesync) installs them into Claude Code, Codex, OpenCode and about 40 other tools, each in its own format.

## What's included

Every folder below installs on its own. Open a group to see what's in it; each folder's README covers its setup.

<details>
<summary>Rules: how the agent works</summary>

| Folder                                                            | Adds                                                                |
| ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| [`rules/shell-preamble`](rules/shell-preamble/)                   | Explain each shell command before running it                        |
| [`rules/shell-preamble-reminder`](rules/shell-preamble-reminder/) | Short preamble reminder placed last in the installed rules          |
| [`rules/scope-secrets-approvals`](rules/scope-secrets-approvals/) | Where to work, what never to touch, what to ask before doing        |
| [`rules/engineering`](rules/engineering/)                         | Small changes, commands, verification                               |
| [`rules/secure-coding`](rules/secure-coding/)                     | The security mistakes AI-written code makes most often              |
| [`rules/communication`](rules/communication/)                     | State assumptions and summarize at the end                          |

</details>

<details>
<summary>Agents: second opinions, local models and security checks</summary>

| Folder                                              | Adds                                                                                                   |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`agents/second-opinion`](agents/second-opinion/)   | `second-opinion` reviews how the session is going; `evaluator` and `metacognitive` check answers and reasoning |
| [`agents/local-model`](agents/local-model/) | Small working turns, scoped delegation and safe pause/resume handoffs for local models or fragile connections |
| [`agents/security-compliance`](agents/security-compliance/) | A security auditor agent and a compliance-check command; included in the default global install |
| [`agents/security-scanning`](agents/security-scanning/) | Security auditor and threat-modeling agents, 5 skills and 3 commands; included in the default global install |

</details>

<details>
<summary>MCP servers: web search, documents, project memory, code graph, PowerPoint, CAD</summary>

| Folder                                                        | Adds                                                                                                                                     | Needs          |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| [`mcp-servers/exa`](mcp-servers/exa/)                         | Exa web search, a web research rule, skills `code-search-exa` and `exa-research`                                                         | An Exa API key |
| [`mcp-servers/docling`](mcp-servers/docling/)                 | Docling, which reads PDFs, Office files and scans, and a rule for using it                                                               | uv             |
| [`mcp-servers/pmb`](mcp-servers/pmb/)                         | PMB, project memory that survives between sessions, and a rule for using it                                                              | uv             |
| [`mcp-servers/codebase-memory`](mcp-servers/codebase-memory/) | A knowledge graph of your codebase for "who calls this" and "what breaks if" questions, and a skill for using it. Installed switched off | uv             |
| [`mcp-servers/presenton`](mcp-servers/presenton/)             | Presenton, for decks you can edit in PowerPoint or Google Slides. Installed switched off                                                 | Docker         |
| [`mcp-servers/freecad`](mcp-servers/freecad/)                 | FreeCAD control: build and edit 3D models, run analyses. Installed switched off                                                          | FreeCAD, uv    |

</details>

<details>
<summary>Skills: explaining, reports, packages, visuals, design, writing, thinking, photo geolocation, careers</summary>

| Folder                                                | Adds                                                                                                      |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [`skills/eli5`](skills/eli5/)                         | `eli5`: a plain-English tutor for one unfamiliar thing                                                    |
| [`skills/report`](skills/report/)                     | `report`: evidence-backed write-ups of material you've gathered                                           |
| [`skills/package-management`](skills/package-management/) | `package-management`, and a rule to load it: installing and running packages safely                   |
| [`skills/visual-explainer`](skills/visual-explainer/) | `visual-explainer`: HTML pages and decks for explanations, plans and reviews                              |
| [`skills/diagram-design`](skills/diagram-design/)     | `diagram-design`: 39 kinds of diagram as static HTML and SVG                                              |
| [`skills/frontend-slides`](skills/frontend-slides/)   | `frontend-slides`: HTML slide decks, with style previews to pick from                                     |
| [`skills/anthropic-design`](skills/anthropic-design/) | `frontend-design` for UI work, `theme-factory` for one shared look across outputs                         |
| [`skills/humanizer`](skills/humanizer/)               | `humanizer`: rewrites text that sounds AI-written                                                         |
| [`skills/distilly`](skills/distilly/)                 | `distilly`: turns a public figure, colleague or someone you know into a skill that thinks the way they do |
| [`skills/geo-sleuth`](skills/geo-sleuth/)             | `geo-sleuth`: works out where and when a photo was taken, with checkable evidence                         |
| [`skills/resume-skills`](skills/resume-skills/)       | 22 skills for resumes, cover letters, applications, interviews and offers. Career group only              |
| [`skills/interview-coach`](skills/interview-coach/)   | `interview-coach`: interview prep, mock interviews, debriefs and a storybank, with scoring. Career group only |
| [`skills/career-workspace`](skills/career-workspace/) | 3 skills that file career records in one folder and build a master resume and official work history from them. Career group only |

</details>

<details>
<summary>Profiles: sets that load only in a folder you choose</summary>

A profile installs into one folder instead of your home folder, keeping specialist context separate from your normal setup. Start your coding tool there to load it; discovery and context costs depend on the assistant.

| Folder                                      | Adds                                                                                                 |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| [`skills/ai-research`](skills/ai-research/) | 98 AI research skills: training, fine-tuning, inference, evaluation, RAG, agents, paper writing      |
| [`skills/trailofbits`](skills/trailofbits/) | 83 security skills and 30 agents from Trail of Bits: code review, static analysis, fuzzing, auditing |
| [`mcp-servers/rea`](mcp-servers/rea/)       | REA, an MCP server and skill for reverse engineering apps, websites, APKs and binaries               |
| [`skills/iothackbot`](skills/iothackbot/) | 13 IoT/firmware/console skills, a shared-tool skill and complete helper assets |
| [`mcp-servers/zap`](mcp-servers/zap/) | Official ZAP MCP connection for web-security workflows; disabled until configured |
| [`mcp-servers/reva`](mcp-servers/reva/) | Shared Ghidra projects and 6 companion skills; MCP connection disabled |
| [`mcp-servers/radare2`](mcp-servers/radare2/) | Optional radare2-native MCP connection; disabled, read-only tools |
| [`agents/reverse-engineering`](agents/reverse-engineering/) | Reverse-engineer, firmware and malware analyst agents, 4 skills |

Each README has its install command.

</details>

<details>
<summary>Plugins: installed through each tool (or by your agent), not rulesync</summary>

Each README has steps for you and steps your agent can follow ("install X by following its README"). Any rule that goes with a plugin installs through rulesync like the rest.

| Folder                                                          | Adds                                                                                                                                                                  |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`plugins/superpowers`](plugins/superpowers/)                   | Superpowers: skills for planning, test-driven development, debugging, code review and finishing work, loaded automatically |
| [`plugins/opencode-quota`](plugins/opencode-quota/)             | Plan quota and token use in OpenCode                                                                                                                                  |
| [`plugins/opencode-claude-auth`](plugins/opencode-claude-auth/) | Use a Claude Pro or Max subscription in OpenCode 2                                                                                                                    |

</details>

## Install

You need [Node.js](https://nodejs.org) 22 or newer; `npx` runs rulesync. Clone the repo and work from its root:

```bash
git clone https://github.com/280Zo/instructions-unclear.git && cd instructions-unclear
```

Then name the folders you want, the tools you use, and the kinds of content to install:

```bash
npx rulesync@33.0.0 generate --global \
  --targets opencode,claudecode \
  --features rules,skills \
  --input-roots rules/shell-preamble rules/scope-secrets-approvals skills/diagram-design
```

| Option          | Meaning                                                                                            |
| --------------- | -------------------------------------------------------------------------------------------------- |
| `--targets`     | The tools to install into, such as `opencode`, `claudecode`, `codexcli`, `geminicli`, `cursor`     |
| `--features`    | Which kinds of content to take: `rules`, `skills`, `subagents`, `commands`, `mcp`                  |
| `--input-roots` | The folders you picked. Leave it out to install everything in `rulesync.jsonc` except the profiles |
| `--global`      | Install into your home folder. Always include it; without it, rulesync writes into this repo       |

Do any setup a folder's README lists (an API key, a `uv tool install`, Docker) before or after; the order doesn't matter.

Before you run it, know what gets replaced:

- `rules` replaces your tool's global instructions file (such as `~/.config/opencode/AGENTS.md` or `~/.claude/CLAUDE.md`) with only the rules from this run.
- `mcp` replaces your tool's MCP server list with only the servers from this run.
- Skills and agents are added. One with the same name as an existing one overwrites it; nothing else is deleted.

Back up anything you want to keep. Because rules and MCP servers are replaced, list every folder you want each time you install. To save your picks, put them in `rulesync.local.jsonc` (git ignores it), and rulesync uses that list instead of `rulesync.jsonc`'s:

```jsonc
{
  "inputRoots": ["rules/shell-preamble", "rules/scope-secrets-approvals", "skills/diagram-design"]
}
```

Then the command is just `npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features rules,skills`.

Plugins install differently: through each tool, or by asking your agent to follow the plugin's README. Profiles install into a folder you choose; their READMEs have the command.

### Install groups

Saved selections, so you don't have to list folders. [`groups/README.md`](groups/) has each one's command and what it includes.

| Group | For |
|---|---|
| `default` | Everything in `rulesync.jsonc`, into OpenCode |
| `work` | OpenCode, Copilot and Copilot CLI on a work machine |
| `writing_reporting` | Writing, reports and visuals, without touching MCP settings |
| `infosec` | Security context, IoTHackBot and a disabled ZAP connection, in a folder you choose |
| `ai_research` | AI research skills, in a folder you choose |
| `career` | Career skills, and a career agent later, in a folder you choose |
| `reverse_engineering` | REA, RE agents, IoTHackBot and disabled ReVa/radare2 connections, in a folder you choose |

```bash
npx rulesync@33.0.0 generate --config groups/default.jsonc --global
```

None of them installs the programs the skills and MCP servers use; each folder's README covers that.

See [reference/](reference/) for published assessments, including the [security and reverse-engineering inventory](reference/security-re-tooling.md) and [persistent agent knowledge investigation](reference/agent-knowledge/README.md). Each integration's README distinguishes installed context from separately required software.

## Updating

Run `git pull`, then the same install command again. Tools a folder depends on, such as the uv-installed MCP servers, update as its README describes.

## Customizing

Fork the repo and make it yours: add your own rules under `rules/`, swap skills and agents in and out, and point `inputRoots` at what you keep. [`AGENTS.md`](AGENTS.md) is the guide for that, written so an AI agent can follow it too: the layout, keeping tool-specific settings portable, adding plugins, keeping secrets out, checking upstreams for updates, and verifying changes.

## License

My own work here is [MIT](LICENSE) licensed, © 2026 280Zo. Third-party files keep their own licenses; see [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
