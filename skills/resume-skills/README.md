# ResumeSkills

22 skills for job hunting: resumes, cover letters, application forms, interviews, salary negotiation and offers.

## Install

Install them into your career folder with the [`career` group](../../groups/README.md#career), or on their own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@33.0.0 generate --targets opencode --features skills --input-roots skills/resume-skills --output-roots ~/AI/career
```

Swap `--targets` for your tools. They aren't in `default`; never add `--global` to the command above.

## Use

Give the agent your resume (a file path or pasted text) and, where it applies, the job posting. The right skill loads from what you ask:

- "Tailor my resume in `resume.md` to this job description" (`resume-tailor`, `resume-ats-optimizer`)
- "Rewrite these bullets with measurable results" (`resume-bullet-writer`, `resume-quantifier`)
- "Write a cover letter for this role" (`cover-letter-generator`)
- "How well do I match this posting, and what's missing?" (`job-description-analyzer`)
- "Prepare me for an interview at X" (`interview-prep-generator`)
- "Compare these two offers" and "help me counter" (`offer-comparison-analyzer`, `salary-negotiation-prep`)

All 22 are in [`skills/`](skills/), one folder each.

## Notes

Upstream's README lists 20 skills; its installer also delivers `application-form-filler` and `cold-email-writer`, which are included here. The email addresses and phone numbers inside the skills (`john@email.com`, `(555) 123-4567`) are upstream's made-up examples.

## Origin

[Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), unchanged, copied 2026-10-09 from an install dated 2026-08-10. No commit was recorded; the first update check records one. [MIT](../../THIRD_PARTY_LICENSES.md#paramchoudharyresumeskills), © 2026 Resume Skills. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
