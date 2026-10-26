# design

Graphic, brand and visual design: palettes, typography, logos and brand identity, social graphics, banners, posters, icons, mockups, image treatment and design critique, plus UI, slides, diagrams and explainer pages. Reads brand settings from .agents/design-context.md in the working folder.

One agent file for every tool. In OpenCode it can use only its own skills (skills/designskills, plus the UI, slide, diagram and explainer skills), the shared ones every agent gets, and the Exa, PMB, Docling, presenton servers; other tools get its instructions without those limits. See [how agents keep skills out of each other's requests](../README.md#how-agents-keep-skills-out-of-each-others-requests) and [what each assistant enforces](../README.md#what-each-assistant-enforces).

## Install

Part of the [`default` group](../../groups/README.md#default), which also installs its skills. For another tool, add `--targets`; see [what each assistant enforces](../README.md#what-each-assistant-enforces) for why the skills are better installed with their folder group there.

## Use

Pick `design` with `/agents` in OpenCode, or ask your main agent to hand it a task. Start OpenCode in the project or brand folder you're working on. The design skills read colors, fonts and style from `.agents/design-context.md` there; `design-context` creates it. Image generation needs a Gemini key; the [design skills README](../../skills/designskills/README.md#what-the-skills-need) lists what the scripts need.

## For agents: install, remove and update

`subagents/design.md` is written by [`agents/generate.py`](../generate.py); change the agent in its manifest and follow [its update steps](../README.md#update). To remove it, follow [Remove](../README.md#remove).

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE).
