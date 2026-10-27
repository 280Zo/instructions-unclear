# frontend-slides

A skill for slide decks that run in a browser. Instead of asking you to describe a look, it builds a few title-slide previews in different styles and lets you pick one, then makes the full deck as a single HTML file. It can also turn an existing PowerPoint file into a web deck.

## Install

This folder holds only the skill. When to use it comes from the repo's routing rule, [`rules/routing`](../../rules/routing/rules/routing.md), which the `default`, `work` and `writing_reporting` [install groups](../../groups/) install. To add just the skill, from the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/frontend-slides
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/frontend-slides` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Make a slide deck about X from `notes.md`": pick a style from the previews, and it builds the deck.
- "Convert `talk.pptx` into web slides": needs Python's `python-pptx`.
- "Export the deck to PDF": installs Playwright the first time. Your package-management rule asks before that install.

The result is HTML, not PowerPoint. For a deck you can edit in PowerPoint or Google Slides, use Presenton (`mcp-servers/presenton/`). `report` sends "as slides" requests here.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- rulesync doesn't install `python-pptx` (for PowerPoint conversion) or Playwright (for PDF export). Install them only when needed and with approval, following the `package-management` skill.
- To verify, start a new session and confirm the skills list includes `frontend-slides`.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `frontend-slides` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name. `report` sends "as slides" requests here, so tell the user. Decks it made, `python-pptx` and Playwright stay.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The upstream commit and path are under [Origin](#origin). After a refresh, follow the routing bullets below.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "a deck that runs in a browser uses `frontend-slides`".
- It does not own editable `.pptx` decks: those go to `documents`, or to the Presenton MCP when it is enabled. `visual-explainer` makes slides only as part of a page it is already building.
- Why: Slides were claimed by four: `frontend-slides`, `visual-explainer`, `documents` and Presenton.
- A `theme-factory` theme, when one is asked for, replaces the palette and fonts of the style this skill would otherwise pick.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule back to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns (for example editable PowerPoint output), or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides), path `plugins/frontend-slides/skills/frontend-slides/`, commit `9906a34d640d2111f724544cbc50f7f130569ae1`, copied 2026-10-13. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#zarazhangruifrontend-slides), © 2025 Zara Zhang. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
