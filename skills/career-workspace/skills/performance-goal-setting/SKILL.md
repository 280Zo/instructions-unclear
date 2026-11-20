---
name: performance-goal-setting
description: 'Use when the user wants to set, draft, write or refine annual performance or promotion goals for a review cycle, asks for SMART goals, or has manager expectations, guidance or a draft to turn into goals. Goals the user already has and only wants recorded go to performance-log.'
---

# Performance goal setting

## Overview

Draft one review cycle's goals for **one goal set per run**: Performance or Promotion. They are unrelated processes with different readers, so each run gathers its own context and never reads the other set's goal-setting files. The run ends with paste-ready goals for the company's HR system and the same goals recorded in `performance/<cycle>/goals.md` through `performance-log`, so the year's log and review track against them. All paths are relative to the career workspace.

| Set | Read by | Write for |
|---|---|---|
| Performance | AVP, sometimes the CISO | Measured results in the role; some technical detail is fine |
| Promotion | CIO and above | Business and organizational impact, scope beyond the role; light on technical detail |

## Rules every goal follows

These are always true, whatever the user, the deadline or the inputs say.

1. **SMART.** Specific (what, where, which system or group), Measurable (a metric and a target), Achievable (the user's own data or history supports it), Relevant (traces to a stated expectation or requirement), Time-bound (a date inside the cycle). A goal that fails any letter isn't finished.
2. **Achievable, but not obviously so.** Commit to a target the user can beat with real effort, never one they might miss and never a gimme. Then word the goal so the lift is visible: the scale (systems, teams, volume), the risk or cost it moves, the people it reaches, the leadership it involves. Under-promise on the number, never on the description of the work.
3. **A measurable, meaningful outcome.** Measure the result (time to remediate, coverage, hours saved, adoption), not activity alone (meetings held, tickets touched).
4. **Never overclaim.** No scope, authority, budget, headcount or result the user doesn't have. `performance-review` scores the year against these goals, and a claim the user can't back costs them there.
5. **Targets are proposed, not invented.** Propose each target from the user's baselines, data or history and say what it's based on. It is `proposed` until the user approves or changes it. With no baseline, write "establish a baseline by <date>, then improve it by <N>" and propose N. Never leave a placeholder such as `[N]` or `[current MTTR]` in a draft.

## Process

0. **Pick the set and the cycle.** The set the user names; otherwise ask. Read `goals.md` frontmatter in every `performance/*/` folder and `profile/work-history.md`. If the set already has goals in the cycle's `goals.md`, ask whether this run replaces or refines them.
1. **Context.** In one message, ask for what the workspace doesn't already say, confirming what it does:
   - role, level and team (confirm the work-history row);
   - the cycle label, start and end dates. **Never invent cycle dates or a label**, and never reuse last cycle's;
   - expectations from the manager, director, AVP and executive leadership, as they were given.
2. **Inputs.** Right after, ask for anything that helps set goals for someone in the user's field: requirements, guidance, company or team documentation, OKRs, last year's review, drafts, data and baselines. Read what they give where it is and summarize each in the working file; filing documents belongs to `career-intake`. If last cycle's goals and its `reviews/*-working.md` exist, offer them as background for this set only. Ask how the HR system wants each goal (fields, length limits, number of goals), or read it from a guide the user gives. Keep the answer in the working file and reuse it next cycle after confirming.
3. **Categories.** Pin down the goal topics before any wording. Ask open questions one at a time, each built on the user's last answer or on something in the inputs. Then propose categories, each with a one-line high-level outcome ("critical vulnerabilities are fixed faster"), and let the user correct them. No solutioning here: no plans, tasks, tools or targets yet. Every category traces to an expectation or requirement from steps 1 and 2.
4. **Wants.** Ask: "Is there anything you want to accomplish, get involved in or explore this year that's outside these requirements, such as a new technology?" For each answer, find the honest fit: the means of delivering a category's outcome (a new tool as the way to automate a required process), a measured pilot inside a category, or part of a development goal if the HR system has one. Show the user how it was fitted. If nothing fits without stretching the truth, say so and let them decide.
5. **Needs.** Ask: "Is there anything you need to accomplish or get involved in this year, such as CPE credits, a certification or a required training?" Fit each the same way, usually as a measured part of a relevant category (CPE hours earned through work that delivers an outcome). Show the user how each was fitted.
6. **Draft.** Write the goals in the HR system's layout and count, following every rule above. Present them in the chat with each proposed target and its basis marked, and the SMART check for each goal.
7. **Approve.** Revise until the user approves the final wording and every target. Approval covers the exact text that will be pasted and recorded.
8. **Write and hand off.** Write `<set>-goals.md` and update `<set>-working.md`. Then load `performance-log` and run its Helper gate and step 0 with the cycle label and dates and the approved goals for this set only: each goal's `### <slug> · <name>` heading, its statement as the requirement text, and its measure, target and date as the `Measured by:` line. Step 0 changes only this set's section of `goals.md` and does its own re-matching. If the Helper gate fails, stop there: tell the user `goals.md` wasn't updated and why, and that the paste-ready file is saved.

**A user in a hurry** ("just give me 5 goals") still gets steps 1–5, asked as one short message with the questions numbered so a one-line answer each works. Without the role, the cycle dates and at least one stated expectation, goals are generic and can't pass the SMART check; say so in one sentence and ask.

## Output contracts

All in `performance/<cycle>/goal-setting/`, where `<set>` is `performance` or `promotion`. A run never overwrites an earlier run's files: when `<set>-goals.md` exists, this run writes `<set>-goals-2.md` and `<set>-working-2.md` (then `-3`), and only the latest approved goals are handed off.

**`<set>-goals.md`** (paste-ready): one block per goal in the HR system's fields and order, within its limits. Plain text the user can paste: no tags, no `proposed` markers, no brackets, no notes.

**`<set>-working.md`**, sections in this order: Context (role, level, team, cycle, expectations by source) · Inputs (one summary per document or note, with where it lives) · HR format · Categories (outcome and the expectation each traces to) · Wants and needs (each item and how it was fitted, or why it wasn't) · Targets (goal, target, basis, `proposed` or `approved`) · Drafts (each revision) · SMART check (one row per goal: S, M, A, R, T, each with the words that meet it) · Handoff (date recorded in `goals.md`, or why not).

## Scope

Writes only in `performance/<cycle>/goal-setting/`. `goals.md` changes only through `performance-log` step 0. Never reads or writes the other set's goal-setting files, and never edits entries, `reviews/`, `people/`, `projects/`, `profile/` or `accomplishments/`.

## Common mistakes

| Mistake | Instead |
|---|---|
| Drafting goals from the manager's note before asking role, team, cycle and expectations | Steps 1 and 2 first, in one message each |
| "Skip the questions": five generic goals with `[N]` and `[current MTTR]` blanks | One short numbered question message; proposed targets with a basis, never blanks |
| Vague targets ("triage promptly", "reduce from baseline", "at least one teammate") | A metric, a proposed number and a date inside the cycle |
| A stretch target the user might miss, or a target that is obviously easy | A target they can beat, with the lift shown in scope, scale and reach |
| "Lead the program" when the user contributes to it | The user's real role in the work, worded with its true weight |
| Adding a goal no expectation or requirement asked for | Every category traces to steps 1 and 2; extras come only from the user's wants and needs |
| Skipping the wants and needs questions because the requirements look complete | Ask both, every run |
| Refusing to draft because `performance-log` only records the user's words | This skill drafts; the user's approval makes the text theirs, and step 0 records it |
| Reading `performance-*` goal-setting files during a Promotion run, or the reverse | One set per run; the other set's files stay closed |
| Writing `goals.md` directly | Hand off to `performance-log` step 0 |
| Approved goals left only in the chat when the helper check fails | Write `<set>-goals.md` first, then hand off; report the failure |
| Making up cycle dates to make goals time-bound | Ask; a goal without the cycle's dates isn't finished |
