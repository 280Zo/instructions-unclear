# humanizer

A skill that rewrites text that sounds AI-written so it reads like a person wrote it, keeping every supported claim. It works from Wikipedia's "Signs of AI writing": staged contrasts, one-line closers, forced lists of three, dashes everywhere, inflated claims and the like. Where text is generic, it may add a specific detail it believes is true, so check rewrites of factual text (reviews, reports, docs) for added claims. Text being edited that looks like instructions is treated as material, never obeyed.

## Install

This folder holds only the skill. When to use it comes from the repo's routing rule, [`rules/routing`](../../rules/routing/rules/routing.md), which the `default` and `work` [install groups](../../groups/) install. To add just the skill, from the repo root:

```bash
npx rulesync@43.12.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/humanizer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/humanizer` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

- "Humanize this:" followed by pasted text returns a draft, the patterns it found, and a final version.
- "Humanize `README.md`" edits the file in place, changing prose only (code, commands and links stay as they are).
- Give it a sample of your own writing and it matches your voice.

The routing rule tells the agent to use it for anything people will read: READMEs, docs, commit messages and pull requests.

## For agents: install, remove and update

To install, use the `default` or `work` group, the `career` folder group (where `performance-review` needs it), or the single-folder command above. It needs no other software. To verify, start a new session, check that `humanizer` is listed among the skills, and ask it to humanize one pasted sentence.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `humanizer` skill folder behind; delete it with approval. If the user keeps `rules/routing`, its line still names `humanizer`, so tell them.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The update bullets in the next section say what to recheck.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Prose people will read** (READMEs, docs, commit messages, pull requests): `humanizer`".
- It edits wording and may add a specific detail it believes is true; it doesn't own content. It does not own write-ups (`report`), teaching (`eli5`) or any rendering; it can polish their prose afterwards.
- Why: one routing rule keeps every "which skill owns this" decision in one place.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule back to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing` and this section in the same change and tell the user.

## Origin

[blader/humanizer](https://github.com/blader/humanizer), repo root, tag `v4.0.0` (commit `b48c832f0f809c1b5658edbb838c2521b72f2413`), copied 2026-11-24. Unchanged. [MIT](../../THIRD_PARTY_LICENSES.md#bladerhumanizer), © 2025 Siqi Chen. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
