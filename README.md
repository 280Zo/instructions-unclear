# instructions-unclear

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Installs with rulesync](https://img.shields.io/badge/installs%20with-rulesync-8A2BE2)](https://github.com/dyoshikawa/rulesync)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-standard-green)](https://agentskills.io)
[![AGENTS.md](https://img.shields.io/badge/AGENTS.md-ready-orange)](https://agents.md)

Rules, agents, skills, MCP servers, and plugins for AI coding tools. Pick the pieces you want and [rulesync](https://github.com/dyoshikawa/rulesync) installs them into Claude Code, Codex, OpenCode and about 40 other tools, each in its own format.

> **Before installing or updating:** [generate a local preview and compare it with your live files](#preview-before-installing). Generation can replace instructions and MCP settings. A preview does not change your live assistant installation.

## Quick Start

### Generate Files

From the repository root, generate the files using the default configuration

```sh
npx rulesync@38.0.0 generate \
    --config groups/default.jsonc \
    --global
```

### Configure or Restore Configurations

Create or copy the coding agent permission safeguards. Permissions are supported, but I've chosen to exclude them because of the privacy and security risks. Instead, I store mine in a dotfile repo I can pull from.

Create or restore in any other ancilary config files like the cli.json for coding agent terminal preferences.

You can also use the init functions of some tools to re-create the config files. For example, the opencode-quota guided installer helps you configure the plugin without having to manually editing JSON files.

```sh
npx @slkiser/opencode-quota@5 init
```

### Configure the plugins separately

Rulesync does **not** install plugins. Follow the READMEs and add the plugins manually, or tell an agent to use agent section of each README to install them for you.

**Check MCP prerequisites before launching**

An MCP definition is an instruction for starting or contacting software. It does not guarantee that software is installed. Check your system to make sure the required software exists.

| Connection      | What is still required                                         |
| --------------- | -------------------------------------------------------------- |
| Docling         | `uv`; startup can download its pinned package and dependencies |
| PMB             | `uv`; startup can download packages and embedding models       |
| Exa             | No key for anonymous search; OAuth or API key for Exa Agent    |
| Presenton       | Separate container/service setup; disabled initially           |
| FreeCAD         | Application, addon and server setup; disabled initially        |
| codebase-memory | Its upstream integration; disabled initially                   |

### Start OpenCode and verify the default profile

Startup may download packages and start enabled MCP servers.

```sh
mkdir -p ~/AI/default-check
cd ~/AI/default-check
opencode
```

In a **new session**:

1. Use /connect for providers that need authentication.
2. Select a model and send a harmless test message.
3. Check /skills.
4. Check /mcps.
5. Confirm Superpowers loads.
6. Run /quota_status if you installed quota.
7. If needed, connect Anthropic using the Claude plugin’s documented flow.

Then test functionality individually:

- Docling: convert one small, non-sensitive document.
- Exa: perform one ordinary search; don’t invoke metered agent research as a smoke test.
- PMB: use a disposable project to test project binding and a harmless operation.
- Permissions: verify expected prompts using dummy files, never real credentials.

### Generate the four folder profiles

In addition to the default profile, the repo contains other groups with scoped use cases. These are installed into a folder to use when needed. When opencode is used outside of the folder the context files won't be available unless you decide to install them globally.

From the repo root, generate each profile:

```sh
for profile in infosec ai_research career reverse_engineering
    mkdir -p "$HOME/AI/$profile"
    or break

    npx rulesync@38.0.0 generate \
        --config "groups/$profile.jsonc" \
        --output-roots "$HOME/AI/$profile"
    or break
end
```

Do **not** add --global.

### Test each profile separately

For example:

```sh
cd ~/AI/career
opencode
```

then test the skills available.

Note that REA can download its package at startup. Native binary analysis still requires its separately installed backends. Trail of Bits and IoTHackBot are separate native integrations; this repo does not claim a verified complete OpenCode installation for them.



### Complete

You should now have access to all the default context files. You can customize them however you'd like so they fit your use cases.

## What's included

Every folder below installs on its own. Open a group to see what's in it; each folder's README covers its setup.

<details>
<summary>Rules: how the agent works</summary>

| Folder                                                            | Adds                                                                          |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| [`rules/shell-preamble`](rules/shell-preamble/)                   | Explain each shell command before running it                                  |
| [`rules/shell-preamble-reminder`](rules/shell-preamble-reminder/) | Short preamble reminder placed last in the installed rules                    |
| [`rules/scope-secrets-approvals`](rules/scope-secrets-approvals/) | Where to work, what never to touch, what to ask before doing                  |
| [`rules/engineering`](rules/engineering/)                         | Small changes, commands, verification                                         |
| [`rules/communication`](rules/communication/)                     | State assumptions and summarize at the end                                    |
| [`rules/routing`](rules/routing/)                                 | Which skill or tool owns each job when several could do it                    |
| [`rules/preferences`](rules/preferences/)                         | Your preferences: vim, fish, pnpm/uv, zellij, firefox, ISO dates, US spelling |

The secure-coding rule now ships inside [`agents/security`](agents/security/).

</details>

<details>
<summary>Agents: second opinions, local models and security checks</summary>

| Folder                                            | Adds                                                                                                                                                                     |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`agents/second-opinion`](agents/second-opinion/) | `second-opinion` reviews how the session is going; `evaluator` and `metacognitive` check answers and reasoning                                                           |
| [`agents/local-model`](agents/local-model/)       | Small working turns, scoped delegation and safe pause/resume handoffs for local models or fragile connections                                                            |
| [`agents/security`](agents/security/)             | One security bundle owned by this repo: secure-coding rule, security auditor and threat-modeling agents, 6 skills and 4 commands; included in the default global install |

</details>

<details>
<summary>MCP servers: web search, documents, project memory, code graph, PowerPoint, CAD</summary>

| Folder                                                        | Adds                                                                                                          | Needs            |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ---------------- |
| [`mcp-servers/exa`](mcp-servers/exa/)                         | Exa search, retrieval and agent research, a web research rule, upstream skills `search` and `Exa Agent`       | Optional key; see setup |
| [`mcp-servers/docling`](mcp-servers/docling/)                 | Docling, which reads PDFs, Office files and scans, and a rule for using it                                    | uv               |
| [`mcp-servers/pmb`](mcp-servers/pmb/)                         | PMB, project memory that survives between sessions, and a rule for using it                                   | uv               |
| [`mcp-servers/codebase-memory`](mcp-servers/codebase-memory/) | Code graph connection, switched off; upstream installer supplies its skill/agents/instructions after rulesync | Upstream install |
| [`mcp-servers/presenton`](mcp-servers/presenton/)             | Presenton, for decks you can edit in PowerPoint or Google Slides. Installed switched off                      | Docker           |
| [`mcp-servers/freecad`](mcp-servers/freecad/)                 | FreeCAD control: build and edit 3D models, run analyses. Installed switched off                               | FreeCAD, uv      |

</details>

<details>
<summary>Skills: explaining, reports, packages, visuals, design, writing, thinking, photo geolocation, careers</summary>

| Folder                                                          | Adds                                                                                                                                                                    |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`skills/eli5`](skills/eli5/)                                   | `eli5`: a plain-English tutor for one unfamiliar thing                                                                                                                  |
| [`skills/report`](skills/report/)                               | `report`: evidence-backed write-ups of material you've gathered                                                                                                         |
| [`skills/package-management`](skills/package-management/)       | `package-management`, and a rule to load it: installing and running packages safely                                                                                     |
| [`skills/visual-explainer`](skills/visual-explainer/)           | `visual-explainer`: HTML pages and decks for explanations, plans and reviews                                                                                            |
| [`skills/diagram-design`](skills/diagram-design/)               | `diagram-design`: 45 types of diagram, with static and motion HTML/SVG templates                                                                                        |
| [`skills/frontend-slides`](skills/frontend-slides/)             | `frontend-slides`: HTML slide decks, with style previews to pick from                                                                                                   |
| [`skills/anthropic-design`](skills/anthropic-design/)           | `frontend-design` for UI work, `theme-factory` for one shared look across outputs                                                                                       |
| [`skills/documents`](skills/documents/)                         | Magnus's shared PDF, Word, Excel and PowerPoint authoring workflow and smoke validator                                                                                  |
| [`skills/transcribe`](skills/transcribe/)                       | OpenAI audio transcription and optional speaker identification                                                                                                          |
| [`skills/speech`](skills/speech/)                               | OpenAI text-to-speech using built-in voices                                                                                                                             |
| [`skills/security-threat-model`](skills/security-threat-model/) | Repository-grounded threat modeling; infosec/work, not default                                                                                                          |
| [`skills/screenshot`](skills/screenshot/)                       | Desktop/window screenshot capture                                                                                                                                       |
| [`skills/playwright`](skills/playwright/)                       | Terminal browser automation through Playwright CLI                                                                                                                      |
| [`skills/humanizer`](skills/humanizer/)                         | `humanizer`: rewrites text that sounds AI-written                                                                                                                       |
| [`skills/distilly`](skills/distilly/)                           | `distilly`: turns a public figure, colleague or someone you know into a skill that thinks the way they do                                                               |
| [`skills/geo-sleuth`](skills/geo-sleuth/)                       | `geo-sleuth`: works out where and when a photo was taken, with checkable evidence                                                                                       |
| [`skills/handoff`](skills/handoff/)                             | `/handoff`: a handoff document so a fresh session can pick up the work                                                                                                  |
| [`skills/teach`](skills/teach/)                                 | `/teach`: a course over several sessions, kept in a teaching workspace folder                                                                                           |
| [`skills/wait-what`](skills/wait-what/)                         | `/wait-what`: re-pitches the agent's last message more simply, with the missing context                                                                                 |
| [`skills/resume-skills`](skills/resume-skills/)                 | 22 skills for resumes, cover letters, applications, interviews and offers. Career group only                                                                            |
| [`skills/interview-coach`](skills/interview-coach/)             | `interview-coach`: interview prep, mock interviews, debriefs and a storybank, with scoring. Career group only                                                           |
| [`skills/career-workspace`](skills/career-workspace/)           | 4 skills that file career records, build a master resume and official work history, and start a reviewed application with `career-start-application`. Career group only |

</details>

<details>
<summary>Profiles: sets that load only in a folder you choose</summary>

A profile installs into one folder instead of your home folder, keeping specialist context separate from your normal setup. Start your coding tool there to load it; discovery and context costs depend on the assistant.

| Folder                                                      | Adds                                                                                            |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| [`skills/ai-research`](skills/ai-research/)                 | 98 AI research skills: training, fine-tuning, inference, evaluation, RAG, agents, paper writing |
| [`mcp-servers/rea`](mcp-servers/rea/)                       | REA, an MCP server and skill for reverse engineering apps, websites, APKs and binaries          |
| [`mcp-servers/zap`](mcp-servers/zap/)                       | Official ZAP MCP connection for web-security workflows; disabled until configured               |
| [`mcp-servers/reva`](mcp-servers/reva/)                     | Shared Ghidra projects and 6 companion skills; MCP connection disabled                          |
| [`mcp-servers/radare2`](mcp-servers/radare2/)               | Optional radare2-native MCP connection; disabled, read-only tools                               |
| [`agents/reverse-engineering`](agents/reverse-engineering/) | Reverse-engineer, firmware and malware analyst agents, 4 skills                                 |

Each README has its install command.

</details>

<details>
<summary>Plugins: installed through each tool (or by your agent), not rulesync</summary>

The `plugins/` READMEs have steps for you and steps your agent can follow ("install X by following its README"). The complete native skill collections stay in their existing `skills/` folders, with their own upstream installation guidance. Any separately authored rule installs through rulesync like the rest.

| Folder                                                          | Adds                                                                                                                       |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| [`plugins/superpowers`](plugins/superpowers/)                   | Superpowers: skills for planning, test-driven development, debugging, code review and finishing work, loaded automatically |
| [`plugins/opencode-quota`](plugins/opencode-quota/)             | Plan quota and token use in OpenCode                                                                                       |
| [`plugins/opencode-claude-auth`](plugins/opencode-claude-auth/) | Use a Claude Pro or Max subscription in OpenCode 2                                                                         |
| [`skills/trailofbits`](skills/trailofbits/)                     | Complete upstream marketplace: 95 skills, 30 agents and supporting resources; native plugins, not rulesync                 |
| [`skills/iothackbot`](skills/iothackbot/)                       | Complete upstream IoT toolkit and 13 skills; native Claude plugin, not a flattened rulesync profile                        |

</details>

## Install

You need [Node.js](https://nodejs.org) 22 or newer; `npx` runs rulesync. Clone the repo and work from its root:

```bash
git clone https://github.com/280Zo/instructions-unclear.git && cd instructions-unclear
```

### Preview before installing

Run from the repository root. This fish example generates the `default` group into a fresh temporary home instead of your real one. It redirects the XDG configuration, data, state and cache directories too. `npx` may download and execute the pinned rulesync package; prefer an existing local copy of that version when available. Redirecting these paths is not a security sandbox.

```fish
mkdir -p /tmp/opencode
set preview (mktemp -d /tmp/opencode/rulesync-preview.XXXXXX)
env HOME="$preview" \
    XDG_CONFIG_HOME="$preview/.config" \
    XDG_DATA_HOME="$preview/.local/share" \
    XDG_STATE_HOME="$preview/.local/state" \
    XDG_CACHE_HOME="$preview/.cache" \
    npx rulesync@38.0.0 generate --config groups/default.jsonc --global

vim "$preview/.config/opencode/AGENTS.md"
diff -u ~/.config/opencode/AGENTS.md "$preview/.config/opencode/AGENTS.md"
diff -rq ~/.config/opencode/agents "$preview/.config/opencode/agents"
diff -rq ~/.config/opencode/skills "$preview/.config/opencode/skills"
```

`diff` exits with 1 when files differ; that is expected. A missing live directory is reported separately, not as a successful comparison. Inspect the generated `commands/` directory too; it may not exist in your live installation yet. To preview another home-folder group, change `--config` to that group's file. Folder-scoped groups instead use `--output-roots "$preview/project"`, without `--global`; see [install groups](groups/README.md).

Inspect the generated `opencode.jsonc` locally as well. **Do not copy live settings or credentials into the preview, commit them, or paste raw configuration diffs.** To test an update to an existing config, create a synthetic config in a separate temporary home with the same setting names and structure, replacing private values with placeholders, then generate into that home. Test both `opencode.json` and `opencode.jsonc` if you use both.

A fresh preview checks which files rulesync generates. It does not prove that updating existing settings preserves everything, that plugins load, that MCP servers connect, or that their required programs are installed. Native plugins and codebase-memory's upstream integration have separate installation steps; apply and verify those in isolation too, in the order their READMEs specify.

Review differences before approving a live run. Install and verify replacements before removing obsolete live skills or agents. With `delete: false`, an old name remains even when its replacement has a new name. Keep files owned by upstream installers, such as codebase-memory's skill.

### Install into your home folder

Then name the folders you want, the tools you use, and the kinds of content to install:

```bash
npx rulesync@38.0.0 generate --global \
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

Follow each folder's setup order. In particular, generate rulesync output **before** applying codebase-memory's native integration; future generation replaces its shared instructions/configuration, so reapply the upstream integration afterward. See its [verified ownership boundary](mcp-servers/codebase-memory/README.md). Other runtimes and native plugins have their own separately approved setup steps.

### What generation changes

The table below is verified for **OpenCode with rulesync 38.0.0**, using this repo's selections (`delete: false`, no `permissions` feature). Other assistants have different config writers; do not assume identical merge or deletion behavior without a preview for that target. OpenCode's own loading and merging of configuration layers is separate from rulesync editing files on disk.

| File or setting                    | What rulesync does                                                                                                                                     | What it leaves behind                                                                                                                                                        |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Global `AGENTS.md` (`rules`)       | Replaces it with the selected rules                                                                                                                    | Live-only instructions are not automatically preserved                                                                                                                       |
| `opencode.json` / `opencode.jsonc` | Updates an existing `.jsonc` preferentially, otherwise `.json`; creates `.jsonc` if neither exists                                                     | Does not reconcile both files when both exist                                                                                                                                |
| MCP server list (`mcp`)            | Replaces the chosen config file's entire `mcp` section                                                                                                 | Servers absent from the selection are removed from that section, even with `delete: false`; another file's entries remain                                                    |
| Native V2 MCP settings             | Rewrites the whole `mcp` section in the older flat layout (still supported by V2). No released rulesync writes `mcp.servers` (checked through v38.0.0) | Shared V2 options such as `mcp.timeout` are lost, and each server's fields are replaced from this repo's definition, including a customized header such as Exa's `x-api-key` |
| Plugin list, model, permissions    | Preserves these unrelated settings during MCP generation                                                                                               | Does not clean obsolete plugin entries or uninstall plugin packages                                                                                                          |
| Skills, agents and commands        | Adds selected entries and overwrites matching names                                                                                                    | Obsolete names remain with `delete: false`; inspect support files in updated skill folders too                                                                               |
| Native installer resources         | Does not run their installers                                                                                                                          | Codebase-memory and native plugins still need their documented setup and verification                                                                                        |
| MCP programs and other software    | Writes connection definitions, not a full software installation                                                                                        | Required commands, containers, applications, credentials and services may still be missing                                                                                   |

**Using OpenCode V2 does not prevent settings loss.** V2 supports existing V1 configuration, but it cannot recover a custom setting that rulesync removed from the file. In a synthetic-config test, generation preserved unrelated plugins/model/permissions, removed an obsolete MCP entry and dropped a shared V2 MCP timeout. Review the result before relying on a live update. See OpenCode's [migration guidance](https://opencode.ai/v2/docs/migrate-v1) and [MCP settings](https://opencode.ai/v2/docs/mcp-servers).

**Keeping a native V2 OpenCode config.** Use the full selection, including `mcp`, for the first install. If you then convert `opencode.jsonc` to native V2 or customize its MCP entries, leave `mcp` out of later OpenCode runs:

```fish
npx rulesync@38.0.0 generate --config groups/default.jsonc --global --features rules,subagents,skills,commands
```

Tested against a converted V2 config: this run leaves `opencode.jsonc` byte-for-byte unchanged and still updates instructions, skills, agents and commands. When an `mcp.jsonc` in this repo changes, apply that change to the live `mcp.servers` entry by hand (or ask an agent to, following the component README) instead of regenerating the MCP section. Any run that includes `mcp` flattens the section again and overwrites customized server fields.

**Updating existing settings is different from starting fresh.** If you delete the live config first, its comments and local settings disappear too. This repo does not reproduce OpenCode's `provider` / native V2 `providers` settings, local model selections, plugin list, or machine-specific permissions. Provider configuration is assistant-specific; it belongs in your private settings or a separately maintained, sanitized personal template, not a copy of your live config committed here. Empty provider declarations are not credentials or custom model definitions. Keep your private backup until the new setup is verified.

Back up anything you want to keep. Because rules and MCP servers are replaced, list every folder you want each time you install. To save your picks, put them in `rulesync.local.jsonc` (git ignores it), and rulesync uses that list instead of `rulesync.jsonc`'s:

```jsonc
{
  "inputRoots": ["rules/shell-preamble", "rules/scope-secrets-approvals", "skills/diagram-design"]
}
```

Then the command is just `npx rulesync@38.0.0 generate --global --targets opencode,claudecode --features rules,skills`.

Plugins install differently: through each tool, or by asking your agent to follow the plugin's README. Profiles install into a folder you choose; their READMEs have the command.

### Install groups

Saved selections, so you don't have to list folders. [`groups/README.md`](groups/) has each one's command and what it includes.

| Group                 | For                                                                                                                                           |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `default`             | Everything in `rulesync.jsonc`, into OpenCode                                                                                                 |
| `work`                | OpenCode, Copilot and Copilot CLI on a work machine                                                                                           |
| `writing_reporting`   | Writing, reports and visuals, without touching MCP settings                                                                                   |
| `infosec`             | Security rule/agents, 11 security and utility skills and a disabled ZAP connection, in a folder you choose; native plugins install separately |
| `ai_research`         | AI research skills, in a folder you choose                                                                                                    |
| `career`              | Career skills, and a career agent later, in a folder you choose                                                                               |
| `reverse_engineering` | REA, RE agents and disabled ReVa/radare2 connections, in a folder you choose; IoTHackBot is native-owned                                      |

```bash
npx rulesync@38.0.0 generate --config groups/default.jsonc --global
```

None of them installs the programs the skills and MCP servers use; each folder's README covers that.

See [reference/](reference/) for published assessments, including the [security and reverse-engineering inventory](reference/security-re-tooling.md) and [persistent agent knowledge investigation](reference/agent-knowledge/README.md). Each integration's README distinguishes installed context from separately required software.

## Updating

Run `git pull`, then the same generation command again. OpenCode plugins aren't updated by rulesync or by replacing the config: OpenCode keeps loading its cached copy until you run `opencode plugin check` and `opencode plugin update` (see [plugins](plugins/README.md#updating-opencode-keeps-cached-versions)). Reapply codebase-memory's upstream integration after generation if you use it, reviewing the affected files and retaining your chosen enabled/disabled state. Native Trail of Bits/IoTHackBot plugins update through their own documented procedure, not rulesync; review stale extracted copies before switching owners. Runtime updates follow each component README and are separate from context generation.

To refresh copied third-party context, use the upstream repository linked in the component README's Origin section, following the update procedure in [`AGENTS.md`](AGENTS.md#check-for-updates). Runtime/package upgrades and regenerating context are separate operations; neither automatically refreshes the copied source files here.

## Customizing

Fork the repo and make it yours: add your own rules under `rules/`, swap skills and agents in and out, and point `inputRoots` at what you keep. [`AGENTS.md`](AGENTS.md) is the guide for that, written so an AI agent can follow it too: the layout, keeping tool-specific settings portable, adding plugins, keeping secrets out, checking upstreams for updates, and verifying changes.

## For agents: private configuration and comments

- Treat rulesync generation, native plugin setup and native V2 conversion as separate operations with separate approval. Apply any approved V2 conversion after the installers that rewrite the same settings. Once the live OpenCode config is native V2 or has customized MCP entries, sync it without the `mcp` feature (see "Keeping a native V2 OpenCode config") and port `mcp.jsonc` changes into `mcp.servers` by hand, preserving the user's local values such as credential references.
- Preserve existing provider/model settings, permissions and explanatory comments during approved edits. Do not infer that a fresh generation reconstructs them. Do not copy live settings, credentials, personal paths or machine-specific permission patterns into this public repo.
- Keep permission rationale beside the matching rules in the private config: ordering, credential and transcript access, instruction-file edits, and the distinction between shell permissions and read-tool permissions. Comments explain policy; they do not enforce it. Recheck claims against the installed OpenCode version rather than blindly restoring historical comments or changing policy to match them.
- For component-specific rationale, use the copyable comments and maintenance guidance in the [Docling](mcp-servers/docling/README.md#for-agents-routing-and-updates) and [Exa](mcp-servers/exa/README.md#for-agents-routing-and-updates) READMEs. During an approved setup or migration, place relevant comments beside the settings they describe; reuse equivalent existing comments instead of duplicating them. This is a manual maintenance step, not a rulesync feature.

## License

My own work here is [MIT](LICENSE) licensed, © 2026 280Zo. Third-party files keep their own licenses; see [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).
