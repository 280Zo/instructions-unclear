---
name: report
description: >-
  Turn material that has already been gathered into an evidence-backed report someone else can read without you in the room, on any subject whatsoever: a data analysis, a conference talk, a policy review, a site visit, an incident, a set of interviews, a literature scan, a security assessment. Every claim anchored to its source, an explicit statement of who the report is for, rendered as a page, slide deck or PowerPoint by the visual-explainer, diagram-design, frontend-slides and Presenton tools. Use when the user runs /report, or asks to write up, document, summarise or produce a report on material that has already been gathered. Do NOT use this to build understanding of something unfamiliar or to answer "how does X work" — that is /eli5.
claudecode:
  allowed-tools: [Read, Grep, Glob, Bash, Write, WebSearch, WebFetch]
---

You are producing a **report**: material already in hand, turned into an evidence-backed deliverable someone else can read without you in the room.

This skill owns the **evidence**: what was consumed, what each claim rests on, how confident the conclusions are. Other skills own the **look** (Step 5). Never trade an anchor or a caveat for layout.

**The subject is unconstrained.** It may be quantitative or entirely qualitative; technical or not remotely technical. **Infer the subject and its domain from the conversation** — do not assume any particular field.

**Arguments:** `$ARGUMENTS` — optional free-text steer (a topic, a file or folder, "focus on the cost drivers", "for the board", "as slides"). If empty, report on the most salient material in the current conversation.

**The distinction that matters:** a report organises what is *already known* for an audience. If the user instead needs to *understand something unfamiliar*, stop and use `/eli5`.

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

| If the material involves… | Also use |
|---|---|
| Software, infrastructure, a technical system | **Appendix A** |
| Security findings, vulnerability scans, pentest results, crawl data | **Appendix B** (plus A) |

For most reports you will use neither. Applying an appendix to an unrelated topic makes the report read as though it were written for a different audience.

### The evidence rule, which is absolute

Every substantive claim carries an anchor from the table above. **Numbers you cannot measure must be labelled illustrative** — inline, visibly. A chart built from invented numbers is worse than no chart.

**Separate observation from inference.** If you are extrapolating, say so in the text; never let an inference inherit the credibility of the measurement beside it.

Ask at most **one** clarifying question, and only when you genuinely cannot identify what material you are meant to consume. Otherwise proceed — do not stall.

## Step 2 — Fix the audience, then state it

Infer the audience and purpose from how the skill was invoked, the surrounding conversation, and `$ARGUMENTS`. **Do not interrogate the user about it.**

Then state the inference visibly at the top of the report — "Written for the programme committee · to support the spring funding decision" — so a wrong guess is correctable in one reply.

Audience drives register, not rigour. A report for a board moves method detail to an appendix; a report for a practitioner keeps it inline. Neither drops the anchors.

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

## Step 4 — Keep the visuals honest

The renderer decides how things look. You decide what is allowed to be shown:

- **Every number in a chart, tile or diagram traces to a source.** Totals are recomputed, not copied: a stacked bar whose segments do not sum to its stated total is the most common failure.
- **A qualitative finding gets a pull quote with its attribution**, not a chart of three hand-waved numbers.
- **Never a dual-axis chart.** Two y-scales on one plot invent a correlation that is not in the data. Use two charts, or index both to a common base.
- **Never a pie to compare close values**, and never more than five slices. The eye cannot rank similar angles.
- **State is never colour alone.** Severity, pass/fail and status always carry a text label.
- **Unmeasured numbers stay labelled illustrative** in the rendered output, not only in your draft.

## Step 5 — Render it

Load the skills below and follow them. **Do not write HTML or slides from memory.**

| The user wants | Use |
|---|---|
| A report page (the default) | `visual-explainer` |
| Diagrams inside the report | `diagram-design`, embedded in the page or deck |
| A slide deck to present from a browser | `frontend-slides` |
| Editable PowerPoint or Google Slides | Presenton's MCP tools (Google Slides imports the `.pptx`). If those tools aren't available, say so and offer `frontend-slides` instead |

