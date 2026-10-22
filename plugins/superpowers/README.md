# Superpowers

[Superpowers](https://github.com/obra/superpowers) is a workflow made of skills: brainstorming before building, writing plans, test-driven development, systematic debugging, verifying before claiming success, requesting and receiving code review, working in git worktrees, and handing tasks to subagents. A small plugin makes the agent check for a relevant skill before acting, so the workflow happens without you asking for each step.

Nothing installs through rulesync for this one. The plugin comes straight from upstream and is used with its defaults.

## Install

| Tool | How |
|---|---|
| OpenCode | Add `"superpowers@git+https://github.com/obra/superpowers.git"` to `plugins` in `~/.config/opencode/opencode.jsonc` and restart |
| Claude Code | `/plugin install superpowers@claude-plugins-official` |
| Codex CLI | `/plugins`, search for `superpowers`, choose **Install Plugin** |
| Others | Upstream's [installation list](https://github.com/obra/superpowers#installation) covers Cursor, Gemini CLI, Copilot CLI and more |

For OpenCode, current upstream requires V2 **2.0.4+**. The git entry is unpinned, but OpenCode keeps loading its cached install until you update it; a restart alone does not install a newer release. After installing or rolling out a new config, run `opencode plugin check` and `opencode plugin update`, then confirm the version with `opencode plugin list` (see [Updating](../README.md#updating-opencode-keeps-cached-versions)). Don't delete caches or lockfiles to force an update. To stay on a reviewed release instead, pin a full commit hash. On October 21, 2026 the unpinned entry resolved to package version 7.0.1; the last reviewed release tag was `v7.0.0` (checked October 20, 2026).

### Let your agent do it

Skip this if you installed it by hand. Otherwise, start your coding tool in this repo and say:

> Install the Superpowers plugin for me, using `plugins/superpowers/README.md`.

The agent follows these steps:

1. Ask the user which tools to install it for, and get their approval before editing any tool config.
2. **OpenCode:** verify V2 2.0.4+ and open only the approved config. If `plugins` already lists a `superpowers@` entry, do not duplicate it; check upstream update guidance if an update was requested. Otherwise add `"superpowers@git+https://github.com/obra/superpowers.git"` to `plugins`. Never add both `plugin` and `plugins`. Edit only the plugin list; keep every comment and other setting. Never open credential files or remove caches/lockfiles automatically.
3. **Claude Code and Codex:** you can't run their slash commands. Give the user the command from the table above to run themselves.
4. Tell the user to restart each tool, and that `using-superpowers` should then load at the start of each session.

## Use

Nothing to call. At the start of every session the plugin adds the `using-superpowers` instructions, which tell the agent to load a matching skill before acting: "let's build X" starts with brainstorming, "fix this bug" starts with systematic debugging, "it's done" triggers verification first. You can also name a skill: "use the writing-plans skill for this".

Superpowers' brainstorming and planning skills save specs and plans under `docs/superpowers/` and suggest committing them. If you don't want those in git, ignore `docs/superpowers/` in your global gitignore; the commit rule in [`rules/scope-secrets-approvals`](../../rules/scope-secrets-approvals/) already makes the agent ask before any commit.

## Origin

[obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent, MIT. Nothing from it is copied into this repo; the plugin installs from upstream.
