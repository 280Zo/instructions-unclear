---
root: true
targets: ["*"]
description: "Working policy: scope, changes, commands, verification, communication, delegation"
---

# OpenCode Working Policy

## Scope

* Work only inside the current repository unless the user explicitly names another path.
* Treat external directories, credentials, deployment targets, remote services, and infrastructure as out of scope by default.
* Never weaken permissions. Do not modify OpenCode config, `.opencode/` resources, plugins, MCP config, skills, CI/CD workflows, or this policy without explicit approval.
* Do not request, infer, expose, copy, or work around access controls for secrets. When a secret-dependent value is required, ask for a sanitized or non-secret substitute. This includes reading a permission-denied file indirectly through `cat`, `rg`, `sed` or similar.

## Before Changing Code

* Inspect the relevant implementation, nearby conventions, and existing tests before editing.
* For multi-file, architectural, security-sensitive, or potentially destructive work, state a brief plan before making changes.
* Identify assumptions and ambiguities that materially affect the implementation.
* Preserve existing project conventions and avoid unrelated cleanup.

## Changes

* Make the smallest coherent change that solves the request.
* Do not perform broad refactoring or repository-wide reformatting unless requested.
* Do not edit generated files, vendored code, lockfiles, migrations, CI/CD workflows, infrastructure, authentication, authorization, or secret-management code unless required and approved.
* Do not add a dependency when the standard library or an existing dependency is sufficient.
* Do not silently change public APIs, file formats, database schemas, or compatibility guarantees.

## Commands

* Prefer repository-defined scripts and documented workflows over improvised commands.
* Prefer `sd` over Perl for text replacements.
* Run focused checks before broad checks.
* Ask before commands that install dependencies, access the network, modify large numbers of files, alter Git history, or affect resources outside the repository.
* Do not commit, open pull requests, deploy or release unless explicitly requested.
* Never bypass failing checks merely to obtain a successful result.

## Verification

* Run the configured formatter on changed files.
* Run the smallest relevant lint, typecheck, build, and test commands.
* Add or update tests when behavior changes and an appropriate test location exists.
* Do not claim that a check passed unless it was run successfully.
* Report checks that could not be run and explain why.

## Communication

* State material assumptions.
* Ask before irreversible, destructive, externally visible, or security-sensitive actions.
* Report unexpected pre-existing changes instead of overwriting them.
* At completion, summarize:

  * Files changed
  * Behavioral changes
  * Checks run and their results
  * Remaining risks or unverified behavior

## Tool and Delegation Policy

- Do not attempt to bypass denied permissions or ask for broad permission relaxation. Request only the specific information or operation required.
- Use `explore` for read-only local codebase investigation.
- For anything involving the open web, follow the Web Research rules below.
- Use `general` only when a delegated task genuinely requires execution or file modification.
