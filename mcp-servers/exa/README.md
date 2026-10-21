# Exa

[Exa](https://exa.ai) provides web discovery, page retrieval and multi-step research through its [MCP server](https://github.com/exa-labs/exa-mcp-server).

## What's in this folder

| File | Origin / purpose |
|---|---|
| `mcp.jsonc` | Repo-authored connection enabling `web_search_exa`, `web_fetch_exa` and `agent_run` |
| `rules/web-research.md` | Repo-authored source-quality and discovery/retrieval guidance |
| `skills/search/` | Upstream `search` skill and all its references, unchanged |
| `skills/exa-agent/` | Upstream `Exa Agent` skill, unchanged |

## Install

Add `mcp-servers/exa` to your selected `inputRoots` and generate with `--features rules,skills,mcp`, keeping your other roots in the same run because rules and MCP settings are replaced. The hosted endpoint uses the `EXA_API_KEY` environment variable through an `x-api-key` header; this repo never contains the real key. Configure that variable where your assistant starts. No local Exa package or installer is required for this hosted connection.

### Authentication after generation

Exa's hosted server supports OAuth and API-key headers; see [upstream authentication](https://github.com/exa-labs/exa-mcp-server#authentication). A V1-era API key is not made obsolete by OpenCode V2. A sign-in prompt does not by itself show that the key was rejected: the client may be attempting OAuth, the header reference may be unresolved, or a project configuration may replace the global connection.

The portable convention in this repo is **one externally supplied `EXA_API_KEY` variable**, not a universal secret-file format. Rulesync source uses `${EXA_API_KEY}` and translates it to each target's supported environment-reference syntax. OpenCode receives `{env:EXA_API_KEY}`. Configure your own secret manager or launcher to supply the existing key to the assistant service; regeneration then recreates the reference without storing the key in this repo. Do not assume a variable set in an interactive terminal is present in an already-running background service. Never print the variable or key, dump the environment, paste a literal key into JSON, or read a real secret file to diagnose this.

For explicitly chosen API-key-only authentication in **native OpenCode V2 configuration**, the connection looks like this:

```jsonc
{
  "mcp": {
    "servers": {
      "exa": {
        "type": "remote",
        "url": "https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa,agent_run",
        "oauth": false,
        "headers": { "x-api-key": "{env:EXA_API_KEY}" }
      }
    }
  }
}
```

This is an OpenCode-specific example, not a replacement for the shared rulesync source or a whole live config. Apply it only with approval, preserving unrelated settings. Do not keep conflicting flat and nested definitions of the same server. The current rulesync generation rewrites the MCP section, so a local authentication customization needs review/reapplication after generation; do not claim it survives automatically. OAuth remains an upstream-supported alternative; do not disable it for a user who chose that method. [OpenCode documents API-key-only configuration](https://opencode.ai/v2/docs/mcp-servers#remote).

For a failed restoration, check the configured reference and selected authentication method without revealing its value, have the user confirm the service's secret provisioning, and inspect only sanitized connection errors. `{file:...}` is client-specific; the nested `{file:{env:XDG_RUNTIME_DIR}/opencode/exa.key}` form needs verification on the installed client using a dummy variable/file before adoption. Do not resolve the real key during that test. Runtime directories can disappear between logins/reboots. A simple supported file reference can reuse a local key, but there is no universal file-reference syntax across assistants.

After an approved config/launcher correction, restart or reconnect the affected service only when it will not interrupt other work. Check `/mcps` or `opencode mcp list`, then request one ordinary search as a separately approved functional test. Do not use metered `agent_run`, delete stored credentials, start OAuth login, or create another key merely to clear a status message. If it still fails, request the redacted server definition and sanitized error, never the key or authentication file.

## Use

- Ask for research across multiple sources: the upstream `search` skill plans search/fetch work and selects its topic-specific references, including `patterns-code.md` for programming questions.
- Ask for multi-step discovery, list-building or enrichment: `Exa Agent` uses `agent_run`. Optional partner-data providers require corresponding account access and may incur costs; they are not enabled or purchased by copying the skill.

The skill bodies retain upstream's assistant-specific wording and model recommendations. Their presence is not a guarantee that every host provides those delegation/model facilities. Host permissions and higher-priority instructions still apply. References must resolve from the installed skill folder.

## Updating and existing installations

This is a fresh upstream import, not the former local research adaptation. The old `code-search-exa` and `exa-research` skill names are no longer shipped. Because `delete: false`, regenerating does not remove old live installations; review and approve removal of those stale skill folders separately. No live files were removed by this repo refresh.

Refresh `skills/search/` and `skills/exa-agent/` together from the recorded upstream source, preserve the complete references, and review the hosted tool selection. Do not rewrite upstream behavior merely to preserve the old local names. If a target parser or host rejects an upstream name/instruction, show the actual failure before adapting it.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Web discovery**: Exa `search`. Multi-step list-building or enrichment: `Exa Agent`."
- `search` does not own multi-step list-building or enrichment (`Exa Agent`), and `Exa Agent` is not the default for ordinary lookups (`search`). Reading local documents is Docling's job.
- Why: on 2026-10-21 the user replaced the per-skill routing rules with one routing rule because several items claimed the same jobs. Here, the two upstream Exa skills overlap on research requests, and `Exa Agent` can use partner-data providers that may incur costs.
- `rules/web-research.md` stays in this folder: it covers source quality and search versus fetch, not which skill owns a job. Keep job ownership in `rules/routing`.
- The rule's `gh` CLI line (current GitHub state) is repo-owned guidance in that rule, not a change to the upstream Exa skills. It needs no GitHub MCP server and does not authorize installing `gh` or changing its authentication.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule here.
- After a refresh, re-read both new `description`s and the hosted tool list. If either skill now claims the other's job or one owned elsewhere, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.
- When an approved manual setup or migration adds comments to the live connection, put the following beside its URL. Recheck the selected tools first: an old comment saying `agent_run` is disabled is wrong for this template. Never change the connection to make a stale comment true. Rulesync does not automatically insert these README comments, and upstream skill files remain unchanged.

```jsonc
// ?tools= replaces the default tool list; omitted tools are not exposed.
// This connection includes agent_run; account access, costs and approvals still apply.
```

## Origin

[exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), paths `skills/search/` and `skills/exa-agent/`, commit `0b499f095c4ca145eee07b09137641c037d58449`, copied October 20, 2026. Skill payloads unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server), © Exa Labs. Connection and rule written for this repo.
