# Rules

How I want all AI agents to behave, split into topics you can install separately. Written for this repo.

| Folder                     | Rule                                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| `shell-preamble/`          | Explain every shell command that isn't a plain read before running it. Installed first       |
| `scope-secrets-approvals/` | Where to work, what never to touch, what to ask before doing                                 |
| `engineering/`             | Inspect first, keep changes small, use `sd` for replacements, verify before claiming success |
| `communication/`           | State assumptions and summarize at the end                                                   |
| `routing/`                 | Which skill, command or tool owns each job when several could do it                          |
| `preferences/`             | Your preferences: vim, fish, pnpm/uv, zellij, firefox, ISO dates, US spelling                |
| `shell-preamble-reminder/` | Repeat the preamble check at the end of the installed rules. Installed last                  |

## Install

rulesync installs rules by **replacing your tool's whole instructions file**, so pick every topic you want at once. Add them to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../README.md#install)), keeping `rules/shell-preamble` first and `rules/shell-preamble-reminder` last, then run your install command with `--features rules`. For example:

```jsonc
{
  "inputRoots": ["rules/shell-preamble", "rules/scope-secrets-approvals", "rules/engineering", "rules/communication", "rules/shell-preamble-reminder"]
}
```

Every rule installs into the same file (`~/.config/opencode/AGENTS.md`, `~/.claude/CLAUDE.md` and so on), in the order listed.

## Notes

- The secure-coding rule moved into the repo-owned [`agents/security`](../agents/security/) bundle. It is based on OpenSSF's [Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) (2025).
- `routing/` replaced the one-line rules that used to live in skill folders (`diagram-design`, `frontend-slides`, `visual-explainer`, `theme-factory`, `humanizer`). Several skills claimed the same jobs, so one rule now names the owner of each job. If a named skill isn't installed, the rule tells the agent to use the closest one that is.
- `preferences/` covers commands and instructions the agent hands to you. The agent's own shell tool may still run bash.

## For agents: maintaining these rules

- **Routing** (`routing/`): the single source for which skill owns which job, chosen by the user on October 21, 2026. Don't add per-skill routing rules back, and don't edit upstream skills to change routing. When a skill is added, removed or refreshed and its description now overlaps another owner's job, update this rule and the skill's README "For agents: routing and updates" section together, and tell the user.
- **Preferences** (`preferences/`): the user's stated preferences. Add to it only what the user asks for.
- **Order**: `shell-preamble` first and `shell-preamble-reminder` last in every group; the other rules sit between them in the order listed in `rulesync.jsonc`.
