---
name: performance-log
description: 'Use when the user pastes or dumps day-to-day work notes in any format and says log this, add this, capture these, add this to my work log, add this to career-intake, or process my log, or gives the goals and dates of a review cycle, or wants work tracked against yearly performance or promotion goals. Explicit resume wins ("for my resume") go to career-intake instead.'
---

# Performance log

## Overview

Turn a dump of work notes into one entry file per piece of work, in a fixed format that `performance-review` can process at year end. Entries hold **facts, not stories**: condensed and organized, but every name, number, unit, date, system, ticket ID and quote exactly as the user wrote it. The user's notes are the record; never add numbers, outcomes, praise or calculations they didn't write. All paths are relative to the career workspace (the folder the tool was started in).

## Helper gate

Run this before anything else, every time. Counting and the index come from `performance/tools/perf_count.py`, built from `helper-spec.md` in this skill's folder; never count or build the index by hand.

1. If `performance/tools/perf_count.py` is missing, or `python3 performance/tools/perf_count.py --version` fails or prints a number lower than the spec's `SPEC_VERSION`, build it from `helper-spec.md`.
2. If `performance/tools/CHECKED` holds the spec's version and the script's current sha256, the helper has passed: go on.
3. Otherwise run the spec's **Check** section exactly. Fix the script, never the fixture or expected output.
4. If the check still fails, stop. Tell the user what differs and file nothing.

## Workspace layout

```text
performance/
  tools/perf_count.py, CHECKED     the helper (built by the gate)
  tools/selftest/                  the gate's fixture and comparison files, kept between runs
  <cycle>/                         one folder per review cycle, named by its label
    goals.md                       cycle dates and both goal sets (templates/performance-goals.md)
    log.md                         optional paste inbox
    raw/<YYYY-MM-DD_HHMM>.md       each paste, unchanged (capture time)
    entries/<date>_<HHMM>_<slug>.md  one file per piece of work (templates/performance-entry.md)
    index.md                       built by the helper
    calendar.md                    optional holidays and PTO: lines "- YYYY-MM-DD <why>"
    reviews/                       written by performance-review
  unfiled/raw/, unfiled/entries/   notes whose date is in no known cycle
```

## Setup

Create missing folders. Copy `templates/performance-entry.md` and `templates/performance-goals.md` from this skill's folder into the workspace `templates/` when missing. Never overwrite an existing file.

## Process

0. **Record cycles and goals the user gives.** When the user gives a cycle's label and dates, or its goals, write `performance/<cycle>/goals.md` from `templates/performance-goals.md`: goal names and requirement text word for word, `Measured by:` only when they state it. If the file exists, change only what the user changed and tell them. Then re-match: move any `unfiled/` entries whose dates the cycle contains into it, and offer to match goals for entries with `goals: []` (all entries, when goals changed), using the step 9 rule.
1. **Find the input.** A paste in the chat, or unprocessed text in a cycle's `log.md`: everything above the marker line `<!-- filed: everything below this line has been processed -->`, or the whole file when there is no marker. After filing, the marker goes at the top with the summary line below it.
2. **Find each note's cycle.** Read `goals.md` frontmatter (`cycle`, `cycle_start`, `cycle_end`) in every `performance/*/` folder. A note goes to the cycle whose dates contain its date. A date without a year takes the latest year that doesn't put it after today. If no cycle contains a date, file that note under `performance/unfiled/` and ask for the cycle's label, start and end dates. **Never invent cycle dates or a cycle label.** When a later run learns the cycle, move `unfiled/` entries and their raw files into it.
3. **Save the raw paste** unchanged to `raw/<capture YYYY-MM-DD_HHMM>.md` in every folder that receives entries from it (a cycle folder, `unfiled/`, or both), so each entry's `source` resolves. For `log.md` input, replace the processed text with one line below the marker: `- <capture time>: filed <n> entries, raw/<file>`.
4. **Split** into entries: one per distinct piece of work per date. Same-day notes about the same work merge into one entry; quotes or feedback about earlier work become their own entry on the day they were given. Small updates still get an entry.
5. **Date and file name.** Use the note's date. No date: use the capture date and set `date_inferred: true`. File name `<date>_<HHMM>_<slug>.md`: HHMM from the note when it gives a time, otherwise the capture time; `<slug>` is 2–5 kebab-case words. Never overwrite: add `-2` if the name exists.
6. **Correlate.** Reuse slugs already in the cycle's `index.md`, other entries, and the workspace's `people/` and `projects/` file names. A name that might be an existing slug but isn't certain ("J. Doe" when `jane-doe` exists) is a question for the user; until it's answered, use the name as written (`j-doe`). New people, projects and topics get new kebab-case slugs in the entry only.
7. **Write each entry** from `templates/performance-entry.md`: every frontmatter key filled, then fact bullets. `employer` is the work-history row covering the date; if work history shows a job change inside the cycle, ask which job.
8. **Tag every number** in the bullets:

   | Tag | When |
   |---|---|
   | `[verified]` | A filed document in the workspace shows it |
   | `[reported]` | The user states it as fact ("12 min", "7 of 9", "112 rules") |
   | `[estimate]` | The user hedges ("~40", "about 4/day", "roughly 3 hrs") |

   A change "from ~40 to 12" tags each side: `~40 [estimate] → 12 [reported]`.
