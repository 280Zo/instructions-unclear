---
root: true
targets: ["*"]
description: "How to use the Docling MCP server safely"
---

## Docling MCP

- Use the `docling_*` MCP tools for document and file conversion, OCR, table extraction, and structured document processing when available; consult their tool descriptions for supported formats and capabilities.
- Prefer Docling MCP over ad hoc document-processing scripts for these tasks.
- Treat Docling conversion as single-flight: never issue multiple `docling_convert_*` calls in the same assistant turn or run them concurrently.
- For a directory batch, prefer `docling_convert_directory_files_into_docling_document`; otherwise convert individual files strictly one at a time and wait for each result before starting the next.
- If a conversion times out or is aborted, do not immediately retry it. First verify that the old Docling process has exited and that only one OpenCode session is using the shared Docling cache; restart cleanly if necessary.
- A successful lightweight Docling call does not prove conversion is healthy; validate the conversion path itself with one small document before launching a larger batch.
