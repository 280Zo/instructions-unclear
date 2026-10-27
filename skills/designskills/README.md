# designskills

19 design skills for graphics, brand and design systems: social graphics, posters, thumbnails, banners, ads and product mockups; brand identity, color palettes, typography, dark mode, icons, motion and design tokens; email templates, image treatment and design critique. `design-context` stores your brand's colors, fonts and style in `.agents/design-context.md`, and the other skills read it from there. Graphics come from Gemini image generation or as HTML/CSS/SVG.

UI pages, slide decks and infographics aren't here: `frontend-design`, `frontend-slides` and `diagram-design` own those jobs (see [Changes from upstream](#changes-from-upstream)).

From this repo it's a **profile**: it lives in one folder you choose, so the descriptions load only when you start your tool there. The [`design` group](../../groups/README.md#design) installs it. In OpenCode, the `default` group also installs it globally for the [`design` agent](../../agents/design/), the only agent that loads these skills. `design-context` still reads and writes `.agents/design-context.md` in the folder you start in.

## Install

From the repo root:

```bash
mkdir -p ~/AI/design
npx rulesync@41.0.0 generate --config groups/design.jsonc --output-roots ~/AI/design
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

## For agents: install, remove and update

### Install

The [`design` group](../../groups/README.md#design) installs this folder profile. Never add `--global` to that command; `default` installs it globally only alongside the filtering [specialist agents](../../agents/README.md).

1. Ask where the folder should go (suggest `~/AI/design`) and which tools to target, then generate as above. Don't add `--global`.
2. Tell the user which runtimes in the table above are missing, and install them only with approval, following the `package-management` skill. Never ask for the Gemini key's value; tell the user to set the variable themselves.
3. To verify, start the tool in the folder, confirm the skills list includes `design-context` and `color-palette`, then run a harmless check from the folder, such as `python .opencode/skills/color-palette/scripts/palette.py --from "#2563eb"` (the skills path depends on the target tool). Don't run `image-generation` as a smoke test; it uses the user's Gemini quota.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component), working inside the design folder (`.opencode/skills/` and so on), not the home folder.

- `delete: false` leaves all 19 skills behind: every directory under `skills/designskills/skills/`. Delete them only with approval.
- Don't delete the whole folder without asking. `.agents/design-context.md` and the graphics, pages and exports the skills made are the user's work and stay unless the user explicitly asks.
- Python packages, Playwright and Chromium, and the `GEMINI_API_KEY` setting stay installed. Offer to remove packages separately, following the `package-management` skill.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The upstream commit and release are under [Origin](#origin). When copying a new release, copy every skill folder except the 9 listed under [Changes from upstream](#changes-from-upstream), then check whether upstream added a skill that overlaps one this repo already has. Ask the user before keeping a new overlap. Update the count in `groups/README.md` if it changed, and rerun the install command into the folder.

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

- Not in [`rules/routing`](../../rules/routing/rules/routing.md), and the folder has no routing rule of its own. Without the 9 overlapping skills, none of the 19 claims a job another installed skill owns.
- The skills depend on each other (shared `design-context`, shared token names, handoffs between skills), so the 19 stay together in this one folder.
- A few kept skills still name removed ones in passing (for example `banner-design` says to use `hero-section` for a hero, and `email-design` names `landing-page-design`). Treat those as pointers to the current owner: `frontend-design` for UI and pages, `frontend-slides` for decks, `diagram-design` for infographics. Don't edit the upstream text to change them.
- After a refresh, re-read the descriptions. If one now claims a job another item owns, or drops one, tell the user and update this section in the same change.
- Prefer copying over upstream's `npx skills add` installer here. That installer writes into every tool it finds globally, but this collection is meant for one folder.

## Changes from upstream

Nine upstream skills that overlap more popular skills in this repo aren't copied. The 19 that are copied are unchanged.

| Not copied | Overlapped with |
|---|---|
| `ui-design`, `landing-page-design`, `hero-section`, `dashboard-design`, `card-design`, `mobile-ui-design`, `layout-composition` | `frontend-design` (anthropics/skills) |
| `presentation-design` | `frontend-slides` |
| `infographic` | `diagram-design` |

`typography` was kept because `design-system`, `brand-identity`, `design-context` and `design-critique` take their type scale from it.

## Origin

[ArnavPuri/designskills](https://github.com/ArnavPuri/designskills), the `skills/` folder (19 of its 28 skills, with their scripts), commit `c7873015add8571ca95043febad0d9e6c97ee5c6` (v1.1.0), copied 2026-10-24. The kept skills are unchanged; the removals are listed above. Upstream's evals, tests, CI and docs aren't copied. [MIT](../../THIRD_PARTY_LICENSES.md#arnavpuridesignskills), © 2026 Arnav Puri. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