9. **Goals and above and beyond.** Add a goal id only when something in the note supports it, and say what in a `Goal fit:` bullet. Weak or guessed fits are left off. Set `above_and_beyond: true` only when the note shows the work is outside the goal or the user's role ("wasn't on our roadmap", "helped the SOC out"), quoted in an `Above and beyond:` bullet. With no `goals.md` goals, use `goals: []` and ask for the goals.
10. **Rebuild the index:** `python3 performance/tools/perf_count.py index performance/<cycle>` for each cycle touched. `unfiled/` has no `goals.md` and no index; don't run the helper on it.
11. **Ask, in one message**, then **report**. Always ask: "Is there anything in this batch you want to highlight?" Add at most three other questions, only ones needed to file correctly: a possible name match, a missing cycle, missing goals, which job. Then list one line per entry: path, goals, `above_and_beyond`, `highlight`. When the user answers, set `highlight: true` with a `Highlight:` bullet in their words, or apply the slug or cycle they gave.

## Scope

Entries, raw pastes, `log.md`, `index.md` and `goals.md` (only with the user's own cycle dates and goal text) only. Never create or edit `people/`, `projects/`, `profile/`, `accomplishments/` or `reviews/` records; those belong to `career-intake`, which `performance-review` hands major accomplishments to. Never write review judgments (status, strength, gaps) into entries or the index.

## Common mistakes

| Mistake | Instead |
|---|---|
| Inventing a layout, one big log file, or a log at the workspace root | The layout above, one entry file per piece of work |
| Writing a person's or project's record (`people/raj-patel.md`) | Slug in the entry only; intake owns records |
| Writing "assumed to be Jane" into a record or entry | Use `j-doe` and ask |
| Computing a number the user didn't write ("roughly 87% fewer") | Copy their numbers only |
| Tagging every number `[estimate]`, or leaving some untagged | Tag each number with the table |
| Creating a cycle ("FY2027, 2026-11-01 to 2027-10-31") or reusing last cycle's goals for it | `unfiled/` and ask for the dates |
| Writing `goals.md` from your own wording, or leaving `goals: []` entries unmatched once goals exist | The user's words only, then step 0's re-match |
| Matching a goal because it might fit ("my own call") | Only with a `Goal fit:` reason from the note |
| Asking for proof, sources, scan dates or measurement windows | File what was given; ask only what filing needs |
| Rewriting notes as a story or summary ("Figures as reported by me") | Fact bullets in the user's terms |
| Skipping the highlight question because the notes said "big" | Ask it every run; the hint can be offered as a suggestion |
| Counting or building the index by hand when the helper fails | Stop and report |
| Skipping the gate because the user says the helper is already there | `CHECKED` decides; a script without a matching `CHECKED` goes through the Check section before use |
| Deleting `selftest/` or writing scratch files outside the workspace | Keep everything in `performance/tools/selftest/` |
