---
name: performance-review
description: 'Use when the user wants their performance review, self-assessment or promotion request written from their work log, asks how they are tracking against yearly performance or promotion goals, or wants a mid-year or year-end goal check.'
---

# Performance review

## Overview

Turn one review cycle's work log (written by `performance-log`) into paste-ready answers for each goal, a working file that shows every decision, and a handoff of major accomplishments to `career-intake`. Pick the **strongest** evidence for each goal, never all of it. Use only facts in the entries. All paths are relative to the career workspace.

## Inputs

- **Cycle:** the one the user names. Otherwise the `performance/<cycle>/` folder whose dates contain today. Use the most recently ended cycle instead, with the as-of date set to its `cycle_end`, when any of these is true: no cycle contains today; the cycle containing today has no entries yet; or the user asks for a year-end review and that ended cycle has no `reviews/review-<its cycle_end>.md` yet. Confirm the choice in step 11's message. One cycle per review: entries from earlier cycles are never assigned to goals. The working file may cite them as context ("sustained since FY2025"), and they reach paste-ready text only if the user agrees.
- **As-of date:** today unless the user gives one. "Year end" means the cycle's `cycle_end`. Entries dated after the as-of date are left out.
- **Files:** `goals.md`, `entries/`, `calendar.md` if present, and the newest `reviews/review-*-working.md` written by an earlier run (same-day ones included), whose assignments and holding area carry forward.
- **Job change:** if `profile/work-history.md` shows a different employer or role inside the cycle, ask whether the goal sets changed with it before scoring.

## Helper gate

Before anything else: load `performance-log` and follow its `## Helper gate`. If it fails, stop and report; never count by hand. Then run `python3 performance/tools/perf_count.py stats performance/<cycle> --as-of <date>` and use its numbers for every count in this review.

## Audiences

| Set | Read by | Write for |
|---|---|---|
| Performance | AVP, sometimes the CISO | Measured results against each goal; some technical and security detail is fine |
| Promotion | CIO and above | Business and organizational impact, scope beyond the role, decisions driven; light on technical detail |

The form answers are not letters: no addressee, no greeting.

## Process

