# opencode-claude-auth-v2

[opencode-claude-auth-v2](https://github.com/heymaaz/opencode-claude-auth-v2) lets OpenCode 2 use your Claude Pro or Max subscription instead of a pay-per-use Anthropic API key. It reuses the login Claude Code already has, so there's no separate sign-in. OpenCode's own tools and permission prompts keep working as normal.

No rules or skills go with it: it changes how OpenCode connects, not what the agent does.

## Install

1. Have Claude Code installed and signed in (`claude auth login`) with a Pro or Max subscription, and Node.js 22+.
2. Add it to `plugins` in `~/.config/opencode/opencode.jsonc` and restart OpenCode:

   ```jsonc
   "plugins": ["opencode-claude-auth-v2@latest"]
   ```

3. In OpenCode, run `/connect` and choose **Anthropic → Import Claude Code subscription**.

This is for OpenCode 2 only. OpenCode 1 uses the original [opencode-claude-auth](https://github.com/griffinmartin/opencode-claude-auth) under a singular `plugin` key; don't put both keys in one config.

### Let your agent do it

Skip this if you installed it by hand. Otherwise, start your coding tool in this repo and say:

> Install opencode-claude-auth for me, using `plugins/opencode-claude-auth/README.md`.

The agent follows these steps:

1. Get the user's approval before editing their OpenCode config.
2. Check the OpenCode version with `opencode --version`. If it's OpenCode 1, stop and point the user to the original plugin linked above.
3. Check that Claude Code is signed in by checking that `~/.claude/.credentials.json` exists (macOS may use the Keychain instead). Don't open or print the file: it holds tokens. If it's missing, ask the user to run `claude auth login`.
4. Open `~/.config/opencode/opencode.jsonc`. If `plugins` already lists `opencode-claude-auth-v2`, stop: it's installed. Otherwise add `"opencode-claude-auth-v2@latest"` to `plugins`. Edit only that list; keep every comment and other setting.
5. Tell the user to restart OpenCode, run `/connect`, and choose **Anthropic → Import Claude Code subscription**. You can't do that step for them.

## Use

Pick any model under **Anthropic** with `/models`. Requests go through your subscription, and the plugin refreshes the login as it expires.

## Notes

- It reads your Claude Code credentials (`~/.claude/.credentials.json`, or the macOS Keychain) and writes refreshed tokens back there. Nothing about them goes into this repo.
- OpenCode 2's plugin API is still in beta, so an OpenCode update can break this plugin until it catches up.
- Using a subscription through a tool other than Claude Code is between you and your plan's terms.

## Origin

[heymaaz/opencode-claude-auth-v2](https://github.com/heymaaz/opencode-claude-auth-v2), a fork of [griffinmartin/opencode-claude-auth](https://github.com/griffinmartin/opencode-claude-auth). MIT. Nothing is copied into this repo.
