# career-workspace

Four skills that keep a personal career record in one folder: file new career data, build a master resume, start a job application, and produce an official work history for forms.

| Skill | What it does |
|---|---|
| `career-intake` | Files wins, numbers, skills, reviews, people, applications, offers and documents into the right workspace file, in your words |
| `career-master-resume` | Builds `resumes/master-resume.md`, the bullet bank the [`resume-skills`](../resume-skills/) choose from |
| `career-start-application` | Starts the application workflow from the existing master; asks for a job link, coordinates required passes and stops at eight review stages |
| `career-work-history` | Lists every employer with official titles, dates, locations and managers for applications and background checks |

## Workflow

**First run:** start your tool in your career folder and say "set up my career folder" (`career-intake`). It creates the folders below, copies the templates and starts `profile/work-history.md`. Then drop resumes, reviews and other documents in `inbox/` and say "ingest the inbox". Any later intake run also adds whatever is missing, and never overwrites a file.

**Setup, repeated whenever your records change:**

1. File your records with `career-intake`.
2. Ask it to "rebuild my master resume" (`career-master-resume`). If something in it is wrong, fix the record and rebuild rather than editing the master resume.

**For each job:**

Say **“Use career-start-application.”** It loads the kickoff instructions and asks for the job-posting link if you haven't supplied one. You can paste the posting instead. Start your tool in the career workspace, or identify its path if it isn't clear. No copied prompt or master rebuild is needed.

The starter coordinates these eight review stages:

| Stage | Skills and result |
|---|---|
| 1. Posting and destinations | `career-intake` preserves the posting/source/date; `resume-version-manager` establishes working files and tracker, linked from the application record |
| 2. Evidence analysis | `job-description-analyzer` maps responsibilities and minimum qualifications to demonstrated, related or unknown evidence |
| 3. Tailored draft | `resume-tailor` → `resume-quantifier` → `resume-bullet-writer` → `resume-section-builder`; select, merge and rewrite supported facts within a two-page budget |
| 4. Reviewed submission files | Required `tech-resume-optimizer` or `executive-resume-writer` → required `resume-ats-optimizer` → `resume-tailor` final fit → `resume-formatter`; document skills export DOCX/PDF and verify rendering; `resume-version-manager` records the reviewed version, not a submission |
| 5. Cover letter, if wanted | `cover-letter-generator`, organized/tracked by version-manager |
| 6. Actual form, if wanted | `application-form-filler` and `career-work-history` after you have the resume and can see the form; official titles for employment fields |
| 7. Sent confirmation | Only after you say it was sent, `resume-version-manager` archives the exact sent files and records the submission |
| 8. Interviews, when needed | [`interview-coach`](../interview-coach/) prepares/practices; `career-intake` files your notes |

The agent stops after each stage for review, not after every routine editing pass. It reports the skills actually loaded, files used and any blockers. A missing required skill stops the workflow rather than being silently skipped. These are agent instructions, not a deterministic automation guarantee or a registered slash command.

Selection and evidence notes stay in the application folder, outside submitted files. The workflow preserves uncertainty, pilot versus production status, target versus measured results, and component versus program-wide scope. Keyword coverage is not an ATS test or proof of eligibility. Document checks cover actual rendered page count, readability, embedded PDF fonts and text extraction; missing tools/checks must be disclosed, not passed off as successful validation.

### Ownership and precedence

The resume-skills take precedence where responsibilities overlap. `resume-version-manager` owns resume organization, naming, archiving, versions and application tracking; intake does not maintain a competing tracker or dictate those output paths. Its application record stores the posting and interview notes, with links to version-manager's outputs and tracker.

Your workflow-wide requirements stay binding across every skill: supported facts, confirmation before new estimates (including calculated ones), an untouched master during applications, review stops, and explicit confirmation before recording a submission as sent. New facts are filed through intake and incorporated only after a separately approved master update.

Later passes read the reviewed draft and selection notes, inherit evidence decisions and agreed length/summary budgets, and check for drift before handing off. Specialist defaults and keyword scores do not justify restoring weaker excluded material or replacing stronger evidence. Factual corrections and better-supported role fit remain allowed, with material changes explained in the notes and at the existing review stop—not extra approval rounds. Only you can change the agreed length budget.

