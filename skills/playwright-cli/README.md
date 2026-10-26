# playwright-cli

Microsoft's own skill for driving a real browser from the terminal with `playwright-cli`: open pages, click, type and fill, take accessibility snapshots and screenshots, mock requests, save storage state, trace, record video, and run or generate Playwright tests. Microsoft recommends this CLI-and-skill pair over the Playwright MCP server for coding agents, because it keeps tool schemas and page trees out of the context. Its description is about 10 words.

It replaced OpenAI's deprecated `playwright` copy on 2026-10-24. It's in `default`, `work` and `infosec`.

## Install

From the repo root, through an [install group](../../groups/), or just this skill:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/playwright-cli
```

rulesync installs only the skill. The skill runs `playwright-cli`, or `npx playwright cli` from a project that has `@playwright/cli` installed locally. The skill text suggests `npm install -g @playwright/cli@latest`; your `package-management` rule takes precedence, so the agent asks first and prefers a pinned, project-local install.

Upstream's own installer (`playwright-cli install --skills`) copies the same skill into `.claude/skills` or `.agents/skills`. Use one or the other for each tool, not both.

### Removing the old skill

`delete: false` means regeneration leaves the old `playwright` skill in place (for example `~/.config/opencode/skills/playwright/`). Both would then be offered for browser work. Remove the old folder from each tool once `playwright-cli` is installed and working; agents ask before deleting it.

## For agents: install, remove and update

1. Install with a group or the command above. Check `playwright-cli --version` or `npx --no-install playwright --version`; if neither works, propose a pinned project-local `npm install -D @playwright/cli@<version>` and wait for approval. Don't install it globally unless the user asks.
2. Verify by asking the agent to open a harmless page (for example `https://playwright.dev`) and take a snapshot. Don't submit forms or log in as a smoke test.
3. Remove the stale `playwright` skill folder from each tool's skills directory only after the user approves, and only after step 2 passes.
4. Not in [`rules/routing`](../../rules/routing/rules/routing.md): `screenshot`'s description already defers to tool-specific capture, so browser automation and page screenshots stay here without a routing line.
5. To remove this skill itself, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `playwright-cli` skill folder behind; delete it with approval. An installed `@playwright/cli`, its browser downloads and any saved storage state, traces or videos stay unless the user asks.
6. To update, follow [Check for updates](../../AGENTS.md#check-for-updates): compare the recorded tag in [Origin](#origin) with upstream's latest release, diff `skills/playwright-cli/`, copy the folder unchanged, and reapply the one adaptation below.

## Changes from upstream

Upstream's top-level `allowed-tools` line is moved, unchanged, under a `claudecode:` section in `SKILL.md`, because rulesync drops tool-specific fields it finds at the top level. Nothing else changed.

## Origin

[microsoft/playwright-cli](https://github.com/microsoft/playwright-cli), `skills/playwright-cli/`, tag v0.1.22, commit `b85c7a736bb473bf55b584e54a09ffa698d6d871`, copied 2026-10-24. [Apache 2.0](../../THIRD_PARTY_LICENSES.md#microsoftplaywright-cli), © Microsoft Corporation. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
