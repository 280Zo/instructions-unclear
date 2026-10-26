# general

Restrictions for OpenCode's helper for research and multi-step work, started by other agents. The file adds only deny rules: OpenCode keeps the built-in `general` agent's prompt, mode (`subagent`) and permissions, and this agent no longer sees the design, career, AI research, threat-modeling and reverse-engineering skills or the ZAP, REA, ReVa, radare2 and FreeCAD servers. Everything else stays available. See [how agents keep skills out of each other's requests](../README.md#how-agents-keep-skills-out-of-each-others-requests).

It installs only for OpenCode. Other tools have their own built-in agents and can't filter skills.

## Install

Part of the [`default` group](../../groups/README.md#default). Install it with the specialist agents and their skill folders; without them, the denied skills have no agent that can load them.

## For agents: install, remove and update

`subagents/general.md` is written by [`agents/generate.py`](../generate.py); follow [its update steps](../README.md#update). To remove the restriction, delete `~/.config/opencode/agents/general.md` with approval. OpenCode then uses its unrestricted built-in agent.

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE).
