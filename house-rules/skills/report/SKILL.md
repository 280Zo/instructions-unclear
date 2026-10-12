---
name: report
description: Produce a self-contained, glass-themed HTML report on any subject whatsoever — a data analysis, a conference talk, a policy review, a site visit, an incident, a set of interviews, a literature scan, a security assessment — with hand-authored inline SVG diagrams and charts, every claim anchored to its source, and an explicit statement of who the report is for. Use when the user runs /report, or asks to write up, document, summarise or produce a report on material that has already been gathered. Do NOT use this to build understanding of something unfamiliar or to answer "how does X work" — that is /eli5.
claudecode:
  allowed-tools: [Read, Grep, Glob, Bash, Write, WebSearch, WebFetch]
---

You are producing a **report** — a single self-contained HTML page that turns material already in hand into an evidence-backed deliverable someone else can read without you in the room.

**The subject is unconstrained.** It may be quantitative or entirely qualitative; technical or not remotely technical. A quarterly budget, a conference talk, a customer interview set, a building inspection, a research paper, a penetration test, a policy consultation. **Infer the subject and its domain from the conversation** — do not assume any particular field.

The only constant is that **some body of material is available to consume and parse.** Your job is to classify it, anchor every claim to it, and present it cleanly.

**Arguments:** `$ARGUMENTS` — optional free-text steer (a topic, a file or folder, "focus on the cost drivers", "for the board"). If empty, report on the most salient material in the current conversation.

**The distinction that matters:** a report organises what is *already known* for an audience. If the user instead needs to *understand something unfamiliar*, stop and use `/eli5`.

**Environment.** This skill is self-contained — everything it needs is in this file or beside it. Steps that use a shell (`mkdir`, `pwd`, `grep`, `node`) assume shell access. **If no shell is available in the current environment, substitute the equivalent:** read the finished file and inspect it directly instead of grepping, and write to the default working location instead of deriving a path from `pwd`. Never skip a check merely because its command is unavailable — perform it by reading.

---

## Step 1 — Intake and classify

Before writing anything, inventory what is actually available and classify it. Everything downstream keys off this.

1. **List the concrete material on hand:** documents read, datasets, transcripts, recordings, notes, images, prior conversation, referenced sources.
2. **Classify each source**, because the classification picks the citation anchor:

| Source type | Anchor every claim with |
|---|---|
| Document, report, book, paper | page + section |
| Talk, interview, meeting, recording | timestamp, or slide number |
| Dataset, spreadsheet, survey | column + filter + row count, or the query itself |
| Published or web source | full URL, plus date accessed |
| Observation, site visit, photo | what was observed, when, by whom |
| Personal account or testimony | who said it, and when |
| Prior conversation | the thing actually run or actually observed — never "as discussed" |

3. **Read the material.** Do not report on sources you have not opened. A report that paraphrases from memory is the failure mode this whole skill exists to prevent. If a cited source is reachable and you have not consulted it, either consult it or do not cite it.

### Conditional appendices — use only what applies

Two appendices at the end of this file carry domain-specific conventions. **For most reports you will use neither, and that is the normal case.**

| If the material involves… | Use |
|---|---|
| Software, infrastructure, a technical system | **Appendix A** |
| Security findings, vulnerability scans, pentest results, crawl data | **Appendix B** (plus A) |

Applying an appendix to an unrelated topic makes the report read as though it were written for a different audience. When in doubt, skip it.

### The evidence rule, which is absolute

Every substantive claim carries an anchor from the table above. **Numbers you cannot measure must be labelled illustrative** — inline, visibly, in the page. A chart built from invented numbers is worse than no chart.

**Separate observation from inference.** If you are extrapolating, say so in the text; never let an inference inherit the credibility of the measurement beside it.

Ask at most **one** clarifying question, and only when you genuinely cannot identify what material you are meant to consume. Otherwise proceed — do not stall.

## Step 2 — Fix the audience, then state it

Infer the audience and purpose from how the skill was invoked, the surrounding conversation, and `$ARGUMENTS`. **Do not interrogate the user about it.**

