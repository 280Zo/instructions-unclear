# screenshot

Desktop/system screenshot capture with OS-specific helpers. Included in `default`, `work` and `infosec`; independently selectable.

## Install

From the repo root:

```bash
npx rulesync@41.0.0 generate --global --features skills --input-roots skills/screenshot
```

All Python, shell, Swift and PowerShell helpers, references and interface assets are retained. This does not install capture utilities or grant screen access. Use one installer per destination; legacy native Codex and rulesync 38 use different default directories (`~/.codex/skills` and `~/.agents/skills`). Review existing duplicates before separately approving cleanup.

## Use and boundaries

Approve the screen/window, sensitive content exposure and output path before capture. Linux uses available tools such as `scrot`, `gnome-screenshot` or ImageMagick `import`; macOS/Windows have their own helpers and permissions. Default OS screenshot locations can be outside the approved workspace. Upstream Screen Recording prompts, Windows execution-policy examples and sandbox escalation advice are not authorization to weaken permissions or bypass denied access. Resolve helpers from their actual installed directory. Packaging checks do not perform desktop capture or establish host compatibility.

## For agents: install, remove and update

To install, use the `default`, `work` or `infosec` group, or the single-folder command above. rulesync doesn't install a capture utility (`scrot`, `gnome-screenshot`, ImageMagick or the OS helper), and installing one follows `package-management`. To verify, start a new session and check that `screenshot` is listed among the skills. Don't take a screenshot as a test unless the user approves the screen and output path.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `screenshot` skill folder behind; delete it with approval. Screenshots already taken and any capture utility stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The pinned commit is in [Updating and origin](#updating-and-origin); the update bullets in the next section say what to recheck.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): its description already limits it to desktop or window capture when tool-specific capture isn't available, so it doesn't compete with `playwright-cli`.
- It does not own browser automation, including screenshots of a page being driven in a browser: those go to `playwright-cli`.
- Why: `screenshot` and `playwright` both claimed capturing screenshots.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/screenshot/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; preserve every OS helper and executable mode and regenerate affected selections when updating.

Publisher: OpenAI. Apache-2.0; the license retains unfilled copyright-example boilerplate, not a named holder. Original [LICENSE.txt](skills/screenshot/LICENSE.txt) and [consolidated terms](../../THIRD_PARTY_LICENSES.md#openaiskills) are retained. Wrapper written for this repo by 280Zo.
