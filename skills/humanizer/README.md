# humanizer

A skill that rewrites text that sounds AI-written so it reads like a person wrote it, without changing what it says. It works from Wikipedia's "Signs of AI writing": staged contrasts, one-line closers, forced lists of three, dashes everywhere, inflated claims and the like.

## Install

This folder holds the skill and a one-line rule (written for this repo) telling the agent when to use it. The rule goes into your tool's instructions file, which rulesync replaces on every run, so to get it, add `skills/humanizer` to `inputRoots` in your `rulesync.local.jsonc` with your other rule folders, or use an [install group](../../groups/). To add just the skill, from the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/humanizer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/humanizer` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Humanize this:" followed by pasted text returns a draft, the patterns it found, and a final version.
- "Humanize `README.md`" edits the file in place, changing prose only (code, commands and links stay as they are).
- Give it a sample of your own writing and it matches your voice.

Its rule tells the agent to use it for anything people will read: READMEs, docs, commit messages and pull requests.

## Origin

[blader/humanizer](https://github.com/blader/humanizer), unchanged, copied 2026-10-01. No commit was recorded; the first update check records one. [MIT](../../THIRD_PARTY_LICENSES.md#bladerhumanizer), © 2025 Siqi Chen. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
