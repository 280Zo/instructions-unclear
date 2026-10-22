# Anthropic design skills

Two of Anthropic's published skills:

| Skill | What it does |
|---|---|
| `frontend-design` | Design direction when building or reshaping a UI: a clear aesthetic, considered typography, and choices that don't look like a template |
| `theme-factory` | 10 ready-made colour and font themes (or a new one made to order) applied to slides, documents, reports and HTML pages, so several outputs share one look |

## Install

This folder holds only the two skills. When to use them comes from the repo's routing rule, [`rules/routing`](../../rules/routing/rules/routing.md), which the `default`, `work` and `writing_reporting` [install groups](../../groups/) install. To add just the skills, from the repo root:

```bash
npx rulesync@38.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/anthropic-design
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/anthropic-design` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- **`frontend-design`** loads by itself when you ask the agent to build or restyle an interface ("build a settings page", "make this landing page less generic").
- **`theme-factory`**: "show me the themes" (it has a showcase PDF), "apply the Ocean Depths theme to this deck", "make a theme for a coffee brand". `report` uses it so a report's page, diagrams and slides match.

When a theme and another skill's style advice disagree on colours or fonts, `report` tells the agent to follow the theme. The themes name desktop fonts (DejaVu, FreeSans), so `report` also adds web-safe fallbacks.

## Notes

Only these two are here. Anthropic's document skills (`pptx`, `docx`, `xlsx`, `pdf`) are proprietary, so they can't be shared in this repo.

## For agents: routing and updates

- Roles in [`rules/routing`](../../rules/routing/rules/routing.md): "**One shared look** across several visual outputs: `theme-factory`. Its theme replaces each renderer's default palette and fonts." and "**UI and frontend design**: `frontend-design`."
- Neither skill renders pages, diagrams or decks: those stay with `visual-explainer`, `diagram-design`, `frontend-slides`, `documents` or Presenton. `theme-factory` only supplies the look they use.
- The routing rule settles one conflict here: when a theme and a renderer's own style advice disagree on colours or fonts, the theme wins.
- Why: on 2026-10-21 the user replaced the per-skill rules (including this folder's `theme-factory` rule) with one routing rule because several skills' descriptions and rules claimed the same jobs. `theme-factory` lists slides, documents, reports and pages, which other skills also claim, so the rule limits it to the theme.
- On upstream updates, don't edit Anthropic's skill text to change routing, and don't add a per-skill routing rule back to this folder.
- After a refresh, re-read both new `description`s. If either now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[anthropics/skills](https://github.com/anthropics/skills), paths `skills/frontend-design/` and `skills/theme-factory/`, commit `dbd4588f9e1033efb41dad4bef2f7947c8993d44`, copied 2026-10-13. Unchanged. Apache 2.0, © Anthropic; the license is `LICENSE.txt` in each skill folder. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
