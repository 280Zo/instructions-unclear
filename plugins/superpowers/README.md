# Superpowers

[Superpowers](https://github.com/obra/superpowers) is a workflow made of skills: brainstorming before building, writing plans, test-driven development, systematic debugging, verifying before claiming success, requesting and receiving code review, working in git worktrees, and handing tasks to subagents. A small plugin makes the agent check for a relevant skill before acting, so the workflow happens without you asking for each step.

| File | What it is |
|---|---|
| `rules/superpowers.md` | A rule rulesync installs: keeps Superpowers' `docs/superpowers/` specs and plans out of git, and routes its other commits through the ask-first commit rule in [`rules/scope-secrets-approvals`](../../rules/scope-secrets-approvals/) |

## Install

Two parts: the plugin installs through each tool, and the rule installs through rulesync.

1. Install the plugin:

   | Tool | How |
   |---|---|
   | OpenCode | Add `"superpowers@git+https://github.com/obra/superpowers.git"` to `plugins` in `~/.config/opencode/opencode.jsonc` and restart |
   | Claude Code | `/plugin install superpowers@claude-plugins-official` |
   | Codex CLI | `/plugins`, search for `superpowers`, choose **Install Plugin** |
   | Others | Upstream's [installation list](https://github.com/obra/superpowers#installation) covers Cursor, Gemini CLI, Copilot CLI and more |

   In OpenCode, the git entry follows upstream's latest commit. To stay on one release, add the tag: `superpowers@git+https://github.com/obra/superpowers.git#v7.0.0`.

2. Add `plugins/superpowers` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features rules` included.

### Install with an agent

Ask your agent: "Install the Superpowers plugin by following `plugins/superpowers/README.md` in this repo." The steps below are for the agent.

1. Ask the user which tools to install it for, and get their approval before editing any tool config.
2. **OpenCode:** open `~/.config/opencode/opencode.jsonc`. If `plugins` (OpenCode 2) or `plugin` (OpenCode 1) already lists a `superpowers@` entry, stop: it's installed. Otherwise add `"superpowers@git+https://github.com/obra/superpowers.git"` to that list, creating `plugins` if neither key exists and never adding both keys. Edit only that list; keep every comment and other setting.
3. **Claude Code and Codex:** you can't run their slash commands. Give the user the command from the table above to run themselves.
4. **The rule:** in the repo root, add `"plugins/superpowers"` to `inputRoots` in `rulesync.local.jsonc` (create the file with the user's current folder list if it doesn't exist; rules are replaced as a set, so the list must hold every folder they want). Then run the user's install command with `--global` and `rules` in `--features`.
5. Tell the user to restart each tool, and that `using-superpowers` should then load at the start of each session.

## Use

Nothing to call. At the start of every session the plugin adds the `using-superpowers` instructions, which tell the agent to load a matching skill before acting: "let's build X" starts with brainstorming, "fix this bug" starts with systematic debugging, "it's done" triggers verification first. You can also name a skill: "use the writing-plans skill for this".

The rule here covers the one place Superpowers' defaults collide with what I want: its brainstorming and planning skills commit their spec and plan files in `docs/superpowers/`, and those should never be committed.

## Origin

[obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent, MIT. Nothing from it is copied into this repo; the plugin installs from upstream. The rule is mine.
