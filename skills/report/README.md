# report

A skill that writes up material you've already gathered (files, notes, a talk, scan results) as a report that anchors every claim to its source and states who it's for.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/report
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/report` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Type `/report`, or ask it to "write up" what you've gathered, optionally "for the board" or "as slides". It renders through [`visual-explainer`](../visual-explainer/), [`diagram-design`](../diagram-design/), [`frontend-slides`](../frontend-slides/), `theme-factory` ([`anthropic-design`](../anthropic-design/)) or [Presenton](../../mcp-servers/presenton/), saving to `Clanker_Crayon_Box/reports/` in the current folder. Without those installed it can still gather and check the evidence, but not render it.

To learn something new rather than write it up, use [`eli5`](../eli5/).

## Notes

Claude Code's `allowed-tools` sits under a `claudecode:` section so other tools ignore it.

## Origin

Written for this repo. [MIT](../../LICENSE).
