# playwright

Terminal browser automation through Playwright CLI, rather than test-spec authoring. Included in `default`, `work` and `infosec`; independently selectable.

## Install context

From the repo root:

```bash
npx rulesync@38.0.0 generate --global --features skills --input-roots skills/playwright
```

The full wrapper, references, interface assets, license and Microsoft notice are retained. Context generation installs neither Node/npm, the CLI nor browser binaries.

## Runtime and approval boundaries

The unchanged wrapper uses `npx --yes --package @playwright/cli playwright-cli`; upstream also describes optional global installation. This source pin does **not** pin that runtime package. Follow higher-priority package policy: use reviewed project-local tooling where appropriate, approve downloads, and do not automatically execute the wrapper or install global tools. A skills install does not authorize browser form submissions or other state-changing operations.

Upstream examples assume `$CODEX_HOME/skills/playwright`, normally under `~/.codex`; rulesync 38's global Codex output uses `~/.agents/skills`, and other hosts differ. Resolve the actual installed helper directory; do not globally change `CODEX_HOME` or rewrite the payload to hide a mismatch. Choose one installer per destination and review live duplicate copies separately. Packaging tests do not launch a browser or verify runtime compatibility.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): `screenshot`'s description already defers to tool-specific capture, so browser automation and page screenshots stay with `playwright` without a routing line (removed 2026-10-24 to save tokens).
- It does not own desktop or window screenshots: those go to `screenshot`. Installing or running the Playwright CLI follows `package-management`, not the wrapper's `npx --yes` line.
- Why: on 2026-10-21 the user replaced the per-skill rules with one routing rule because several skills' descriptions and rules claimed the same jobs. Here, `playwright` and `screenshot` both claimed capturing screenshots.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/playwright/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; preserve full supporting content, executable modes and notices when reviewing a new revision, then regenerate affected selections.

Apache-2.0; [LICENSE.txt](skills/playwright/LICENSE.txt) names **Microsoft Corporation**. [NOTICE.txt](skills/playwright/NOTICE.txt) identifies material from `microsoft/playwright-cli` and OpenAI's Codex adaptations. Full [terms/notice](../../THIRD_PARTY_LICENSES.md#openaiskills) are consolidated. Source publisher: OpenAI; wrapper written for this repo by 280Zo.
