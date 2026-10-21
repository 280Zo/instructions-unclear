# opencode-claude-auth

[opencode-claude-auth](https://github.com/griffinmartin/opencode-claude-auth) lets OpenCode use an existing Claude subscription. OpenCode 2 support was merged into upstream 3.0.0; the former `heymaaz/opencode-claude-auth-v2` fork is retired. No plugin code, credentials or settings are copied into this repo.

## Install

Follow the [upstream installation instructions](https://github.com/griffinmartin/opencode-claude-auth/blob/main/installation.md). For OpenCode 2, use:

```jsonc
"plugins": ["opencode-claude-auth@latest"]
```

For OpenCode 1 only, upstream specifies `opencode-claude-auth@2.2.1` under its legacy singular `plugin` key. Never add both keys or load both the retired fork and upstream plugin.

OpenCode keeps loading its cached copy of an `@latest` entry until you update it. A machine that used OpenCode 1 may still have the V1-only 2.2.1 release cached under the same `opencode-claude-auth@latest` entry, and a fresh V2 config will load it. After installing or rolling out a new config, run `opencode plugin check` and `opencode plugin update`, then confirm 3.0.0 or newer with `opencode plugin list` (see [Updating](../README.md#updating-opencode-keeps-cached-versions)).

If the retired fork is already present, replace that one entry rather than adding a second authentication plugin. Preserve all other settings. Restart OpenCode and, if reconnection is needed, run `/connect`, choose **Anthropic**, then **Import Claude Code subscription**. Authentication is handled by the host/plugin; do not paste tokens into this repo.

### Let your agent do it

Skip this if you installed it by hand. Otherwise, start your coding tool in this repo and say:

> Install opencode-claude-auth for me, using `plugins/opencode-claude-auth/README.md`.

The agent follows these steps:

1. Ask which OpenCode version is in use and get approval before editing any tool config. Do not read credential files or Keychain contents.
2. Inspect only the plugin list in the approved OpenCode config. If the correct upstream entry is already present, do not add another. If the retired fork is present, show the single-entry replacement for approval.
3. Use `opencode-claude-auth@latest` in V2's `plugins`, or `opencode-claude-auth@2.2.1` in V1's `plugin`. Never add both keys. Keep comments and all unrelated settings. Do not run an unrelated installer or change provider/model settings.
4. Tell the user to restart and perform the `/connect` step above themselves if required. Never print, copy or manually migrate credentials.

## Use

Select an Anthropic model after connecting. Use the plugin defaults and upstream troubleshooting guidance. Subscription use remains subject to the provider's terms. The plugin handles credential discovery and refresh; installation instructions must not expose those credentials.

## Origin

[griffinmartin/opencode-claude-auth](https://github.com/griffinmartin/opencode-claude-auth), MIT; current upstream release 3.0.0 and [fork retirement notice](https://github.com/heymaaz/opencode-claude-auth-v2/releases/tag/migration-to-upstream) checked October 20, 2026. Nothing is copied into this repo. Future updates come from upstream, not the retired fork.
