---
name: career-intake
description: 'Use when a user gives career data to store, one item or a batch: a win, a note, numbers, a skill, an offer, a review, a person, a project, or documents dropped in inbox/, or when they want to set up a new career workspace. Triggers include "log this", "add this", "file these", "ingest", "remember this for my resume", "set up my career folder".'
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
| Resume file | Use `resume-version-manager` for organization, archiving and tracking; link its chosen location from the application record | — |
| Study material | `study/<topic>.md` | — |
| Side project | `projects/<slug>.md` | `templates/project.md` |
| Offer or compensation | `offers/YYYY-MM-DD_<company>.md` | `templates/offer.md` |
| Original document | `archive/<employer>/` (or `archive/general/`), linked from the record | — |
| Tax, ID, salary, signature document | `archive/private/`, unread | — |

Templates are read from the workspace's `templates/` folder, which Setup fills from this skill's own `templates/` folder.

One item can touch two places (a manager's rating goes in `reviews/` and is linked from the matching accomplishment). Write each fact once and link to it elsewhere.

## Setup

At the start of every run, create whatever is missing; never overwrite an existing file:

- Folders: `profile/`, `accomplishments/`, `reviews/`, `people/`, `references/`, `applications/`, `offers/`, `projects/`, `study/`, `resumes/`, `inbox/`, `archive/private/`, `templates/`.
- `templates/`: each file from this skill's own `templates/` folder that isn't there yet.
- `profile/work-history.md`: this table header, followed by an empty `## Notes` section:

  ```markdown
  | Employer | Official title | Resume title | Start | End | Location | Manager |
  | --- | --- | --- | --- | --- | --- | --- |
  ```

If the user only asked to set up, report what was created and tell them to drop documents in `inbox/` and say "ingest the inbox".

## Process

1. **Read** every item. Documents in `inbox/`: read with Docling, one at a time. Private documents: move to `archive/private/` without reading.
2. **File** each item using the table. Copy the user's facts and numbers exactly. In accomplishments only, tag a number `[estimate]`, or `[verified]` when a filed document shows it; other records carry no tags. When new data replaces an old number, replace it and keep one line noting the old value.
3. **Move originals** from `inbox/` to `archive/<employer>/` and link them.
4. **Ask** only when an item can't be filed without the answer: which employer, which job, which date. One message, three questions at most. Everything else is filed as given.
5. **Report**: one line naming any folders or files Setup created, then one line per item with the full path it went to, then any questions.

## Scope

Records only. Apart from Setup, add exactly the items the user gave: no new application folders, people, to-dos or calculations they didn't mention. `resumes/master-resume.md` and resume/application drafts are built by other skills; this skill leaves them as they are. Filing a posting or interview notes is intake's job. Resume organization, archiving, versions and application tracking belong to `resume-version-manager`: load it for resume-file requests instead of creating a second tracker. Intake's application record holds source material and links to its outputs, not a separate submission history. Follow the resume-skills where responsibilities overlap; the master builder's explicit three-job and older-accomplishment placement rules remain exceptions. Preserve existing files and links; do not migrate, delete or convert them without the user's approval.

## Common mistakes

| Mistake | Instead |
| --- | --- |
| Asking for proof, files, screenshots or statistics | The user's statement is enough. File it. |
| Writing "until a document backs it" or other proof notes | Tag the number; say nothing else. |
| Asking about details the user didn't offer (vesting cliff, p-values, plans) | Store what they gave. |
| Creating records the user didn't mention | Only the items in the batch. |
| Updating the master resume or a resume draft | Leave them; mention in the report if a stored number changed. |