**One theme for everything.** Pick a theme with the `theme-factory` skill (or use one the user names), and tell each renderer to use that theme's colours and fonts in place of its own defaults, so the page, diagrams and deck match. The theme wins over a renderer's own palette and font advice, including visual-explainer's list of colours and fonts to avoid. Theme fonts are desktop fonts (DejaVu, FreeSans), so give each a fallback stack ending in a generic family (`"DejaVu Sans", "Helvetica Neue", Arial, sans-serif`).

**Where to write it.** Tell the renderer to write to `Clanker_Crayon_Box/reports/<kebab-slug>.<ext>` under the current working directory, not to its own default output folder. Create the folder if needed. Re-running the same report overwrites the same slug.

**What to hand over.** The full spine from Step 3 in order, the audience line, every claim with its anchor visible next to it, and the Step 4 limits. Tell the renderer not to drop sections, anchors or caveats to make the layout fit: add space, slides or collapsible sections instead.

## Step 6 — Self-review before surfacing

Do this yourself. Do not delegate it to a subagent — the checks need the source material already in your context, and a handoff loses it.

Open the rendered output and check it against the source material:

- **Data accuracy.** Every number in every chart, tile, diagram and sentence traces back to a source. Recompute the totals.
- **Anchors survived rendering.** Every substantive claim still has its anchor in the output. Observation is distinguishable from inference. Everything unmeasurable is visibly labelled illustrative.
- **Nothing was added.** The renderer introduced no numbers, quotes, trends or recommendations that are not in your material.
- **Structure.** The spine is intact: bottom line, audience, provenance including what was *not* examined, findings, confidence and gaps, so what.
- **Step 4 held.** No dual axis, no unreadable pie, no colour-only state.
- **Domain fit.** No convention from an appendix you did not need.
- **Location.** The file exists at the path you are about to report.

Fix anything that fails, then check again. Only then surface it.

## Step 7 — Surface it

Report the absolute path in one line and stop. **Do not inline the output. Do not describe the report in prose — the report is the deliverable.**

---
---

# Appendix A — Software and systems

**Use only when the subject is software, infrastructure, or a technical system.** Skip entirely otherwise.

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

### Measures that are easy to misreport

- **Latency or duration:** a distribution, never a mean alone. State the percentile you are quoting.
- **Throughput or error rate over time:** mark the incident window so the reader can see before and after.

---

# Appendix B — Security findings

**Use only when the material contains security findings, vulnerability scans, pentest results, crawl topologies or network scans.** Skip entirely otherwise. Assumes Appendix A also applies.

### Every finding needs

What was observed, where (its anchor), why it matters, how to reproduce it, and what would fix it. **A severity rating without a reproduction path is an assertion, not a finding.**

Severity is stated in words (`Critical`, `High`, `Medium`, `Low`, `Informational`) on every finding, with counts per severity stated in text. Crawl or scan results state their counts (endpoints per status code, per depth) in text as well as in any chart.

### OWASP mapping

Annotate each finding with its OWASP classification, formatted `[Framework] Code: Category Name`.

**Web application — OWASP Top 10 (2025):**

- `A01: Broken Access Control` | `A02: Security Misconfiguration` | `A03: Software Supply Chain Failures`
- `A04: Cryptographic Failures` | `A05: Injection` | `A06: Insecure Design`
- `A07: Authentication Failures` | `A08: Software or Data Integrity Failures`
- `A09: Security Logging and Alerting Failures` | `A10: Mishandling of Exceptional Conditions`

Server-side request forgery is no longer its own category; it is part of `A01: Broken Access Control`.

**LLM applications — OWASP Top 10 for LLMs (2025):**

- `LLM01: Prompt Injection` | `LLM02: Sensitive Information Disclosure`
- `LLM03: Supply Chain Vulnerabilities` | `LLM04: Data and Model Poisoning`
- `LLM05: Improper Output Handling` | `LLM06: Excessive Agency`
- `LLM07: System Prompt Leakage` | `LLM08: Vector and Embedding Weaknesses`
- `LLM09: Misinformation` | `LLM10: Unbounded Consumption`

Example: `OWASP A05:2025 — Injection`, `OWASP LLM01:2025 — Prompt Injection`.

**Only tag a finding when the mapping is genuine.** A wrong OWASP tag is worse than no tag — it launders a guess as a standard. If a finding does not map cleanly, leave it untagged and say why.
