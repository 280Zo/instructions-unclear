# Docling

[Docling MCP](https://github.com/docling-project/docling-mcp) converts documents and images (PDF, Office files, scans) into text the AI can read, including OCR and tables.

## What's in this folder

| File | Becomes |
|---|---|
| `mcp.jsonc` | The `docling` entry in OpenCode's MCP server list |
| `rules/docling.md` | The "Docling MCP" section of `AGENTS.md` |

## Install

1. Install the server once with [uv](https://docs.astral.sh/uv/). The `[local]` extra does conversion on your machine and is a large download:

   ```bash
   uv tool install 'docling-mcp[local]'
   ```

2. This folder adds a rule and an MCP server, and rulesync installs both by replacing your tool's whole set. So add `mcp-servers/docling` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features rules,mcp`.

The MCP entry runs the installed `docling-mcp-server`. Update it with `uv tool upgrade --all`.

## Use

Point the agent at a file by path: "read `/path/report.pdf` and summarize section 3", "pull the tables out of `invoice.pdf`", "what does this scanned letter say?". The rule makes it convert with Docling (including OCR for scans and table extraction) instead of writing its own conversion scripts, and convert one file at a time, since parallel conversions collide. For a whole folder, ask for the folder and it converts the batch in one call. Converted documents are cached in `/tmp/opencode/docling`.

## Why the settings look the way they do

- **`conversion generation` (the tool groups).** The default set is "conversion generation manipulation": 19 tools, all loaded into every request. Dropping "manipulation" leaves 14 and removes the in-place editing tools (`get_overview_of_document_anchors`, `search_for_text_in_document_anchors`, `get_text_of_document_item_at_anchor`, `update_text_of_document_item_at_anchor`, `delete_document_items_at_anchors`). "generation" is required: `export_docling_document_to_markdown` lives there, so "conversion" alone can convert but never read the result.
- **`CACHE_DIR`** has no `DOCLING_MCP_` prefix on purpose: Docling reads exactly `CACHE_DIR`. Without it, converted documents are saved inside the installed package's folder. If the AI isn't allowed to read that folder, the only way to see a converted document is a full export that always starts at page 1, which is unusable past about 5 pages. `/tmp/opencode/docling` is a folder the AI can read; change it to suit your setup.
- **`DOCLING_MCP_KEEP_IMAGES=true`** is required by the `page_thumbnail` tool. Without it the tool fails with "The Docling document has no images."

- **`timeout: 300000`** (5 minutes): large conversions can exceed the default.

## Permissions depend on the server's name

OpenCode names each tool `<server name>_<tool>`, e.g. `docling_convert_...`. Permission rules such as `"docling_*": "allow"` match on that name. If you rename the server here, that rule silently stops matching and every Docling call starts asking for approval. Rename it in your permission rules too.
