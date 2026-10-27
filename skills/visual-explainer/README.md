# visual-explainer

A skill that turns explanations, plans, code reviews and data into a self-contained HTML page or slide deck, instead of ASCII art and long tables in the terminal.

## Install

This folder holds only the skill. When to use it comes from the repo's routing rule, [`rules/routing`](../../rules/routing/rules/routing.md), which the `default`, `work` and `writing_reporting` [install groups](../../groups/) install. To add just the skill, from the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/visual-explainer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/visual-explainer` to `inputRoots` in your `rulesync.local.jsonc`. It works best alongside `diagram-design` and `theme-factory`.

## Use

- "Make a visual explanation of how our auth flow works"
- "Show this comparison as a page", "turn this plan into something I can read"
- "Make slides from this summary"

Used on its own, it writes to `~/.agent/diagrams/` and opens the page in your browser. Through [`report`](../report/) or [`eli5`](../eli5/), it writes into the current project instead (`Clanker_Crayon_Box/`).

Pages are written as `<name>.src.html` and rendered through `kit/render.mjs` to the final `<name>.html`. Follow the installed skill's current references. The complete upstream plugin payload is retained, including commands and helper assets; presence in this repo does not register every integration automatically.

Pages load Mermaid and Chart.js from `cdn.jsdelivr.net` and fonts from Google Fonts, so diagrams and fonts need an internet connection to show.

## Notes

The folder also holds upstream's slash commands (`/diff-review`, `/plan-review` and others), Pi extension, MCP server and PowerPoint exporter. rulesync installs the folder but doesn't register the commands, so in this setup you ask in plain words instead.

## For agents: install, remove and update

To install, use the `default`, `work` or `writing_reporting` group, or the single-folder command above. rulesync installs no other software; rendering through `kit/render.mjs` needs Node.js, and pages need an internet connection for their CDN scripts and fonts. To verify, start a new session, check that `visual-explainer` is listed among the skills, and ask for a small test page.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `visual-explainer` skill folder behind; delete it with approval. Pages already written to `~/.agent/diagrams/` or `Clanker_Crayon_Box/` are the user's files and stay unless the user asks. If the user keeps `rules/routing`, its line still names this skill, and `report` and `eli5` render through it, so tell them.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The version and commit are in [Origin](#origin); the update bullets in the next section say what to recheck.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Page** (explanation, plan, review or comparison shown as a page): `visual-explainer`", including a page built around figures, with the figures drawn by `diagram-design`.
- It does not own standalone diagrams (`diagram-design`), browser decks (`frontend-slides`), editable `.pptx` (`documents` or Presenton), a shared theme (`theme-factory`), an explanation drawn as an invented physical machine (`anatomy`) or audio. Its slides are used "only as part of a page it is already making".
- Why: This skill overlapped the most: diagrams with `diagram-design`, slides with `frontend-slides`, `documents` and Presenton, and its narration features with `speech`/`transcribe`.
- `report` and `eli5` delegate page rendering here, so changes to its workflow (such as the 0.14.0 `kit/render.mjs` step) can affect them.
- When a `theme-factory` theme is in use, it replaces this skill's default palette and fonts.
- On upstream updates, don't edit the upstream skill text or commands to change routing, and don't add a per-skill routing rule back to this folder.
- After a refresh, re-read the new `description`, triggers and commands. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer), path `plugins/visual-explainer/`, version 0.14.0, commit `5f378868e0ea745a6284b51e710c390f0c76f72c`, copied 2026-10-20. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#nicobailonvisual-explainer), © 2025 Nico Bailon. The new kit's kepano MIT and Lucide ISC notices are retained in `kit/vendor/PELE-LICENSE` and [consolidated here](../../THIRD_PARTY_LICENSES.md#visual-explainer-kit-vendor-notices). Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
