# anatomy

`anatomy` explains a technical idea by inventing a physical machine whose working *is* the idea, then drawing it as a detailed, interactive isometric SVG figure. A cache key that skips unchanged work becomes a pin-tumbler lock; one GPU context serving many canvases becomes a plotter with one print head. Figures can add WebGL effects (fire, water, lamp light) or an optional 3D mode, and can print as A4 PDFs. It ships eight complete example machines in `examples/`, which the skill opens and builds from.

It's in the `default` and `work` groups next to `visual-explainer` and `diagram-design`, and in the `design` folder group.

## Install

From the repo root, through an [install group](../../groups/), or just this skill:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/anatomy
```

rulesync copies the skill, its kit, scripts and examples (about 27 MB). It doesn't install what they run:

| Needed for | Install | Notes |
|---|---|---|
| Building figures (`node examples/<name>/build.mjs`, the kit) | Node.js 20.10 or newer | Uses only Node's built-in modules; nothing to `npm install` |
| The skill's own checks, captures and PDF printing (`scripts/capture.mjs`, `drive.mjs`, `print.mjs`, `turn-check.mjs`) | Google Chrome or Chromium | Started headless; on Linux with `--no-sandbox` and `--allow-file-access-from-files`, so only render pages you generated |
| Publishing to the community gallery (`scripts/publish.mjs --submit`) | `git` and an authenticated GitHub CLI (`gh`) | Opens a pull request on the user's behalf |

## Use

- "Explain how a token bucket rate limiter works as an interactive figure"
- "Draw our build cache as an isometric machine for the docs"
- "Print that figure as an A4 poster"

## For agents: install, remove and update

### Install

1. Install with the `default`, `work` or `design` group, or the command above.
2. Check `node --version` (20.10 or newer) and whether Chrome or Chromium is installed. Install either only with approval, following the `package-management` skill.
3. To verify, confirm `anatomy` is in the skills list, then build the smallest example from the installed skill folder: `node examples/dial-indicator/build.mjs`. It writes a standalone HTML page beside the script and touches nothing else.

### Publishing needs an explicit request

`scripts/publish.mjs` copies a figure into a local clone of the community gallery. With `--submit` it also creates a branch and opens a pull request with `gh`, after asking for confirmation. Run it only when the user asks to publish a specific figure, show them the plan first, and never pass `--yes`. Opening a pull request is externally visible, so the user's own approval rules apply on top of the script's question.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `anatomy` skill folder behind in each tool's skills directory (and inside the design folder if the `design` group installed it); delete it only with approval. Figures, PDFs and pages the user built stay. Node, Chrome and `gh` stay installed unless the user asks.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The pinned commit is under [Origin](#origin). Copy the same paths again (`SKILL.md`, `LICENSE`, `agents/`, `kit/`, `references/`, `scripts/`, `examples/`), then re-read the description and the routing bullets below.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Explanation as a physical object**: `anatomy`". Its description is broad and also claims explanatory diagrams and SVGs that show how a system works, so the routing line keeps diagrams of the system itself with `diagram-design` and explanation pages with `visual-explainer`. Use `anatomy` when the user wants the idea shown as an invented machine, or asks for an isometric, interactive or "premium" technical figure.
- Don't edit the upstream text to change routing.
- After a refresh, re-read the description. If it claims more jobs another item owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[wheresryan22/anatomy](https://github.com/wheresryan22/anatomy), repo root (the skill files listed under Update), `main` at commit `1482e8469b0a9e0d8cc18ea2740a01423d29ae80` (2026-10-18, 53 commits after the v1.1.0 release), copied 2026-10-25. Unchanged. Upstream's tests, evals, CI, changelog and contributor docs aren't copied. [MIT](../../THIRD_PARTY_LICENSES.md#wheresryan22anatomy), © 2026 Ryan. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
