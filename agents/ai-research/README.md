# ai-research

AI and machine-learning research and engineering: training, fine-tuning, RL, quantization, inference serving, evaluation, interpretability, safety, RAG and vector stores, agent frameworks, experiment tracking, research ideation and ML paper writing.

One agent file for every tool. In OpenCode it can use only its own skills (skills/ai-research), the shared ones every agent gets, and the Exa, PMB, Docling servers; other tools get its instructions without those limits. See [how agents keep skills out of each other's requests](../README.md#how-agents-keep-skills-out-of-each-others-requests) and [what each assistant enforces](../README.md#what-each-assistant-enforces).

## Install

Part of the [`default` group](../../groups/README.md#default), which also installs its skills. For another tool, add `--targets`; see [what each assistant enforces](../README.md#what-each-assistant-enforces) for why the skills are better installed with their folder group there.

## Use

Pick `ai-research` with `/agents` in OpenCode, or ask your main agent to hand it a task. Some skills install Python packages or use paid GPUs and cloud accounts when used; the agent asks first.

## For agents: install, remove and update

`subagents/ai-research.md` is written by [`agents/generate.py`](../generate.py); change the agent in its manifest and follow [its update steps](../README.md#update). To remove it, follow [Remove](../README.md#remove).

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE).
