# eli5

A skill that teaches one unfamiliar thing in plain English: a concept, an event, a mechanism, a protocol, a paper.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/eli5
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/eli5` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Type `/eli5 <topic>`, or ask "how does X work?" or "explain like I'm five". It researches, then teaches in short turns and checks you can use each idea. At the end it offers to save a one-page explainer; that needs [`visual-explainer`](../visual-explainer/) and [`diagram-design`](../diagram-design/).

To write up material you've already gathered, use [`report`](../report/) instead.

## Notes

Claude Code's `allowed-tools` sits under a `claudecode:` section so other tools ignore it.

## Origin

Written for this repo. [MIT](../../LICENSE).
