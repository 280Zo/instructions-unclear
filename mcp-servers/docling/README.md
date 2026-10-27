# Docling

[Docling MCP](https://github.com/docling-project/docling-mcp) converts documents and images (PDF, Office files, scans) into text the AI can read, including OCR and tables.

Extraction, picture descriptions and durable knowledge are separate things. Retained pixels and OCR do not enable captions, visual search or automatic PMB ingestion. Current upstream has opt-in picture-description settings, but the installed version must be checked before changing this setup.

## What's in this folder

| File | Becomes |
|---|---|
| `mcp.jsonc` | The `docling` entry in OpenCode's MCP server list |
| `rules/docling.md` | The "Docling MCP" section of `AGENTS.md` |

## Install

1. Have [uv](https://docs.astral.sh/uv/) available. The MCP entry selects the reviewed release; the `[local]` extra does conversion on your machine and is a large download:

   ```bash
   uvx --from 'docling-mcp[local]==3.3.0' docling-mcp-server conversion generation --transport stdio
   ```

2. This folder adds a rule and an MCP server, and rulesync installs both by replacing your tool's whole set. So add `mcp-servers/docling` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features rules,mcp`.

That is the launch command, not an extra server to start alongside your assistant's process. Reviewed runtime baseline: `docling-mcp 3.3.0`, checked October 20, 2026. First launch may download dependencies; approve that operation before enabling it. The top-level package is pinned, not the whole transitive dependency graph. Refresh this README and `mcp.jsonc` together when reviewing a new release; do not use a blanket live-tool upgrade as a substitute.

## Use

Point the agent at a file by path: "read `/path/report.pdf` and summarize section 3", "pull the tables out of `invoice.pdf`", "what does this scanned letter say?". The rule makes it convert with Docling (including OCR for scans and table extraction) instead of writing its own conversion scripts, and convert one file at a time, since parallel conversions have collided in this setup. For a whole folder, ask for the folder and it converts the batch in one call. `/tmp/opencode/docling` is shared scratch output, not project-owned archival storage. Save durable exports and required image assets explicitly inside the authorized project.

## Why the settings look the way they do

- **`conversion generation` (the tool groups).** Selects conversion and export/generation while omitting anchor-editing manipulation tools. Counts and context exposure depend on server/client versions; inspect the catalog rather than relying on a fixed historical count. `export_docling_document_to_markdown` belongs to generation.
- **`CACHE_DIR`** has no `DOCLING_MCP_` prefix: the server reads exactly `CACHE_DIR` for filesystem output. The upstream in-process document cache is separate and not a durable database or automatic restart recovery mechanism. This template's fixed temporary path is not project isolation; a project-contained output design requires a separate approved configuration change.
- **`DOCLING_MCP_KEEP_IMAGES=true`** retains page pixels needed for thumbnails. It does not enable VLM descriptions or guarantee the client/model receives usable original-resolution images. Save structured exports with their required images/provenance for durable use.

- **`timeout: 300000`** (5 minutes): large conversions can exceed the default.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `docling_convert_...`. Permission rules such as `"docling_*": "allow"` match on that name. If you rename the server here, that rule silently stops matching and every Docling call starts asking for approval. Rename it in your permission rules too.

## For agents: install, remove and update

### Install

- It's in the `default` and `work` [install groups](../../groups/README.md), and `writing_reporting` installs its rule but leaves MCP settings alone. Follow [Install](#install) above.
- It needs [uv](https://docs.astral.sh/uv/). The first launch downloads `docling-mcp[local]==3.3.0` and its large dependencies, so get the user's approval first.
- The connection is written switched on.
- To verify, check in a new session that `docling` connects, then convert one small harmless document. Convert one file at a time, as `rules/docling.md` says.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `docling` MCP entry and the "Docling MCP" rule section, because each run replaces both.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- If the user syncs a native V2 config without the `mcp` feature, remove the `docling` entry from `mcp.servers` by hand, keeping every other setting.
- The uv cache, downloaded models and the scratch output in `/tmp/opencode/docling` stay. Never delete them without the user's explicit approval. Permission rules such as `"docling_*"` are the user's to keep or remove.

### Update

- Follow [Check for updates](../../AGENTS.md#check-for-updates). The pin is `docling-mcp[local]==3.3.0` in `mcp.jsonc`. Change it together with the version and baseline text in [Install](#install).
- Then follow the update bullets in [For agents: routing and updates](#for-agents-routing-and-updates).

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): this folder's `rules/docling.md` already makes Docling the tool for converting, OCR and extracting text or tables, so a routing line would repeat it. Creating and editing Office files stays with `documents` through the routing rule.
- It does not own creating or editing Office and PDF files: that is the `documents` skill. Speech to text is `transcribe`.
- Why: The `documents` skill also covers extraction, so the rule keeps reading with Docling and authoring with `documents`.
- `rules/docling.md` stays in this folder: it covers how to run Docling (one conversion at a time, timeouts, cache) and already says to prefer Docling for reading documents, so `rules/routing` doesn't repeat that. If another installed skill starts competing for document reading, add a line there.
- When reviewing a new Docling release or tool groups, or refreshing `documents`, check whether either now claims the other's job. If so, update `rules/routing` and this section in the same change and tell the user.
- During an approved manual configuration setup or migration, retain the rationale above as comments beside the matching settings. The comments below describe this template, not every upstream release; recheck them when changing the settings. Rulesync does not automatically insert README comments into the live config. Do not restore historical fixed tool counts.

```jsonc
// conversion + generation keep document import and export; manipulation is omitted.
// CACHE_DIR is intentionally unprefixed and points to temporary filesystem output.
// Retain page images for thumbnails; this does not enable VLM descriptions.
// Allow five minutes for large conversion requests.
```