`career-master-resume` assembles source records into the master structure defined by `resume-version-manager`. Its three-full-job limit and existing older-accomplishment placement rules remain explicit exceptions to resume-skills precedence. The application workflow reads the master without editing it or creating another master.

Existing files are preserved. This change does not move, delete or convert earlier archives or tracking files; any migration needs your approval. All upstream files under `skills/resume-skills/` are unchanged.

## Install

Install them into your career folder with the [`career` group](../../groups/README.md#career), or on their own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@41.0.0 generate --targets opencode --features skills --input-roots skills/career-workspace --output-roots ~/AI/career
```

Never add `--global` to this command: the skills read paths relative to the folder you start your tool in. The workflow also needs [`resume-skills`](../resume-skills/) and [`interview-coach`](../interview-coach/); the `career` group installs all three folders.

In OpenCode, the `default` group installs all three folders and the career routing rule globally for the [`career` agent](../../agents/career/), the only agent that loads these skills. Start OpenCode in your career folder so records land there.

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
- "Use career-start-application" → asks for the job link and starts the reviewed application workflow
- "Give me my full work history for this background check" → `career-work-history`

Intake reads documents with Docling when it's available. If an interview or offer turns up a new win or number, file it with `career-intake` and rebuild the master resume so the next application has it.

## For agents: install, remove and update

### Install

- For tools other than OpenCode, this folder installs into a career folder, never the home folder. The [`career` group](../../groups/README.md#career) installs it with `resume-skills` and `interview-coach`, run with `--output-roots` into a folder the user picks (suggest `~/AI/career`). Never add `--global` to that command. OpenCode's `default` group installs it globally behind the `career` agent's permissions; the user still starts OpenCode in the career folder.
- The single-folder command under [Install](#install) uses `--features skills`, so it skips `rules/career-routing.md`. The workflow still needs `resume-skills` and `interview-coach`, so prefer the group.
- Docling is optional; intake uses it for documents when it's available. Document export in stage 4 relies on document skills and their own runtimes, which rulesync doesn't install.
- To verify, start the tool in the career folder and confirm the skills list includes `career-intake` and `career-start-application`, and that the folder's `AGENTS.md` contains the career routing rule. Don't run intake as a test unless the user wants the workspace folders created.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component), working inside the career folder (`.opencode/skills/` and so on), not the home folder.

- `delete: false` leaves `career-intake`, `career-master-resume`, `career-start-application` and `career-work-history` behind; delete them only with approval. Leave the `resume-skills` and `interview-coach` skills alone unless the user is removing those too.
- The career routing rule goes away when the folder's `AGENTS.md` is regenerated without this folder. This is the only folder in the `career` group with rules, so regeneration may leave the old file in place. Check it, and if it holds only the career routing rule, delete it with approval.
- Never delete the career folder itself or anything the skills created: `profile/`, `accomplishments/`, `reviews/`, `people/`, `references/`, `applications/`, `offers/`, `projects/`, `study/`, `resumes/`, `inbox/`, `archive/`, `templates/` and the files `resume-version-manager` keeps. They are the user's career records and stay unless the user explicitly asks.

### Update

This folder is written for this repo, so there is no upstream to check. When changing it, follow the reconciliation steps in the routing section below, then regenerate the `career` group into the career folder. For `resume-skills` and `interview-coach`, follow [Check for updates](../../AGENTS.md#check-for-updates) and their own READMEs.

## For agents: routing and updates

`career-start-application` owns starting an application, not building the master.
`career-master-resume` owns the bullet bank; `career-work-history` owns official
employment fields. That routing lives in this folder's
[`rules/career-routing.md`](rules/career-routing.md), which the career group
installs into the career folder's own `AGENTS.md`. It lives here rather than in
the global `rules/routing`, so it installs only where these skills do.
The starter also keeps its own required-skill contract, so it still works when
the skills are installed without the rule.

When updating this workflow, reconcile the starter, builder hand-off and README
together. Preserve required resume passes, version-manager ownership and factual
gates; do not edit upstream resume-skills to adapt routing. Check career group
counts and generate the changed group into an isolated folder.

## Origin

Written for this repo by 280Zo. [MIT](../../LICENSE), © 2026 280Zo.
