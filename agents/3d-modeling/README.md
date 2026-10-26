# 3d-modeling

3D CAD modeling in FreeCAD through its MCP server, once FreeCAD and its addon are set up and the connection is switched on: parts, sketches, assemblies, measurements and exports. Use anatomy instead for isometric explainer drawings.

One agent file for every tool. In OpenCode it can use only its own skills (the general writing, documents, visuals and browser skills), the shared ones every agent gets, and the Exa, PMB, Docling, freecad servers; other tools get its instructions without those limits. See [how agents keep skills out of each other's requests](../README.md#how-agents-keep-skills-out-of-each-others-requests) and [what each assistant enforces](../README.md#what-each-assistant-enforces).

## Install

Part of the [`default` group](../../groups/README.md#default), which also installs its skills. For another tool, add `--targets`; see [what each assistant enforces](../README.md#what-each-assistant-enforces) for why the skills are better installed with their folder group there.

## Use

Pick `3d-modeling` with `/agents` in OpenCode, or ask your main agent to hand it a task. FreeCAD, its MCP addon and server must be set up, and the `freecad` connection switched on; it's written switched off. Follow the [FreeCAD README](../../mcp-servers/freecad/README.md).

## For agents: install, remove and update

`subagents/3d-modeling.md` is written by [`agents/generate.py`](../generate.py); change the agent in its manifest and follow [its update steps](../README.md#update). To remove it, follow [Remove](../README.md#remove).

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE).
