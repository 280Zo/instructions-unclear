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

Add `mcp-servers/exa` to your selected `inputRoots` and generate with `--features rules,skills,mcp`, keeping your other roots in the same run because rules and MCP settings are replaced. No local Exa package or installer is required for this hosted connection.

Exa's hosted server supports free, rate-limited anonymous search and page retrieval. An API key is optional. Higher limits and Exa Agent (`agent_run`) require OAuth or an API key; see [upstream authentication](https://github.com/exa-labs/exa-mcp-server#authentication).

### Let your agent do it

Tell your agent: "Set up Exa using this README. Ask whether I have an API key; if I don't, use the free anonymous connection."

The agent follows these steps:

1. Ask whether the user has an Exa API key. Ask only whether they have one, never for its value. If they do not, use anonymous access without requiring an account, key or OAuth sign-in. OAuth remains an option if the user explicitly chooses it.
2. Preview generation in an isolated output folder and get approval before changing live assistant settings. Preserve unrelated configuration and any existing authentication choice; do not replace a working connection without approval.
3. For a user who chooses their API key, use the shared `mcp.jsonc` template. OpenCode reads the key from `$XDG_RUNTIME_DIR/opencode/exa.key`; the user creates the `opencode` directory and that file (mode `600`) in each login session. Other tools read the `EXA_API_KEY` variable, which the user supplies where their assistant starts. Never copy the key into the repo or a config example, and never read or create the key file yourself.
4. For anonymous access, use the connection below in the target client's supported format. Remove the Exa API-key header entirely, rather than leaving an unresolved or empty variable reference. Select only `web_search_exa` and `web_fetch_exa`; do not offer `agent_run` as an anonymous capability. If the client attempts OAuth automatically, use its documented anonymous/API-key-only setting to suppress that flow, with approval. Do not disable OAuth for a user who chose it.
5. Review the generated connection before installing it. The shared template remains key-based: generation with MCP enabled restores its header and `agent_run` selection. Reapply the approved anonymous choice after each such generation; do not claim rulesync detects the user's choice or preserves it automatically.
6. With separate approval, reconnect and test one ordinary search. Do not use metered `agent_run` as an installation test. Report sanitized failures without reading credentials or starting a login flow unasked.

### Free anonymous connection

For clients using the standard `mcpServers` shape:

```json
{
  "mcpServers": {
    "exa": {
      "type": "streamable-http",
      "url": "https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa"
    }
  }
}
```

This is a connection example, not a replacement for a whole config. Adapt the wrapper and transport fields to the target client. Native OpenCode V2 uses `mcp.servers.exa` with `type: "remote"`; for explicitly chosen anonymous access, set `oauth: false` and omit `headers`. Anonymous limits still apply, and built-in search may share the same provider or limits.

### Authentication after generation

The following guidance applies when authentication was chosen; anonymous search does not require it. A V1-era API key is not made obsolete by OpenCode V2. A sign-in prompt does not by itself show that the key was rejected: the client may be attempting OAuth, the header reference may be unresolved, or a project configuration may replace the global connection.

Rulesync source uses `${EXA_API_KEY}` for every tool and translates it to each target's environment-reference syntax. OpenCode is the exception: an `opencode.mcpServers` block in `mcp.jsonc` gives it `"x-api-key": "{file:{env:XDG_RUNTIME_DIR}/opencode/exa.key}"` and `"oauth": false`. OpenCode replaces `{env:…}` before resolving `{file:…}`; a test on 2.1.3 with a dummy runtime directory and key file sent the file's contents, without its trailing newline, as the header. That path holds no secret, but the file it names does. When the file is missing, or `XDG_RUNTIME_DIR` is unset so the path becomes `/opencode/exa.key`, OpenCode 2.1.3 logs `config file reference is missing or unreadable`, loads the rest of the config, and sends an empty `x-api-key` header (both tested with a dummy setup). Exa then fails to connect; other servers are unaffected, and `"oauth": false` means no sign-in prompt appears. Runtime directories are cleared at logout or reboot, so the user recreates `$XDG_RUNTIME_DIR/opencode/` and the key file each session, for example from a secret manager at login. A user without a key should remove the header for anonymous access, as described above. Configure your own secret manager or launcher to supply the existing key to the assistant service; regeneration then recreates the reference without storing the key in this repo. Do not assume a variable set in an interactive terminal is present in an already-running background service. Never print the variable or key, dump the environment, paste a literal key into JSON, or read a real secret file to diagnose this.

For explicitly chosen API-key-only authentication in **native OpenCode V2 configuration**, the connection looks like this:

```jsonc
{
  "mcp": {
    "servers": {
      "exa": {
        "type": "remote",
        "url": "https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa,agent_run",
        "oauth": false,
        "headers": { "x-api-key": "{file:{env:XDG_RUNTIME_DIR}/opencode/exa.key}" }
      }
    }
  }
}
```

