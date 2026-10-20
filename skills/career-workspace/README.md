# career-workspace

Three skills that keep a personal career record in one folder and build from it: file new career data, build a master resume, and produce an official work history for forms.

| Skill | What it does |
|---|---|
| `career-intake` | Files wins, numbers, skills, reviews, people, applications, offers and documents into the right workspace file, in your words |
| `career-master-resume` | Builds `resumes/master-resume.md`, the bullet bank the [`resume-skills`](../resume-skills/) choose from, and hands you a prompt for the next step |
| `career-work-history` | Lists every employer with official titles, dates, locations and managers for applications and background checks |

## Workflow

**Setup, repeated whenever your records change:**

1. File your records with `career-intake`.
2. Ask it to "rebuild my master resume" (`career-master-resume`). If something in it is wrong, fix the record and rebuild rather than editing the master resume.

**For each job:**

1. Give `career-intake` the posting. It creates an application folder and saves the posting in it.
2. Run `job-description-analyzer` on the posting and `resumes/master-resume.md` to get the match, the gaps and the keywords.
3. Run `resume-tailor` on the master and have it save `applications/<folder>/resume.md`. It should never edit the master.
4. Optionally run `resume-ats-optimizer`, a role-specific optimizer, or `resume-formatter` on that file.
5. Write the cover letter with `cover-letter-generator`.
6. For forms, use `application-form-filler` for the written answers and `career-work-history` for the employment section, which uses official titles rather than resume titles.
7. File the resume you sent back through `career-intake` so it's archived and logged in `resumes/versions.md`.
8. Prepare for interviews with [`interview-coach`](../interview-coach/), then file your interview notes with `career-intake`.

You don't have to type the per-job steps yourself. Each time `career-master-resume` finishes, it ends its reply with a **hand-off prompt** that has your workspace paths filled in. Paste that prompt into a new session, add the job posting, and the agent works through steps 1 to 8, stopping after each one for your review.

The master resume uses the structure `resume-version-manager` defines (every bullet, several summaries, all skills, keywords per job), which the other resume skills work from. The resume skills don't know this workspace's layout, which is why the hand-off prompt names every file.

## Install

Install them into your career folder with the [`career` group](../../groups/README.md#career), or on their own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@33.0.0 generate --targets opencode --features skills --input-roots skills/career-workspace --output-roots ~/AI/career
```

Never add `--global`: the skills read paths relative to the folder you start your tool in. The workflow also needs [`resume-skills`](../resume-skills/) and [`interview-coach`](../interview-coach/); the `career` group installs all three folders.

## Workspace layout

All paths are relative to the career folder. Create the folders you need; the skills write into them.

```text
profile/          contact.md, work-history.md, skills.md, certifications.md, education.md, awards.md
accomplishments/  <employer>.md
reviews/          <employer>.md
people/           <slug>.md
references/       letters, plus index.md
applications/     YYYY-MM-DD_<company>_<role>/ (posting.md, resume.md, cover-letter.md, interviews.md)
offers/           YYYY-MM-DD_<company>.md
projects/         <slug>.md
study/            <topic>.md
resumes/          master-resume.md, versions.md, archive/
inbox/            drop documents here for intake
archive/          originals by employer; archive/private/ is never read
templates/        optional; career-intake falls back to its own copies
```

`profile/work-history.md` needs an **Official title** column (used for forms) and a **Resume title** column (used for resumes), with `present` as the end date of the current job. A Notes section below the table records conflicting dates or titles.

The seven record templates ship in [`skills/career-intake/templates/`](skills/career-intake/templates/). Copy them into the workspace's `templates/` to customize them.

## Example requests

- "Log this: cut deploy time from 40 to 12 minutes at Acme" or "ingest the inbox" → `career-intake`
- "Rebuild my master resume" → `career-master-resume`
- "Give me my full work history for this background check" → `career-work-history`

Intake reads documents with Docling when it's available. If an interview or offer turns up a new win or number, file it with `career-intake` and rebuild the master resume so the next application has it.

## Origin

Written for this repo. [MIT](../../LICENSE).
