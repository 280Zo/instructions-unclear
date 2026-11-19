# Meeting template

Record what changed because the meeting happened: what was decided, who will do what by when, and what's still open.

## Before drafting

Ask what the meeting was for when the material doesn't say, and wait. The purpose decides which details are worth keeping.

## Frontmatter

Shared properties, plus:

- `date`: the day of the meeting, or `null` if unknown. `created` is when the note was written.
- `time`: quoted 24-hour time, only when known.
- `attendees`: list of links to people who attended. Not people only invited or mentioned, and not `Unknown speaker N` labels.
- `purpose`: one line, only when it adds something the title doesn't.
- `summary`: one line on the outcome, for reviews.

## Sections, in this order

1. `## Decisions`: choices that stood at the end of the meeting, with conditions. If a decision was reopened and not settled, it goes under Open questions.
2. `## Action items`: agreed work and explicit commitments, as task lines. An owner and a due date appear only when stated. The person who raised a task doesn't own it unless they said so. A tentative offer is marked "(tentative)".
3. `## Open questions`: unsettled proposals and anything still to find out.
4. `## Details`: context that matters for the purpose, such as figures, constraints, risks and attributed positions. Name a speaker when the source names one.
5. The collapsed reasoning callout, when the material gives reasoning.

Steps someone walked through become a separate how-to note (propose the split first). The meeting note links to it.

Elapsed transcript timestamps (`[00:12:03]`) locate a point and aren't clock times. Keep one only when it helps verify a disputed point.

## Example

```markdown
---
type: meeting
title: Reading pilot scope
created: 2026-05-12
date: 2026-05-12
time: "14:30"
attendees:
  - "[[Alex]]"
  - "[[Quinn]]"
summary: Pilot runs at two branches; Saturday coverage still open.
source: meeting transcript
tags: [library]
---

## Decisions
- Run the pilot at two branches.

## Action items
- [ ] [[Alex]] sends the schedule by 16:00 📅 2026-05-15

## Open questions
- Who covers Saturdays?

## Details
- [[Quinn]] said one trainer can cover both branches on weekdays.
- Unknown speaker 2 said `[unclear: staffing?]` might delay the start.

> [!note]- Why two branches
> Alex proposed four. Quinn pointed out there is one trainer, so the group settled on two.
```
