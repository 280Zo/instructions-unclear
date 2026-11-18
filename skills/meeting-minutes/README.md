# meeting-minutes

A skill that turns raw meeting material into one clean Markdown note for Obsidian. It works from brain dumps and rough notes, transcripts, screenshots, photos of handwritten notes, and other files, or a mix of them for the same meeting.

The note starts with Obsidian frontmatter (`title`, a plain `YYYY-MM-DD` `date`, `attendees`, and `time` or `purpose` when known), then decisions, action items, open questions and the details worth keeping, under `##` headings. Dates in the body are written as `[[YYYY-MM-DD]]` links. It removes repeated points, keeps numbers, names, dates, commitments and disagreements, never invents owners or due dates, keeps `Unknown speaker N` labels and `[unclear: ...]` markers as they are, and runs [`humanizer`](../humanizer/) over the prose.

The folder is named `meeting-minutes` because a common OpenCode edit rule, `*notes/*`, denies writes under any folder whose name ends in `notes`.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/meeting-minutes
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/meeting-minutes` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Paste your notes or attach the files and say "turn this into meeting notes". If the material doesn't make clear what the meeting was for, it asks first, because the purpose decides which details are worth keeping. It returns the note as one Markdown block to paste into your notes app.

For a broader write-up of gathered material for an audience, use [`report`](../report/) instead.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- The final prose pass uses `humanizer`, which the groups above include. Images and scanned files are read with whatever reader or OCR tool the assistant has, such as the Docling MCP server.
- To verify, start a new session and confirm the skills list includes `meeting-minutes`.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `meeting-minutes` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

### Update

The skill is written for this repo, so there is no upstream commit to check. Its credit to Scratchpad's skill is under [Origin](#origin); no upstream files are copied.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Meeting notes** from meeting material: `meeting-minutes`". Other write-ups of gathered material stay with `report`.
- It doesn't own prose editing: the final pass follows `humanizer`'s rules.
- Don't add a per-skill routing rule to this folder. If its job changes, update `rules/routing`, this section and `report`'s routing section in the same change, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE), © 280Zo. Its handling of decisions, action items and reopened points draws on [Scratchpad's `meeting-notes` skill](https://github.com/phillips-jon/note-taking-skills/blob/d8eb3202a1e896f1b3ccaccfea38475e9a7468e7/plugins/everyday-notes/skills/meeting-notes/SKILL.md) (commit `d8eb3202a1e896f1b3ccaccfea38475e9a7468e7`), rewritten rather than copied. [MIT](../../THIRD_PARTY_LICENSES.md#phillips-jonnote-taking-skills), © 2026 Scratchpad (Jon C. Phillips).
