# handoff

`handoff` writes a short document that lets a fresh agent session pick up where this one left off. It summarizes the conversation, points to specs, plans, issues and commits by path or URL instead of copying them, suggests which skills the next agent should load, and redacts secrets and personal information. Upstream saves it to your OS temp folder (`$TMPDIR`, else `/tmp`), not the project.

It only runs when you call it. It is never loaded automatically.

## Install

From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/handoff
```

Swap `--targets` for your tools. The `default`, `work` and `writing_reporting` groups include it.

## Use

- `/handoff` before you close a long session or switch tools.
- `/handoff next session reviews the PR` tailors the document to what comes next.

Then start the new session and point it at the file it saved.

## For agents: install, remove and update

To install, use the `default`, `work` or `writing_reporting` group, or the single-folder command above. It needs no other software. To verify, start a new session and check that `handoff` is listed among the skills. Don't run `/handoff` as a test unless the user wants a handoff document.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `handoff` skill folder behind; delete it with approval. Handoff documents it already saved in the OS temp folder are the user's files and stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The copied commit is in [Origin](#origin); the update bullets in the next section say what to keep.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): it's user-invoked only (`disable-model-invocation`), so the model never chooses it and a routing line would only cost tokens (removed 2026-10-24). The `local-model` agent's own pause/resume notes are separate and need no routing.
- It does not own the `local-model` agent's pause/resume notes. That agent writes its own `local-model-handoff.md` as part of its working style; leave that alone when the user is running it.
- Why: added on 2026-10-21 after an overlap check against the existing skills and agents. The only neighbor was `local-model`'s built-in handoff, which serves one agent's loop, so the user approved `handoff` as the general one.
- The skill is user-invoked only (`disable-model-invocation: true`, kept under the `claudecode:` and `opencode:` sections so rulesync passes it to both). Don't remove it to make the skill load automatically.
- On upstream updates, copy the new folder unchanged, keep the tool sections, and record the new commit below. Don't edit the upstream text to change routing. If the new description claims a job another skill owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[mattpocock/skills](https://github.com/mattpocock/skills), path `skills/productivity/handoff/`, commit `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, copied 2026-10-21. Unchanged except that `argument-hint` and `disable-model-invocation` moved from the top-level frontmatter into the `claudecode:` (both) and `opencode:` (`disable-model-invocation`) sections. [MIT](../../THIRD_PARTY_LICENSES.md#mattpocockskills), © 2026 Matt Pocock. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
