---
name: career-master-resume
description: Use when a user asks to draft, build, rebuild or refresh their master resume (resumes/master-resume.md), or when career records changed and the master resume is out of date.
---

# Career master resume

## Overview

Draft `resumes/master-resume.md`: the bullet bank the resume skills choose from. It shows the user's current job and the two jobs before it in full. Older accomplishments join the bullet banks of those two previous jobs; older employers appear on one line only. All paths are relative to the user's career workspace.

## Sources

- `profile/contact.md`, `profile/education.md`, `profile/certifications.md`
- `profile/work-history.md`: employers, dates, locations; titles from the **Resume title** column
- `profile/skills.md`: only rows explicitly confirmed as hands-on by the user, marked `hands-on (user-confirmed …)` or with another confirmation marker the user wrote.
- `accomplishments/<employer>.md`, `profile/awards.md`, `projects/`

## Rules

1. **Jobs shown in full:** the current job (the `present` row) and the two most recent jobs before it.
2. **Older relevant jobs:** one line, no bullets: `**Earlier experience:** <Employer>, <Employer>, <Employer> (<first year>–<last year>)`. Jobs before the user's target career are left out.
3. **Older accomplishments:** place each worthwhile older accomplishment under whichever of the two previous jobs fits its tools, domain or responsibilities better. Never place older work under the current job. Use normal accomplishment bullets, without an original-employer label, relocation note or separate earlier-achievements section. Preserve the real employer and dates in the private records unchanged.
4. **Numbers:** use every number in the records, whatever its tag. Skip only items the records say the user told not to use.
5. **Bullets in final form:** action verb, what, number, result. One accomplishment per bullet.

## Output

Follow `resume-version-manager`'s master resume structure, in this order: CONTACT INFORMATION; PROFESSIONAL SUMMARY VERSIONS (3–4, by role type, covering the whole career); ALL SKILLS (technical, soft, industry); PROFESSIONAL EXPERIENCE (each of the three jobs as `### Employer | Resume title | City | Mon YYYY - Mon YYYY` with **All Bullets** and **Keywords this experience covers**, then the Earlier experience line); EDUCATION; CERTIFICATIONS; PROJECTS. Preserve the user's manual edits; reconcile the existing draft before replacing it.

## Completion check

- Exactly three full job entries, determined from work history rather than hard-coded employer names.
- Current-job bullets contain only that job's work. Older accomplishments are in either previous job's bullet bank.
- Older employers have one Earlier experience line and no separate bullet bank.
- Contact, titles, dates and numbers retained; private records unchanged.

## Reply

The reply has two parts, in this order:

1. **Result:** the full path of the master resume, the bullet count per job, and a brief list of placements for the user to review.
2. **Next steps:** the two instructions below. Include the workspace's absolute
   path so the user can identify it in a new session.

Next steps:

> **Whenever your records change:** file them with `career-intake`, then ask to rebuild the master resume. Fix mistakes in the records, not in the master resume.
>
> **For each job:** say “Use career-start-application” in your career workspace.
> It loads the application workflow and asks for the job-posting link; you can
> paste the posting instead. It reads the existing master without editing or
> rebuilding it and stops after each application stage for your review. No
> copied hand-off prompt is needed. Starting an application is separate from
> rebuilding the master; do not start it automatically after this builder finishes.
