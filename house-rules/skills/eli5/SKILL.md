---
name: eli5
description: >-
  Teach ONE unfamiliar thing end to end in plain English. Asks the user first whether they want a guided back-and-forth conversation that actually teaches them, or a self-contained glass-themed HTML explainer page — one hand-authored SVG diagram plus tight prose, capped at a single page. Works on any subject: a scientific concept, a historical event, a legal or financial mechanism, an organisation, a piece of jargon, a process, a protocol, a paper, a system. Use when the user runs /eli5, says ELI5 or "explain like I'm five", or asks how something works, what something is, why something exists, to understand something, to be taught something, or to be walked through something. Do NOT use this to write up findings or material already gathered for an audience — that is /report.
claudecode:
  allowed-tools: [Read, Grep, Glob, Bash, Write, WebSearch, WebFetch, AskUserQuestion]
---

Your job is to make one unfamiliar thing genuinely click for one reader, fast, in plain English.

**There are two ways to deliver that, and you ask which one before you start** (Step 2):

- **Mode A — an explainer page.** A single self-contained HTML page: one diagram, the mental model, the traps. Something they keep and re-read.
- **Mode B — teach me.** No file. A guided back-and-forth that starts where they already are and checks they can use each idea before moving on.

Same research bar, same plain-English discipline, completely different deliverable. Everything up to Step 4 is shared; then the tracks split.

**The subject is unconstrained.** A tax mechanism, a chemical process, a treaty, an art movement, a supply chain, a medical procedure, a network protocol. **Infer the subject and its domain from the conversation** — assume no particular field.

**The distinction that matters:** this skill *acquires* understanding the reader does not yet have. A report *organises* material already in hand for an audience. If the user already has the answer and needs it shaped for someone else, stop and use `/report`.

**Arguments:** `$ARGUMENTS` — the thing to explain, optionally with a steer ("focus on how the money moves", "I already know the basic chemistry"). If empty, explain the most salient unfamiliar thing in the current context.

**Environment.** This skill is self-contained — everything it needs is in this file or beside it. Steps that use a shell (`mkdir`, `pwd`, `grep`, `node`) assume shell access. **If no shell is available in the current environment, substitute the equivalent:** read the finished file and inspect it directly instead of grepping, and write to the default working location instead of deriving a path from `pwd`. Never skip a check merely because its command is unavailable — perform it by reading.

---

## Step 1 — Pick exactly one subject

**One subject.** Not a subject and its three neighbours. If the material sprawls, pick the load-bearing piece — the thing that, once understood, makes the rest inferable. Breadth is what makes explainers useless.

**Infer the reader's baseline** from the conversation and `$ARGUMENTS` — do not interview them. What do they already know well? That determines *where you start* and what you may treat as given.

Baseline and ELI5 are not in tension, and confusing them is the most common way this skill goes wrong. **Baseline decides where you start. ELI5 decides how you say everything after that.** You never dumb down the mechanism; you always plain-language the delivery.

If the subject is genuinely ambiguous, ask **one** question. Otherwise proceed.

## Step 2 — Ask which mode, before doing anything else

This skill can deliver in two very different ways, and **you must ask which one before you start researching.** Researching first and asking later wastes a full research pass if they wanted to be taught rather than handed a document.

Ask with `AskUserQuestion` if it is available. If it is not, ask in plain text and **stop for an answer** — do not pick for them.

> **Do you want a page, or do you want to learn it?**
>
> - **Explainer page** — I research it and hand you a single self-contained HTML page: one diagram, the mental model, the traps. Good for a concept you want captured, skimmable and re-readable later.
> - **Teach me** — no file. We work through it together in conversation: I start where you already are, one idea at a time, and check you can use it before moving on. Slower, and you actually retain it.

**Skip the question and go straight to a mode when the user has already chosen**, explicitly or by phrasing:

| Straight to **page** | Straight to **teach me** |
|---|---|
| "make me a page/explainer/writeup on X" | "teach me X", "walk me through X" |
| "I need something to send someone" | "help me understand X", "I want to learn X" |
| "document X for me" | "quiz me on X", "I keep not getting X" |
| they asked to re-generate an existing explainer | they are mid-conversation asking follow-ups |

When it is genuinely ambiguous — a bare `/eli5 <topic>`, or "what is X" — **ask.** Do not guess. The two outputs are different enough that guessing wrong wastes the whole turn.

Once the mode is known:

- **Teach me** → do Step 3 (research), Step 4 (voice), then go to **Mode B**. Ignore Steps 5–9 entirely; you are not writing a file.
- **Explainer page** → do Steps 3 and 4, then Steps 5–9 as written.