Then render the inference visibly in the page header, so a wrong guess is correctable in one reply:

```html
<div class="sub">Written for the programme committee · to support the spring funding decision</div>
```

Audience drives register, not rigour. A report for a board drops method detail into an appendix; a report for a practitioner keeps it inline. Neither drops the anchors.

## Step 3 — Choose the findings shape

The report's spine is fixed. Only the findings section varies. Pick **one** shape:

| Shape | Use when | Findings become |
|---|---|---|
| **Analytical** | the material is quantitative | measure → movement → driver |
| **Synthesis** | the material is a talk, a document set, interviews, reading | theme → supporting instances → tension between them |
| **Investigative** | there was a question to answer | question → answer → evidence chain |
| **Narrative** | the material is an event, incident or process | timeline → impact → response |

The fixed spine, in order:

1. **Bottom line** — one sentence, before anything else. Not a summary of the report; the actual conclusion.
2. **Written for / to support** — from Step 2.
3. **Provenance** — what was consumed, its limits, and **explicitly what was not examined**. This section is what makes the report trustworthy; do not skip it.
4. **Findings** — in the chosen shape, each with its anchor.
5. **Confidence and gaps** — what you would need to raise confidence.
6. **So what** — implications or recommendations, ranked, most consequential first.

---

## Step 4 — Build the page

Produce **one self-contained `.html` file**.

For reports specifically: **one strong diagram + 1–3 supporting charts + tight prose.** A wall of charts is a failure, not thoroughness. If a finding is qualitative, do not manufacture a chart for it — a well-set pull quote with its attribution is a legitimate visual, and better than a bar chart of three hand-waved numbers.

### Hard rules

- **No build step. No CDN. No runtime JS for visuals.** The page must render with zero external requests, so it works from `file://`, from any viewer, and under a strict CSP that blocks every external host. That means **no `<script src=…>`, no `<link>` to a CDN, no remote `<img>`, no `@import`, no `url(https://…)` in CSS.**
- **Author every diagram and chart as hand-written inline `<svg>` or CSS.** No Mermaid, Chart.js, D3, or ECharts. You draw the SVG directly. This is the whole point of the format: a frozen, static, portable page. *(Runtime JS is prohibited; pure-CSS hover states, tooltips and toggle drawers are allowed and encouraged.)*
- **Self-contained:** all CSS inline in a `<style>` block. Nothing fetched at runtime.

### SVG authoring

- Give each `<svg>` an explicit `viewBox` and `width="100%"` so it scales inside the glass card; add `role="img"` and a `<title>` child for hover and screen readers.
- **Relationships, processes, sequences, structures:** inline `<svg>` with `<rect>` nodes (rounded via `rx`), `<text>` labels, `<line>`/`<path>` edges, and a reusable arrowhead `<marker>` in `<defs>`.

```html
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
  </marker>
</defs>
<line x1="40" y1="30" x2="160" y2="30" stroke="currentColor" marker-end="url(#arrow)"/>
```

- **Draw the mechanism, not the vocabulary.** Five labelled boxes with no edges is a glossary, not a diagram. Show what moves, in what direction, in what order — whether that is a request, a payment, a shipment, a decision, or an argument.
- **Label the edges, not just the nodes.** What travels along an arrow is usually the thing the reader is missing.
- Number the steps when order matters — small circled digits on the edges beat a separate legend.
- **Theme without JS:** colour shapes, strokes and text with the CSS custom properties (`fill="var(--s1)"`, `stroke="var(--muted)"`, `fill="var(--txt)"`) or with `currentColor` driven by a class. The vars flip under `@media (prefers-color-scheme: dark)`, so the SVG recolours automatically. **Never bake a raw hex into SVG for anything theme-dependent.**

### Progressive disclosure without JS

When a diagram would be cluttered by every label at once, hide detail behind a pure-CSS toggle rather than dropping it. The checkbox hack works inside SVG via `<label>`:

