# ResumeSkills

22 skills for job hunting: resumes, cover letters, application forms, interviews, salary negotiation and offers.

## Install

Install them into your career folder with the [`career` group](../../groups/README.md#career), or on their own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@41.0.0 generate --targets opencode --features skills --input-roots skills/resume-skills --output-roots ~/AI/career
```

Swap `--targets` for your tools. Never add `--global` to the command above. In OpenCode, `default` installs them globally for the [`career` agent](../../agents/career/), the only agent that loads them.

## Use

Give the agent your resume (a file path or pasted text) and, where it applies, the job posting. The right skill loads from what you ask:

- "Tailor my resume in `resume.md` to this job description" (`resume-tailor`, `resume-ats-optimizer`)
- "Rewrite these bullets with measurable results" (`resume-bullet-writer`, `resume-quantifier`)
- "Write a cover letter for this role" (`cover-letter-generator`)
- "How well do I match this posting, and what's missing?" (`job-description-analyzer`)
- "Give me a one-page prep sheet for an interview at X" (`interview-prep-generator`). Coached prep, practice and mock interviews go to [`interview-coach`](../interview-coach/), as set in `skills/career-workspace/rules/career-routing.md`.
- "Compare these two offers" and "help me counter" (`offer-comparison-analyzer`, `salary-negotiation-prep`)

All 22 are in [`skills/`](skills/), one folder each.

## Notes

Upstream's README lists 20 skills; its installer also delivers `application-form-filler` and `cold-email-writer`, which are included here. The email addresses and phone numbers inside the skills (`john@email.com`, `(555) 123-4567`) are upstream's made-up examples.

## For agents: install, remove and update

To install, use the [`career` group](../../groups/README.md#career) or the folder command above, into a folder the user picks; never with `--global`. They need no other software. To verify, start the tool in that folder and check that the 22 skills, such as `resume-tailor`, are listed.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves all 22 skill folders inside the career folder (for example `.opencode/skills/`), one per directory name in [`skills/`](skills/); delete them with approval, and keep any name another installed folder also provides. Resumes, cover letters and other files the skills wrote are the user's and stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). No commit was recorded yet (see [Origin](#origin)); the first check records one.

## Origin

[Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), unchanged, copied 2026-10-09 from an install dated 2026-08-10. No commit was recorded; the first update check records one. [MIT](../../THIRD_PARTY_LICENSES.md#paramchoudharyresumeskills), © 2026 Resume Skills. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
