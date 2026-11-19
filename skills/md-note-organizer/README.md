# md-note-organizer

A skill that turns raw material into Obsidian notes in one house style: brain dumps, rough notes, transcripts, AI chat sessions, research findings, project updates, journal thoughts, images and files.

It has a template for each kind of note:

| Template | For |
|---|---|
| Meeting | Decisions, action items, open questions and the details worth keeping |
| How-to | Steps you'll follow again, with what you need first, how to check it worked and how to undo it |
| Research | Options compared against your needs, the pick, and when to revisit it |
| Inbox | Quick, unrelated items to sort later |
| Session recap | An AI chat session: what was decided, where things are, and how to reopen it |
| Project | Status, blockers and tasks first, then a dated log |
| Journal | A first-person story of a memory, written after a short interview |

Every note gets frontmatter with shared properties (`type`, `title`, `created`, `tags`, plus `project`, `related` and `source` when known), so Dataview and Bases queries work across note types. Body dates are `[[YYYY-MM-DD]]` links, task lines use the Tasks plugin's `📅` dates, and the reasoning behind a choice sits at the bottom in a collapsed callout. The skill never invents owners, dates or details, keeps `Unknown speaker N` and `[unclear: ...]` markers as written, writes secrets as pointers to your password manager instead of their values, and runs [`humanizer`](../humanizer/) over the prose.

## Install

Skills are added alongside what you already have, so this folder can be installed on its own. From the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/md-note-organizer
```

Swap `--targets` for your tools. To keep it in your regular install, add `skills/md-note-organizer` to `inputRoots` in your `rulesync.local.jsonc`.

## Use

Paste the material or attach files and ask for notes: "turn this into meeting notes", "make a how-to from this chat", "stash these thoughts in my inbox". It asks first when it needs to: what a meeting was for, which notes to split mixed material into, or questions for a journal entry.

| Ask | It does |
|---|---|
| A new note from material | Picks the template, or asks |
| "Update this note" with new material | Merges the material in, flags conflicts, and logs what changed |
| "Refresh this research note" | Re-checks each item online, when the session has a search tool |
| "Review my inbox" | Suggests an action per item, then carries out what you approve |
| "Make a shareable version" | A copy without personal details or private remarks, plus a list of what it removed |

Notes come back as Markdown blocks to paste. If you name your vault folder, it can find and update notes there instead, showing each change and writing only after you say yes.

For a broader write-up of gathered material for an audience, use [`report`](../report/). For a document another AI session picks up, use [`handoff`](../handoff/).

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default), [`work`](../../groups/README.md#work) and [`writing_reporting`](../../groups/README.md#writing_reporting) groups install it globally. For this folder alone, use the command under [Install](#install) above; it skips `rules/routing`.
- The prose pass uses `humanizer`, which the groups above include. Images and scanned files are read with whatever reader or OCR tool the assistant has, such as the Docling MCP server. Refresh mode needs a web search tool.
- In OpenCode's default install, the `build`, `plan` and `general` agents can load it.
- To verify, start a new session and confirm the skills list includes `md-note-organizer`.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `md-note-organizer` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

### Update

The skill is written for this repo, so there is no upstream commit to check. `reference/obsidian.md` records the plugin syntax the templates rely on, each with its source. Recheck those sources when Obsidian, Tasks or Dataview change their syntax.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Notes** from raw material (meeting notes, how-tos, research, inbox, session recaps, projects, journal): `md-note-organizer`". Audience write-ups stay with `report`, AI-to-AI handoffs with `handoff`, and epics, features and user stories made from notes with `work-item-writer`.
- It doesn't own prose editing: the final pass follows `humanizer`'s rules.
- Don't add a per-skill routing rule to this folder. If its job changes, update `rules/routing`, this section and `report`'s routing section in the same change, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE), © 280Zo. Its handling of decisions, action items and reopened points draws on [Scratchpad's `meeting-notes` skill](https://github.com/phillips-jon/note-taking-skills/blob/d8eb3202a1e896f1b3ccaccfea38475e9a7468e7/plugins/everyday-notes/skills/meeting-notes/SKILL.md) (commit `d8eb3202a1e896f1b3ccaccfea38475e9a7468e7`), rewritten rather than copied. [MIT](../../THIRD_PARTY_LICENSES.md#phillips-jonnote-taking-skills), © 2026 Scratchpad (Jon C. Phillips).
