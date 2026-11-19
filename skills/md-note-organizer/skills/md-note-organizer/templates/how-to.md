# How-to template

Steps someone will follow again, written so they work next time without rework. Keep the steps lean. Background and dead ends go at the bottom, folded away.

## Frontmatter

Shared properties, plus:

- `title`: starts with "How to".
- `verified`: the date the steps last worked, as shown by the material. Leave it out when nothing confirms they worked.
- `updated`: set when the note is updated.
- `environment`: list of the OS, app and tool versions the steps were done on, when known.

## Sections, in this order

1. `## Goal`: one line on what you end up with.
2. `## Before you start`: what's needed first, such as access, files, versions, and where a credential lives (a pointer, never the value).
3. `## Steps`: a numbered list with one action per step. Put each command in its own code block. Explain a placeholder like `<server-name>` the first time it appears. Put the expected result right after the step that produces it ("Expected: ..."). Mark a step the material didn't confirm as "(not confirmed)". Keep the order that worked, including "stop the service before editing" when the material found that out the hard way.
4. `## Check it worked`: how to tell it succeeded.
5. `## Undo`: how to roll back, when the material gives a way (a backup that was made, for example).
6. `## Troubleshooting`: problems that came up and their fixes.
7. `## Why it's done this way`: a collapsed callout with alternatives, dead ends and reasons.
8. A collapsed change log callout, added when the note is first updated.

A step that only happened once, such as "the laptop is done, the phone isn't yet", isn't part of the procedure. Put it in an open-items line under Troubleshooting or in a linked session note, not among the steps.

When a procedure has more than about 12 steps, propose splitting it into linked sub-notes.

## Example

````markdown
---
type: how-to
title: How to rotate the VPN server key
created: 2026-11-18
verified: 2026-11-18
environment: [WireGuard 1.0.20210914, Debian 12]
project: "[[Homelab]]"
tags: [vpn]
source: AI chat session
---

## Goal
A new server key pair, with clients reconnected.

## Before you start
- Router admin login: in Bitwarden: home router.

## Steps
1. Back up the config.
   ```bash
   sudo cp /etc/wireguard/wg0.conf /etc/wireguard/wg0.conf.bak
   ```
2. Stop the interface.
   ```bash
   sudo systemctl stop wg-quick@wg0
   ```

## Check it worked
Run `sudo wg show`. Each client shows a recent handshake.

## Undo
Restore `wg0.conf.bak` and restart the interface.

## Troubleshooting
- Edits to `wg0.conf` were overwritten: `SaveConfig = true` writes the running config back on shutdown. Stop the interface before editing.

## Why it's done this way
> [!note]- Dead ends
> Editing with the interface running lost the change when it stopped.
````
