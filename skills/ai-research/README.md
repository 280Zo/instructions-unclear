# AI research skills

98 skills covering AI research end to end: picking ideas, model architecture, tokenization, fine-tuning, post-training (RLHF, GRPO and others), distributed training, optimization and quantization, inference serving, evaluation, RAG, agents, interpretability, multimodal models, MLOps and writing papers. Most are expert guides to one framework (vLLM, Unsloth, DeepSpeed, TRL, LangChain and so on), plus `autoresearch`, which runs a whole research project and calls on the others.

From this repo it's a **profile**: it lives in one folder you choose. All 98 descriptions together add about 7,000 tokens to every request, so they load only when you start your tool in that folder.

In OpenCode, the `default` group also installs all 98 globally for the [`ai-research` agent](../../agents/ai-research/). Only that agent loads them, so other agents' requests don't include them.

## Install

From the repo root:

```bash
mkdir -p ~/research
npx rulesync@41.0.0 generate --config skills/ai-research/profile.jsonc --output-roots ~/research --targets claudecode,codexcli,opencode
```

Swap `--targets` for your tools. Never add `--global` to this command: without the agent filter, every session would load all 98. Run the same command again to update the folder.

## Use

```bash
cd ~/research
opencode        # or claude, codex
```

Then ask as you normally would; the matching skill loads itself:

- "Fine-tune Llama 3 8B on `data.jsonl` with Unsloth and LoRA"
- "Serve this model with vLLM and benchmark throughput"
- "Set up GRPO training for this reward function"
- "Evaluate my checkpoint on MMLU with the eval harness"
- "Find a research idea in long-context efficiency and run the experiments" (`autoresearch`)
- "Turn these results into a conference paper draft" (`ml-paper-writing`)

Some skills install Python packages or use cloud GPUs (Modal, Lambda Labs, SkyPilot) when you use them. Each skill says what it needs, and your package-management rule asks before installs.

## For agents: install, remove and update

### Install

- This folder is a profile. The [`ai_research` group](../../groups/README.md#ai_research) installs it, and so does the command under [Install](#install) above, run with `--output-roots` into a folder the user picks (suggest `~/research` or `~/AI/ai_research`). Never add `--global`. The `default` group installs it globally only alongside the filtering [specialist agents](../../agents/README.md).
- It installs skills only, with no rules and no MCP servers. Python packages, GPUs and cloud accounts are not installed; each skill asks for what it needs when used.
- To verify, start the tool in that folder and confirm the skills list includes `autoresearch` and `serving-llms-vllm`. Don't run training, serving or cloud jobs as a test.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component), working inside the chosen folder (`.opencode/skills/`, `.claude/skills/` and so on), not the home folder.

- `delete: false` leaves all 98 skills behind: every directory under `skills/ai-research/skills/`. The `name` fields often differ from the directory names (for example `0-autoresearch-skill` holds `autoresearch`, `vllm` holds `serving-llms-vllm`), so check the generation output for the installed folder names before deleting.
- The folder gets no generated `AGENTS.md` from this profile, because it has no rules.
- If nothing else lives in the folder, the user may prefer to delete the whole folder. Ask first, since research code, data and results may be stored there.
- Python environments, packages, model downloads and cloud resources the skills set up stay unless the user asks to remove them.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The upstream commit is recorded under [Origin](#origin). On refresh, flatten the category folders again, update the count here and in `groups/README.md`, and update the license sections in `THIRD_PARTY_LICENSES.md` (including the nested template inventory). Then rerun the install command into the folder.

## Origin

[Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs), every skill under the numbered category folders, commit `773a52944ba4747a18bd4ae9ade53fff041adcbc`, copied 2026-10-13. Unchanged except that the category folders are flattened (`skills/<skill>/` here instead of `<category>/<skill>/`). The collection's own material is [MIT](../../THIRD_PARTY_LICENSES.md#orchestra-researchai-research-skills), © 2025 Claude AI Research Skills Contributors; this is not a blanket license for nested third-party assets. The [consolidated template inventory and notices](../../THIRD_PARTY_LICENSES.md#nested-ml-paper-writing-template-assets) cover the bundled conference files, TeX packages, PDFs and other template assets, including LPPL material and files whose exact license is not established. Original notices stay in their files. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md); don't use upstream's `npx` installer, which installs into every tool it finds.
