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

## For agents: install, remove and update

### Install

- It's in the `default` [install group](../../groups/README.md), written switched off. Follow [Install](#install) above. In OpenCode, only the [`3d-modeling` agent](../../agents/3d-modeling/) may use its tools.
- It needs FreeCAD, [uv](https://docs.astral.sh/uv/) and the FreeCADMCP addon from tag `v0.1.27` in FreeCAD's `Mod` folder. rulesync installs none of them. Get the user's approval before downloading or copying the addon. The first start downloads `freecad-mcp@0.1.27`.
- Leave the connection off unless the user asks for it. They turn it on as [Use](#use) describes, after starting the RPC server in FreeCAD.
- To verify, once it's on and FreeCAD's RPC server is running, check that `freecad` connects and its tools are listed. Then, with approval, make a small test object in a new, unsaved document. Don't touch the user's existing models.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `freecad` MCP entry, because each run replaces the whole MCP list.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- If the user syncs a native V2 config without the `mcp` feature, remove the `freecad` entry from `mcp.servers` by hand, keeping every other setting.
- FreeCAD, the `Mod/FreeCADMCP` addon and the uv cache stay. Never delete them without the user's explicit approval.

### Update

- Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The pin is `freecad-mcp@0.1.27` in `mcp.jsonc`. Change it together with the addon tag and the versions in this README.

## Origin

[neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp), MIT. This folder holds only the connection entry; no FreeCAD MCP code is copied here.
