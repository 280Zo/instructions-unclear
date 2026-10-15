# Exa

[Exa](https://exa.ai) is a web search API. Its MCP server gives the AI real search and clean page fetching.

## What's in this folder

| File | Becomes | Origin |
|---|---|---|
| `mcp.jsonc` | The `exa` entry in your tool's MCP server list | Me |
| `rules/web-research.md` | The "Web Research" section of `AGENTS.md` | Me |
| `skills/code-search/` | Skill `code-search-exa` | [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server) |
| `skills/exa-research/` | Skill `exa-research` | Exa's `skills/search` from [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), which I renamed and changed. [MIT](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server) |

## Install

1. Get an Exa API key and export it as `EXA_API_KEY` (below).
2. This folder adds a rule and an MCP server, and rulesync installs both by replacing your tool's whole set. So add `mcp-servers/exa` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features rules,skills,mcp`.

## Use

Ask anything that needs the web ("what changed in Node 24?", "find the docs for X"). The web research rule makes the agent use Exa search instead of guessing URLs. For more:

- **`code-search-exa`**: "find real examples of using X's API", "how do people configure Y".
- **`exa-research`**: "research everything about X", "compare the top tools for Y". It plans the work, sends subagents to search in parallel, and returns a sourced summary.

## Notes

`code-search`'s folder name doesn't match its skill name (`code-search-exa`). That's how upstream ships it, and OpenCode loads it anyway.

`code-search` has a `context: fork` setting, which tells Claude Code to run the skill in a separate sub-conversation. It sits under a `claudecode:` section in the skill's header, so rulesync writes it for Claude Code and leaves it out for OpenCode, which doesn't use it. (Upstream has it at the top level; it was moved here so rulesync keeps it.)

`exa-research` writes reference paths as `<skill-dir>/references/...` and tells the AI to fill in the skill's folder before handing a path to a subagent. Tested: OpenCode reports the folder when the skill loads, and a subagent given the filled-in path could read the file.

## API key

You need an [Exa](https://exa.ai) API key. The MCP entry sends it from the `EXA_API_KEY` environment variable, and the key itself is never written into any file: OpenCode's config gets `{env:EXA_API_KEY}`, Claude Code's gets `${EXA_API_KEY}`, and Codex's gets the variable's name. So rulesync doesn't need the key, but your coding tool does. Set it where the tool starts, for example in your shell profile:

```bash
export EXA_API_KEY=paste-your-exa-key-here
```

If it's missing, Exa calls fail authentication.

To read the key from a file instead, change the header in **this folder's** `mcp.jsonc` to `"x-api-key": "{file:/path/to/exa.key}"` and regenerate. Don't edit it in `opencode.jsonc` directly: the next generate with the `mcp` feature overwrites that.

## Why the URL looks the way it does

- **`?tools=` replaces Exa's default tool list; it doesn't add to it.** Leave out a default and it disappears.
- **`web_search_advanced_exa`** is off by default, and it's what the research-paper, financial-report and personal-site searches need (category filters, domain restrictions, date ranges, highlights).
- **`agent_run` is deliberately not enabled:** it's billed per run.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `exa_web_search_exa`. Permission rules such as `"exa_*": "allow"` match on that name, and so do the rules and skills here, which name `exa_web_search_exa` and friends directly. If you rename the server, update your permission rules, `rules/web-research.md`, and both skills.