## Step 3 — Research it properly

This is research, not browsing. **The bar is that you could teach the topic end to end afterwards** — not that you found a page that mentions it.

### The procedure

1. **Map before you read.** Write down the 5–8 things a reader must know to actually understand this. That list is your coverage checklist and your stop condition. Without it you will read until you feel finished, which is not the same as being finished.

2. **Work the source ladder, top down.** The tiers hold in every field; only the instances change.

   | Tier | What it is | Looks like |
   |---|---|---|
   | **Primary** | the thing itself, or its authoritative record | the source code; the spec or RFC; the paper; the statute or ruling; the original document or archive; the raw dataset; the artifact; the filing |
   | **Practitioner** | people who built or operate it | design notes, changelogs, minutes, correspondence, practitioner interviews, institutional records |
   | **Reputable secondary** | expert explanation | textbooks, review articles, standards commentary, conference talks, well-regarded journalism |
   | **Everything else** | leads to chase — never a citation | SEO articles, content farms, forum answers, encyclopedia summaries |

   **If the primary source is directly available to you, go to it.** A document *about* the thing never outranks the thing.

3. **Cross-check every load-bearing claim against at least two independent sources.** Two articles derived from the same upstream are one source, not two. Where good sources genuinely disagree, say so — in the page, or out loud in conversation. A visible disagreement is more useful than a false consensus.

4. **Search iteratively, driven by gaps.** Each query should close a specific unchecked item on your list, not follow curiosity sideways. After each pass ask: *which checklist item is still uncovered, and what query would close it?* Then run that. Stop chasing anything that has drifted off the one subject.

5. **Check currency.** Note dates, versions, editions. Things change — software releases, revised standards, superseded findings, amended law, restructured organisations. A confident source that predates a change is a confident wrong answer. Name the version, year or edition you are describing.

6. **Stop when all three hold**, not before:
   - every item on your checklist is covered,
   - you can narrate the whole thing end to end without hedging,
   - you know where the topic's boundaries are — what it does *not* cover, and what it is commonly confused with.

7. **Research wide, write narrow.** Most of what you learn will not appear on the page. That is correct, and it is exactly what makes the page confident instead of tentative. The cap in Step 5 applies to the output, never to the research.

**If the subject is software, infrastructure or a technical system, see Appendix A** at the end of this file. For most subjects you will not need it, and that is the normal case — applying it to an unrelated topic makes the page read as though it were written for a different audience.

### Honesty rules

- An explainer that is confidently wrong is worse than none, because the reader has no way to detect it.
- **Numbers you cannot measure must be labelled illustrative**, inline and visibly.
- Where you remain uncertain after research, say so — in the page in Mode A, out loud in Mode B. A hedge the reader can see is a feature; a hedge you silently smoothed over is a defect.
- Link the primary source for anything a reader might reasonably want to verify.

## Step 4 — Write it ELI5

**These rules apply in both modes.** They govern how you say things, so they hold whether you are writing a page or talking to someone.

ELI5 means **removing unnecessary difficulty, not pretending the subject is simple.** You are stripping jargon, formalism and inherited vocabulary — never the actual mechanism. A reader should finish knowing how the thing really works, having never had to decode a sentence.

The working standard is not a literal five-year-old. It is **a sharp person from an adjacent field**: capable, curious, and entitled to not already know your vocabulary.

**Do:**

- **Define every term of art at first use, in-line, in plain words — or cut it.** If a sentence needs three defined terms to parse, rewrite the sentence.
- **Lead the mental model with a concrete analogy** to something physical and everyday, then **immediately state where the analogy breaks.** An unbounded analogy builds a confident wrong model, which is worse than no analogy at all.
- **Be concrete.** Real names, real numbers, real quotes, real dates — not "a party", "a value", "some amount".
- **One idea per sentence.** Short sentences. This is the single highest-leverage edit.
- **Name the thing people get wrong** and say why the wrong model is tempting. Understanding is often built by correcting a misconception, not by adding a fact.

**Do not:**

- **Never write "simply", "just", "obviously", "trivially", "of course".** These words do no work and make a stuck reader feel stupid. Delete them on sight.
- Do not hide difficulty behind a smooth sentence. If a step is genuinely hard, say it is hard, then explain it anyway.
- Do not use a formal definition where a worked example does the job.
- Do not preserve a term only because the field uses it. If the standard name is opaque, explain the concept first and attach the name afterward.

---

# Mode B — Teach me (no file)

**Take this track only when the user chose "teach me" in Step 2.** When you finish here, you are done — do not continue to Step 5, and do not write a file.

