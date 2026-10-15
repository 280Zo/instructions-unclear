# Anthropic design skills

Two of Anthropic's published skills:

| Skill | What it does |
|---|---|
| `frontend-design` | Design direction when building or reshaping a UI: a clear aesthetic, considered typography, and choices that don't look like a template |
| `theme-factory` | 10 ready-made colour and font themes (or a new one made to order) applied to slides, documents, reports and HTML pages, so several outputs share one look |

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/anthropic-design
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/anthropic-design` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- **`frontend-design`** loads by itself when you ask the agent to build or restyle an interface ("build a settings page", "make this landing page less generic").
- **`theme-factory`**: "show me the themes" (it has a showcase PDF), "apply the Ocean Depths theme to this deck", "make a theme for a coffee brand". `report` uses it so a report's page, diagrams and slides match.

When a theme and another skill's style advice disagree on colours or fonts, `report` tells the agent to follow the theme. The themes name desktop fonts (DejaVu, FreeSans), so `report` also adds web-safe fallbacks.

## Notes

Only these two are here. Anthropic's document skills (`pptx`, `docx`, `xlsx`, `pdf`) are proprietary, so they can't be shared in this repo.

## Origin

[anthropics/skills](https://github.com/anthropics/skills), paths `skills/frontend-design/` and `skills/theme-factory/`, commit `dbd4588f9e1033efb41dad4bef2f7947c8993d44`, copied 2026-10-13. Unchanged. Apache 2.0, © Anthropic; the license is `LICENSE.txt` in each skill folder. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
