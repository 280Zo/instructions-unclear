---
name: career-intake
description: 'Use when a user gives career data to store, one item or a batch: a win, a note, numbers, a skill, an offer, a review, a person, a project, or documents dropped in inbox/. Triggers include "log this", "add this", "file these", "ingest", "remember this for my resume".'
---

# Career intake

## Overview

File what the user gives into the right place in the career workspace, in their words, and report where it went. The user's statement is the record. Storing is the whole job. All paths below are relative to that workspace.

## Where each type goes

| Type | File | Template |
| --- | --- | --- |
| Contact details | `profile/contact.md` | — |
| Work history (employer, titles, dates, location, manager) | `profile/work-history.md` | — |
| Accomplishment | `accomplishments/<employer>.md` (employer from the item; if none given, the `present` row of work history) | `templates/accomplishment.md` |
| Skill | `profile/skills.md`; mark `hands-on (user-confirmed YYYY-MM-DD)` when the user says they used it | — |
| Certification | `profile/certifications.md` | — |
| Education or training | `profile/education.md` | — |
| Performance review, rating, manager feedback | `reviews/<employer>.md` | `templates/review.md` |
| Award or recognition | `profile/awards.md` | — |
| Reference or letter | `references/` + `references/index.md` | — |
| Person (manager, colleague, interviewer, recruiter) | `people/<slug>.md` | `templates/person.md` |
| Application or job posting | `applications/YYYY-MM-DD_<company>_<role>/` | `templates/application.md` |
| Interview notes | `interviews.md` in that application folder | `templates/interview-debrief.md` |
| Resume file | `resumes/archive/` + a row in `resumes/versions.md` | — |
| Study material | `study/<topic>.md` | — |
| Side project | `projects/<slug>.md` | `templates/project.md` |
| Offer or compensation | `offers/YYYY-MM-DD_<company>.md` | `templates/offer.md` |
| Original document | `archive/<employer>/` (or `archive/general/`), linked from the record | — |
| Tax, ID, salary, signature document | `archive/private/`, unread | — |

Templates are read from the workspace's `templates/` folder. If one is missing there, use the copy in this skill's own `templates/` folder.

One item can touch two places (a manager's rating goes in `reviews/` and is linked from the matching accomplishment). Write each fact once and link to it elsewhere.

## Process

1. **Read** every item. Documents in `inbox/`: read with Docling, one at a time. Private documents: move to `archive/private/` without reading.
2. **File** each item using the table. Copy the user's facts and numbers exactly. In accomplishments only, tag a number `[estimate]`, or `[verified]` when a filed document shows it; other records carry no tags. When new data replaces an old number, replace it and keep one line noting the old value.
3. **Move originals** from `inbox/` to `archive/<employer>/` and link them.
4. **Ask** only when an item can't be filed without the answer: which employer, which job, which date. One message, three questions at most. Everything else is filed as given.
5. **Report**: one line per item with the full path it went to, then any questions.

## Scope

Records only. Add exactly the items the user gave: no new application folders, people, to-dos or calculations they didn't mention. `resumes/master-resume.md` and the files in application folders are built by other skills; this skill leaves them as they are.

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Asking for proof, files, screenshots or statistics | The user's statement is enough. File it. |
| Writing "until a document backs it" or other proof notes | Tag the number; say nothing else. |
| Asking about details the user didn't offer (vesting cliff, p-values, plans) | Store what they gave. |
| Creating records the user didn't mention | Only the items in the batch. |
| Updating the master resume or a resume draft | Leave them; mention in the report if a stored number changed. |
