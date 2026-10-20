# interview-coach

An interview coach covering the whole interview cycle: decoding a job posting, company and interviewer research, a prep brief for each round, a storybank of interview-ready stories, practice drills and full mock interviews, transcript analysis, same-day debriefs, outcome tracking and salary negotiation. It scores answers on five dimensions and adapts its coaching to your weak spots.

## Install

Install it into your career folder with the [`career` group](../../groups/README.md#career), or on its own. From the repo root:

```bash
mkdir -p ~/AI/career
npx rulesync@33.0.0 generate --targets opencode --features skills --input-roots skills/interview-coach --output-roots ~/AI/career
```

Swap `--targets` for your tools. It isn't in `default`; never add `--global` to the command above.

## Use

Start your tool in the folder where you keep your job-search files. The skill saves its progress to `coaching_state.md` in that folder and picks up from it next time.

- "kickoff" to set up your profile, then share your resume
- "prep [company]" before an interview, "mock" for a full mock interview
- "debrief" right after an interview, or paste a transcript and say "analyze"
- "stories" to build or drill your storybank, "negotiate" when an offer arrives

The full command list is in [`skills/interview-coach/SKILL.md`](skills/interview-coach/SKILL.md).

## Notes

Use a private job-search folder: the skill automatically saves personal coaching notes and interview history to `coaching_state.md`, including mid-session saves, and can migrate or summarize older state. Some workflows also write application drafts under `job-search/`. Keep backups if you need the original detailed history. Your tool's permissions still apply; the skill does not authorize sending messages or submitting applications.

Upstream's `.claude/settings.json` (a Claude Code permission allow-list for Read, Edit, Write, WebFetch and WebSearch) is not copied; it isn't part of the skill, and your own tool permissions apply instead. `.gitignore` isn't copied either. Everything else is unchanged.

## Origin

[noamseg/interview-coach-skill](https://github.com/noamseg/interview-coach-skill), repo root, commit `634a8dd8689e0420c21e5f0c8ae3cfa9e1a7ab7e`, copied 2026-10-19. [MIT](../../THIRD_PARTY_LICENSES.md#noamseginterview-coach-skill), © 2026 Noam Segal. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