This is what rulesync 41 generates for OpenCode from `mcp.jsonc`. Apply it by hand only with approval, preserving unrelated settings. Do not keep conflicting flat and nested definitions of the same server. Generation with `mcp` rewrites the server list, so any other local authentication customization needs review/reapplication afterward; do not claim it survives automatically. OAuth remains an upstream-supported alternative; do not disable it for a user who chose that method. [OpenCode documents API-key-only configuration](https://opencode.ai/v2/docs/mcp-servers#remote).

For a failed restoration, check the configured reference and selected authentication method without revealing its value, have the user confirm the service's secret provisioning, and inspect only sanitized connection errors. For OpenCode, ask the user to confirm that `$XDG_RUNTIME_DIR/opencode/exa.key` exists in the session the service runs in; don't read it. `{file:...}` is OpenCode-specific, which is why only the OpenCode block uses it. To retest the nested form on a new OpenCode release, use a dummy runtime directory and key file, never the real key.

After an approved config/launcher correction, restart or reconnect the affected service only when it will not interrupt other work. Check `/mcps` or `opencode mcp list`, then request one ordinary search as a separately approved functional test. Do not use metered `agent_run`, delete stored credentials, start OAuth login, or create another key merely to clear a status message. If it still fails, request the redacted server definition and sanitized error, never the key or authentication file.

## Use

- Ask for research across multiple sources: the upstream `search` skill plans search/fetch work and selects its topic-specific references, including `patterns-code.md` for programming questions.
- Ask for multi-step discovery, list-building or enrichment: `Exa Agent` uses `agent_run`. Optional partner-data providers require corresponding account access and may incur costs; they are not enabled or purchased by copying the skill.
- If Exa search is rate-limited or unavailable, the repo-owned web-research rule permits the host's built-in search tool when available and allowed. Disclose the fallback. It does not replace Exa Agent's structured runs, enrichment or partner-data access.

The skill bodies retain upstream's assistant-specific wording and model recommendations. Their presence is not a guarantee that every host provides those delegation/model facilities. Host permissions and higher-priority instructions still apply. References must resolve from the installed skill folder.

## Updating and existing installations

Refresh `skills/search/` and `skills/exa-agent/` together from the recorded upstream source, preserve the complete references, and review the hosted tool selection. If a target parser or host rejects an upstream name/instruction, show the actual failure before adapting it.

## For agents: install, remove and update

### Install

- It's in the `default` and `work` [install groups](../../groups/README.md), and `writing_reporting` installs its rule and skills but leaves MCP settings alone.
- Follow [Let your agent do it](#let-your-agent-do-it) above. Nothing needs installing locally. A key is optional; ask only whether the user has one, never for its value. With a key, OpenCode needs the user's `$XDG_RUNTIME_DIR/opencode/exa.key` file and other tools need `EXA_API_KEY`.
- The connection is written switched on. To verify, run one ordinary search with separate approval. Don't use `agent_run` as a test.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `exa` MCP entry and the web-research rule, because each run replaces both.
- `delete: false` leaves the `search` and `exa-agent` skill folders (skill name `Exa Agent`) behind. Delete them only with approval, using the AGENTS.md table. Older installs may also have the stale `code-search-exa` and `exa-research` folders described in [Updating and existing installations](#updating-and-existing-installations).
- If the user syncs a native V2 config without the `mcp` feature, or set up the anonymous connection by hand, remove the `exa` entry from `mcp.servers` by hand, keeping every other setting.
- An Exa API key, OAuth sign-in and any stored client credentials are the user's to revoke. Don't open credential files or start a login or logout flow.

### Update

- Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating and existing installations](#updating-and-existing-installations). The upstream commit lives in [Origin](#origin). Refresh `skills/search/` and `skills/exa-agent/` together, recheck the `?tools=` list in `mcp.jsonc`, and update the [license section](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server) if upstream's license changed.
- Then follow the update bullets in [For agents: routing and updates](#for-agents-routing-and-updates).

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): this folder's `rules/web-research.md` already sends discovery to Exa search and multi-step research to `Exa Agent`, so a routing line would repeat it.
- `search` does not own multi-step list-building or enrichment (`Exa Agent`), and `Exa Agent` is not the default for ordinary lookups (`search`). Reading local documents is Docling's job.
- Why: The two upstream Exa skills overlap on research requests, and `Exa Agent` can use partner-data providers that may incur costs.
- `rules/web-research.md` stays in this folder: it covers source quality, search versus fetch, and which Exa tool to use. Because it already assigns those jobs, `rules/routing` doesn't repeat them; if another installed skill starts competing for web research, add a line there.
- The rule's `gh` CLI line (current GitHub state) is repo-owned guidance in that rule, not a change to the upstream Exa skills. It needs no GitHub MCP server and does not authorize installing `gh` or changing its authentication.
- The rule's search-fallback policy is a repo-owned override of the upstream `search` skill's instruction not to fall back on authentication/rate-limit errors. Keep upstream skill text unchanged. Exa remains preferred; disclose fallback use, retain source-quality checks, and do not present ordinary search as an equivalent to `agent_run`.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule here.
- After a refresh, re-read both new `description`s and the hosted tool list. If either skill now claims the other's job or one owned elsewhere, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.
- When an approved manual setup or migration adds comments to the live connection, put the following beside its URL. Recheck the selected tools first: an old comment saying `agent_run` is disabled is wrong for this template. Never change the connection to make a stale comment true. Rulesync does not automatically insert these README comments, and upstream skill files remain unchanged.

```jsonc
// ?tools= replaces the default tool list; omitted tools are not exposed.
// This connection includes agent_run; account access, costs and approvals still apply.
```

## Origin

[exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), paths `skills/search/` and `skills/exa-agent/`, commit `0b499f095c4ca145eee07b09137641c037d58449`, copied October 20, 2026. Skill payloads unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server), © Exa Labs. Connection and rule written for this repo.
