# PMB

[PMB](https://pypi.org/project/pmb-ai/) (`pmb-ai`) is a local, per-project memory for AI agents: decisions, lessons and progress that survive between sessions.

## What's in this folder

| File | Becomes |
|---|---|
| `mcp.jsonc` | The `pmb` entry in OpenCode's MCP server list |
| `rules/60-pmb-memory.md` | The "PMB Memory" section of `AGENTS.md` |

The detailed usage instructions the AI sees ("read before you write", one `record_batch` per turn, and so on) come from the PMB server itself when it connects. They aren't copied here, so they can't go stale.

## Install

Install it once with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install pmb-ai
```

That provides `pmb`, `pmb-ai`, `pmb-chat`, `pmb-hook` and `pmb-mcp`. The MCP entry runs the installed `pmb-mcp`. Update it with `uv tool upgrade --all`.

## Per-project setup

- **Memory location.** `PMB_HOME=.pmb` is a relative path: memory goes into a `.pmb/` folder inside whichever folder PMB starts in. `"cwd": "."` makes PMB start in the current project, so each project gets its own memory. Add `.pmb/` to your global gitignore so it's never committed.
- **Connecting a project.** Run `pmb connect --active` in a project to set it up.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `pmb_prepare`. Any permission rule written as `"pmb_*": ...` matches on that name. If you rename the server, update those rules too.
