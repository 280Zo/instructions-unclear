# package-management

A skill for installing and running packages safely: prefer repo-local tools, use the repo's package manager and lockfile, never disable install safeguards. It comes with a rule that tells the agent to load it before any install, `npx`, `uvx` or similar command.

## Install

The rule installs into your tool's instructions file, which rulesync replaces on every run, so add `skills/package-management` to `inputRoots` in your `rulesync.local.jsonc` together with your other rule folders (see the [root README](../../README.md#install)). Then run your install command with `--features rules,skills`.

## Use

Nothing to do: the skill loads by itself before installs and download-and-run commands, as the rule asks.

## Origin

Written for this repo. [MIT](../../LICENSE).
