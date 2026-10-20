# frontend-slides

A skill for slide decks that run in a browser. Instead of asking you to describe a look, it builds a few title-slide previews in different styles and lets you pick one, then makes the full deck as a single HTML file. It can also turn an existing PowerPoint file into a web deck.

## Install

This folder holds the skill and a one-line rule (written for this repo) telling the agent when to use it. The rule goes into your tool's instructions file, which rulesync replaces on every run, so to get it, add `skills/frontend-slides` to `inputRoots` in your `rulesync.local.jsonc` with your other rule folders, or use an [install group](../../groups/). To add just the skill, from the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/frontend-slides
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/frontend-slides` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Make a slide deck about X from `notes.md`": pick a style from the previews, and it builds the deck.
- "Convert `talk.pptx` into web slides": needs Python's `python-pptx`.
- "Export the deck to PDF": installs Playwright the first time. Your package-management rule asks before that install.

The result is HTML, not PowerPoint. For a deck you can edit in PowerPoint or Google Slides, use Presenton (`mcp-servers/presenton/`). `report` sends "as slides" requests here.

## Origin

[zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides), path `plugins/frontend-slides/skills/frontend-slides/`, commit `9906a34d640d2111f724544cbc50f7f130569ae1`, copied 2026-10-13. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#zarazhangruifrontend-slides), © 2025 Zara Zhang. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
