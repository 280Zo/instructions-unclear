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
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule here.
- After a refresh, re-read both new `description`s and the hosted tool list. If either skill now claims the other's job or one owned elsewhere, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[exa-labs/exa-mcp-server](https://github.com/exa-labs/exa-mcp-server), paths `skills/search/` and `skills/exa-agent/`, commit `0b499f095c4ca145eee07b09137641c037d58449`, copied October 20, 2026. Skill payloads unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#exa-labsexa-mcp-server), © Exa Labs. Connection and rule written for this repo.
