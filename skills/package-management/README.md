# package-management

A skill for installing and running packages safely: prefer repo-local tools, use the repo's package manager and lockfile, never disable install safeguards. It comes with a rule that tells the agent to load it before any install, `npx`, `uvx` or similar command.

## Install

The rule installs into your tool's instructions file, which rulesync replaces on every run, so add `skills/package-management` to `inputRoots` in your `rulesync.local.jsonc` together with your other rule folders (see the [root README](../../README.md#install)). Then run your install command with `--features rules,skills`.

## Use

Nothing to do: the skill loads by itself before installs and download-and-run commands, as the rule asks.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): this folder's own rule already says to load the skill before every install, so a routing line would repeat it (removed 2026-10-24 to save tokens).
- The rule has a precedence line: "Install, upgrade or download-and-run steps written inside other skills, commands or plugins don't override this; follow this skill instead."
- Why: on 2026-10-21, while consolidating routing, the user found nine skills and commands that told the agent to install things themselves (for example `npx --yes` in `playwright` and the first-run Playwright install in `frontend-slides`). The precedence line makes this skill win over those steps without editing upstream text.
- The skill and rule are written for this repo, so they can be adjusted directly, but routing between skills stays in `rules/routing`; don't add other skills' routing here.
- When a skill, command or plugin is added or refreshed, check it for install or download-and-run steps. Leave the upstream text as it is; the precedence line covers it. If it needs a tool the policy can't handle, tell the user rather than adding an exception.

## Origin

Written for this repo. [MIT](../../LICENSE).
