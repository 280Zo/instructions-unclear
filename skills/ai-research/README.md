# AI research skills

98 skills covering AI research end to end: picking ideas, model architecture, tokenization, fine-tuning, post-training (RLHF, GRPO and others), distributed training, optimization and quantization, inference serving, evaluation, RAG, agents, interpretability, multimodal models, MLOps and writing papers. Most are expert guides to one framework (vLLM, Unsloth, DeepSpeed, TRL, LangChain and so on), plus `autoresearch`, which runs a whole research project and calls on the others.

From this repo it's a **profile**: it lives in one folder you choose. All 98 descriptions together add about 7,000 tokens to every request, so they load only when you start your tool in that folder.

## Install

From the repo root:

```bash
mkdir -p ~/research
npx rulesync@38.0.0 generate --config skills/ai-research/profile.jsonc --output-roots ~/research --targets claudecode,codexcli,opencode
```

Swap `--targets` for your tools. Never add `--global`: that would load all 98 in every session. Run the same command again to update the folder.

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

## Origin

[Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs), every skill under the numbered category folders, commit `773a52944ba4747a18bd4ae9ade53fff041adcbc`, copied 2026-10-13. Unchanged except that the category folders are flattened (`skills/<skill>/` here instead of `<category>/<skill>/`). The collection's own material is [MIT](../../THIRD_PARTY_LICENSES.md#orchestra-researchai-research-skills), © 2025 Claude AI Research Skills Contributors; this is not a blanket license for nested third-party assets. The [consolidated template inventory and notices](../../THIRD_PARTY_LICENSES.md#nested-ml-paper-writing-template-assets) cover the bundled conference files, TeX packages, PDFs and other template assets, including LPPL material and files whose exact license is not established. Original notices stay in their files. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md); don't use upstream's `npx` installer, which installs into every tool it finds.