**The conversation is the deliverable.** The failure mode of this mode is producing Mode A's six sections as a wall of chat text. That is a report you pasted into the conversation, not teaching. If your reply is longer than a couple of short paragraphs, you are doing it wrong.

### The loop

1. **Open with the one-sentence answer, then stop.** Give them the anchor before anything else, so everything that follows has somewhere to attach.
2. **Find out what they already know — one concrete question.** "Have you run into X before?" beats "what's your background?" A concrete question gets a usable answer; an abstract one gets a shrug.
3. **Teach one idea, then hand the turn back.** Roughly 150 words, maximum. The pause is not politeness — it is what makes this different from a document.
4. **Check by asking them to *use* it, not recall it.** "Given that, what do you think happens if…?" beats "does that make sense?" — the second question always gets "yes," including from people who are lost.
5. **Follow their questions over your outline.** Where they are confused is better information about what to teach next than your plan is. Your Step 3 checklist is a safety net for coverage, not a script.
6. **Correct misconceptions immediately, and kindly.** Say what is actually true, why the wrong model was a reasonable thing to think, and what it would break. Never let a wrong model stand because correcting it would interrupt the flow.
7. **Finish when they can explain it back** — not when you have covered your list. Ask them to put it in their own words, then fix what is off. That final round is where it sticks.

### Still true in this mode

- Every rule in Step 4 applies. The voice does not relax because it is conversation.
- The Step 3 research bar applies. Keep researching between turns when a question takes you past what you actually verified — and say so rather than improvising: *"let me check that properly"* is always better than a confident guess.
- The honesty rules apply. Uncertainty gets stated out loud.
- You may sketch small diagrams in plain text or ASCII when a shape helps. Do not build HTML.

### The bridge

When they can explain it back, offer once, in one line: *"want this as a page you can keep? I can generate one."* If they say yes, run Steps 5–9 — you already have the research, so it is cheap. If they say no, stop. Do not offer twice.

---

## Step 5 — The structure, and the cap

**Steps 5–9 are Mode A only** — the explainer page. If the user chose "teach me," you should be in Mode B above and finished.


Six sections, in this order. This is the whole page:

1. **What it is** — one sentence, in plain English. Not a paragraph. If you cannot do it in one sentence you do not yet understand it well enough to explain it.
2. **Why it exists** — what problem it solves, and what people did before it. Motivation is what makes a mechanism memorable.
3. **The mental model** — the analogy, and **the one diagram that makes it click.** This is the centre of the page and the reason it is HTML rather than prose. Everything else is support.
4. **A minimal concrete example** — the smallest real instance the reader could actually follow, run or point at. Real specifics, not a sketch.
5. **The three things that trip people up** — the misconceptions, the traps, the surprising default. Usually the highest-value section on the page.
6. **Where to go deeper** — 2–3 pointers, ranked, each with one line on what it is good for. Prefer primary sources.

### The cap is the product

- **One page**, readable in a single sitting without scroll fatigue.
- **~600 words of prose, maximum.**
- **One primary diagram, plus at most two supporting visuals.**

The cap is not a style preference — it is what makes this different from documentation. When you are over, **cut scope rather than shrinking sections**: explain less, not more thinly.

### Anti-goals — what this is not

- **Not a tutorial.** No numbered setup steps. You are building a model, not walking a path.
- **Not a reference manual.** Never enumerate an exhaustive surface — every parameter, every clause, every date, every exception. One representative example beats a complete table.
- **Not a report.** No findings, no evidence sections, no recommendations, no audience line.
- **Not a history lecture.** "Why it exists" is one short paragraph, not a lineage.
- **Not a literature review.** You did deep research; the page shows its conclusions, not its bibliography.

---

## Step 6 — Build the page

Produce **one self-contained `.html` file**.

### Hard rules

- **No build step. No CDN. No runtime JS for visuals.** The page must render with zero external requests, so it works from `file://`, from any viewer, and under a strict CSP that blocks every external host. That means **no `<script src=…>`, no `<link>` to a CDN, no remote `<img>`, no `@import`, no `url(https://…)` in CSS.**
- **Author every diagram as hand-written inline `<svg>` or CSS.** No Mermaid, Chart.js, D3, or ECharts. You draw the SVG directly. *(Runtime JS is prohibited; pure-CSS hover states, tooltips and toggle drawers are allowed and encouraged.)*
- **Self-contained:** all CSS inline in a `<style>` block. Nothing fetched at runtime.

### The primary diagram

This is the page. Spend your effort here.

