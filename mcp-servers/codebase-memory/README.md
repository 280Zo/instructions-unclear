# codebase-memory

[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) maintains a local structural code graph. **Upstream owns its complete integration:** server installation, skill, three agent profiles, instructions and the OpenCode augmentation extension. This repo doesn't copy its skill.

| File | What this repo owns |
|---|---|
| `mcp.jsonc` | Optional connection template, disabled until explicitly enabled |
| `README.md` | Installation order and the verified ownership boundary |

## Install and update

Reviewed release: **v0.12.1**, commit `a7158ac2f48ca646b4527341b76f930f2aeff87e`, checked October 20, 2026. Follow the [upstream installation instructions](https://github.com/DeusData/codebase-memory-mcp#installation), selecting only the clients you intend to configure. Read and approve installer operations first; do not pipe downloaded scripts directly into a shell.

1. Generate your selected rulesync configuration first, keeping all desired roots in the run. This folder needs the `mcp` feature, not `skills`.
2. Install/activate the reviewed upstream release following its supported procedure. The native command supports `install --clients=opencode --dry-run` to preview the OpenCode integration; specify other intended clients rather than configuring every detected client accidentally. Follow its prompts only after reviewing the affected paths. Do not use noninteractive overwrite flags on an unreviewed live installation.
3. Apply the upstream integration **after** rulesync generation. Review any existing-file replacements. The installer supplies its own skill, instructions, agents and extension; there is no copied skill to install from this folder.
4. If the generated connection remains disabled, enable it only when you want its tools available. Upstream respects an existing disabled setting; installation is not permission to turn on a server automatically.

Repeat the final upstream integration step after future rulesync runs that replace instructions or its MCP settings. Runtime updates and context generation are distinct operations. Upstream activation may stop its running sessions; approve that separately in a real environment.

## Verified rulesync conflict

Running rulesync after upstream's installer replaces upstream's instruction block and sets its MCP entry to this repo's disabled template; its agents and extension survive.

The approved exception is **rulesync first, upstream integration last**. In an isolated test, the native installer restored the exact release skill and its instruction block while preserving other generated MCP entries and rules. It retained the existing disabled state. This ordering is an observed integration requirement, not a general reason to avoid upstream installers.

The standard Linux amd64 build failed during C++ locale initialization in the test sandbox before installer code ran; the checksum-verified upstream portable build of the same release passed. Use upstream's supported platform/build selection and verify the chosen artifact; do not assume every build works on every distribution.

## Use

After enabling the intended connection, ask to index a repository, trace callers or inspect change impact. Follow the upstream-installed skill rather than a separately maintained copy. The 0.12.1 release notes describe index/schema changes that can require a full rebuild; nothing here rebuilds or migrates live indexes.

## For agents: install, remove and update

### Install

- It's in the `default` and `work` [install groups](../../groups/README.md), written switched off. This folder only supplies the `codebase-memory-mcp` connection, so it needs the `mcp` feature.
- Follow [Install and update](#install-and-update) above. The `codebase-memory-mcp` program comes from the upstream release, not from rulesync. Run rulesync first and the upstream integration last, with the user's approval for each step.
- Leave the connection off unless the user asks for it. In OpenCode they turn it on with `"enabled": true` on `codebase-memory-mcp`, or from `/mcps`.
- To verify, once it's on, check in a new session that `codebase-memory-mcp` connects and its tools are listed. Don't index a repository as a smoke test unless the user approves it, because indexing writes data.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes its MCP entry, because each run replaces the whole MCP list. As the [verified conflict](#verified-rulesync-conflict) shows, a run also replaces the instruction block upstream wrote into the shared rules file.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- The upstream skill, three agents, instructions and OpenCode extension belong to the upstream installer. This README doesn't name an uninstall command. Use upstream's documented uninstall procedure, show the user what it will change and get approval first. Don't delete its files by guesswork.
- If the user syncs a native V2 config without the `mcp` feature, remove the `codebase-memory-mcp` entry from `mcp.servers` by hand, keeping every other setting.
- The installed program and any code indexes it built stay. Never delete them without the user's explicit approval.

### Update

- Follow [Check for updates](../../AGENTS.md#check-for-updates). The reviewed release and commit live in [Install and update](#install-and-update) and [Origin](#origin); `mcp.jsonc` has no version pin. Change those together, plus the [license section](../../THIRD_PARTY_LICENSES.md#deusdatacodebase-memory-mcp) if upstream's license changed.
- After any rulesync run, reapply the upstream integration. Then follow the update bullets in [For agents: routing and updates](#for-agents-routing-and-updates).

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): it's switched off by default, and when enabled its upstream integration supplies its own instructions for structural code questions. If you enable it and the agent ignores the graph tools, add a line back.
- The connection is disabled by default, so the rule's fallback (plain code search) is the normal case. Don't enable the server to answer a question.
- Why: The upstream-installed skill and instructions describe when to use the graph; the routing rule only decides graph versus direct search.
- Upstream owns its skill, agents and instructions, so don't edit them and don't add a routing rule to this folder.
- After applying a new upstream release, re-read the installed skill's description and instructions. If they now claim a job another item owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

Connection and installation guide written for this repo. Upstream: [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp), release [v0.12.1](https://github.com/DeusData/codebase-memory-mcp/releases/tag/v0.12.1), commit `a7158ac2f48ca646b4527341b76f930f2aeff87e`. No upstream skill or executable is now vendored. Upstream [MIT notice](../../THIRD_PARTY_LICENSES.md#deusdatacodebase-memory-mcp), © 2025 DeusData.
