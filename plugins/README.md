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

A plugin that brings skills needs an owner in the [agent setup](../agents/README.md#adding-a-plugin-that-brings-skills), or OpenCode's `build`, `plan` and `general` agents see all of its skills in every request. Superpowers goes to every agent; the Trail of Bits and IoTHackBot native plugins go to `security` and `reverse-engineering`.

## Updating: OpenCode keeps cached versions

OpenCode installs each plugin entry once into `~/.cache/opencode/npm/` and keeps loading that copy. For entries that aren't pinned (`@latest`, or a git URL without a full commit hash), startup only *checks* for a newer release; it doesn't install it ([OpenCode docs](https://opencode.ai/v2/docs/plugins#reload)). Replacing or regenerating your config doesn't clear this cache, so a fresh config can still load an old plugin, including a release built for OpenCode 1.

After installing, updating, or rolling out a new config:

```fish
opencode plugin check
opencode plugin update
opencode plugin list
```

Restart OpenCode, then confirm each plugin's version in `opencode plugin list`. To stay on a reviewed release instead, pin an exact npm version (`name@1.2.3`) or a full git commit hash; pinned entries are never updated for you.

Use `opencode plugin check` and `opencode plugin update` exactly as written. OpenCode 1 treated `opencode plugin <word>` as "install the npm package named `<word>`", so older setups can end up with unrelated `check` or `update` packages listed as plugins in a project's `.opencode/opencode.json`. If the log shows `failed to load plugin target=check` (or `update`), remove those entries from the config that lists them before clearing their cache folders. Otherwise OpenCode downloads them again.

### For agents: plugin updates

- Run `opencode plugin check` first and show the user what would change. Run `opencode plugin update` only after they approve, then verify the versions with `opencode plugin list` and ask the user to restart.
- Don't delete `~/.cache/opencode` or lockfiles to force an update; use the commands above.
- When a plugin fails to load, find the config entry that lists it before touching the cache. Don't remove entries from a config outside the current repo without approval.

## For agents: install, remove and update

To install, follow step 6 of [Installing on a machine](../AGENTS.md#6-ask-about-plugins): offer every plugin in the table above, then follow the "Let your agent do it" steps in each chosen plugin's README, one plugin at a time. No group installs a plugin. When adding a new plugin to this repo, follow step 6 of [Plugins](../AGENTS.md#plugins) so its skills get an owning agent. To verify in OpenCode, run `opencode plugin list` and check each plugin in a new session as its README says.

To remove, get approval, then delete only that plugin's entry from the tool's plugin list (OpenCode's `plugins`, or `plugin` in V1), keeping comments and every other setting, and ask the user to restart. The cache in `~/.cache/opencode/npm/` can stay. Never open credential files. For tools where the plugin was installed with a slash command, the user removes it through that tool's plugin manager. Each plugin's README lists what else stays behind, and [Removing or replacing a component](../AGENTS.md#removing-or-replacing-a-component) has the general procedure.

To update, follow [Updating: OpenCode keeps cached versions](#updating-opencode-keeps-cached-versions) and the plugin updates notes above. Nothing is copied into this repo, so [Check for updates](../AGENTS.md#check-for-updates) only checks that each README's install line still matches upstream.
