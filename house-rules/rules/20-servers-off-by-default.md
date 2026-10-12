---
root: true
targets: ["*"]
description: "MCP servers that are intentionally disabled and how to ask for them"
---

### Servers that are off by default

A disabled MCP server contributes no tools and is invisible to you, so you will
not notice it is missing. This one is intentionally off:

- **GitHub MCP.** For live repo state (is this PR merged, is this issue open)
  prefer the `gh` CLI, which costs no resident tokens. Use Exa for discovery
  (finding projects, star counts, reading around an issue) — but remember Exa is
  a search index and is stale for exact current state. If a task genuinely needs
  the GitHub MCP, say so and ask me to enable it; it needs a restart.