```html
<input type="checkbox" id="detail-1" class="drawer-toggle" hidden>
<g class="node">
  <label for="detail-1">
    <rect x="60" y="40" width="120" height="44" rx="10" class="node"/>
    <text x="120" y="67" text-anchor="middle" class="node-label">Review board</text>
  </label>
</g>
```

```css
.drawer { display: none; }
#detail-1:checked ~ .drawer-1 { display: block; }
```

Highlight connected paths on hover with `:has()`, no script required:

```css
.diagram:has(.node-target:hover) .edge-target { stroke: var(--error); stroke-width: 3px; }
```

### Logos and vendor icons

Never fetch an icon CDN or a remote logo — it breaks the zero-external-request rule and the image will silently fail to load. Represent any named entity (a company, a department, a product, a service) as a labelled rounded `<rect>` with its name as `<text>`. A labelled box the reader can read beats a logo they have to squint at.

### Charts

Charts are read by people and executed by you. Follow this order — **colour comes last.**

**1. Pick the form by the job.** Sometimes the answer is not a chart:

| The data is… | Use | Not |
|---|---|---|
| A single current value | a stat tile (value + delta) | a one-bar bar chart |
| A handful of headline numbers | a KPI row of stat tiles | a grouped bar chart |
| A single ratio against a limit | a meter | a 2-slice pie |
| More than ~7 meaningful classes | a table, or table + chart | more colours |

| Job (what the reader must do) | Default form | Colour job |
|---|---|---|
| Compare magnitude | bar / column; heatmap for a grid | sequential (one hue) |
| Trend over time | line; area for a single series | sequential or 1 categorical |
| Tell distinct series apart | grouped/stacked bar, multi-line | categorical |
| One series is the point, rest are context | **emphasis** — highlight one, gray the rest | 1 hue + gray |
| Above/below a baseline; delta to target | diverging bar | diverging |
| Part-to-whole | **stacked bar** (horizontal for long names) | categorical |
| Ordered-scale share (agree↔disagree, sentiment) | diverging stacked bar, centred on neutral | diverging |
| Before → after per item | dumbbell | 1 hue, 2 shades |

**Emphasis is the most underused form.** If the story is "this one moved," that is emphasis — one series in `--s1`, the rest in `--muted` — not eight categorical hues.

**2. Pie and donut charts are a last resort.**

- **Deprioritise them.** A stacked bar or plain bar is almost always better for part-to-whole, and always better for comparing close values.
- **Hard cap: 5 segments.** Beyond five, fold the tail into "Other" or switch to a bar.
- **Never a 2-slice pie** — that is a stat tile. **Never a pie to compare close values** — the eye cannot rank similar angles.
- If you ship one, direct-label every slice with its value. A pie whose values live only in a legend is unreadable.

**3. Assign colour by the job it does.**

- **Series identity → the `--s1..--s5` slots, assigned in fixed order, never cycled.** A 6th series folds into "Other" or becomes small multiples. Never generate a new hue.
- **Magnitude → one hue, light to dark.** Never a rainbow.
- **Polarity → two opposed hues + a neutral gray midpoint.** Never a hue at the midpoint.
- **State → the status tokens** `--good` / `--amber` / `--error`, reserved and never used for "series 4." Status always ships with a text label, never colour alone.
- **Colour follows the entity, not its rank.** Never recolour by sort order — a reader who learned "the north region is blue" is misled when filtering repaints it.
- **Never colour nominal bars by their value.** One series → every bar takes `--s1`. Colouring darker-where-bigger burns the identity channel re-encoding what bar length already shows.

**4. Marks and chrome — this is what "clean and modern" means.**

- Thin marks, hairline grid and axes one shade off the surface, **solid never dashed**, generous padding. Thick saturated blocks with heavy gridlines read loud and childish.
- 4px rounded data-ends anchored to the baseline; 2px lines; ≥8px markers.
- A **2px surface-coloured gap** between adjacent fills and stacked segments — a gap, not a border drawn around each mark.
- **Never a number on every data point.** Direct-label selectively: the endpoint, the extreme, the one series that matters. Let the axis carry the rest.
- Text wears text tokens (`--txt`, `--txt2`, `--muted`), never the series colour. A coloured mark *beside* the text carries identity.
- A legend is present whenever there are ≥2 series; a single series needs none — the title names it.
- Never render a label inside a mark unless it fits with padding; otherwise move it outside the bar end.
- Size every chart container to include the x-axis label band, or let it grow with content. A fixed height that clips the axis produces a tiny nested scrollbar.

