# visual-explainer

A skill that turns explanations, plans, code reviews and data into a self-contained HTML page or slide deck, instead of ASCII art and long tables in the terminal.

## Install

This folder holds the skill and a one-line rule (written for this repo) telling the agent when to use it. The rule goes into your tool's instructions file, which rulesync replaces on every run, so to get it, add `skills/visual-explainer` to `inputRoots` in your `rulesync.local.jsonc` with your other rule folders, or use an [install group](../../groups/). To add just the skill, from the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/visual-explainer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/visual-explainer` to `inputRoots` in your `rulesync.local.jsonc`. It works best alongside `diagram-design` and `theme-factory`.

## Use

- "Make a visual explanation of how our auth flow works"
- "Show this comparison as a page", "turn this plan into something I can read"
- "Make slides from this summary"

Used on its own, it writes to `~/.agent/diagrams/` and opens the page in your browser. Through [`report`](../report/) or [`eli5`](../eli5/), it writes into the current project instead (`Clanker_Crayon_Box/`).

Pages load Mermaid and Chart.js from `cdn.jsdelivr.net` and fonts from Google Fonts, so diagrams and fonts need an internet connection to show.

## Notes

The folder also holds upstream's slash commands (`/diff-review`, `/plan-review` and others), Pi extension, MCP server and PowerPoint exporter. rulesync installs the folder but doesn't register the commands, so in this setup you ask in plain words instead.

## Origin

[nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer), path `plugins/visual-explainer/`, commit `33a6b4d43958d2d152c9cb13762af802062fade5`, copied 2026-10-13. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#nicobailonvisual-explainer), © 2025 Nico Bailon. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
