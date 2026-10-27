# Rules

How I want all AI agents to behave, split into topics you can install separately. Written for this repo.

| Folder                     | Rule                                                                                         |
| -------------------------- | -------------------------------------------------------------------------------------------- |
| `shell-preamble/`          | Explain every shell command that isn't a plain read before running it. Installed first       |
| `scope-secrets-approvals/` | Where to work, what never to touch, what to ask before doing                                 |
| `engineering/`             | Inspect first, keep changes small, use `sd` for replacements, verify before claiming success |
| `communication/`           | State assumptions and summarize at the end                                                   |
| `routing/`                 | Which skill owns each job when several installed skills could do it                          |
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

## For agents: install, remove and update

Install. The `default`, `work` and `writing_reporting` home-folder groups include all seven rule folders in the right order; see [`groups/README.md`](../groups/README.md). For a custom set, follow [Install](#install). Rules need no programs. The preamble and its reminder work as a pair, so warn the user before leaving one of them out. To verify, ask the user to open the installed instructions file (for OpenCode, `~/.config/opencode/AGENTS.md`) and check that it starts with the shell preamble and ends with its reminder.

Remove. Drop the rule folders from `inputRoots` in the user's `rulesync.local.jsonc` (or pick a group without them), keeping `rules/shell-preamble` first and `rules/shell-preamble-reminder` last, then regenerate with `rules` in `--features`. Every run replaces the whole instructions file, so removed rules disappear and leave no files behind. A run without `rules` in `--features` leaves the old file as it was. See [Removing or replacing a component](../AGENTS.md#removing-or-replacing-a-component).

Update. These rules are written for this repo, so there is no upstream or pin to check. Edit the rule file, keep `root: true`, `targets: ["*"]` and the `description`, and regenerate. The rulesync version pin is covered by [Check for updates](../AGENTS.md#check-for-updates). Routing changes follow the next section.

## For agents: maintaining these rules

- **Routing** (`routing/`): which globally installed skill owns which job. It loads on every request, so it lists only real conflicts between installed skills; it leaves out duplicates of other rules, skills that don't compete and user-invoked skills. Folder-only collections keep their routing in their own folder (`skills/career-workspace`); `default` also installs that folder for the OpenCode `career` agent, so its rule is global there. Don't edit upstream skills to change routing. When a skill is added, removed or refreshed and its description now overlaps another owner's job, update this rule and the skill's README "For agents: routing and updates" section together, and tell the user.
- **Preferences** (`preferences/`): the user's stated preferences. Add to it only what the user asks for.
- **Order**: `shell-preamble` first and `shell-preamble-reminder` last in every group; the other rules sit between them in the order listed in `rulesync.jsonc`.