**5. Never a dual-axis chart.** Two y-scales on one plot invent a correlation that is not in the data. Two measures of different scale → two charts, small multiples, or both indexed to a common base.

**6. A distribution bar.** For part-to-whole at a glance. Note the 2px gaps and the counts stated in the header, so values never depend on colour alone:

```html
<div class="glass">
  <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-weight:600; font-size:13px;">
    <span>Budget by programme</span>
    <span>Facilities 45% · Staffing 35% · Outreach 20%</span>
  </div>
  <div style="display:flex; gap:2px; height:10px; border-radius:5px; overflow:hidden; background:var(--border);">
    <div style="flex:45; background:var(--s1);" title="Facilities — 45%"></div>
    <div style="flex:35; background:var(--s2);" title="Staffing — 35%"></div>
    <div style="flex:20; background:var(--s3);" title="Outreach — 20%"></div>
  </div>
</div>
```

**7. Validate any colour you change — never eyeball colourblind-safety.** The `--s1..--s5` values below already pass in both modes. Any substitution must be re-checked with the bundled validator (Node, no dependencies), which sits in this skill's own directory:

```bash
node scripts/validate_palette.js "#2563eb,#b45309,#059669,#7c3aed,#dc2626" --mode light --surface "#f1f5f9"
node scripts/validate_palette.js "#3b82f6,#d97706,#059669,#8b5cf6,#ef4444" --mode dark  --surface "#0f1117"
```

It reports lightness band, chroma floor, CVD separation under simulated protanopia/deuteranopia, a normal-vision floor, and contrast against the surface. Exit 0 means no hard failure. Two things it catches that intuition will not:

- **Darkening a warm hue can collapse it into an adjacent one.** Amber against red measured ΔE 2.8 under deuteranopia — indistinguishable — while looking fine to full-colour vision.
- **Slot order is itself the safety mechanism.** When a pair collapses, the fix is usually to re-order the slots rather than re-pick a hue.

Pass `--pairs all` for scatter, bubble or small-multiple charts, where any two marks can end up side by side. Do not run it on a sequential ramp — it validates categorical palettes and will fail a good ramp by design. **If Node is unavailable, do not substitute judgement — keep the documented values unchanged.**

### Theme — glass tokens

Use this block verbatim inside `<style>`.

> **Two colour roles, kept separate.** `--good`/`--amber`/`--error`/`--purple` are **status** tokens: reserved semantic meaning (state), always paired with a text label. `--s1..--s5` are **series** slots for chart identity, assigned in fixed order. Never use a status token as a series colour, or a series slot for state. The series slots carry different values per mode because each was validated against that surface — light and dark are *selected*, not an automatic flip.