- **Draw the mechanism, not the vocabulary.** Five labelled boxes with no edges is a glossary, not a diagram. Show what moves, in what direction, in what order — whether that is a request, a payment, a shipment, a decision, or an argument.
- **Label the edges, not just the nodes.** What travels along an arrow is usually the thing the reader is missing.
- Number the steps when order matters — small circled digits on the edges beat a separate legend.
- Give each `<svg>` an explicit `viewBox` and `width="100%"` so it scales inside the glass card; add `role="img"` and a `<title>` child.

```html
<defs>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
          markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
  </marker>
</defs>
<line x1="40" y1="30" x2="160" y2="30" stroke="currentColor" marker-end="url(#arrow)"/>
```

**Theme without JS:** colour shapes, strokes and text with the CSS custom properties (`fill="var(--s1)"`, `stroke="var(--muted)"`, `fill="var(--txt)"`) or with `currentColor` driven by a class. The vars flip under `@media (prefers-color-scheme: dark)`, so the SVG recolours automatically. **Never bake a raw hex into SVG for anything theme-dependent.**

### Logos and vendor icons

Never fetch an icon CDN or a remote logo — it breaks the zero-external-request rule and the image will silently fail to load. Represent any named entity (a company, a department, a product, a service) as a labelled rounded `<rect>` with its name as `<text>`. A labelled box the reader can read beats a logo they have to squint at.

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

Use these to keep the primary diagram uncluttered — not to smuggle a second page of content past the cap.

### If you include a chart

An explainer rarely needs one — a chart earns its place only when a *shape* (growth, distribution, a tradeoff) is itself the insight. An explainer is not a dashboard. If you do include one:

- **Pick the form by the job.** Magnitude → bar. Trend over time → line. Part-to-whole → stacked bar. Above/below a baseline → diverging bar. One series is the point → **emphasis**: highlight it in `--s1`, gray the rest in `--muted`.
- **A single number is a stat tile, not a one-bar chart.** More than ~7 meaningful classes is a table, not more colours.
- **Pie and donut charts are a last resort.** Deprioritise them; prefer a bar or stacked bar. **Hard cap 5 segments**, never 2 slices, never to compare close values, and every slice direct-labelled with its value.
- **Series identity uses `--s1..--s5` in fixed order, never cycled.** A 6th series folds into "Other." Status tokens (`--good`/`--amber`/`--error`) mean state only and always carry a text label. Never colour nominal bars by their value — one series, every bar takes `--s1`.
- **Never a dual-axis chart.** Two y-scales invent a correlation that is not in the data.
- Thin marks, hairline grid one shade off the surface, **solid never dashed**, generous padding, a 2px surface-coloured gap between adjacent fills. Never a number on every data point — label the endpoint or the extreme and let the axis carry the rest. A legend whenever there are ≥2 series.
- Text wears text tokens (`--txt`, `--txt2`, `--muted`), never the series colour.
- Size the container to include the x-axis label band, or let it grow with content.

**Validate any colour you change — never eyeball colourblind-safety.** The values below already pass in both modes. Any substitution must be re-checked with the bundled validator (Node, no dependencies), which sits in this skill's own directory:

```bash
node scripts/validate_palette.js "#2563eb,#b45309,#059669,#7c3aed,#dc2626" --mode light --surface "#f1f5f9"
node scripts/validate_palette.js "#3b82f6,#d97706,#059669,#8b5cf6,#ef4444" --mode dark  --surface "#0f1117"
```

Two things it catches that intuition will not: **darkening a warm hue can collapse it into an adjacent one** (amber against red measured ΔE 2.8 under deuteranopia — indistinguishable, while looking fine to full-colour vision), and **slot order is itself the safety mechanism**, so when a pair collapses the fix is usually to re-order rather than re-pick. **If Node is unavailable, do not substitute judgement — keep the documented values unchanged.**

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
/* the glass surface — wrap diagrams, examples and callouts in this */
.glass{background:var(--card);backdrop-filter:blur(var(--blur)) saturate(1.4);
-webkit-backdrop-filter:blur(var(--blur)) saturate(1.4);
border:1px solid var(--border);border-radius:var(--radius);padding:18px 20px;margin:16px 0;
box-shadow:inset 0 1px 0 0 var(--specular),0 4px 24px rgba(0,0,0,.06)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid2{grid-template-columns:1fr}}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12.5px;color:var(--muted);margin:8px 0}
.note{font-size:12px;color:var(--muted);font-style:italic;margin-top:8px}
/* the one-sentence answer, set larger than body text */
.lede{font-size:18px;line-height:1.5;color:var(--txt)}
/* the analogy, and the line where it breaks */
.analogy{border-left:3px solid var(--accent);padding-left:14px;margin:14px 0}
.analogy .breaks{color:var(--txt2);font-size:13.5px;margin-top:6px}
/* one of the three things that trip people up */
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

