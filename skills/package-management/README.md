# package-management

A skill for installing and running packages safely: prefer repo-local tools, use the repo's package manager and lockfile, never disable install safeguards. It comes with a rule that tells the agent to load it before any install, `npx`, `uvx` or similar command.

## Install

The rule installs into your tool's instructions file, which rulesync replaces on every run, so add `skills/package-management` to `inputRoots` in your `rulesync.local.jsonc` together with your other rule folders (see the [root README](../../README.md#install)). Then run your install command with `--features rules,skills`.

## Use

Nothing to do: the skill loads by itself before installs and download-and-run commands, as the rule asks.

## For agents: install, remove and update

To install, use the `default`, `work` or `writing_reporting` group, or add this folder to `rulesync.local.jsonc` as [Install](#install) says. Installing only the skill without the rule leaves nothing telling the agent to load it. It needs no other software. To verify, start a new session, check that the generated rules file contains the "Package & Tool Management" rule and that `package-management` is listed among the skills.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder drops the rule; `delete: false` leaves the `package-management` skill folder behind, which you delete with approval. The `rules/preferences` rule still says this skill governs every install, so tell the user.

To update, there is no upstream: the skill and rule are written for this repo and change in place. The next section says what to check when other skills or plugins change.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): this folder's own rule already says to load the skill before every install, so a routing line would repeat it.
- The rule has a precedence line: "Install, upgrade or download-and-run steps written inside other skills, commands or plugins don't override this; follow this skill instead."
- Why: several skills and commands tell the agent to install things itself (for example the first-run Playwright install in `frontend-slides`). The precedence line makes this skill win over those steps without editing upstream text.
- The skill and rule are written for this repo, so they can be adjusted directly, but routing between skills stays in `rules/routing`; don't add other skills' routing here.
- When a skill, command or plugin is added or refreshed, check it for install or download-and-run steps. Leave the upstream text as it is; the precedence line covers it. If it needs a tool the policy can't handle, tell the user rather than adding an exception.

## Origin

Written for this repo. [MIT](../../LICENSE).