```html
<style>
:root {
  --bg: #f1f5f9; --card: rgba(255,255,255,.55); --glass: rgba(255,255,255,.75);
  --border: rgba(0,0,0,.08); --specular: rgba(255,255,255,.9);
  --txt: #1e293b; --txt2: #475569; --muted: #94a3b8;
  /* status — reserved meaning, always shipped with a text label */
  --accent: #3b82f6; --good: #10b981; --amber: #f59e0b; --error: #ef4444; --purple: #a78bfa;
  /* series slots — validated for the light surface; assign in order, never cycle */
  --s1: #2563eb; --s2: #b45309; --s3: #059669; --s4: #7c3aed; --s5: #dc2626;
  --blur: 24px; --radius: 22px;
  --font: "Satoshi", system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0f1117; --card: rgba(30,30,42,.5); --glass: rgba(30,30,40,.75);
    --border: rgba(255,255,255,.08); --specular: rgba(255,255,255,.06);
    --txt: #e2e8f0; --txt2: #94a3b8; --muted: #64748b;
    /* series slots re-stepped for the dark surface — not the same values */
    --s1: #3b82f6; --s2: #d97706; --s3: #059669; --s4: #8b5cf6; --s5: #ef4444;
  }
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.6 var(--font);padding-bottom:64px}
header{padding:32px 40px;border-bottom:1px solid var(--border);
background:linear-gradient(135deg,rgba(59,130,246,.10),rgba(167,139,250,.06))}
h1{margin:0 0 6px;font-size:26px;letter-spacing:-.01em}
header .sub{color:var(--muted);font-size:14px}
main{max-width:1080px;margin:0 auto;padding:0 24px}
h2{margin:44px 0 12px;font-size:20px;border-bottom:1px solid var(--border);padding-bottom:8px}
h3{margin:24px 0 8px;font-size:15px;color:var(--accent)}
code{font-family:var(--mono);font-size:.85em;background:color-mix(in srgb,var(--txt) 8%,transparent);
padding:1px 5px;border-radius:5px}
/* the glass surface — wrap diagrams, charts and callouts in this */
.glass{background:var(--card);backdrop-filter:blur(var(--blur)) saturate(1.4);
-webkit-backdrop-filter:blur(var(--blur)) saturate(1.4);
border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;margin:16px 0;
box-shadow:inset 0 1px 0 0 var(--specular),0 4px 24px rgba(0,0,0,.06)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12.5px;color:var(--muted);margin:8px 0}
.note{font-size:12px;color:var(--muted);font-style:italic;margin-top:8px}
/* the evidence anchor that follows every claim */
.cite{font-family:var(--mono);font-size:11.5px;color:var(--muted)}
/* a caveat callout */
.gotcha{border-left:3px solid var(--amber);padding-left:14px;margin:14px 0}
footer{max-width:1080px;margin:40px auto 0;padding:16px 24px;color:var(--muted);
font-size:12px;border-top:1px solid var(--border)}
/* SVG helpers — class shapes so they inherit themed colours */
svg{max-width:100%;height:auto}
.node{fill:var(--card);stroke:var(--accent);stroke-width:1.5;transition:all .2s ease}
.node:hover{stroke-width:2.5px;filter:drop-shadow(0 0 6px var(--accent))}
.node-label{fill:var(--txt);font:600 12px var(--font)}
.edge{stroke:var(--muted);stroke-width:1.5;fill:none}
.edge-label{fill:var(--txt2);font:11px var(--mono)}
.axis{stroke:var(--border)}
.tick{fill:var(--muted);font:11px var(--font)}
.bar{fill:var(--s1)}
</style>
```

---

## Step 5 — Write the file

1. Give the page a concise `<title>` in its `<head>`.
2. Resolve an absolute path and make the directory, via shell from the working root:
   `mkdir -p Clanker_Crayon_Box/reports` — then build a kebab-slug from the topic.
3. Write to `<absolute-cwd>/Clanker_Crayon_Box/reports/<slug>.html`. You **must** know the absolute path — get it with `pwd` and prefix the slug with it. Without a shell, write to `Clanker_Crayon_Box/reports/<slug>.html` relative to the working directory and report the path you used.

## Step 6 — Self-review before surfacing

Do this yourself, in this skill. Do not delegate it to a subagent — the checks need the source material already in your context, and a handoff loses it.

**First, the mechanical check.** Run it; do not reason about it:

```bash
grep -nE '<script[^>]+src=|<link[^>]+href="https?:|<img[^>]+src="https?:|@import|url\(https?:' <path>
```

Any hit violates the zero-external-request rule — fix it. Then confirm the file exists at the exact path you are about to report. **Without a shell, read the file and scan for the same five patterns by eye.**

**Then re-read the rendered page against the source material** and verify:

