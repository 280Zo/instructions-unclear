# designskills

28 design skills for graphics, UI and design systems: social graphics, posters, thumbnails, ads, mockups and infographics; UI, landing pages, dashboards, mobile, hero sections, cards, dark mode and email; color palettes, typography, layout, brand identity, icons and design tokens; plus critique, motion, presentation design and image treatment. `design-context` stores your brand's colors, fonts and style in `.agents/design-context.md`, and the other skills read it from there. Graphics come from Gemini image generation or as HTML/CSS/SVG.

From this repo it's a **profile**: it lives in one folder you choose, so the 28 descriptions load only when you start your tool there. The [`design` group](../../groups/README.md#design) installs it.

## Install

From the repo root:

```bash
mkdir -p ~/AI/design
npx rulesync@38.0.0 generate --config groups/design.jsonc --output-roots ~/AI/design
```

Add `--targets` for tools other than OpenCode. Never add `--global`. Run the same command again to update the folder.

### What the skills need

rulesync copies the skills and their scripts. It doesn't install what the scripts run:

| Needed for | Install | Notes |
|---|---|---|
| `image-generation`, and graphics that use it | `uv` (or pip) packages `google-genai` and `Pillow`, and `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in your environment | Sends your prompts and reference images to Google's Gemini API |
| `graphic-design/scripts/render.mjs`, `design-critique/scripts/audit.mjs` | Playwright with Chromium | `audit.mjs` loads `axe-core@4` from the jsDelivr CDN when it isn't installed locally; that version isn't pinned |
| `color-palette/scripts/palette.py`, `design-context/scripts/contrast.py` | Python 3 | Standard library only |

Code-only output (HTML/CSS) needs none of these.

## For agents: install and verify

1. Ask where the folder should go (suggest `~/AI/design`) and which tools to target, then generate as above. Don't add `--global`.
2. Tell the user which runtimes in the table above are missing, and install them only with approval, following the `package-management` skill. Never ask for the Gemini key's value; tell the user to set the variable themselves.
3. To verify, start the tool in the folder, confirm the skills list includes `design-context` and `color-palette`, then run a harmless check from the folder, such as `python .opencode/skills/color-palette/scripts/palette.py --from "#2563eb"` (the skills path depends on the target tool). Don't run `image-generation` as a smoke test; it uses the user's Gemini quota.

## Use

```bash
cd ~/AI/design
opencode
```

Start with `design-context` to record your brand, then ask for the work:

- "Set up design context for a fintech startup: navy and teal, modern sans-serif, minimal"
- "Generate an accessible palette from `#2563eb` with dark-mode tokens" (`color-palette`)
- "Make an Instagram post announcing the launch from `product.png`" (`social-media-graphic`)
- "Critique this landing page" (`design-critique`)

## For agents: routing and updates

- Routing lives in this folder's [`rules/design-routing.md`](rules/design-routing.md), which the design group writes into the design folder's own `AGENTS.md`. Inside that folder these skills own design work ahead of `frontend-design`, `frontend-slides`, `diagram-design`, `visual-explainer` and `theme-factory` (user decision, 2026-10-24). The global `rules/routing` doesn't mention them, so outside the folder nothing changes. Editable `.pptx` files still go to Presenton or `documents`.
- The skills depend on each other (shared `design-context`, shared token names, handoffs between skills), so the collection stays in this one folder. Don't split a skill out for another group; the user chose the design group only for `color-palette` on 2026-10-24 for this reason.
- After a refresh, re-read the descriptions. If one now claims a job another item owns, or drops one, update `rules/design-routing.md` and this section in the same change and tell the user.
- Prefer copying over upstream's `npx skills add` installer here. That installer writes into every tool it finds globally, but this collection is meant for one folder.

## Origin

[ArnavPuri/designskills](https://github.com/ArnavPuri/designskills), the `skills/` folder (all 28 skills, with their scripts), commit `c7873015add8571ca95043febad0d9e6c97ee5c6` (v1.1.0), copied 2026-10-24. The skills are unchanged; `rules/design-routing.md` is written for this repo and isn't upstream's. Upstream's evals, tests, CI and docs aren't copied. [MIT](../../THIRD_PARTY_LICENSES.md#arnavpuridesignskills), © 2026 Arnav Puri. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
