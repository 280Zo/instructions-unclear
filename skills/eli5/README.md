# eli5

A skill that teaches one unfamiliar thing in plain English: a concept, an event, a mechanism, a protocol, a paper.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/eli5
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/eli5` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Type `/eli5 <topic>`, or ask "how does X work?" or "explain like I'm five". It researches, then teaches in short turns and checks you can use each idea. At the end it offers to save a one-page explainer; that needs [`visual-explainer`](../visual-explainer/) and [`diagram-design`](../diagram-design/).

To write up material you've already gathered, use [`report`](../report/) instead.

## Notes

Claude Code's `allowed-tools` sits under a `claudecode:` section so other tools ignore it.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- The saved explainer needs `visual-explainer` and `diagram-design`, and research uses Exa `search` when it's installed. The groups above include them; the single-folder command doesn't.
- To verify, start a new session and confirm the skills list includes `eli5`, or that `/eli5` is offered.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `eli5` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name. Explainer pages it already saved stay.

### Update

The skill is written for this repo, so there is no upstream commit to check. Keep the `claudecode: allowed-tools` section when syncing a live copy back (see the tool-sections table in `AGENTS.md`), and follow the routing bullets below when a renderer it uses changes.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Teaching** one unfamiliar thing: `eli5`". Writing up material already gathered is `report`'s job. A course spread over several sessions is `teach`'s, which the user starts with `/teach`, so it has no routing line.
- It doesn't own rendering: the saved explainer page goes to `visual-explainer`, with its diagram drawn by `diagram-design`. Web discovery during research goes to Exa `search`.
- Why: `eli5` delegates its page to `visual-explainer`, so it has to follow the same owners as everything else.
- The skill is written for this repo, so its own text can be adjusted to match routing, but `rules/routing` stays the single source: change the rule first and keep this skill consistent with it.
- Don't add a per-skill routing rule to this folder. When a renderer it uses is added, removed or refreshed and its job changes, update `rules/routing`, this skill's references to it and this section in the same change, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE).
