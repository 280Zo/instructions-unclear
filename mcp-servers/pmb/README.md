# PMB

[PMB](https://pypi.org/project/pmb-ai/) (`pmb-ai`) is a local, per-project memory for AI agents: decisions, lessons and progress that survive between sessions.

Upstream source and update notes: [oleksiijko/pmb](https://github.com/oleksiijko/pmb). The server supplies its own context instructions; updating `pmb-ai` updates those, while this repo's connection template and rule are maintained here.

See the [agent-knowledge objectives](../../reference/agent-knowledge/01-objectives-and-requirements.md) and [technology evidence](../../reference/agent-knowledge/03-technology-landscape.md) for the complete-system investigation and PMB's source-checked capabilities and limits. PMB's association graph, optional image features and hybrid search do not establish a fully transactional multimodal evidence store; concurrent sessions and project binding still need validation.

## What's in this folder

| File | Becomes |
|---|---|
| `mcp.jsonc` | The `pmb` entry in OpenCode's MCP server list |
| `rules/pmb-memory.md` | The "PMB Memory" section of `AGENTS.md` |

The detailed usage instructions the AI sees ("read before you write", one `record_batch` per turn, and so on) come from the PMB server itself when it connects. They aren't copied here, so they can't go stale.

## Install

1. Have [uv](https://docs.astral.sh/uv/) available. The MCP entry selects the reviewed package version explicitly:

   ```bash
    uvx --from pmb-ai==1.2.3 pmb-mcp
   ```

   This is the launch command, not a command to run alongside your assistant's server. First launch may download dependencies; review that operation before enabling it. The pin selects the top-level package, not a complete transitive dependency lock. Refresh the reviewed pin here and in `mcp.jsonc` together; regenerating the config does not upgrade an already-running process.

2. This folder adds a rule and an MCP server, and rulesync installs both by replacing your tool's whole set. So add `mcp-servers/pmb` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features rules,mcp`.

## Use

Start the configured server in the intended project and verify its workspace before writes. The rule has the agent read memory before starting work and save decisions, lessons and progress as it goes. Ask "where were we?", "what did we decide about X?" or "what are the open goals?" to use it directly. Say "remember that…" to pin something important. Reviewed runtime baseline: `pmb-ai 1.2.3`, checked October 20, 2026; server-provided instructions remain owned by upstream, not copied into this repo.

PMB also offers `pmb connect --active`, but inspect and approve its host-configuration changes first: the source-reviewed release includes shared-daemon connection defaults, which are different from this repo's explicit `pmb-mcp` stdio entry. Do not run it as an automatic prerequisite for an already configured server.

## Per-project setup

- **Memory location.** `PMB_HOME=.pmb` is relative to the server process directory; the host must resolve `"cwd": "."` to the intended workspace. Verify both the physical memory path and PMB's selected workspace, including nested folders/worktrees. An already-running server does not retarget when an agent changes directory. Keep `.pmb/` out of Git through the project's approved ignore setup.
- **Isolation and concurrency.** Project-local configuration routes calls; it is not an OS sandbox. The inspected release has separate event/vector/cache stores and shared session bookkeeping; multiple sessions/processes need a non-sensitive concurrency test before dependable shared use is claimed.
- **Offline behavior.** Local embeddings may download an uncached model on startup/prewarming. Provision and verify model artifacts before expecting offline operation. No additional generative-model API is required for the basic explicit-memory route; optional processing can change that.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `pmb_prepare`. Any permission rule written as `"pmb_*": ...` matches on that name. If you rename the server, update those rules too.
