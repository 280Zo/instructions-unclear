# Obsidian syntax the templates rely on

Each entry was checked against the source linked under it.

## Task due dates and done dates (Tasks plugin)

Put the due date at the end of the task line, after the due-date signifier, in `YYYY-MM-DD` form. A finished task can carry its done date after `✅`:

```markdown
- [ ] Alex sends the schedule 📅 2026-05-15
- [x] Set up restic on host B ✅ 2026-11-17
```

Tasks reads only this format. A linked date such as `[[2026-05-15]]` on a task line isn't recognized, so task lines are the one place dates aren't linked. Relative words such as `📅 today` aren't understood either.

Sources: https://github.com/obsidian-tasks-group/obsidian-tasks/blob/main/docs/Getting%20Started/Dates.md, https://github.com/obsidian-tasks-group/obsidian-tasks/blob/main/docs/Reference/Task%20Formats/Tasks%20Emoji%20Format.md

## Collapsed callouts

A minus sign right after the type identifier makes a callout start collapsed. A plus sign makes it start expanded:

```markdown
> [!note]- Alternatives and why each lost
> Text that stays folded until opened.
```

Source: https://obsidian.md/help/callouts

## Embedding part of another note

Put `!` in front of a link to embed it. A heading or block can be embedded on its own, and the embed stays current when the source changes:

```markdown
![[How to rotate the VPN key#Steps]]
```

Source: https://help.obsidian.md/embeds

## Properties

Frontmatter properties have a type: text, list, number, checkbox, date, date and time, or tags. A property name has one type across the whole vault, so the same name must hold the same kind of value in every note. `tags` is a list. Use plain `YYYY-MM-DD` values for Date properties, and quote links: `pick: "[[Vaultwarden]]"`.

Source: https://help.obsidian.md/properties

## Open tasks from notes that link to this note (Dataview)

`TASK` queries list tasks. `FROM [[]]` selects pages that link to the current note. `completed` is true for tasks marked done.

````markdown
```dataview
TASK
FROM [[]]
WHERE !completed
```
````

Sources: https://blacksmithgu.github.io/obsidian-dataview/queries/query-types/, https://blacksmithgu.github.io/obsidian-dataview/reference/sources/, https://blacksmithgu.github.io/obsidian-dataview/annotation/metadata-tasks/

## Reopening an OpenCode session

`opencode session list` lists top-level sessions for the current project. `opencode mini --session <id>` reopens a specific session in the minimal interface. Run them from the folder where the session worked.

Source: https://opencode.ai/docs/cli/commands/

For other tools, record the session ID, the tool and the folder. Write a reopen command only when that tool's documentation gives one.
