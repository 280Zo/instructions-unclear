# Session recap template

An AI chat session, kept so you remember what happened and can pick it back up. Keep any context you'd otherwise have to rediscover, and drop the back-and-forth.

## Frontmatter

Shared properties, plus:

- `tool`: the assistant, such as OpenCode.
- `session_id`: exactly as given.
- `directory`: the folder the session worked in.
- `status`: `open` while work remains, `done` when finished.

## Sections, in this order

1. `## Outcome`: what the session achieved, in a line or two.
2. `## Decisions`: each decision with a one-line reason.
3. `## Where things are`: repo, branch, commits, file paths and URLs, exactly as given.
4. `## Open items`: what's left, as task lines.
5. `## Approach`: what was done and why, briefly.
6. `## Reopen`: the session ID, tool and folder, and how to get back to it. Write a command only when the tool documents one. `reference/obsidian.md` lists the documented ways to reopen an OpenCode session. Otherwise say to find the session ID in the tool's session list.
7. `## Why it went this way`: a collapsed callout with the alternatives considered or tried, and why they lost.

Steps worth repeating, such as how to run what was built, go in a how-to note. Propose the split; this note links to the how-to under `related`.

Record only what the session established. Don't add claims about how a tool behaves that the session didn't test. If something looks worth checking, add it under Open items as a question.

## Example

```markdown
---
type: session
title: Sorting photos by EXIF date
created: 2026-11-18
tool: OpenCode
session_id: ses_0000example
directory: ~/code/photo-sorter
status: open
project: "[[photo-sorter]]"
related: ["[[How to sort photos by EXIF date]]"]
source: AI chat session
tags: [ai-sessions]
---

## Outcome
A command that sorts photos into year and month folders by EXIF date, committed on a branch.

## Decisions
- Use the EXIF capture date, because copying a file resets its modified time.

## Where things are
- Branch `exif-sort`, commit `1a2b3c4`.

## Open items
- [ ] Handle videos

## Approach
Tried file modified time, then switched to [[exiftool]].

## Reopen
Session `ses_0000example` in OpenCode, folder `~/code/photo-sorter`. From that folder: `opencode mini --session ses_0000example`, or find it with `opencode session list`.

## Why it went this way
> [!note]- Alternatives
> File modified time was rejected because copies reset it.
```