1. **Counts.** From the helper output: workdays and workdays with entries, entries per goal, project, person and topic, project spans, near-duplicate tags, invalid entries.
2. **Inferred metrics.** Find what the log shows but the user never stated: notes on X of Y workdays (strong attendance), a project worked across N months, M distinct collaborators across teams, a duty done every week, a trend across reported numbers (queue 63 → 3). Each gets its computation and source entries and status `unconfirmed`. **Unconfirmed metrics never appear in paste-ready text.** A day without notes isn't proof of absence; attendance is claimed only after the user confirms it.
3. **Score, per set.** Every entry, or a group of linked entries forming one initiative, gets 1–3 on each of: **impact** (size of the measured result and its scope), **applicability** (how directly it meets the goal's requirement or measure), **visibility** for that set's audience. Score the two sets separately; the same work can rank high for one and low for the other.
4. **Assign, per set.** Give each goal its highest-scoring evidence: as many items as it takes to make the case (usually one to three), no more. Within a set an item supports one goal only, unless it's the only way to cover a goal or a goal has too little data; record which reason. Reuse across the two sets is fine. Note real overlap between goals.
5. **Swap.** Start from the earlier working file's assignments. If an item fits a goal better than one already there, swap it in and move the displaced item to the **holding area** with a note: use elsewhere, or drop.
6. **Correlate.** Look for entries that share people, projects or topics but aren't linked; sequences that make one larger initiative (kickoff → pilot → approval); near-duplicate tags that are the same person or project; work that supports a goal it isn't tagged with. Use them in scoring and list them in the working file. Don't edit entries.
7. **Progress and gaps.** For each goal: the evidence, its strength (strong / partial / thin / none) and what's missing. When the as-of date is before `cycle_end`, give concrete suggestions to close each gap before then, grounded in the goal text and work already under way. A suggestion is never written as done.
8. **Draft the paste-ready text**, following the user's guidance:

   > It's the story. Not a one-liner. Not a novel. Just a succinct description of what I accomplished. Direction from executive leadership is simple. Tell the story. You can match that up with traditional things like STAR method or whatever, but the story is what's most important. The story can include bullet points or cite raw data. That's neither a requirement or something to avoid. Whatever method allows for the best story telling should be prioritized on a per-story basis. Real names and numbers would be very useful in telling the story.

   Only facts from the assigned entries and confirmed inferred metrics. `[verified]` and `[reported]` numbers are used exactly; `[estimate]` numbers are worded as approximate ("about 30%"); quotes are exact, with who said them. Tags don't appear in paste-ready text. A goal with no evidence says plainly that it isn't met yet; it gets no placeholder.
9. **Humanize.** Load the `humanizer` skill and apply it to the paste-ready text only. Then **fact-check** the result against the draft: every number, name, date, ticket ID and quote must be unchanged ("14 critical tickets" stays 14, never "over a dozen"). Restore any that drifted and record them in the working file. If `humanizer` can't be loaded, save the draft as `reviews/review-<as-of>-draft.md` with the first line `Draft, not humanized: not ready to paste.`, write the working file, then stop and report the missing skill as a blocker. Never humanize by hand instead.
10. **Write the working file** and **the intake handoff** (contracts below).
11. **Ask, in one message:** the unconfirmed inferred metrics as one list ("confirm, reword or drop"), "File these with career-intake now?", and at most two other questions that change the text. Never ask for proof, sources or measurements. When the user confirms metrics, add them to the paste-ready text and re-run step 9's fact check. On yes to the handoff, load `career-intake` and file the handoff's items.

## Output contracts

All in `performance/<cycle>/reviews/`. A run never overwrites files an earlier run wrote: when `review-<as-of>.md` already exists, this run's three files take a suffix (`review-<as-of>-2.md`, `review-<as-of>-2-working.md`, `intake-handoff-<as-of>-2.md`, then `-3`). Within one run, step 11's confirmations update that run's own files.

**`review-<as-of>.md`** (paste-ready), in this order:

```markdown
# <cycle> review, as of <as-of>

## Performance (AVP / CISO)

### <goal name>
<story>
Above and beyond: <only when an assigned item has above_and_beyond: true>

### Above and beyond
<the strongest above-and-beyond work for this audience>

## Promotion (CIO and above)

### <goal name>
<story>
Above and beyond: <only when real>

### Above and beyond
<summary>
```

No other sections: no summary, no "additional contributions", no next-cycle goals, no brackets or placeholders. A set with no above-and-beyond work leaves out its `### Above and beyond` summary, and the working file says so.

**`review-<as-of>-working.md`**, sections in this order: Counts (helper output, as-of, range) · Inferred metrics (metric, computation, entries, status) · Scores (per set) · Assignments (per set: goal, entries, why, exception reason) · Holding area (entry, displaced from, use elsewhere or drop) · Overlaps · Correlations · Progress and gaps (per goal, with suggestions before `cycle_end`) · Fact check (what the humanizer changed and what was restored).

**`intake-handoff-<as-of>.md`:** the major accomplishments (the top-scoring items across both sets), each in the workspace's `templates/accomplishment.md` format with a `Source entries:` line linking the entries. Facts from entries only. `[reported]` numbers become `[estimate]`, because intake tags only `[verified]` (a filed document shows it) and `[estimate]`.

## Scope

Writes only in `performance/<cycle>/reviews/`. Never edits entries, `goals.md`, `people/`, `projects/`, `profile/` or `accomplishments/`; career records change only through `career-intake` after the user says yes to the handoff.

## Common mistakes

| Mistake | Instead |
|---|---|
| Putting every accomplishment in, or an "Additional contributions" section | Strongest per goal; the rest stays in the working file |
| Promotion work in the performance answers, or the reverse | Each set from its own assignments, framed for its audience |
| No above-and-beyond lines or summary | Per-goal line when real, plus one summary per set |
| A computed trend or coverage figure in paste-ready text before the user confirms it | Working file, `unconfirmed`, ask |
| Never offering attendance or coverage as an accomplishment | Always compute it and offer it |
| Writing wins into `accomplishments/` or editing `projects/` directly | The handoff file, then ask; intake files on yes |
| `[reported]` tags in the handoff | Map to `[estimate]` |
| Humanizer missing, so "I wrote it plainly myself instead" | Draft file, working file, stop, report the blocker |
| Humanizing, then pasting without checking numbers and names | Fact-check against the draft and restore |
| Addressing the promotion request to the manager, or writing a letter | Form answers for the CIO, no addressee |
| `[target title]`, `[Add when ...]` or next-cycle goal ideas in paste-ready text | Gaps and suggestions go in the working file |
| Asking for pre-change measurements, dashboards or other proof | Use what the entries say |
| Mentioning entries dated after the as-of date | Leave them out |
| A year-end review run after the cycle ended picks the new, empty cycle | Most recently ended cycle, as of its `cycle_end`, confirmed with the user |
