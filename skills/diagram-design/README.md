# diagram-design

A skill for clean, editorial diagrams: 45 types, from architecture and flowcharts to sequence diagrams, timelines, Sankey charts and database schemas, with HTML/SVG templates in light, dark or full-editorial styles.

Static diagrams and motion variants have different runtime requirements: the bundled templates load Google Fonts from the internet, and motion variants use JavaScript for animation controls. They are not all offline or JavaScript-free. For strictly offline output, ask for system fonts and no external assets; for JavaScript-free output, choose a static diagram rather than a motion variant.

## Install

This folder holds only the skill. When to use it comes from the repo's routing rule, [`rules/routing`](../../rules/routing/rules/routing.md), which the `default`, `work` and `writing_reporting` [install groups](../../groups/) install. To add just the skill, from the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/diagram-design
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/diagram-design` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Draw an architecture diagram of this repo"
- "Make a sequence diagram of the login flow", "a timeline of the project milestones"
- "Match the style of https://example.com" (it reads the site to pick colours and fonts)
- "Redraw this Mermaid diagram properly" (it converts draw.io and Mermaid sources)

The routing rule sends diagram requests here, and `report` uses it for the diagrams in reports. Browse every type in [upstream's gallery](https://cathrynlavery.github.io/diagram-design/), or open `skills/diagram-design/assets/index.html` locally.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- Nothing extra is required for HTML/SVG output. The bundled templates load Google Fonts from the internet unless the user asks for system fonts.
- To verify, start a new session and confirm the skills list includes `diagram-design`, or open `assets/index.html` in the installed skill folder.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `diagram-design` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name. `report`, `eli5` and `visual-explainer` hand diagrams to it, so tell the user those lose their diagram renderer. Diagrams it already made stay.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The upstream commit is under [Origin](#origin). Copy the whole skill folder, including exporters and assets, then follow the routing bullets below.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Diagram** on its own: `diagram-design`". It also draws the figures when `visual-explainer` builds a page around them.
- It does not own pages (explanations, plans, reviews, comparisons): those go to `visual-explainer`. A shared look across outputs belongs to `theme-factory`, whose theme replaces this skill's default palette and fonts. An explanation drawn as an invented physical machine (an interactive isometric figure) belongs to `anatomy`; diagrams of the system itself stay here.
- Why: `diagram-design` and `visual-explainer` both claimed diagrams.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule back to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design), path `skills/diagram-design/`, commit `f2f4d49ea8d632f17cf196ba26599277a93f767b`, copied 2026-10-20. Unchanged, including the PNG/SVG exporters and all supporting assets. [MIT](../../THIRD_PARTY_LICENSES.md#cathrynlaverydiagram-design), © 2025 Cathryn Lavery. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
