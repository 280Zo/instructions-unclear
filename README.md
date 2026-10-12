# instructions-unclear

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Installs with rulesync](https://img.shields.io/badge/installs%20with-rulesync-8A2BE2)](https://github.com/dyoshikawa/rulesync)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-standard-green)](https://agentskills.io)
[![AGENTS.md](https://img.shields.io/badge/AGENTS.md-ready-orange)](https://agents.md)

AI context files for any coding agent. These are the rules, agents, skills and MCP servers I use every day, in one repo you can install into Claude Code, Codex, Cursor, Gemini CLI, OpenCode and about 40 other AI coding tools with one command.

- 7 rules covering shell safety, working policy, web research, document handling and project memory
- 3 agents that review answers, keep long tasks on track and step in when a session stalls
- 28 skills, from research reports and plain-English explainers to a full resume and job-search kit
- 3 MCP servers: Exa for web search, Docling for reading documents, PMB for project memory
- Written once and translated into each tool's own format, so nothing gets copied by hand

## Quick start

```bash
git clone https://github.com/280Zo/instructions-unclear.git && cd instructions-unclear
npx rulesync generate --global --targets claudecode,codexcli,opencode --features rules,subagents,skills
```

Swap the `--targets` list for the tools you use (see [Supported tools](#supported-tools)). This installs the rules, agents and skills. Adding the MCP servers takes two more steps, covered in [Installation](#installation).

> [!WARNING]
> Installing replaces each tool's global instructions file, such as `~/.claude/CLAUDE.md` or `~/.config/opencode/AGENTS.md`. Back up anything you want to keep first.

## Contents

- [Why](#why)
- [What's included](#whats-included)
- [Supported tools](#supported-tools)
- [Installation](#installation)
- [Usage](#usage)
- [Updating](#updating)
- [Contributing](#contributing)
- [Credits](#credits)
- [License](#license)

## Why

Every AI coding tool keeps its context in a different place and a different format. Claude Code wants `CLAUDE.md`, OpenCode and Codex want `AGENTS.md`, and MCP servers are configured in JSON for one tool and TOML for another. I got tired of copying the same rules between them, and of rebuilding everything on a new machine.

This repo is the single copy. [rulesync](https://github.com/dyoshikawa/rulesync) reads it and writes each tool's files in that tool's format. Changing a rule means editing one file and reinstalling.

## What's included

| Folder | Rules | Skills | Agents | MCP server |
|---|---|---|---|---|
| [`house-rules/`](house-rules/) | Shell preamble, working policy, servers that are off by default, package management | `report`, `eli5`, `package-management` | `course-corrector`, `evaluator`, `metacognitive` | |
| [`tools/docling/`](tools/docling/) | How to use Docling | | | Docling, for documents and OCR |
| [`tools/exa/`](tools/exa/) | Web research | `code-search-exa`, `exa-research` | | Exa, for web search |
| [`tools/pmb/`](tools/pmb/) | Project memory | | | PMB, for project memory |
| [`collections/careers/`](collections/careers/) | | 22 resume and job-search skills | | |
| [`collections/humanizer/`](collections/humanizer/) | | `humanizer` | | |

`house-rules/` holds my general setup. Each folder under `tools/` is one MCP server with the rules and skills that go with it, and `collections/` holds skill packs from other authors. Every folder has its own README explaining where things came from and why settings look the way they do.

## Supported tools

rulesync writes to about 45 AI coding tools. These are the ones I've checked:

| Tool | `--targets` | Rules | Skills | Agents | MCP servers |
|---|---|---|---|---|---|
| OpenCode | `opencode` | Tested | Tested | Tested | Tested |
| Claude Code | `claudecode` | Written | Tested | Written | Tested |
| Codex | `codexcli` | Written | Written | Written | Tested |
| Gemini CLI | `geminicli` | Written | Written | Written | Not supported by rulesync 29.0.0 |
| Cursor | `cursor` | Not written in global mode | Written | Written | Not checked |

"Tested" means I installed it into a throwaway home folder and checked the output. "Written" means rulesync writes the files there, but I haven't checked them in the tool itself. `--targets '*'` installs to every tool rulesync knows.

## Installation

### Requirements

| Needed for | Requirement |
|---|---|
| Everything | [Node.js](https://nodejs.org) 22 or newer. `npx` runs rulesync without installing it. Tested with rulesync 29.0.0 |
| MCP servers | [uv](https://docs.astral.sh/uv/), to install PMB and Docling |
| Web search | An [Exa](https://exa.ai) API key |

### 1. Back up

rulesync replaces each tool's global instructions file, and with `--features mcp` it also replaces that tool's MCP server list. Skills and agents with the same name as one here are overwritten. Anything else it leaves alone, because `rulesync.jsonc` sets `"delete": false`.

I tested what happens to account files with fake credentials:

| Tool | What changes | What's kept |
|---|---|---|
| Claude Code | The top-level server list in `~/.claude.json` | Every other key in `~/.claude.json` (your account, API key, projects and history), and `~/.claude/.credentials.json` and `settings.json` untouched |
| Codex | The server list in `~/.codex/config.toml`, and any comments in that file are deleted | Your other settings and profiles, and `~/.codex/auth.json` untouched |
| OpenCode | The `mcp` section of `opencode.jsonc`, plus the `tools` section | Comments and every other setting |

Your Exa key isn't written anywhere. Claude Code's config gets `${EXA_API_KEY}` and Codex's gets the variable's name, so each reads the key from your environment.

```bash
cp -a ~/.config/opencode ~/.config/opencode.backup   # OpenCode
cp -a ~/.claude ~/.claude.backup                      # Claude Code
cp ~/.claude.json ~/.claude.json.backup               # Claude Code MCP servers
cp -a ~/.codex ~/.codex.backup                        # Codex
```

### 2. Install the MCP servers

```bash
uv tool install pmb-ai
uv tool install 'docling-mcp[local]'
```

The `[local]` extra makes Docling convert files on your own machine. It's a large download.

Set your Exa key in the environment your coding tool starts from, for example in your shell profile:

```bash
export EXA_API_KEY=your-key-here
```

The key never gets written into any file. The generated config only refers to `EXA_API_KEY`.

### 3. Install everything

```bash
npx rulesync generate --global --targets claudecode,codexcli,opencode --features rules,subagents,skills,mcp
```

> [!IMPORTANT]
> Always include `--global`. Without it, rulesync writes into this repo instead of your home folder.

## Usage

### Pick what to install

`--features` chooses the kind of content:

| Feature | Installs |
|---|---|
| `rules` | One global instructions file per tool |
| `subagents` | Agents |
| `skills` | Skills |
| `mcp` | MCP servers |

If you already manage your own MCP servers, leave out `mcp` so your server list isn't replaced. The `permissions` feature is never used here, because it would replace your tool's whole permission settings.

To install only some folders, list them with `--input-roots`:

```bash
npx rulesync generate --global --targets opencode --input-roots house-rules tools/pmb --features rules,mcp
```

> [!WARNING]
> Partial installs don't add up the same way for everything:
>
> | Content | A later run with different folders |
> |---|---|
> | Rules | Replace the instructions file with only that run's rules |
> | MCP servers | Replace the server list with only that run's servers |
> | Skills and agents | Get added; earlier ones stay |
>
> For rules and MCP servers, list every folder you want on every run. The easiest way is to set `inputRoots` in `rulesync.jsonc` once and reuse the same command.

The rules mention Exa, Docling, PMB and the `package-management` skill. If you leave one of those out, also leave out its folder so its rules aren't installed.

### Start from a clean slate

> [!CAUTION]
> With `"delete": true` in `rulesync.jsonc`, or `--delete` on the command line, rulesync first deletes everything in the folders it manages, including skills and agents it didn't create. Run with `--dry-run` first to see what would go.

### Settings only one tool understands

Some settings mean something to one tool only. They sit under that tool's name, so each tool gets its own and nothing else:

```yaml
---
name: code-search-exa
description: ...
claudecode:
  context: fork
---
```

Claude Code's copy gets `context: fork` and the other tools' copies don't. A setting like that placed at the top level would be dropped for every tool.

## Updating

Get the latest rules, agents and skills:

```bash
git pull
npx rulesync generate --global --targets claudecode,codexcli,opencode --features rules,subagents,skills,mcp
```

Update the MCP servers:

```bash
uv tool list --outdated
uv tool upgrade --all
```

### If you rename an MCP server

Tools name each MCP tool after its server, as in `docling_convert_...`. Permission rules such as `"docling_*": "allow"` match on that name. Renaming a server here breaks those rules without any error, and every call to the server starts asking for approval. Rename it in your permission settings too.

## Contributing

[`AGENTS.md`](AGENTS.md) is the guide for adding or changing anything here, whether you're a person or an AI agent. It covers the file layout, keeping tool-specific settings portable, keeping secrets out of the repo, and checking your changes before you commit.

When I change a skill in a live install, I copy its folder back over the one here and put back any `claudecode:` or `opencode:` section the repo copy had.

> [!CAUTION]
> Don't use `rulesync import` to copy changes back. It copies your live config word for word, including any tokens in MCP server settings, and it can't sort files into this layout anyway. The repo's `.gitignore` blocks the folder it writes and common credential files, but the safest habit is not to run it.

## Credits

I wrote the seven rules, the three agents, and the `report` and `eli5` skills. The rest comes from these authors, and keeps their copyright and license:

| Skill | Author and source | License |
|---|---|---|
| `code-search-exa` | Exa Labs, [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server). Unchanged apart from moving its Claude Code setting under `claudecode:` | [MIT](https://github.com/exa-labs/exa-mcp-server/blob/main/LICENSE), © 2025 Exa Labs |
| `exa-research` | Exa Labs' `search` skill from [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), which I renamed and changed | [MIT](https://github.com/exa-labs/exa-mcp-server/blob/main/LICENSE), © 2025 Exa Labs |
| `humanizer` | Siqi Chen, [blader/humanizer](https://github.com/blader/humanizer), based on Wikipedia's [Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) by WikiProject AI Cleanup | [MIT](https://github.com/blader/humanizer/blob/main/LICENSE), © 2025 Siqi Chen |
| 22 career skills | Resume Skills, [Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills) | [MIT](https://github.com/Paramchoudhary/ResumeSkills/blob/main/LICENSE), © 2026 Resume Skills |
| `package-management` | Unknown. I couldn't find where it came from | Unknown, so my license doesn't cover it |

<details>
<summary>The 22 career skills</summary>

`academic-cv-builder`, `application-form-filler`, `career-changer-translator`, `cold-email-writer`, `cover-letter-generator`, `creative-portfolio-resume`, `executive-resume-writer`, `interview-prep-generator`, `job-description-analyzer`, `linkedin-profile-optimizer`, `offer-comparison-analyzer`, `portfolio-case-study-writer`, `reference-list-builder`, `resume-ats-optimizer`, `resume-bullet-writer`, `resume-formatter`, `resume-quantifier`, `resume-section-builder`, `resume-tailor`, `resume-version-manager`, `salary-negotiation-prep`, `tech-resume-optimizer`

</details>

Built on [rulesync](https://github.com/dyoshikawa/rulesync) by dyoshikawa, with MCP servers from [Exa](https://github.com/exa-labs/exa-mcp-server), [Docling](https://github.com/docling-project/docling-mcp) and [PMB](https://pypi.org/project/pmb-ai/).

## License

My own work here is [MIT](LICENSE) licensed, © 2026 280Zo. Items credited to other authors keep their own licenses.
