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

The reply has three parts, in this order:

1. **Result:** the full path of the master resume, the bullet count per job, and a brief list of placements for the user to review.
2. **Next steps:** the two short lists below, copied as written.
3. **Hand-off prompt:** the fenced block below, with `<WORKSPACE>` replaced by the workspace's absolute path everywhere it appears. The user pastes it into a new session along with a job posting.

Next steps:

> **Whenever your records change:** file them with `career-intake`, then ask to rebuild the master resume. Fix mistakes in the records, not in the master resume.
>
> **For each job:** paste the hand-off prompt below into a new session with the job posting. It runs `career-intake` → `job-description-analyzer` → `resume-tailor` → optional `resume-ats-optimizer` / role optimizer / `resume-formatter` → `cover-letter-generator` → `application-form-filler` + `career-work-history` → `career-intake` (file the sent resume) → `interview-coach`.

Hand-off prompt:

````text
I'm applying for a job. My career workspace is <WORKSPACE>.
My master resume, the bullet bank to choose from, is <WORKSPACE>/resumes/master-resume.md. Read it, but never edit it.

The job posting is below (or I'll paste it next). Work through these steps, stopping after each one so I can review:

1. Use career-intake to file the posting. It creates <WORKSPACE>/applications/YYYY-MM-DD_<company>_<role>/ and saves the posting as posting.md. Call that folder <APP> from now on.
2. Use job-description-analyzer on <APP>/posting.md and the master resume. Report the match, the gaps and the keywords to lead with.
3. Use resume-tailor to choose bullets, a summary and skills from the master resume for this posting. Save the result as <APP>/resume.md. Use only facts that are in the master resume.
4. Offer these optional passes on <APP>/resume.md: resume-ats-optimizer, tech-resume-optimizer or executive-resume-writer for the role type, and resume-formatter.
5. Use cover-letter-generator with <APP>/resume.md and the posting. Save the result as <APP>/cover-letter.md.
6. If there's an application form, use application-form-filler for the written answers and career-work-history for the employment section. Forms need official titles, not resume titles.
7. When I say it's sent, use career-intake to file the final resume in <WORKSPACE>/resumes/archive/ and add a row to <WORKSPACE>/resumes/versions.md.
8. For interviews, use interview-coach (prep, mock), then use career-intake to file my interview notes in <APP>/interviews.md.

If a step turns up a new accomplishment or number, file it with career-intake and tell me to rebuild the master resume.

Posting:
````
