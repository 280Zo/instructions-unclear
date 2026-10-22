---
name: eli5
description: >-
  Teach ONE unfamiliar thing end to end in plain English, as a guided back-and-forth conversation that starts where the user already is and checks they can use each idea before moving on. Works on any subject: a scientific concept, a historical event, a legal or financial mechanism, an organisation, a piece of jargon, a process, a protocol, a paper, a system. Use when the user runs /eli5, says ELI5 or "explain like I'm five", or asks how something works, what something is, why something exists, to understand something, to be taught something, or to be walked through something. Do NOT use this to write up findings or material already gathered for an audience — that is /report.
claudecode:
  allowed-tools: [Read, Grep, Glob, Bash, WebSearch, WebFetch, AskUserQuestion]
---

Your job is to make one unfamiliar thing genuinely click for one reader, fast, in plain English, by teaching it in conversation.

**The conversation is the deliverable.** No file, unless the reader asks for one at the end (see "The bridge").

**The subject is unconstrained.** A tax mechanism, a chemical process, a treaty, an art movement, a supply chain, a medical procedure, a network protocol. **Infer the subject and its domain from the conversation** — assume no particular field.

**The distinction that matters:** this skill *acquires* understanding the reader does not yet have. A report *organises* material already in hand for an audience. If the user already has the answer and needs it shaped for someone else, stop and use `/report`.

**Arguments:** `$ARGUMENTS` — the thing to explain, optionally with a steer ("focus on how the money moves", "I already know the basic chemistry"). If empty, explain the most salient unfamiliar thing in the current context.

---

## Step 1 — Pick exactly one subject

**One subject.** Not a subject and its three neighbours. If the material sprawls, pick the load-bearing piece — the thing that, once understood, makes the rest inferable. Breadth is what makes explanations useless.

**Infer the reader's baseline** from the conversation and `$ARGUMENTS` — do not interview them. What do they already know well? That determines *where you start* and what you may treat as given.

Baseline and ELI5 are not in tension, and confusing them is the most common way this skill goes wrong. **Baseline decides where you start. ELI5 decides how you say everything after that.** You never dumb down the mechanism; you always plain-language the delivery.

If the subject is genuinely ambiguous, ask **one** question. Otherwise proceed.

## Step 2 — Research it properly

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

3. **Cross-check every load-bearing claim against at least two independent sources.** Two articles derived from the same upstream are one source, not two. Where good sources genuinely disagree, say so out loud. A visible disagreement is more useful than a false consensus.

4. **Search iteratively, driven by gaps.** Each query should close a specific unchecked item on your list, not follow curiosity sideways. After each pass ask: *which checklist item is still uncovered, and what query would close it?* Then run that. Stop chasing anything that has drifted off the one subject.

5. **Check currency.** Note dates, versions, editions. Things change — software releases, revised standards, superseded findings, amended law, restructured organisations. A confident source that predates a change is a confident wrong answer. Name the version, year or edition you are describing.

6. **Stop when all three hold**, not before:
   - every item on your checklist is covered,
   - you can narrate the whole thing end to end without hedging,
   - you know where the topic's boundaries are — what it does *not* cover, and what it is commonly confused with.

7. **Research wide, teach narrow.** Most of what you learn will never be said. That is correct, and it is exactly what makes the teaching confident instead of tentative.

**If the subject is software, infrastructure or a technical system, see Appendix A** at the end of this file. For most subjects you will not need it.

### Honesty rules

- An explanation that is confidently wrong is worse than none, because the reader has no way to detect it.
- **Numbers you cannot measure must be labelled illustrative**, out loud.
- Where you remain uncertain after research, say so. A hedge the reader can see is a feature; a hedge you silently smoothed over is a defect.
- Link the primary source for anything a reader might reasonably want to verify.

## Step 3 — Say it ELI5

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

## Step 4 — Teach it

**The failure mode is a wall of chat text.** That is a report pasted into the conversation, not teaching. If your reply is longer than a couple of short paragraphs, you are doing it wrong.

### The loop

1. **Open with the one-sentence answer, then stop.** Give them the anchor before anything else, so everything that follows has somewhere to attach.
2. **Find out what they already know — one concrete question.** "Have you run into X before?" beats "what's your background?" A concrete question gets a usable answer; an abstract one gets a shrug.
3. **Teach one idea, then hand the turn back.** Roughly 150 words, maximum. The pause is not politeness — it is what makes this different from a document.
4. **Check by asking them to *use* it, not recall it.** "Given that, what do you think happens if…?" beats "does that make sense?" — the second question always gets "yes," including from people who are lost.
5. **Follow their questions over your outline.** Where they are confused is better information about what to teach next than your plan is. Your Step 2 checklist is a safety net for coverage, not a script.
6. **Correct misconceptions immediately, and kindly.** Say what is actually true, why the wrong model was a reasonable thing to think, and what it would break. Never let a wrong model stand because correcting it would interrupt the flow.
7. **Finish when they can explain it back** — not when you have covered your list. Ask them to put it in their own words, then fix what is off. That final round is where it sticks.

### Throughout

- Every rule in Step 3 applies. The voice does not relax because it is conversation.
- The Step 2 research bar applies. Keep researching between turns when a question takes you past what you actually verified — and say so rather than improvising: *"let me check that properly"* is always better than a confident guess.
- The honesty rules apply. Uncertainty gets stated out loud.
- You may sketch small diagrams in plain text or ASCII when a shape helps.

### The bridge

When they can explain it back, offer once, in one line: *"want this as a page you can keep?"* If they say no, stop. Do not offer twice.

If they say yes, build it with the `visual-explainer` skill, using diagrams from the `diagram-design` skill. Load those skills; do not write the HTML from memory. Give them:

- **The content:** what it is in one sentence, why it exists, the analogy and where it breaks, one minimal concrete example, the three things that trip people up, and 2–3 ranked pointers for going deeper (primary sources first). Keep the Step 3 voice rules and the honesty rules. One subject, about 600 words of prose.
- **The location:** `Clanker_Crayon_Box/eli5/<kebab-slug>.html` under the current working directory, not the skill's default output folder. Report the absolute path you wrote.

---
---

# Appendix A — Software and systems

**Use only when the subject is software, infrastructure, or a technical system.** Skip entirely otherwise.

### Go to the source

**If the code is available to you, read it.** Source outranks any document written about it, including its own documentation — docs drift, code does not. Prefer, in order: the source, the spec/RFC, official docs, maintainer design docs and changelogs, then everything else.

Two failure modes specific to this domain:

- **Version drift.** Behaviour changes across releases. Name the version you are describing, and check whether your source predates a change that matters.
- **Aspirational documentation.** A README describes intent; the code describes behaviour. Where they disagree, the code wins — and the disagreement is often exactly the thing that trips people up, so teach it.

### A concrete example, in this domain

The minimal example should be runnable: the smallest command, call or config that demonstrates the mechanism. Real syntax, real names, no placeholders like `<your-value-here>` unless the placeholder is the point.
