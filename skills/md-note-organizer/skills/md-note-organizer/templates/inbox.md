# Inbox template

Fleeting capture: quick, unrelated items with no home yet, or items that belong to a note the user doesn't want changed until the picture is complete. Sort them so they're easy to process later. Don't develop them.

## Frontmatter

Shared properties, plus:

- `status`: `open`, or `processed` once every item has been dealt with.

## Section

`## Items`: one line per item, starting with its label:

- `Idea:` something to build or try. Name the project it might belong to as a link when the material does.
- `Learn:` something to find out or study.
- A to-do is a task line, with `📅` when a date is stated.
- `For [[Existing note]]:` material that belongs to an existing note. Linking it puts it in that note's backlinks without changing the note. Keep "not confirmed" when the material says so.
- `Ephemeral:` a short-lived item, with when it stops mattering. A one-time code or password is still a secret: write where it's kept, or that it was received, never the value.
- `Look up:` a book, product or name to identify later, kept exactly as the user wrote it. Don't complete a title or name from memory.

## Promoting an item

When the user asks, turn an item into a note of the right type, or merge it into the existing note (update mode). Then remove it from the inbox. Set `status: processed` when no items are left.

## Example

```markdown
---
type: inbox
title: Inbox 2026-11-18
created: 2026-11-18
status: open
source: brain dump
tags: [inbox]
---

## Items
- Idea: a local dashboard for homelab backups, maybe part of [[Homelab]]
- Learn: how [[Obsidian]] Bases formulas work
- [ ] Renew the domain before December 1 📅 2026-12-01
- For [[How to rotate the VPN key]]: the phone app may also need a restart (not confirmed)
- Ephemeral: an ISP reset code was received; it's only valid on [[2026-11-18]]
- Look up: a book by Cal Newport whose title starts with "Slow"
```
