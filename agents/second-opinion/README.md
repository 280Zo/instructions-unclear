# second-opinion

Three agents that check the main agent's work.

- **`second-opinion`**: a primary agent for stalled or off-track sessions, high-stakes strategy reviews and critical deliverable checks. It reviews the conversation and files, verifies external claims against current primary sources, and reports findings with evidence. It asks before edits or shell commands; then you switch back.
- **`evaluator`**: a subagent that checks an answer for correctness, evidence, completeness and concision before it's delivered.
- **`metacognitive`**: a subagent that checks the reasoning stays on the question and doesn't go down rabbit holes.

## Install

Agents are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features subagents --input-roots agents/second-opinion
```

Swap `--targets` for your tools. To keep it in your regular install, add `agents/second-opinion` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- In OpenCode, run `/agents`, pick `second-opinion`, ask "how is this session going?", then switch back to your working agent. Choose the model separately with `/models` if needed.
- Ask for the others by name: "have the evaluator check this", "run the metacognitive check on this plan". `second-opinion` calls `evaluator` itself.

`second-opinion` runs a metacognitive check and requires an explicit evaluator
PASS before delivering its report. Missing or denied delegation produces a
blocker notice, not a report falsely labeled validated. Both reviews are
read-only. The agent keeps the research, uncertainty, tone and precedence rules
alongside the session-audit checklist and findings table.

Official docs, specifications and project repositories/changelogs come before
forums or posts. Secondary evidence is labeled; model memory alone cannot
verify an external factual claim. Current tool access and approvals still
apply. Some harnesses cannot delegate from custom agents, so the strict review
protocol needs a compatible harness and both reviewers installed.

## Notes

The reviewer was renamed from `course-corrector` to `second-opinion`. Because
rulesync uses `delete: false`, an old live copy may remain after installing the
new name. Review any local customizations and approve its removal separately;
this repo does not remove live agents automatically.

Tool-only settings stay under `opencode:` (`mode`, `permissions`) and `claudecode:` (`tools`) sections, so each tool gets only its own. The reviewer tool list includes `Agent` and `Task` for harness versions that use those names; the prompt uses the native delegation tool instead of assuming a nesting-depth setting.

OpenCode selection and delegation details: [Agents](https://opencode.ai/v2/docs/agents/)
and [TUI](https://opencode.ai/v2/docs/cli/tui/).

## Origin

Written for this repo. [MIT](../../LICENSE).
