# local-model

A working agent for local LLMs and unreliable connections: small changes,
short turns, focused checks and working state to iterate on. It keeps mandatory
skills, approvals and safety rules. It does not pick or install a model.

## Install

From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features subagents --input-roots agents/local-model
```

Swap `--targets` for your tools. This folder is also in the default install.
Adding it does not select it or change your current model. OpenCode installs it
with `mode: all`, so it can be the primary agent or a delegated worker. Other
assistants may expose custom agents only as delegated workers; selection and
inherited skills depend on the harness.

## Use other agents while local-model is primary

Install the [second-opinion set](../second-opinion/) for `evaluator` and
`metacognitive`, or another bundle containing the specialist you need.

Keep `local-model` selected and ask for another agent when you need one. Say
what it should check and whether it may edit files. Independent checks can run
in the background; avoid giving workers overlapping edits. Background work may
outlive a lost connection.

The main agent checks the results before continuing. If it asks permission to
delegate, approve only the task you intended. Do not broaden permissions to
work around a denial.

Each child starts with fresh context, so the task brief must include the
relevant paths, evidence, constraints and expected result. A child uses its
configured model or inherits the parent model; a local primary model does not
guarantee every specialist also runs locally. Nested delegation may be denied
or unsupported, in which case the agent reports the limitation.

The `second-opinion` reviewer is primary-only. To audit the whole conversation,
use `/agents` to select it, then select `local-model` again when done. Its
`evaluator` and `metacognitive` helpers are subagents and can be requested
without switching the primary agent.

## Use

- "Make the smallest working change, check it, then let me try it."
- "Pause, I'm switching models." Saves a short `local-model-handoff.md` in the
  project when permitted, otherwise reports the handoff in chat and stops.
- "Stop now, no handoff." Stops starting work without saving a note.
- "Resume from the local-model handoff." Rechecks the actual working state
  before continuing, including any job that might have survived disconnection.

 Origin

Written for this repo. [MIT](../../LICENSE).

OpenCode behavior is documented in [Agents](https://opencode.ai/v2/docs/agents/)
and [TUI](https://opencode.ai/v2/docs/cli/tui/).
