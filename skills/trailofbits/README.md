# Trail of Bits security plugins

The complete [Trail of Bits marketplace](https://github.com/trailofbits/skills): 46 plugins containing 95 skills, 30 agents, commands, hooks, workflows, tests and supporting resources. `upstream/` preserves the complete upstream tree unchanged. It is **not a rulesync source root**.

## Install

Prefer upstream's native plugin installation, selecting only the plugins you need:

- **Claude Code:** `/plugin marketplace add trailofbits/skills`, then `/plugin menu` to select plugins.
- **Codex:** `codex plugin marketplace add trailofbits/skills`, then `codex plugin list` and `codex plugin add <plugin-name>@trailofbits`.
- **Local reviewed copy:** upstream supports adding a local marketplace. In Claude Code, use `/plugin marketplace add ./skills/trailofbits/upstream` from this repo, then choose plugins. Keep that tree available; local installation may reference its original folder rather than copy everything into a cache.

See [upstream installation and compatibility guidance](upstream/README.md). These are native assistant installations, not folder-scoped rulesync profiles. Get approval before changing a real assistant's plugin list or running installer operations. Do not install the entire marketplace merely to use one scanner.

**OpenCode:** upstream does not document an equivalent complete integration. The old flattened profile is retired, not silently advertised as native-compatible. Workflows can depend on host-specific tools such as `Workflow`, namespaced agents, plugin hooks and `${CLAUDE_PLUGIN_ROOT}`. A successful file copy cannot supply them. No new OpenCode adapters or tool-section rewrites are introduced here.

## Which agent uses it

The skills belong to the [`security` agent](../../agents/security/). Where an assistant filters skills per agent (OpenCode), only `security` may load them and every other agent denies them, so they never add to everyday requests. The [agent map](../../agents/README.md) lists them as installed separately. The skill IDs are read from `upstream/` by [`agents/generate.py`](../../agents/generate.py) (`NATIVE_PLUGINS`), so regenerate after updating this tree.

## Why native ownership

The new regression-hunt and patching-bugs workflows resolve plugin-level scripts, schemas and records through relative paths. Zeroize-audit resolves agents under its original `agents/`, not rulesync's relocated `subagents/`. Several existing workflows also need plugin roots and registered host facilities. Flattening only skills/agents loses those relationships.

Isolated, network-disabled tests with Claude Code 2.1.296 validated the marketplace and installed all 46 plugins. Critical regression/patching scripts and zeroize agent links resolved in the full tree. Subsequent generation of the reduced infosec and reverse-engineering selections preserved all native files and all 47 installed plugins (including IoTHackBot) remained enabled. Codex was not installed in the test environment, so its procedure is documented from upstream, not locally verified. No model-driven audits, external MCP services or scanners were launched.

Native plugins can register hooks and MCP servers: for example, zeroize-audit declares a Serena `uvx` server. Some patching workflows require a local commit. Review each selected plugin's resources and runtime effects before enabling it; copying this tree grants no approval to execute them, download packages, commit or modify targets. Higher-priority permission and scope instructions still apply.

## Existing installations

`delete: false` leaves old extracted skill/agent copies in place. Review and explicitly approve removing stale copies before enabling the same native plugins; do not run duplicate owners. The infosec group installs only its rule, security agent bundles and disabled ZAP connection; native plugins are separate.

## Use and prerequisites

Choose a workflow for code review, vulnerability triage, static analysis, fuzzing, protocol/crypto or smart-contract review. Follow that plugin's README and complete supporting content. Native packaging does not install Semgrep, CodeQL, compiler/fuzzer toolchains, Python environments, ProVerif, accounts or model access. Review and approve those dependencies separately. Upstream tests and unused support files remain included rather than being pruned.

## Updating

Review upstream changes, refresh the complete `upstream/` tree without modifying bodies, metadata or directory layout, and validate native installation followed by rulesync generation in isolation. Show any actual host conflict before choosing an adaptation. Keep this wrapper, catalog, groups and license notice consistent.

## For agents: install, remove and update

To install, use the native plugin procedure in [Install](#install), choosing only the plugins the user needs. No group includes it, and rulesync never installs it. Claude Code and Codex users run the slash commands themselves; get approval before any plugin list change. Scanners, toolchains and accounts in [Use and prerequisites](#use-and-prerequisites) are separate installs. To verify, check that the chosen plugins appear in the tool's plugin list (`/plugin` in Claude Code, `codex plugin list` in Codex). Don't run an audit or scanner as a test.

To remove, use the same tool's plugin manager that installed the plugin or marketplace, with approval, and restart the tool. Never delete files in this repo's `upstream/` to uninstall it; a local marketplace may still point there. Old extracted skill and agent copies from the retired flattened profile are removed as [Existing installations](#existing-installations) and [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component) describe. Their names weren't recorded here, so list what's actually installed and confirm each one with the user. Scanners, toolchains and Python environments stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The copied commit is in [Origin](#origin). Then run `python3 agents/generate.py` and the tests, so added or renamed skills get the `security` agent's permissions; see [Adding a plugin that brings skills](../../agents/README.md#adding-a-plugin-that-brings-skills).

## Origin

[trailofbits/skills](https://github.com/trailofbits/skills), complete tree at commit `a3131740a39291e42fd15b9eac07e0b393ad71b1`, copied October 20, 2026. [CC BY-SA 4.0](../../THIRD_PARTY_LICENSES.md#trailofbitsskills), by Trail of Bits; full text also retained in `upstream/LICENSE`. No local tool sections or body adaptations. Wrapper written for this repo by 280Zo.
