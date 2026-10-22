# screenshot

Desktop/system screenshot capture with OS-specific helpers. Included in `default`, `work` and `infosec`; independently selectable.

## Install

From the repo root:

```bash
npx rulesync@38.0.0 generate --global --features skills --input-roots skills/screenshot
```

All Python, shell, Swift and PowerShell helpers, references and interface assets are retained. This does not install capture utilities or grant screen access. Use one installer per destination; legacy native Codex and rulesync 38 use different default directories (`~/.codex/skills` and `~/.agents/skills`). Review existing duplicates before separately approving cleanup.

## Use and boundaries

Approve the screen/window, sensitive content exposure and output path before capture. Linux uses available tools such as `scrot`, `gnome-screenshot` or ImageMagick `import`; macOS/Windows have their own helpers and permissions. Default OS screenshot locations can be outside the approved workspace. Upstream Screen Recording prompts, Windows execution-policy examples and sandbox escalation advice are not authorization to weaken permissions or bypass denied access. Resolve helpers from their actual installed directory. Packaging checks do not perform desktop capture or establish host compatibility.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "Desktop or window screenshots: `screenshot`".
- It does not own browser automation, including screenshots of a page being driven in a browser: those go to `playwright`.
- Why: on 2026-10-21 the user replaced the per-skill rules with one routing rule because several skills' descriptions and rules claimed the same jobs. Here, `screenshot` and `playwright` both claimed capturing screenshots.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/screenshot/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; preserve every OS helper and executable mode and regenerate affected selections when updating.

Publisher: OpenAI. Apache-2.0; the license retains unfilled copyright-example boilerplate, not a named holder. Original [LICENSE.txt](skills/screenshot/LICENSE.txt) and [consolidated terms](../../THIRD_PARTY_LICENSES.md#openaiskills) are retained. Wrapper written for this repo by 280Zo.
