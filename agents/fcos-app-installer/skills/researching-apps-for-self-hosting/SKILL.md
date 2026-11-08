---
name: researching-apps-for-self-hosting
description: "Researches a self-hosted app from its official sources before it is installed: image and tag, containers, ports, storage and size, settings, secrets, whether it starts as root, paths clients call without a browser, single sign-on support, mail, credentials it prints at start, and its logo. Writes every fact with its source. Use when planning to self-host an app in containers, before writing any configuration for it."
license: MIT
---

# Researching an app for self-hosting

Find each fact below in the app's **official** sources: its documentation,
its image registry page, its source repository (compose files, Dockerfile,
entrypoint, example config). A forum post or issue only fills a gap the
official sources leave, and is labelled as such. Never fill a gap from memory.
When a fact can't be found, say so and ask the person instead of guessing.

Write the results to `research.md` beside the app's other files: one row per
fact, with the source link (and the version or commit it was read at).
Label every row whose source isn't official.

## Facts to find

| Fact | Where it usually is |
|---|---|
| Image on its official registry, pinned to a major-version tag (never `latest`) | registry page, release notes |
| Each container it needs (app, worker, database, cache) and their start order | official compose file |
| Port each container listens on | Dockerfile `EXPOSE`, compose, docs |
| Every path it writes: config, data, cache, uploads, database | volumes in compose, docs |
| Expected size of each path; a database or data over 5 GB needs a decision before installing | docs, sizing notes |
| Database engine and version it supports | docs, compose |
| Settings: environment variables and command line | `.env.example`, docs |
| Secrets (keys, passwords, signing keys), and which must stay the same after a rebuild because data depends on them | `.env.example`, docs |
| What each secret must look like (format, length, prefix) | `.env.example`, docs |
| Whether the image starts as root inside the container, and why (an entrypoint that changes owners, a port below 1024) | Dockerfile `USER`, entrypoint |
| Shared memory or read-only folders it asks for | compose, docs |
| Paths desktop or mobile clients call without a browser (sync, API, CalDAV/CardDAV, WebDAV) | docs, client setup pages |
| Single sign-on: OpenID Connect, trusted login headers, or none; how sharing works without it | docs, issues (label them) |
| Two-step login (MFA): whether the app has it (authenticator codes, passkeys, security keys), where it is turned on, whether an admin can require it | docs |
| Mail it sends (reminders, invitations): its mail driver, a log driver, and the sender address it needs even when nothing is sent | mail config, `.env.example` |
| Credentials it prints at start (a generated admin password, a key, an OAuth client secret) | entrypoint, first-start code, docs |
| Its logo: an SVG or PNG the project publishes | repository, website |

## Notes

- **Credentials it prints at start** matter because logs get read while
  checking a new install. Knowing what the app prints says what must never be
  read in its log.
- **Mail without a mail server:** many apps refuse to build a message without
  a sender address even with a log driver. A link in such a mail can be a
  credential (an invitation lets someone join).
- **Single sign-on:** check the app's own docs, then its issue tracker for
  the current state (label it). "None" is a valid answer; record how people
  share the app instead (invitations, shared accounts).
- **Two-step login:** only what the app's own docs describe counts; give the
  page. "None" is a valid answer. When the app has it, the person decides
  whether to turn it on, and the steps come from those docs, not from memory.
- **Root at start** is a decision for the person, with the reason from the
  entrypoint, not a fact to work around.
- Show the person the logo before using it; they may prefer their own.