Use `.lede` for the one-sentence answer, `.analogy` with its `.breaks` line for the mental model, and `.gotcha` for each trap.

---

## Step 7 — Write the file

1. Give the page a concise `<title>` in its `<head>`.
2. Resolve an absolute path and make the directory, via shell from the working root:
   `mkdir -p Clanker_Crayon_Box/eli5` — then build a kebab-slug from the subject.
3. Write to `<absolute-cwd>/Clanker_Crayon_Box/eli5/<slug>.html`. You **must** know the absolute path — get it with `pwd` and prefix the slug with it. Without a shell, write to `Clanker_Crayon_Box/eli5/<slug>.html` relative to the working directory and report the path you used.

Re-explaining the same subject overwrites the same slug. Explainers are current understanding, not a log.

## Step 8 — Self-review before surfacing

Do this yourself, in this skill. Do not delegate it to a subagent — the checks need the research already in your context.

**First, the mechanical check.** Run it; do not reason about it:

```bash
grep -nE '<script[^>]+src=|<link[^>]+href="https?:|<img[^>]+src="https?:|@import|url\(https?:' <path>
```

Any hit violates the zero-external-request rule — fix it. Then confirm the file exists at the exact path you are about to report. **Without a shell, read the file and scan for the same five patterns by eye.**

**Then re-read the page against your research** and verify:

- **Accuracy.** Every claim traces to something you actually read. Nothing is asserted from memory. Load-bearing claims were cross-checked. Anything unmeasurable is visibly labelled illustrative, and residual uncertainty is stated rather than smoothed over.
- **Coverage.** Every item on your Step 3 checklist is either on the page or deliberately out of scope. Read the page as someone who knew nothing: could they now explain this to a third person?
- **ELI5 discipline.** No undefined jargon. No "simply", "just", "obviously", "trivially". The analogy is present **and** its breaking point is stated. Sentences carry one idea each.
- **The cap held.** One subject. Under ~600 words of prose. One primary diagram, ≤2 supporting visuals. If over, cut scope.
- **The diagram shows a mechanism.** Edges labelled with what travels along them. Not a box glossary.
- **All six sections present**, and "what it is" is genuinely one sentence.
- **No anti-goal leaked in** — no setup steps, no exhaustive table, no findings, no bibliography.
- **Domain fit.** No convention from Appendix A if the subject was not technical.
- **Colour.** Series use `--s1..--s5` in order; status tokens carry text labels; nothing theme-dependent is a raw hex.
- **Both themes.** Mentally toggle `prefers-color-scheme` — every colour comes from a var that flips, and text stays legible on both surfaces.
- **Markup.** SVG tags closed, `viewBox` on every `<svg>`, every `var(--x)` referenced is defined.

Fix anything that fails, then re-run the mechanical check.

## Step 9 — Surface it

Report the path in one line and stop. **Do not inline the HTML. Do not re-explain the subject in prose — the page is the deliverable.**

The page makes zero external requests, so it can be published as a shareable Claude Artifact if the user later asks. Do not offer it unprompted.

---
---

# Appendix A — Software and systems

**Use only when the subject is software, infrastructure, or a technical system.** Skip entirely otherwise. Applying this to a non-technical topic is what makes a general-purpose page read as though it were written for a different audience.

### Go to the source

**If the code is available to you, read it.** Source outranks any document written about it, including its own documentation — docs drift, code does not. Prefer, in order: the source, the spec/RFC, official docs, maintainer design docs and changelogs, then everything else.

Two failure modes specific to this domain:

- **Version drift.** Behaviour changes across releases. Name the version you are describing, and check whether your source predates a change that matters.
- **Aspirational documentation.** A README describes intent; the code describes behaviour. Where they disagree, the code wins — and the disagreement is often exactly the thing that trips people up, so it belongs in section 5.

### Architecture diagrams

Never fetch a vendor icon CDN (AWS, Azure, GCP, or any other). Represent each service as a labelled rounded `<rect>` with the service name as `<text>`; tint with `--s1..--s5` if grouping helps.

Label the edges with what actually travels: the protocol, the payload, the trigger. A diagram of named services with unlabelled arrows tells the reader nothing they could not get from a list — and for an explainer, the edge labels *are* the explanation.

### A concrete example, in this domain

The minimal example (section 4) should be runnable: the smallest command, call or config that demonstrates the mechanism. Real syntax, real names, no placeholders like `<your-value-here>` unless the placeholder is the point.
