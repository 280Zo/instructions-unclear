---
root: true
targets: ["*"]
description: "Never ask for, read, print or store a secret or a real value; keep real values in the private workspace"
---

# Secrets and private values

How secrets and the owner's real values are handled.

## Secrets

- **Never ask for, read, print or store a secret value.** List secrets by
  names only.
- **The owner creates secrets** on the machine that uses them, from a hidden
  prompt, so a value never appears on screen, in shell history or in a file the
  agent can read. Values that data depends on (database passwords, signing
  keys) are kept in the owner's password manager, because a rebuild needs the
  same value.
- **Logs can hold secrets.** Apps print generated credentials at first start
  (an admin password, a key, an OAuth client secret). Read logs only through
  the toolkit's redacting log reader, which shows `[hidden]` in place of
  anything that looks like a secret; never read a log, an environment or a
  secret store another way, and never work around the redaction.
- **If a secret value ever appears in the agent's context**, stop and tell the
  owner to rotate it.

## Private values

- Every real value (names, addresses, domains, users, servers) lives only in
  the owner's private workspace, a folder outside the repository.
- Never write a real value into a published file: guides, templates, tools,
  skills, rules, tests, examples, agents or commands. Use placeholders there:
  `192.0.2.x` addresses, `example.org`, `<admin>`, "the owner".
