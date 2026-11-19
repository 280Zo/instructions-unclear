# Research template

Options weighed against needs. Someone reopens a research note for one of two reasons: to see how the chosen option was set up, or to check whether it's still the best fit. Lead with the answer and keep what's needed to re-check it.

## Frontmatter

Shared properties, plus:

- `checked`: the date the facts in the note were current.
- `status`: `open` (no pick yet, or the pick still depends on something), `decided`, or `superseded`.
- `pick`: a quoted link to the chosen option, when there is one. While `status` is `open`, a leaning goes in the Answer section, not in `pick`.

## Sections, in this order

1. `## Answer`: the pick, or the current leaning and what it depends on, in a line or two. Link the how-to for setting up the pick when one exists or is being written.
2. `## Needs`: must-haves, then nice-to-haves. These are what a revisit re-checks.
3. `## Options compared`: a table with options as columns and the needs as rows. Prices and versions are as of `checked`, with their own date when different (a sale seen on another day). Mark uncertain values ("32 or 33 in., unconfirmed"). After the table, a short line per option for anything that doesn't fit the table, with opinions attributed ("[[Dana]] expects the cushions to sag within a few years").
4. `## Open questions`: what still has to be found out before deciding, as task lines when they're actions.
5. `## Revisit when`: what would change the answer, such as a price change, a new version or changed needs.
6. `## Sources`: where each fact came from (a site, a store visit with its date, a person).
7. `## Why this won`: a collapsed callout with each rejected option and why it lost, and dissent.

When research ends in a setup, propose a how-to note for the setup as well.

## Updating and refreshing

New findings or a refresh update the table and the Answer, move `checked`, and add a change log line. If the pick changes, set this note's `status: superseded`, link the new pick in the Answer, and record the switch in the change log.

## Example

```markdown
---
type: research
title: Best self-hosted password manager (2026)
created: 2026-11-18
checked: 2026-11-18
status: decided
pick: "[[Vaultwarden]]"
related: ["[[How to set up Vaultwarden]]"]
source: research notes
tags: [password-managers]
---

## Answer
[[Vaultwarden]]. Setup: [[How to set up Vaultwarden]].

## Needs
- Must have: self-hosted, works with the Bitwarden apps, runs on a small server.
- Nice to have: free.

## Options compared
| Need | Vaultwarden | Passbolt |
|---|---|---|
| Bitwarden apps | Yes | No |
| Runs on a small server | Yes | Yes |
| Price | Free | Free tier |

## Revisit when
- The Bitwarden apps stop working with Vaultwarden.

## Sources
- Project documentation for each option, read [[2026-11-18]].

## Why this won
> [!note]- Alternatives
> Passbolt lost because it needs its own apps.
```
