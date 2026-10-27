# wait-what

`wait-what` is for the moment an agent's last message doesn't land. It tells the agent to re-pitch it: add the context you're missing and say it in ASD-STE100 Simplified Technical English. If the project has a `GLOSSARY.md` (or a `GLOSSARY-MAP.md` pointing to several), it uses that vocabulary too. Projects without one work fine.

It only runs when you call it.

## Install

From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/wait-what
```

Swap `--targets` for your tools. The `default`, `work` and `writing_reporting` groups include it.

## Use

Type `/wait-what` right after a reply you couldn't follow.

## For agents: install, remove and update

To install, use the `default`, `work` or `writing_reporting` group, or the single-folder command above. It needs no other software and no `GLOSSARY.md`. To verify, start a new session and check that `wait-what` is listed among the skills.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `wait-what` skill folder behind; delete it with approval. It writes no files of its own, and any project `GLOSSARY.md` stays.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The copied commit is in [Origin](#origin); the update bullets in the next section say what to keep.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): it's user-invoked only (`disable-model-invocation`), so the model never chooses it and a routing line would only cost tokens.
- It does not own polishing prose for readers (`humanizer`) or teaching a new subject (`eli5`, `teach`). It only restates the agent's own last message.
- Why: no other installed skill does this.
- `GLOSSARY.md` and `GLOSSARY-MAP.md` are a convention from Matt Pocock's other skills (`grill-with-docs`, `setup-matt-pocock-skills`), which this repo doesn't include. Don't add them just to support this skill; it works without the files.
- The skill is user-invoked only (`disable-model-invocation: true`, kept under the `claudecode:` and `opencode:` sections). Don't remove it.
- On upstream updates, copy the folder unchanged, keep the tool sections, and record the new commit below. If the new description claims a job another skill owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[mattpocock/skills](https://github.com/mattpocock/skills), path `skills/productivity/wait-what/`, commit `5beb35b040e3de97e54fa9e386d7e42d15c295c2`, copied 2026-10-21. Unchanged except that `disable-model-invocation` moved from the top-level frontmatter into the `claudecode:` and `opencode:` sections. [MIT](../../THIRD_PARTY_LICENSES.md#mattpocockskills), © 2026 Matt Pocock. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
