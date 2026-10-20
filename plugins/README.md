# Plugins

Plugins I use. rulesync can't install plugins (it installs rules, skills, agents, commands, hooks and MCP servers), so each one installs through its own tool, straight from upstream.

| Plugin | What it does | Tools |
|---|---|---|
| [`superpowers`](superpowers/) | A full workflow of skills for planning, test-driven development, debugging, code review and finishing work | OpenCode, Claude Code, Codex and more |
| [`opencode-quota`](opencode-quota/) | Shows your plan's remaining quota and token use, without adding to the context | OpenCode |
| [`opencode-claude-auth`](opencode-claude-auth/) | Lets OpenCode use your Claude Pro or Max subscription | OpenCode 2 |

## Install

Each README gives you two options:

- **By hand:** the plugin entry or command for each tool.
- **Let your agent do it:** start your coding tool in this repo and say, for example, "Install the Superpowers plugin for me, using `plugins/superpowers/README.md`". The numbered steps in that section are for the agent: it checks whether the plugin is already there, asks before editing your tool's config, edits only the plugin list, and hands you any step it can't do itself, such as a Claude Code slash command.

In OpenCode, plugins go in the `plugins` list in `~/.config/opencode/opencode.jsonc` (OpenCode 1 called it `plugin`). Restart OpenCode after changing it.
