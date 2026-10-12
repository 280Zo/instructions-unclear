# House rules

Rules, skills and agents that aren't tied to one tool.

| File | Becomes | Origin |
|---|---|---|
| `rules/00-shell-preamble.md` | "RULE 0 — Shell Preamble", first in `AGENTS.md` | Me |
| `rules/10-working-policy.md` | "OpenCode Working Policy" | Me |
| `rules/20-servers-off-by-default.md` | "Servers that are off by default" | Me |
| `rules/30-package-management.md` | "Package & Tool Management" | Me |
| `skills/report/` | Skill `report` | Me |
| `skills/eli5/` | Skill `eli5` | Me |
| `skills/package-management/` | Skill `package-management` | **Origin unknown.** No public source was found. Not covered by this repo's MIT license |
| `subagents/course-corrector.md` | Agent `course-corrector` (primary) | Me |
| `subagents/evaluator.md` | Agent `evaluator` (subagent) | Me |
| `subagents/metacognitive.md` | Agent `metacognitive` (subagent) | Me |

The agent files use rulesync's format: a `name`, `targets`, and OpenCode-only settings under `opencode:`. The generated files in `~/.config/opencode/agents/` are plain OpenCode agents.

`report` and `eli5` also carry an `allowed-tools` field that only Claude Code uses. It sits under a `claudecode:` section in their headers, so rulesync writes it for Claude Code and leaves it out for OpenCode.