- **Data accuracy.** Every number in every chart, every bar width, every count, every SVG coordinate traces back to a source. **Recompute the totals** — a stacked bar whose segments do not sum to its stated total is the most common failure.
- **Anchors.** Every substantive claim has one. Observation is distinguishable from inference. Everything unmeasurable is visibly labelled illustrative.
- **Colour.** Series use `--s1..--s5` in order and are never cycled; status tokens are used only for state and always carry a text label; nothing theme-dependent is a raw hex.
- **Charts read cleanly.** No dual axis. No pie over 5 segments, no 2-slice pie, no pie comparing close values. No number on every data point. No dashed gridlines. No label clipped by its bar.
- **Both themes.** Mentally toggle `prefers-color-scheme` — every colour must come from a var that flips, and text must stay legible on both surfaces.
- **Structure.** The Step 3 spine is intact: bottom line, audience, provenance including what was *not* examined, findings, confidence and gaps, so-what.
- **Domain fit.** No convention from an appendix you did not need. A general report should carry no trace of a specialism it does not have.
- **Markup.** SVG tags closed, `viewBox` present on every `<svg>`, every `var(--x)` referenced is defined.

Fix anything that fails, then re-run the mechanical check. Only then surface it.

## Step 7 — Surface it

Report the path in one line and stop. **Do not inline the HTML. Do not describe the page in prose — the page is the deliverable.** A one-line acknowledgement is enough.

The page makes zero external requests, so it can be published as a shareable Claude Artifact if the user later asks. Do not offer it unprompted, and never regenerate the HTML to publish it — publish the file as written.

---
---

# Appendix A — Software and systems

**Use only when the subject is software, infrastructure, or a technical system.** Skip entirely otherwise. Applying this to a non-technical topic is what makes a general-purpose page read as though it were written for a different audience.

### Evidence anchors

| Source | Anchor every claim with |
|---|---|
| Source file | `path/to/file.ts:42` |
| Commit / PR | short SHA, or `#1234` |
| Log / trace | timestamp + the matched line |
| Query / dataset | the query itself, plus row count |
| Scan or tool output | tool name + version + the raw finding ID |
| Config | file + key path (`values.yaml → ingress.tls`) |
| Dependency | package name + exact version |

### Go to the source

**If the code is available to you, read it.** Source outranks any document written about it, including its own documentation — docs drift, code does not. Prefer, in order: the source, the spec/RFC, official docs, maintainer design docs and changelogs, then everything else.

Two failure modes specific to this domain:

- **Version drift.** Behaviour changes across releases. Name the version you are describing, and check whether your source predates a change that matters.
- **Aspirational documentation.** A README describes intent; the code describes behaviour. Where they disagree, the code wins and the disagreement is worth stating.

### Architecture diagrams

Never fetch a vendor icon CDN (AWS, Azure, GCP, or any other). Represent each service as a labelled rounded `<rect>` with the service name as `<text>`; tint with `--s1..--s5` if grouping helps.

Label the edges with what actually travels: the protocol, the payload, the trigger. A diagram of named services with unlabelled arrows tells the reader nothing they could not get from a list.

### Charts that recur here

- **Latency or duration distributions** — a histogram, never a mean alone. State the percentile you are quoting.
- **Throughput or error rate over time** — a line, with the incident window marked as a shaded band rather than a dashed vertical rule.
- **Resource breakdown** — a horizontal stacked bar; service names are long and wrap badly on vertical bars.
- **Version or dependency spread** — a bar, ordered by count, tail folded into "Other."

All of these are one series unless you are genuinely comparing named entities — so every bar takes `--s1`.

---

# Appendix B — Security findings

**Use only when the material contains security findings, vulnerability scans, pentest results, crawl topologies or network scans.** Skip entirely otherwise. Assumes Appendix A also applies.

### Findings severity

Group and badge findings using the **status** palette. Severity is *state*, not series identity, so it always carries its text label — never colour alone:

- `Critical` / `High` → `--error`
- `Medium` → `--amber`
- `Low` / `Informational` → `--good` or `--accent`

