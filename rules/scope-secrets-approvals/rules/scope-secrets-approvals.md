---
root: true
targets: ["*"]
description: "Scope, secrets and approvals: where to work, what never to touch, what to ask before doing"
---

# Scope, Secrets and Approvals

## Scope

* Work only inside the current repository unless the user explicitly names another path.
* Treat external directories, credentials, deployment targets, remote services, and infrastructure as out of scope by default.

## Secrets and permissions

* Do not request, infer, expose, copy, or work around access controls for secrets. When a secret-dependent value is required, ask for a sanitized or non-secret substitute. This includes reading a permission-denied file indirectly through `cat`, `rg`, `sed` or similar.
* Never weaken permissions, bypass a denial, or ask for broad permission relaxation. Request only the specific information or operation required.
* Do not modify your own assistant configuration (such as `opencode.json`, `.opencode/`, `.claude/`, `.codex/`), plugins, MCP config, skills, CI/CD workflows, or these rules without explicit approval.

## Ask first

* Ask before shell commands that install dependencies, access the network, modify large numbers of files, alter Git history, or affect resources outside the repository.
* Ask before any other irreversible, destructive, externally visible, or security-sensitive action.

## Never

* Never discard uncommitted work without approval: no `git checkout -- <path>`, `git restore`, `git reset --hard` or `git clean` on changes you did not make.
* Report unexpected pre-existing changes instead of overwriting them.
* Do not open pull requests, deploy or release unless explicitly requested.
* Do not commit unless the user asked you to or approves it. You may ask to commit when a commit fits the work. Before asking, show the exact command you will run, the commit message, which files are included, and a summary of what changes in them. Commit only after the user says yes to that specific commit.
* Never bypass failing checks merely to obtain a successful result.
