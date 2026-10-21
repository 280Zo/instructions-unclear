---
root: true
targets: ["*"]
description: "The user's tool and format preferences"
---

# Preferences

* **Editor:** never suggest `nano`. Use `vim` whenever a command or instruction opens an editor, including `EDITOR`/`VISUAL` values and `git` editor settings.
* **Shell:** write commands meant for the user to run in `fish` syntax unless they ask for another shell. Use `set -x VAR value` (or `set -gx`) instead of `export`, `(command)` for command substitution, and fish config paths (`~/.config/fish/config.fish`). Fish 3 also accepts `&&`/`||`. Your own shell tool may run bash; this applies to commands you hand to the user, not to the tool's syntax.
* **Package managers:** when a project hasn't already chosen one, use `pnpm` for JavaScript/TypeScript and `uv` for Python. A project's existing lockfile and documented tooling always win, and the `package-management` skill still governs every install.
* **Terminal multiplexer:** `zellij`, not `tmux` or `screen`.
* **Browser:** open pages for the user to view in `firefox` (for example `firefox <file-or-url>`), not the system default or another browser. This doesn't change which browser automation tools such as Playwright drive.
* **Dates and times:** ISO 8601: `YYYY-MM-DD`, and 24-hour `HH:MM` when a time is needed.
* **Spelling:** US English.
