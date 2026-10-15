# codebase-memory

[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) indexes a codebase into a knowledge graph on your machine (functions, classes, imports, routes and how they connect) so the agent can answer structural questions with a query instead of reading file after file. It covers 160+ languages and needs no API key or external service.

| File | What it is |
|---|---|
| `mcp.jsonc` | The `codebase-memory-mcp` MCP server, installed switched off |
| `skills/codebase-memory/` | When and how to use the graph instead of grep |

## Install

1. Install the server once. It's on PyPI, so it fits the other uv-installed servers here:

   ```bash
   uv tool install codebase-memory-mcp
   ```

   Update it with `uv tool upgrade --all`. Don't run `codebase-memory-mcp install`: that edits every coding tool it finds (MCP entries, instructions, hooks), which is what this repo does for you.

2. This folder adds an MCP server, and rulesync installs those by replacing your tool's whole list. So add `mcp-servers/codebase-memory` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features skills,mcp` included.

## Use

The server is installed switched off, so it doesn't add its tools to every request while you're not using it. To use it, turn it on in your tool (in OpenCode, set `"enabled": true` on `codebase-memory-mcp` in `opencode.jsonc`), then in a project:

- "Index this repo" (first time per project; later changes are picked up automatically while a session is open)
- "Who calls `parseConfig`?", "trace the call chain from the HTTP handler to the database"
- "What would break if I change `UserService`?", "find dead code", "show the architecture"

The index is stored in `~/.cache/codebase-memory-mcp/`.

## Origin

[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp). The skill isn't a file upstream; the program carries it as text and writes it out during `install`. Here it was extracted from `src/cli/cli.c` at tag `v0.11.0` (commit `8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798`), unchanged, on 2026-10-14. [MIT](../../THIRD_PARTY_LICENSES.md#deusdatacodebase-memory-mcp), © 2025 DeusData. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md); extract the skill again from the new release's `skill_content` in `src/cli/cli.c`.
