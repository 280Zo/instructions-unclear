---
name: package-management
description: Use before installing, adding, removing, upgrading or downgrading any dependency, tool or CLI. Triggers on npm, pnpm, yarn, bun, pip, uv, poetry, pipx, cargo, gem, go install, composer, brew, apt, dnf, pacman, apk, winget, choco, scoop, npx, bunx, uvx, package.json, lockfiles, "install this", "add a dependency", "is X available", "curl | sh".
---

# Package & Tool Management

## Before installing anything

Check whether the repository already provides the tool, via package-manager
scripts, local dependencies, task runners, Makefiles, dev environments,
containers, or other checked-in tooling. Prefer repo-local over global, always.

If it genuinely isn't available, prefer the repository's documented setup
method over inventing an installation.

## Dependency changes

- Use the package manager and lockfile the repo already established. Never
  switch managers or regenerate a lockfile with a different tool.
- Do not add, remove, upgrade or downgrade anything unless the task requires it.
- Preserve lockfiles. Do not delete or regenerate one just to make an install
  succeed.
- Do not add a dependency when the standard library or an existing dependency
  is sufficient.

## Installing without changing the dependency graph

Use the reproducible/frozen mode:

| Manager | Command |
|---|---|
| npm | `npm ci` |
| pnpm | `pnpm install --frozen-lockfile` |
| Yarn | `yarn install --immutable` |
| Bun | `bun install --frozen-lockfile` |
| uv | `uv sync --frozen` |
| Cargo | `--locked` |

## Identifying the manager

Infer from the lockfile: `package-lock.json`→npm, `pnpm-lock.yaml`→pnpm,
`yarn.lock`→Yarn, `bun.lock`/`bun.lockb`→Bun, `uv.lock`→uv,
`poetry.lock`→Poetry, `Pipfile.lock`→Pipenv, `Gemfile.lock`→Bundler,
`Cargo.lock`→Cargo, `composer.lock`→Composer.

Repository documentation and established conventions override this inference.

## Security posture

Installing a package executes third-party code — install hooks, build scripts,
plugins, native code.

- Never disable integrity checks, signature verification, lifecycle-script
  protections or sandboxing to make an install succeed. If it only works with
  protections off, stop and report that.
- Do not modify registries, mirrors, auth or trust settings.
- Never `curl ... | sh`, `wget ... | sh`, or equivalent remote-script execution.

## Download-and-execute runners

`npx`, `npm exec`, `pnpx`, `bunx`, `uvx` download and immediately execute code.
Treat them as third-party code execution, not as command invocation.

- Prefer an existing project script (`npm run lint`) over invoking a runner.
- If docs say `npx <tool>`, first check whether `<tool>` is already available
  locally or via a repo script.
- When a one-off is genuinely necessary, pin an exact version — never `latest`
  or a bare package name.
- Do not use `-y` / `--yes` to skip the download prompt.

## Global and system scope

Do not install, remove or modify global, user-level or system packages unless
explicitly requested. This covers `-g` / `--user` / `--global` forms of every
manager above, plus `pipx`, `uv tool install`, `cargo install`, `gem install`,
`go install`, and all OS package managers (`brew`, `apt`, `dnf`, `pacman`,
`apk`, `winget`, `choco`, `scoop`).

Avoid creating ambient machine state that the repository does not describe.
Never prefer a global tool when a repo-local version exists.
