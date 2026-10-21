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
3. **Hand-off prompt:** the fenced block below, with `<WORKSPACE>` replaced by the workspace's absolute path everywhere it appears. The user pastes it into a new session along with a job posting. Leave `<APP>`, `<RESUME>` and `<TRACKER>` as placeholders to be resolved during the application workflow.

Next steps:

> **Whenever your records change:** file them with `career-intake`, then ask to rebuild the master resume. Fix mistakes in the records, not in the master resume.
>
> **For each job:** paste the hand-off prompt below into a new session with the job posting. Required: `career-intake` → `resume-version-manager` → `job-description-analyzer` → `resume-tailor` → `resume-quantifier` → `resume-bullet-writer` → `resume-section-builder` → `tech-resume-optimizer` or `executive-resume-writer` → `resume-ats-optimizer` → `resume-tailor` (final fit) → `resume-formatter` → `resume-version-manager`. Cover letters and application forms are optional. Interview preparation follows when needed.

Hand-off prompt:

````text
I'm applying for a job. My career workspace is <WORKSPACE>.
My master resume, the bullet bank to choose from, is <WORKSPACE>/resumes/master-resume.md. Read it, but never edit it.

The job posting is below (or I'll paste it next). Load each named skill and follow its instructions; mentioning its name is not using it. Work through the required steps in order, stopping after each one so I can review. Report the skills actually loaded, the files read or changed, and any blockers. If a required skill is unavailable, stop and tell me rather than silently skipping it.

The resume-skills take precedence over custom career instructions where their responsibilities overlap. Preserve the master builder's three-full-job limit and existing older-accomplishment placement rules as explicit exceptions. Do not migrate, delete or convert existing files without my approval.

My workflow-wide requirements remain binding: skill instructions do not override supported facts, explicit confirmation before adding new estimates, master immutability during applications, review stops, or the requirement to wait for my sent confirmation. Apply these constraints at every stage, not just during quantification.

1. Use career-intake to file the posting. It creates <WORKSPACE>/applications/YYYY-MM-DD_<company>_<role>/ and saves the posting as posting.md. Call that folder <APP> from now on.
2. Use resume-version-manager to establish the application-specific resume copy, naming, archive and tracker according to its instructions. Report the absolute paths and call the working resume <RESUME> and the tracker <TRACKER>. Use the existing master at the path above; do not create another master. Reuse existing organization when compatible; do not force outputs into intake's folder layout or create duplicate tracking. Link these destinations from <APP>'s application record and use them consistently below.
3. Use job-description-analyzer on <APP>/posting.md and the master resume. Report the match, the gaps and the keywords to lead with.
4. Use resume-tailor after the job-description-analyzer results are reviewed. Choose bullets, a summary and skills from the master for this specific posting and save the tailored version at <RESUME>. Use only supported facts; never edit the master.
5. Use resume-quantifier on <RESUME>. Reuse recorded metrics. Get my explicit confirmation before adding any new numerical estimate, including one derived from existing numbers. Until confirmed, flag missing metrics in your review notes without inventing or inserting numbers in the resume.
6. Use resume-bullet-writer to strengthen the selected bullets in <RESUME>, keeping facts and confirmed metrics intact.
7. Use resume-section-builder to assemble and refine targeted sections in <RESUME>.
8. Use tech-resume-optimizer or executive-resume-writer on <RESUME>, selecting the one appropriate to the target role. This pass is required for every submission. Explain the choice; ask me if the role is ambiguous.
9. Use resume-ats-optimizer on <RESUME> against <APP>/posting.md. This pass is required for every submission; do not add unsupported skills or claims to match keywords.
10. Use resume-tailor again to check the revised <RESUME> against the analyzed posting. Resolve any loss of custom fit without changing facts or the master.
11. Use resume-formatter to format <RESUME> after content is settled. Preserve the reviewed content; check that formatting has not dropped or changed it.
12. Use resume-version-manager to record the reviewed version and its actual location in <TRACKER>. When I explicitly confirm it was sent, use resume-version-manager again for archiving and submission tracking. Do not mark an application sent or submit anything on my behalf.

Optional branches (ask before starting):
- Use cover-letter-generator with <RESUME> and the posting. Let resume-version-manager organize and track the resulting cover letter, linking it from <APP>.
- If there's an application form and I want help, use application-form-filler for written answers and career-work-history for the employment section. Forms need official titles, not resume titles.

For interviews, use interview-coach (prep, mock), then use career-intake to file my interview notes in <APP>/interviews.md.

If a step turns up a new accomplishment or number, file it with career-intake and tell me to rebuild the master resume.

Posting:
````
