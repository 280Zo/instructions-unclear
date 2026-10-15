# diagram-design

A skill for clean, editorial diagrams: 39 types, from architecture and flowcharts to sequence diagrams, timelines, Sankey charts and database schemas. Each is a static HTML and SVG file with no JavaScript and nothing loaded from the internet, in a light, dark or full-editorial style.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/diagram-design
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/diagram-design` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Draw an architecture diagram of this repo"
- "Make a sequence diagram of the login flow", "a timeline of the project milestones"
- "Match the style of https://example.com" (it reads the site to pick colours and fonts)
- "Redraw this Mermaid diagram properly" (it converts draw.io and Mermaid sources)

The communication rule sends diagram requests here, and `report` uses it for the diagrams in reports. Browse every type in [upstream's gallery](https://cathrynlavery.github.io/diagram-design/), or open `skills/diagram-design/assets/index.html` locally.

## Origin

[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design), path `skills/diagram-design/`, commit `11b08eade8049c441ed3df1895e3b527c26c0fbe`, copied 2026-10-13. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#cathrynlaverydiagram-design), © 2025 Cathryn Lavery. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
