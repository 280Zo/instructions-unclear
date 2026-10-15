# Plugins

Plugins I use. rulesync can't install plugins (it installs rules, skills, agents, commands, hooks and MCP servers), so each plugin installs through its own tool. Where a plugin works better with a rule or skill, that file sits in the plugin's folder and installs through rulesync like any other.

| Plugin | What it does | Tools | Also installs through rulesync |
|---|---|---|---|
| [`superpowers`](superpowers/) | A full workflow of skills for planning, test-driven development, debugging, code review and finishing work | OpenCode, Claude Code, Codex and more | A rule fitting Superpowers to the [rules](../rules/) |
| [`opencode-quota`](opencode-quota/) | Shows your plan's remaining quota and token use, without adding to the context | OpenCode | Nothing |
| [`opencode-claude-auth`](opencode-claude-auth/) | Lets OpenCode use your Claude Pro or Max subscription | OpenCode 2 | Nothing |

## Install

Each README has two ways:

- **By hand:** the plugin entry or command for each tool, plus the rulesync step if the folder has rules or skills.
- **With an agent:** open your coding tool in this repo and ask, for example, "Install the Superpowers plugin by following `plugins/superpowers/README.md`". Each README has an "Install with an agent" section written for the agent: it checks whether the plugin is already there, asks before editing your tool's config, edits only the plugin list, and tells you about any step it can't do itself, such as a Claude Code slash command.

In OpenCode, plugins go in the `plugins` list in `~/.config/opencode/opencode.jsonc` (OpenCode 1 called it `plugin`). Restart OpenCode after changing it.
