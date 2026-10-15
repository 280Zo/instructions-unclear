# Trail of Bits security skills

83 skills and 30 agents from the security firm Trail of Bits: security-focused code review, static analysis with Semgrep and CodeQL, finding variants of a known bug, fuzzing, property-based and mutation testing, dependency risk, insecure defaults, cryptographic timing leaks, smart-contract auditing, and more.

From this repo it's a **profile**: it lives in one folder you choose, so it loads only when you start your tool there for security work.

## Install

From the repo root:

```bash
mkdir -p ~/security
npx rulesync@33.0.0 generate --config skills/trailofbits/profile.jsonc --output-roots ~/security --targets claudecode,codexcli,opencode
```

Swap `--targets` for your tools. Never add `--global`. Run the same command again to update the folder.

Optional: for the parts this copy leaves out (slash commands, hooks, workflows, and five skills that need them; see "Changes from upstream"), also install Trail of Bits' own plugins. These install globally in that tool, not just in the profile folder.

- Claude Code: `/plugin marketplace add trailofbits/skills`, then `/plugin menu` to pick plugins.
- Codex: `codex plugin marketplace add trailofbits/skills`, then `codex plugin add <plugin-name>@trailofbits`.

## Use

The profile folder is where your tool starts, not where your code has to be. Start the tool there and point it at the code by path:

```bash
cd ~/security
opencode        # or claude, codex
```

- "Do a security review of the changes on branch `feature-x` in `~/code/app`" (`differential-review`)
- "Find error-prone APIs and dangerous configurations in `~/code/app`" (`sharp-edges`)
- "Run Semgrep on `~/code/app` and triage the findings" (`semgrep`, `fp-check`)
- "We fixed this bug; find other places with the same pattern" (`variant-analysis`)
- "Check the supply-chain risk of this project's dependencies" (`supply-chain-risk-auditor`)

Many skills drive tools you install yourself: Semgrep, CodeQL, fuzzers, sanitizers, `cargo +nightly`. Each skill names what it needs.

## Changes from upstream

- Claude Code-only settings moved under a `claudecode:` section so rulesync keeps them: `allowed-tools`, `argument-hint`, `effort` and `disable-model-invocation` in 38 skills, and `tools`, `model` and `color` in all 30 agents. The values are unchanged.
- Every agent gained `targets: ["*"]`, which rulesync needs.
- `firebase-apk-scanner`: its `argument-hint` value `[apk-file-or-directory]` is quoted. Unquoted, YAML reads it as a list and rulesync rejects the skill.
- Only the skill and agent folders are copied. Upstream's slash commands, hooks, and the `workflows/`, `prompts/` and `scripts/` folders outside the skill folders aren't. That leaves out two plugins that are only commands and workflows: `insecure-defaults` and `git-cleanup`. Five skills look for those through `${CLAUDE_PLUGIN_ROOT}` and fall back when it isn't set, so they work only partly: `code-improver`, `pr-improver`, `skill-improver`, `rust-review` and `c-review`. The optional install step above covers them.

Reapply these after each update.

## Origin

[trailofbits/skills](https://github.com/trailofbits/skills), every `plugins/*/skills/*` and `plugins/*/agents/*`, commit `4a48f7fa49c991be70cf2cbcecd9bad20cb2c544`, copied 2026-10-14. [CC BY-SA 4.0](../../THIRD_PARTY_LICENSES.md#trailofbitsskills), by Trail of Bits; the files here, changes included, stay under the same license. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
