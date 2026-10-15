# Career skills

22 skills for job hunting: resumes, cover letters, application forms, interviews, salary negotiation and offers.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/careers
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/careers` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Give the agent your resume (a file path or pasted text) and, where it applies, the job posting. The right skill loads from what you ask:

- "Tailor my resume in `resume.md` to this job description" (`resume-tailor`, `resume-ats-optimizer`)
- "Rewrite these bullets with measurable results" (`resume-bullet-writer`, `resume-quantifier`)
- "Write a cover letter for this role" (`cover-letter-generator`)
- "How well do I match this posting, and what's missing?" (`job-description-analyzer`)
- "Prepare me for an interview at X" (`interview-prep-generator`)
- "Compare these two offers" and "help me counter" (`offer-comparison-analyzer`, `salary-negotiation-prep`)

The full list of 22 is in the [root README's credits](../../README.md#credits).

## Notes

Upstream's README lists 20 skills; its installer also delivers `application-form-filler` and `cold-email-writer`, which are included here. The email addresses and phone numbers inside the skills (`john@email.com`, `(555) 123-4567`) are upstream's made-up examples.

## Origin

[Paramchoudhary/ResumeSkills](https://github.com/Paramchoudhary/ResumeSkills), unchanged, copied 2026-10-09 from an install dated 2026-08-10. No commit was recorded; the first update check records one. [MIT](../../THIRD_PARTY_LICENSES.md#paramchoudharyresumeskills), © 2026 Resume Skills. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
