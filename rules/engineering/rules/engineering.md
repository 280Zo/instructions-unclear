---
root: true
targets: ["*"]
description: "Engineering: preparation, scope of changes, commands, verification"
---

# Engineering

## Before changing code

* Inspect the relevant implementation, nearby conventions, and existing tests before editing.
* For multi-file, architectural, security-sensitive, or potentially destructive work, state a brief plan before making changes.
* Identify assumptions and ambiguities that materially affect the implementation.

## Changes

* Make the smallest coherent change that solves the request.
* Preserve existing project conventions. Avoid unrelated cleanup, broad refactoring, and repository-wide reformatting unless requested.
* Do not edit generated files, vendored code, lockfiles, migrations, CI/CD workflows, infrastructure, authentication, authorization, or secret-management code unless required and approved.
* Do not silently change public APIs, file formats, database schemas, or compatibility guarantees.

## Commands

* Prefer repository-defined scripts and documented workflows over improvised commands.
* For search-and-replace from the shell, use `sd`, never `perl -pi`/`perl -e` or `sed -i`. Preview with `sd -p` first, and use `sd -F` for literal text. If `sd` is not installed, use the file edit tool instead.

## Verification

* Run the configured formatter on changed files.
* Run focused checks before broad ones: the smallest relevant lint, typecheck, build, and test commands.
* Add or update tests when behavior changes and an appropriate test location exists.
* Do not claim that a check passed unless it was run successfully.
* Report checks that could not be run and explain why.
