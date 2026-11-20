# meeting-brief

A skill that catches you up before a meeting. Give it a meeting and it searches everything it can reach for the topic, the projects and the people on the invite, then gives you:

- a TLDR: what the meeting is about, where things stand, what changed since you last looked, and what you'll probably be asked for
- a short catch-up, newest first
- the top 5 things to bring, each marked as a follow-up (something owed, yours first), a question or a comment

Every point names its source and date, so you can check it before you rely on it. The brief ends with the sources it checked and the ones it couldn't reach.

It only reads. It never sends, replies or changes anything in your notes or tools. Ask it to email or message something and you get a draft to send yourself.

## Install

The [`work`](../../groups/README.md#work) group installs it. For this folder alone, from the repo root:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/meeting-brief
```

Swap `--targets` for your tools.

## Use

Ask before a meeting: "prep me for my meetings today", "brief me for this", or paste the invite.

| Ask | It does |
|---|---|
| "Prep me for my remaining meetings today" | Uses a connected calendar tool. Without one, it asks you to paste the meetings |
| A pasted invite (title, time, description, attendees) | One brief. Several invites get one brief each, in start-time order |
| "Just give me the questions" | Only the top 5, still with sources |
| "Save it" | Shows the exact note it would add to your vault and writes it only after you say yes to that content |

Where it looks, when it can:

| Source | Needs |
|---|---|
| Your Obsidian vault, in [`md-note-organizer`](../md-note-organizer/)'s format: open action items and questions from earlier meetings, project status and blockers | The vault's path, from you or your own instructions |
| Your work log from the [career workspace](../career-workspace/) (`performance/*/entries/`) | The workspace's path. It uses the entries' facts only, never their goal, highlight or "above and beyond" fields |
| PMB memory | The PMB MCP server |
| Slack, Teams, email, Notion or another messaging or notes app | A connected tool for it in your session |
| Your calendar | A connected calendar tool |

It asks for the vault and workspace paths when it doesn't know them, and never searches your disk for them. Names that might match ("J. Doe" on the invite, Jane Doe in your notes) are marked unconfirmed. A note that holds a password or token is named, and its value never appears in the brief.

The saved note is the start of a meeting note: the brief under `## Prep`, with empty Decisions, Action items, Open questions and Details sections. After the meeting, `md-note-organizer` can fill them in.

## For agents: install, remove and update

### Install

- The [`work` group](../../groups/README.md#work) installs it globally. It isn't in `default` or `rulesync.jsonc`. For this folder alone, use the command under [Install](#install) above.
- It needs no software. Calendar, messaging, email, notes and PMB tools are used only when the session already has them; the skill adds no connection.
- It reads files outside the session folder (the vault and the career workspace), so OpenCode may ask permission for those reads.
- To verify, start a new session and confirm the skills list includes `meeting-brief`.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `meeting-brief` in each tool's global skills folder; delete it only with approval. No other folder in this repo provides that name.

### Update

The skill is written for this repo, so there is no upstream commit to check. If `md-note-organizer`'s meeting template or `performance-log`'s entry format changes, update the fields this skill reads and writes in the same change.

## For agents: routing and updates

- No line in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed skill prepares for a meeting. `md-note-organizer` turns material into notes after the meeting, and the career skills own the work log and reviews.
- Don't add a per-skill routing rule to this folder. If its job changes so it competes with another skill, add the line to `rules/routing`, update this section, and tell the user.

## Origin

Written for this repo. [MIT](../../LICENSE), © 280Zo.