```html
<div class="glass" style="margin-bottom:24px;">
  <div style="display:flex; justify-content:space-between; margin-bottom:8px; font-weight:600; font-size:13px;">
    <span>Finding severity distribution</span>
    <span>2 Critical · 5 Medium · 12 Low</span>
  </div>
  <div style="display:flex; gap:2px; height:10px; border-radius:5px; overflow:hidden; background:var(--border);">
    <div style="flex:2;  background:var(--error);" title="Critical/High — 2"></div>
    <div style="flex:5;  background:var(--amber);" title="Medium — 5"></div>
    <div style="flex:12; background:var(--good);"  title="Low/Info — 12"></div>
  </div>
</div>
```

Group findings in distinct glass cards with a colour-coded badge beside each title:

```html
<span style="background:color-mix(in srgb, var(--error) 15%, transparent); color:var(--error);
border:1px solid var(--error); padding:2px 8px; border-radius:12px; font-size:11px;
font-weight:700;">CRITICAL</span>
```

Each finding needs, at minimum: what was observed, where (its anchor), why it matters, and what would fix it. **A severity badge without a reproduction path is an assertion, not a finding.**

### Crawl topology maps

Render with **pre-calculated inline SVG + CSS state hacks**. Do not attempt a JS layout engine (D3/Vis.js).

- **Pre-computed coordinates:** fixed (x,y) positions derived from crawl depth — root at top/left, discovered endpoints branching outward.
- **Status colour coding** on node `stroke`, with a visible label on each node: `--good` (200 OK), `--amber` (3xx redirect), `--error` (4xx/5xx), `--purple` (auth required).

Attack-path highlighting on hover, no script:

```css
.topology-container:has(.node-target:hover) .edge-target {
  stroke: var(--error);
  stroke-width: 3px;
}
```

Click-to-inspect drawer for endpoint detail (headers, params, findings) via the checkbox hack:

```html
<input type="checkbox" id="inspect-node-1" class="drawer-toggle" hidden>
<g class="node">
  <label for="inspect-node-1">
    <circle cx="100" cy="100" r="18" class="node" />
    <text x="100" y="104" text-anchor="middle" class="node-label">/admin</text>
  </label>
</g>
```

```css
.drawer { display: none; }
#inspect-node-1:checked ~ .drawer-node-1 { display: block; }
```

### Crawl analytics

Pair the topology map with 1–2 supporting charts.

**HTTP status breakdown** — a distribution bar (Step 4, chart rule 6), using status tokens rather than series slots, with counts in the header so nothing depends on colour alone.

**Depth histogram** — an inline SVG bar chart of endpoints discovered per crawl depth (D0, D1, D2, …) with `<rect>` bars and `<text>` ticks. This is one series: every bar takes `--s1`.

### OWASP mapping

Annotate each finding with its OWASP classification, rendered as inline `<code>` badges formatted `[Framework] Code: Category Name`.

**Web application — OWASP Top 10 (2021):**

- `A01: Broken Access Control` | `A02: Cryptographic Failures` | `A03: Injection`
- `A04: Insecure Design` | `A05: Security Misconfiguration` | `A06: Vulnerable and Outdated Components`
- `A07: Identification and Authentication Failures` | `A08: Software and Data Integrity Failures`
- `A09: Security Logging and Monitoring Failures` | `A10: Server-Side Request Forgery (SSRF)`

**LLM applications — OWASP Top 10 for LLMs (2025):**

- `LLM01: Prompt Injection` | `LLM02: Sensitive Information Disclosure`
- `LLM03: Supply Chain Vulnerabilities` | `LLM04: Data and Model Poisoning`
- `LLM05: Improper Output Handling` | `LLM06: Excessive Agency`
- `LLM07: System Prompt Leakage` | `LLM08: Vector and Embedding Weaknesses`
- `LLM09: Misinformation` | `LLM10: Unbounded Consumption`

```html
<div style="display:flex; gap:8px; align-items:center; margin-top:6px;">
  <code>OWASP A03:2021 — Injection</code>
  <code>OWASP LLM01:2025 — Prompt Injection</code>
</div>
```

**Only tag a finding when the mapping is genuine.** A wrong OWASP tag is worse than no tag — it launders a guess as a standard. If a finding does not map cleanly, leave it untagged and say why.
