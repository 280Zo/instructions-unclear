# opencode-quota

[opencode-quota](https://github.com/slkiser/opencode-quota) shows how much of your plan's quota you've used and how many tokens your sessions burn, for providers including Anthropic, OpenAI, GitHub Copilot, Cursor and others. It reads usage outside the conversation, so checking it doesn't add to the context.

No rules or skills go with it: you call it with commands, and the agent has no decisions to make about it.

## Install

Add it to `plugins` in `~/.config/opencode/opencode.jsonc` and restart OpenCode:

```jsonc
"plugins": ["@slkiser/opencode-quota@latest"]
```

Current stable release checked 2026-11-24: **6.3.0**. OpenCode 2 requires **2.0.26+** (the package declares `@opencode/plugin` 2.0.28+), with Node **22.13+ or 23.4+**. OpenCode 1 must use `@slkiser/opencode-quota@4` under its legacy `plugin` key, not `@latest`. The `next` prerelease tag is not the stable installation target.

OpenCode keeps loading its cached copy of an `@latest` entry until you update it. After installing or rolling out a new config, run `opencode plugin check` and `opencode plugin update`, then confirm the version with `opencode plugin list` (see [Updating](../README.md#updating-opencode-keeps-cached-versions)).

Upstream's `opencode plugin add @slkiser/opencode-quota` does the same. `/quota_settings` turns on the sidebar panel and status line. All settings live in the global `opencode-quota/settings.jsonc`. Project-level `opencode-quota/quota-toast.jsonc` files aren't read, and 4.x/5.x settings are converted on first start. Chutes, NanoGPT, Synthetic and Kilo aren't built in; add them as custom providers. Some providers, Anthropic among them, need a setup step; `/quota_status` tells you which.

### Let your agent do it

Skip this if you installed it by hand. Otherwise, start your coding tool in this repo and say:

> Install opencode-quota for me, using `plugins/opencode-quota/README.md`.

The agent follows these steps:

1. Get the user's approval before editing their OpenCode config.
2. Confirm the OpenCode version and prerequisites. Open only the approved config. Use `@slkiser/opencode-quota@latest` in V2's `plugins`, or `@slkiser/opencode-quota@4` in V1's `plugin`. If the right entry already exists, do not duplicate it; show an incorrect-version replacement for approval. Never add both keys. Edit only the plugin list; keep every comment and other setting. Do not open credential files.
3. Don't edit `opencode-quota/settings.jsonc` for the user. Tell them `/quota_settings` turns on the sidebar and status line.
4. Tell the user to restart OpenCode and run `/quota_status` to see which providers need setup.

## For agents: install, remove and update

To install, follow the steps in [Let your agent do it](#let-your-agent-do-it). No group includes it; rulesync can't install plugins. To verify, run `opencode plugin list` and check the version, then have the user run `/quota_status` in a new session.

To remove, get approval, then delete only the `@slkiser/opencode-quota` entry from the plugin list (`plugins` in V2, `plugin` in V1), keeping comments and every other setting, and ask the user to restart OpenCode. The cache in `~/.cache/opencode/npm/` can stay. Never open credential files. Settings the user changed in `opencode-quota/settings.jsonc` are theirs to keep or undo; don't guess which ones they changed. See also [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component).

To update, follow [Updating: OpenCode keeps cached versions](../README.md#updating-opencode-keeps-cached-versions). The last checked stable release is in [Install](#install).

## Use

| Command | Shows |
|---|---|
| `/quota` | A window with Usage, Limits and Plugin tabs |
| `/quota_usage [today\|24h\|7d\|30d\|90d\|all\|session\|between]` | Tokens used over that range, with cost. The older `/tokens_*` names still work |
| `/quota_status` | Setup problems: authentication, provider detection, pricing |
| `/quota_settings` | Settings, including the sidebar panel and status line (TUI only) |

From a terminal: `npx @slkiser/opencode-quota@latest show` (or `status`). Running it downloads the package; the plugin itself doesn't put a command on your `PATH`.

## Origin

[slkiser/opencode-quota](https://github.com/slkiser/opencode-quota), MIT. Nothing is copied into this repo.
