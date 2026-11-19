# Project template

An ongoing effort. Status, blockers and tasks come first, because they're what you open the note for.

## Frontmatter

Shared properties, plus:

- `status`: `active`, `blocked`, `on-hold`, `done` or `cancelled`. Use `blocked` only when the whole project is stuck. A blocked part goes under Blockers.
- `summary`: one line on where things stand, for reviews and Bases views.
- `updated`: the date of the last update.
- `target`: the target date, when stated.

## Sections, in this order

1. `## Status`: where it stands, in a line or two, ending with `Updated: [[YYYY-MM-DD]]`.
2. `## Blockers`: one line each, saying what's blocked, what or whom it's waiting on, and since when (as a linked date). Leave the section out when nothing is blocked.
3. `## Tasks`: the project's own task lines, then this query, which lists open tasks from notes that link to the project:

   ````markdown
   ```dataview
   TASK
   FROM [[]]
   WHERE !completed
   ```
   ````

4. `## Done when`: what finished looks like.
5. `## Log`: dated lines, newest first, each linking the note the news came from when there is one.
6. `## Why it's going this way`: a collapsed callout with decisions and alternatives.

## Updating

Most project notes change through update mode. New material from a meeting, a session or a quick dump does the following:

- updates Status and `summary`
- adds or clears blockers
- checks off finished tasks (`- [x] Task ✅ YYYY-MM-DD` when the finish date is known)
- adds new tasks
- adds a log line at the top of the Log
- sets `updated`

The change log callout isn't needed here, because the Log is the record.

## Example

````markdown
---
type: project
title: Homelab backup overhaul
created: 2026-11-01
updated: 2026-11-18
status: active
summary: Restic running on both hosts; offsite waiting on account approval.
target: 2026-12-31
source: project updates
tags: [homelab]
---

## Status
Both hosts back up nightly to local storage. Offsite isn't set up yet. Updated: [[2026-11-18]]

## Blockers
- Offsite backups: waiting on [[Backblaze]] to approve the account, since [[2026-11-14]].

## Tasks
- [x] Set up restic on host B ✅ 2026-11-17
- [ ] Test a full restore

```dataview
TASK
FROM [[]]
WHERE !completed
```

## Done when
Both hosts back up nightly to local and offsite storage, and a full restore has been tested.

## Log
- [[2026-11-17]] Restic set up on host B.
- [[2026-11-10]] Restic set up on host A.
````
