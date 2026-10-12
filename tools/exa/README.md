# Exa

[Exa](https://exa.ai) is a web search API. Its MCP server gives the AI real search and clean page fetching.

## What's in this folder

| File | Becomes | Origin |
|---|---|---|
| `mcp.jsonc` | The `exa` entry in OpenCode's MCP server list | Me |
| `rules/45-web-research.md` | The "Web Research" section of `AGENTS.md` | Me |
| `skills/code-search/` | Skill `code-search-exa` | [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), unchanged. [MIT](https://github.com/exa-labs/exa-mcp-server/blob/main/LICENSE) |
| `skills/exa-research/` | Skill `exa-research` | Exa's `skills/search` from [exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), which I renamed and changed. [MIT](https://github.com/exa-labs/exa-mcp-server/blob/main/LICENSE) |

`code-search`'s folder name doesn't match its skill name (`code-search-exa`). That's how upstream ships it, and OpenCode loads it anyway.

`code-search` has a `context: fork` setting, which tells Claude Code to run the skill in a separate sub-conversation. It sits under a `claudecode:` section in the skill's header, so rulesync writes it for Claude Code and leaves it out for OpenCode, which doesn't use it. (Upstream has it at the top level; it was moved here so rulesync keeps it.)

`exa-research` writes reference paths as `<skill-dir>/references/...` and tells the AI to fill in the skill's folder before handing a path to a subagent. Tested: OpenCode reports the folder when the skill loads, and a subagent given the filled-in path could read the file.

## API key

The MCP entry sends your key from the `EXA_API_KEY` environment variable. Generating writes `{env:EXA_API_KEY}` into OpenCode's config, never the key itself, so rulesync doesn't need the key. **OpenCode does.** Set the variable where OpenCode starts, e.g. in your shell profile, so every terminal that launches OpenCode has it. If it's missing, Exa calls fail authentication.

To read the key from a file instead, change the header in **this folder's** `mcp.jsonc` to `"x-api-key": "{file:/path/to/exa.key}"` and regenerate. Don't edit it in `opencode.jsonc` directly: the next generate with the `mcp` feature overwrites that.

## Why the URL looks the way it does

- **`?tools=` replaces Exa's default tool list; it doesn't add to it.** Leave out a default and it disappears.
- **`web_search_advanced_exa`** is off by default, and it's what the research-paper, financial-report and personal-site searches need (category filters, domain restrictions, date ranges, highlights).
- **`agent_run` is deliberately not enabled:** it's billed per run.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `exa_web_search_exa`. Permission rules such as `"exa_*": "allow"` match on that name, and so do the rules and skills here, which name `exa_web_search_exa` and friends directly. If you rename the server, update your permission rules, `rules/45-web-research.md`, and both skills.
