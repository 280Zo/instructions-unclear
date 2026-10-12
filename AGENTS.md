# AGENTS.md — instructions for AI agents working on this repo

This repo stores AI context files (rules, skills, agents, MCP server definitions) and installs them into a user's home folder with [rulesync](https://github.com/dyoshikawa/rulesync). It is public and meant to work with every assistant rulesync supports. Read `README.md` for the human-facing overview.

## Never

- **Never run `rulesync generate` without `--global`.** Without it, rulesync writes project-scope output into this repo and **overwrites this file**. If that happens, restore it with `git checkout -- AGENTS.md` and delete the other generated files (they're listed in `.gitignore`).
- **Never use the `permissions` feature.** It replaces the user's whole `permission` section.
- **Never run `rulesync import`.** It copies live config word for word, including tokens in MCP server `env` values and headers (tested with a fake token). Copy changes back by hand instead, replacing secret values with `${VAR}` placeholders.
- **Never commit secrets or personal data.** See "Secrets and personal data" below.
- **Never copy auth or settings files** into the repo: `~/.claude.json`, `~/.claude/.credentials.json`, `~/.codex/auth.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, OAuth files, `opencode.json(c)`, `.pmb/`. Only context files belong here.

## Layout

Each top-level folder is one rulesync source tree, listed in `inputRoots` in `rulesync.jsonc`:

```
house-rules/            rules, skills, agents not tied to one tool
tools/<tool>/           one MCP server: mcp.jsonc, its rules, its skills, README.md
collections/<source>/   skill collections from one upstream source, README.md
```

Inside a source tree: `rules/*.md`, `skills/<name>/SKILL.md`, `subagents/*.md`, `mcp.jsonc`. `README.md` files are ignored by rulesync.

## Adding or updating content

### Rules

- Frontmatter: `root: true`, `targets: ["*"]`, and a `description`. Non-root rules are written to separate files that OpenCode v2 does not load.
- Order in the generated `AGENTS.md` = folder order in `inputRoots`, then filename. Use numeric prefixes (`00-`, `10-`, …). `house-rules/rules/00-shell-preamble.md` must stay first.

### Skills

- One folder per skill: `skills/<name>/SKILL.md`. The `name` must be unique across the whole repo.
- **Top-level frontmatter is only the shared Agent Skills fields:** `name`, `description`, `license`, `compatibility`, `metadata`.
- **Anything only one assistant understands goes under that assistant's section**, or rulesync drops it for every assistant:

  ```yaml
  ---
  name: code-search-exa
  description: ...
  claudecode:
    context: fork
    allowed-tools: [Read, Grep]
  ---
  ```

- Add a row to the folder's README: what it is, origin, license link, copyright holder.

### Agents

`subagents/*.md` need `name`, `targets: ["*"]`, and a **quoted** `description` (strict YAML). OpenCode-only settings go under `opencode:` (e.g. `mode: subagent`).

### Syncing a changed skill or agent from a live install

Live copies (e.g. `~/.config/opencode/skills/<name>/`) are plain tool files. Repo copies may carry tool sections the live copy doesn't have. When copying a live file back:

1. Diff the live folder against the repo folder.
2. Take the body and shared fields from the live copy.
3. **Keep the repo's tool sections** (`claudecode:`, `opencode:`, `name`, `targets`).

Files that currently carry tool sections:

| File | Section |
|---|---|
| `house-rules/skills/report/SKILL.md` | `claudecode: allowed-tools` |
| `house-rules/skills/eli5/SKILL.md` | `claudecode: allowed-tools` |
| `tools/exa/skills/code-search/SKILL.md` | `claudecode: context` |
| `house-rules/subagents/*.md` | `name`, `targets`, `opencode: mode` |

Third-party skills (`collections/`, Exa's) should stay identical to upstream apart from tool sections. Note any other change in the folder's README.

### MCP servers

- One `mcp.jsonc` per tool folder; rulesync merges them all.
- Commands are installed programs run by name (e.g. `pmb-mcp`, installed with `uv tool install pmb-ai`). Never use an absolute path.
- Supported per-server fields that carry over to OpenCode, Claude Code and Codex: `command`, `args`, `env`, `cwd`, `timeout`, `url`, `headers`.
- If the MCP server's name changes, warn the user: their OpenCode permission rules match tools by `<server name>_*`.

## Keep the credits current

`README.md` has a "Credits" section listing every rule, agent and skill with its author, source and license. Update it whenever you:

- add, rename or remove a rule, agent, skill or MCP server, or
- find context files on the user's machine that aren't in the list (for example a skill in `~/.agents/skills/`, `~/.claude/skills/` or `~/.config/opencode/skills/` with no row).

For each item, record the author, a link to the upstream repo, a link to its license and the copyright holder from that license. Check the upstream `LICENSE` file rather than assuming. Installer records can help find the source: `~/.agents/.skill-lock.json` lists skills installed with `npx skills`, and folder dates show which skills arrived together. If the origin can't be found, list it as "Origin unknown" and mark it as not covered by this repo's license. Never guess an author.

## Secrets and personal data

- **Keys and tokens are placeholders, never values.** Write `"x-api-key": "${EXA_API_KEY}"` in `mcp.jsonc`. rulesync turns that into OpenCode's `{env:EXA_API_KEY}`, so the real key is never written to any file. Document the variable in the tool's README.
- When copying from a live config, **never copy a header, env value, or `{file:...}` reference that holds or points to a secret.** Replace it with a `${VAR}` placeholder.
- **No personal paths or names:** no `/home/<user>`, `/run/user/<uid>`, usernames or real emails. Use installed command names, `~`, or environment variables.
- Identity values: copyright and author are `280Zo`. Anything unknown uses the placeholder `ILL_CHANGE_THIS_LATER`.

## Verify before committing

Generate into a throwaway home folder, never the real one:

```bash
mkdir -p /tmp/opencode/rulesync-check
HOME=/tmp/opencode/rulesync-check npx rulesync generate --global --features rules,subagents,skills,mcp
```

Leak scan over the files git would commit:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':!AGENTS.md' \
  | xargs -0 rg -n -i \
      -e '/home/' -e '/run/user/' \
      -e 'sk-[a-z0-9_-]{16,}' -e 'gh[pousr]_[a-z0-9]{20,}' -e 'xox[abpr]-' -e 'AKIA[0-9A-Z]{16}' \
      -e '"[a-z0-9_-]*(token|secret|password|passwd|api[_-]?key)[a-z0-9_-]*"\s*:\s*"[^${]' \
      -e '[a-z0-9_-]*(token|secret|password|api_key)[a-z0-9_-]*\s*=\s*"[^$]'
```

Expect no output. The patterns catch home paths, common token formats (Anthropic and OpenAI `sk-`, GitHub, Slack, AWS), and any token, secret, password or API key field holding a literal value. `${VAR}` placeholders and `{env:...}` / `{file:...}` references pass. The scan skips this file, which quotes the patterns. It was checked against fake Claude Code, Codex and imported MCP credentials, and caught all of them.

`.gitignore` also blocks common credential files (`.claude.json`, `.credentials.json`, `auth.json`, `.env`, keys) and the `.rulesync/` folder that `import` writes, as a backstop. The `collections/careers` skills contain made-up example emails and phone numbers; those are fine. Commits use the author email `1754228+280Zo@users.noreply.github.com`.
