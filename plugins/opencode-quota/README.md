# opencode-quota

[opencode-quota](https://github.com/slkiser/opencode-quota) shows how much of your plan's quota you've used and how many tokens your sessions burn, for providers including Anthropic, OpenAI, GitHub Copilot, Cursor and others. It reads usage outside the conversation, so checking it doesn't add to the context.

No rules or skills go with it: you call it with commands, and the agent has no decisions to make about it.

## Install

Add it to `plugins` in `~/.config/opencode/opencode.jsonc` and restart OpenCode:

```jsonc
"plugins": ["@slkiser/opencode-quota@latest"]
```

Current stable release checked October 20, 2026: **5.0.3**. OpenCode 2 requires **2.0.16+**, with Node **22.13+ or 23.4+**. OpenCode 1 must use `@slkiser/opencode-quota@4` under its legacy `plugin` key, not `@latest`. The `next` prerelease tag is not the stable installation target.

OpenCode keeps loading its cached copy of an `@latest` entry until you update it. After installing or rolling out a new config, run `opencode plugin check` and `opencode plugin update`, then confirm the version with `opencode plugin list` (see [Updating](../README.md#updating-opencode-keeps-cached-versions)).

Upstream's setup wizard (`npx @slkiser/opencode-quota init`) does the same and also offers a sidebar panel and a status line. Some providers, Anthropic among them, need a setup step; `/quota_status` tells you which.

### Let your agent do it

Skip this if you installed it by hand. Otherwise, start your coding tool in this repo and say:

> Install opencode-quota for me, using `plugins/opencode-quota/README.md`.

The agent follows these steps:

1. Get the user's approval before editing their OpenCode config.
2. Confirm the OpenCode version and prerequisites. Open only the approved config. Use `@slkiser/opencode-quota@latest` in V2's `plugins`, or `@slkiser/opencode-quota@4` in V1's `plugin`. If the right entry already exists, do not duplicate it; show an incorrect-version replacement for approval. Never add both keys. Edit only the plugin list; keep every comment and other setting. Do not open credential files.
3. Don't run the `init` wizard: it's interactive. Tell the user they can run it themselves for the sidebar and status line.
4. Tell the user to restart OpenCode and run `/quota_status` to see which providers need setup.

## Use

| Command | Shows |
|---|---|
| `/quota` | Remaining quota and usage per provider |
| `/tokens_today`, `/tokens_weekly`, `/tokens_monthly` | Tokens used over that period (monthly includes cost) |
| `/tokens_session` | Tokens used in this session |
| `/quota_status` | Setup problems: authentication, provider detection, pricing |

From a terminal: `opencode-quota show`.

## Origin

[slkiser/opencode-quota](https://github.com/slkiser/opencode-quota), MIT. Nothing is copied into this repo.
