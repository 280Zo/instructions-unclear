# codebase-memory

[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) maintains a local structural code graph. **Upstream owns its complete integration:** server installation, skill, three agent profiles, instructions and the OpenCode augmentation extension. This repo no longer extracts or maintains its embedded skill separately.

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

An isolated v0.12.1 native installation followed by rulesync generation replaced upstream's instruction block, changed its MCP entry to this repo's disabled template, and overwrote the newer skill with the formerly shipped extracted copy. Agents and the extension survived. Removing our extracted copy prevents that skill overwrite, but generation still replaces the shared instructions/configuration it owns.

The approved exception is **rulesync first, upstream integration last**. In an isolated test, the native installer restored the exact release skill and its instruction block while preserving other generated MCP entries and rules. It retained the existing disabled state. This ordering is an observed integration requirement, not a general reason to avoid upstream installers.

The standard Linux amd64 build failed during C++ locale initialization in the test sandbox before installer code ran; the checksum-verified upstream portable build of the same release passed. Use upstream's supported platform/build selection and verify the chosen artifact; do not assume every build works on every distribution.

## Use

After enabling the intended connection, ask to index a repository, trace callers or inspect change impact. Follow the upstream-installed skill rather than a separately maintained copy. The 0.12.1 release notes describe index/schema changes that can require a full rebuild; this repo refresh does not rebuild or migrate live indexes.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): it's switched off by default, and when enabled its upstream integration supplies its own instructions for structural code questions (line removed 2026-10-24 to save tokens). If you enable it and the agent ignores the graph tools, add a line back.
- The connection is disabled by default, so the rule's fallback (plain code search) is the normal case. Don't enable the server to answer a question.
- Why: on 2026-10-21 the user replaced the per-skill routing rules with one routing rule because several items claimed the same jobs. The upstream-installed skill and instructions describe when to use the graph; the routing rule only decides graph versus direct search.
- Upstream owns its skill, agents and instructions, so don't edit them and don't add a routing rule to this folder.
- After applying a new upstream release, re-read the installed skill's description and instructions. If they now claim a job another item owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

Connection and installation guide written for this repo. Upstream: [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp), release [v0.12.1](https://github.com/DeusData/codebase-memory-mcp/releases/tag/v0.12.1), commit `a7158ac2f48ca646b4527341b76f930f2aeff87e`. No upstream skill or executable is now vendored. Upstream [MIT notice](../../THIRD_PARTY_LICENSES.md#deusdatacodebase-memory-mcp), © 2025 DeusData.
