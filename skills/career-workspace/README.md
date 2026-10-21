# career-workspace

Three skills that keep a personal career record in one folder and build from it: file new career data, build a master resume, and produce an official work history for forms.

| Skill | What it does |
|---|---|
| `career-intake` | Files wins, numbers, skills, reviews, people, applications, offers and documents into the right workspace file, in your words |
| `career-master-resume` | Builds `resumes/master-resume.md`, the bullet bank the [`resume-skills`](../resume-skills/) choose from, and hands you a prompt for the next step |
| `career-work-history` | Lists every employer with official titles, dates, locations and managers for applications and background checks |

## Workflow

**First run:** start your tool in your career folder and say "set up my career folder" (`career-intake`). It creates the folders below, copies the templates and starts `profile/work-history.md`. Then drop resumes, reviews and other documents in `inbox/` and say "ingest the inbox". Any later intake run also adds whatever is missing, and never overwrites a file.

**Setup, repeated whenever your records change:**

1. File your records with `career-intake`.
2. Ask it to "rebuild my master resume" (`career-master-resume`). If something in it is wrong, fix the record and rebuild rather than editing the master resume.

**For each job:**

1. Give `career-intake` the posting. It creates an application folder and saves the posting in it.
2. Use `resume-version-manager` to establish the application-specific resume copy, naming, archive and application tracker. Report the actual paths and link them from the intake application record; use those paths throughout.
3. Run `job-description-analyzer` on the posting and `resumes/master-resume.md` to get the match, the gaps and the keywords.
4. Run `resume-tailor` using that analysis to create a custom fit for the posting. Save to the working resume path chosen above; never edit the master.
5. Run `resume-quantifier`. New estimates, including calculated ones, require your explicit confirmation before inclusion. Otherwise report missing metrics without inserting invented numbers.
6. Run `resume-bullet-writer` to strengthen the selected bullets while preserving facts and confirmed metrics.
7. Run `resume-section-builder` to assemble and refine targeted sections.
8. Run **`tech-resume-optimizer` or `executive-resume-writer`** for the target role. One is required on every submission; the agent explains its choice and asks if the role is ambiguous.
9. Run **`resume-ats-optimizer`** against the posting. Required on every submission; no unsupported claims or skills for keyword matching.
10. Run `resume-tailor` again for a final custom-fit check after the content passes.
11. Run `resume-formatter` after the content is settled, checking that formatting preserves it.
12. Use `resume-version-manager` to record the reviewed version. Once you confirm it was sent, it handles archiving and submission tracking too. Nothing is submitted on your behalf.

**Optional:** ask for `cover-letter-generator` to write a cover letter, or `application-form-filler` for form answers with `career-work-history` for official employment details. Version-manager organizes and tracks any resulting cover letter. For interviews, use [`interview-coach`](../interview-coach/), then file your interview notes with `career-intake`.

You don't have to type the per-job steps yourself. Each time `career-master-resume` finishes, it ends its reply with a **hand-off prompt** that has your workspace paths filled in. Paste it into a new session with the posting. It instructs the agent to load each required skill, report the skills actually loaded and files used, and stop after each stage for your review. If a required skill is missing, the agent must stop rather than skip it. These are instructions to the agent, not an automated execution guarantee.

### Ownership and precedence

The resume-skills take precedence where responsibilities overlap. `resume-version-manager` owns resume organization, naming, archiving, versions and application tracking; intake does not maintain a competing tracker or dictate those output paths. Its application record stores the posting and interview notes, with links to version-manager's outputs and tracker.

Your workflow-wide requirements stay binding across every skill: supported facts, confirmation before new estimates, an untouched master during applications, review stops, and explicit confirmation before recording a submission as sent.

`career-master-resume` assembles source records into the master structure defined by `resume-version-manager`. Its three-full-job limit and existing older-accomplishment placement rules remain explicit exceptions to resume-skills precedence. The application workflow reads the master without editing it or creating another master.

Existing files are preserved. This change does not move, delete or convert earlier archives or tracking files; any migration needs your approval. All upstream files under `skills/resume-skills/` are unchanged.

## Install

Install them into your career folder with the [`career` group](../../groups/README.md#career), or on their own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@38.0.0 generate --targets opencode --features skills --input-roots skills/career-workspace --output-roots ~/AI/career
```

Never add `--global`: the skills read paths relative to the folder you start your tool in. The workflow also needs [`resume-skills`](../resume-skills/) and [`interview-coach`](../interview-coach/); the `career` group installs all three folders.

## Workspace layout

All paths are relative to the career folder. `career-intake` creates the folders and `templates/` on any run where they're missing.

```text
profile/          contact.md, work-history.md, skills.md, certifications.md, education.md, awards.md
accomplishments/  <employer>.md
reviews/          <employer>.md
people/           <slug>.md
references/       letters, plus index.md
applications/     YYYY-MM-DD_<company>_<role>/ (posting.md, interviews.md, record with links)
offers/           YYYY-MM-DD_<company>.md
projects/         <slug>.md
study/            <topic>.md
resumes/          master-resume.md
inbox/            drop documents here for intake
archive/          originals by employer; archive/private/ is never read
templates/        record templates, copied from career-intake; edit them freely
```

`profile/work-history.md` starts with an **Official title** column (used for forms) and a **Resume title** column (used for resumes). Put `present` as the end date of the current job. The Notes section below the table records conflicting dates or titles.

Tailored resumes, cover letters, archives and the application tracker use the destinations established by `resume-version-manager`, linked from the application record rather than fixed by this layout.

The seven record templates ship in [`skills/career-intake/templates/`](skills/career-intake/templates/). Intake copies only missing ones, so your edits to the workspace copies are kept.

## Example requests

- "Log this: cut deploy time from 40 to 12 minutes at Acme" or "ingest the inbox" → `career-intake`
- "Rebuild my master resume" → `career-master-resume`
- "Give me my full work history for this background check" → `career-work-history`

Intake reads documents with Docling when it's available. If an interview or offer turns up a new win or number, file it with `career-intake` and rebuild the master resume so the next application has it.

## Origin

Written for this repo. [MIT](../../LICENSE).
