# FreeCAD

[FreeCAD MCP](https://github.com/neka-nat/freecad-mcp) lets your agent drive [FreeCAD](https://www.freecad.org): create and edit 3D models, run FreeCAD Python scripts, inspect documents and run FEM analyses, while you watch the model change in FreeCAD.

| File | What it is |
|---|---|
| `mcp.jsonc` | The `freecad` MCP server, run as `uvx freecad-mcp@0.1.27`, installed switched off |

It has two halves: an addon inside FreeCAD that listens for commands, and the MCP server your coding tool starts, which sends them.

## Install

1. Have FreeCAD and [uv](https://docs.astral.sh/uv/). The server needs Python 3.12+, which `uvx` provides.
2. Install the addon into FreeCAD: copy `addon/FreeCADMCP` from [the FreeCAD MCP repo](https://github.com/neka-nat/freecad-mcp) (at tag `v0.1.27`, to match the server) into FreeCAD's `Mod` folder, so you end up with `Mod/FreeCADMCP`, then restart FreeCAD. The `Mod` folder depends on your system and FreeCAD version; for example `~/.local/share/FreeCAD/v1-1/Mod/` on Arch with FreeCAD 1.1, or `~/Library/Application Support/FreeCAD/v1-1/Mod/` on macOS. Upstream's [installation guide](https://github.com/neka-nat/freecad-mcp/blob/main/docs/installation.md#addon-directory) lists the rest.
3. Add `mcp-servers/freecad` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features mcp` included. rulesync replaces your tool's whole MCP server list, so keep your other server folders in that list too.

## Use

1. Open FreeCAD, switch to the **MCP Addon** workbench and click **Start RPC Server**.
2. Turn the `freecad` server on in your tool. In OpenCode, set `"enabled": true` on it in `opencode.jsonc`.
3. Ask: "make a 40 mm cube with a 10 mm hole through the centre", "add 2 mm fillets to the top edges", "run a stress analysis on this bracket with 500 N on the top face".
4. When you're done, turn the server off again.

## Updating

Change `freecad-mcp@0.1.27` in `mcp.jsonc` to the new version from [PyPI](https://pypi.org/project/freecad-mcp/), and copy the addon from the matching tag. "Check for updates" in [`AGENTS.md`](../../AGENTS.md) finds new versions.

## Origin

[neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp), MIT. This folder holds only the connection entry; no FreeCAD MCP code is copied here.
