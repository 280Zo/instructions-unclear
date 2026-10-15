---
root: true
targets: ["*"]
description: "Web research: Exa for discovery and retrieval, webfetch only for narrow cases"
---

### Web Research

**Source priority:** prefer current official documentation and primary sources
(vendor docs, specifications, the project's own repository and changelog).
Check version and date applicability. Forums, posts and Q&A are secondary:
use them to fill gaps, label them, and corroborate consequential advice. They
do not silently override applicable official docs. Model memory and cached
summaries are search leads, never the sole support for an external factual
claim. Read the current source before citing it. If official evidence is
missing, inaccessible or conflicting, disclose that and state uncertainty
instead of inventing a citation or falling back silently to recollection.

`webfetch` is a raw HTTP GET, not a search engine. Using it to "look something
up" means guessing a URL — your most common source of confident wrong answers.

- **Discovery → `exa_web_search_exa`.** Mandatory for any find/research/what-is/
  which-library question, even when you think you know the answer. Use
  `exa_web_search_advanced_exa` for category, domain, date or highlight filters.
- **Retrieval from a known URL → `exa_web_fetch_exa`.** Clean markdown, batched
  URLs, `maxCharacters`. Measured on one GitHub page, `webfetch` returned ~7k
  chars of nav chrome and base64 badges before any content.
- **`webfetch` only for:** localhost/private IPs; `format: html|text` where raw
  markup matters; a URL the user or these instructions gave you; Exa failing.
- **Never build a doc URL from memory.** No user/file/Exa source → search first.
- Breaking these is allowed. Doing it silently is not.

Built-in `websearch` is unauthenticated Exa and is off here. Don't ask for it.
