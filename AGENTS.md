# AGENTS.md — instructions for AI agents working on this repo

This repo stores AI context files (rules, skills, agents, MCP server definitions) and installs them into a user's home folder with [rulesync](https://github.com/dyoshikawa/rulesync). It is public and meant to work with every assistant rulesync supports. Read `README.md` for the human-facing overview.

## Never

- **Never run `rulesync generate` without `--global`**, except for a profile with `--output-roots` pointing outside this repo (see that folder's README). Without either, rulesync writes project-scope output into this repo and **overwrites this file**. If that happens, restore it with `git checkout -- AGENTS.md` and delete the other generated files (they're listed in `.gitignore`).
- **Never use the `permissions` feature.** It replaces the user's whole `permission` section.
- **Never run `rulesync import`.** It copies live config word for word, including tokens in MCP server `env` values and headers (tested with a fake token). Copy changes back by hand instead, replacing secret values with `${VAR}` placeholders.
- **Never commit secrets or personal data.** See "Secrets and personal data" below.
- **Never copy auth or settings files** into the repo: `~/.claude.json`, `~/.claude/.credentials.json`, `~/.codex/auth.json`, `~/.codex/config.toml`, `~/.gemini/settings.json`, OAuth files, `opencode.json(c)`, `.pmb/`. Only context files belong here.

## Layout

File each thing by what it is, judged by what its own README and repo name call it (for my own work, by what it does). Everything it contains stays with it and installs from that one folder. Never split a thing across top-level folders by file type, and never file by file count. Things that were only grouped by topic aren't parts of each other; each gets its own folder.

The folders under these are rulesync source trees, listed in `inputRoots` in `rulesync.jsonc` (or in a `profile.jsonc`):

```
rules/<topic>/          a standalone rule
skills/<name>/          a skill or skill collection, plus its rules and helper files. A skill collection that uses its own agents internally (Trail of Bits) stays here whole
agents/<set>/           an agent or set of agents, plus their skills, rules and commands
mcp-servers/<server>/   an MCP server: mcp.jsonc, plus its rules and skills
plugins/<plugin>/       a plugin rulesync can't install: README with human and agent install steps
```

Every folder has a README (`rules/` has one README for all its topics), and a `profile.jsonc` if it's a profile. The README's Origin section says where it came from: the upstream for third-party content, or "Written for this repo" for my own.

A profile is a folder meant to load only in one directory the user picks, not the home folder. Its `profile.jsonc` is a rulesync config listing that folder in `inputRoots`; the folder is not listed in `rulesync.jsonc`. Paths in `profile.jsonc` are relative to the repo root, so profile commands run from there.

`groups/*.jsonc` are named install selections, not source trees. Home-folder
groups (`default`, `work`, `writing_reporting`) run with `--config` and
`--global`; each carries a complete rule selection with the preamble first and
the reminder last. Folder groups (`infosec`, `ai_research`,
`reverse_engineering`) run with `--output-roots` and never `--global`.
`groups/default.jsonc` mirrors `rulesync.jsonc`: change both together. Each
group's README section states whether it writes MCP settings. All groups are
documented in the single `groups/README.md`, with a one-line row in the root
README; groups don't get their own folders or READMEs.

**Whenever you add, rename, move or remove a folder anywhere in this repo, check `groups/*.jsonc` and `groups/README.md` and update them in the same change.** Decide which groups the folder belongs in (for example, a new security skill goes in `infosec`; anything in `rulesync.jsonc` also goes in `groups/default.jsonc`), keep the preamble first and the reminder last, and update the counts and descriptions in `groups/README.md`. Then generate each changed group into a throwaway folder to check it.

Third-party license texts all live in `THIRD_PARTY_LICENSES.md`, one section per upstream; each folder's README links to its section. Whenever you add, update or remove third-party files (skills, agents, extracted skill text), add, update or remove that upstream's section in the same change, with the full license text copied from upstream's `LICENSE` file, the folder it applies to, and the source link. Never add a third-party folder without it. MIT and Apache 2.0 require shipping the license text with copies, so a link to upstream alone isn't enough. Licenses that sit inside an upstream skill folder (Anthropic's `LICENSE.txt`) stay where they are, because that folder is copied unchanged.

Things are separate folders so people can install only the ones they want with `--input-roots`.

Inside a source tree: `rules/*.md`, `skills/<name>/SKILL.md`, `subagents/*.md`, `mcp.jsonc`. `README.md` files are ignored by rulesync.

## Adding or updating content

### Rules

- Frontmatter: `root: true`, `targets: ["*"]`, and a `description`. Non-root rules are written to separate files that OpenCode v2 does not load.
- One rule per folder, named after its topic (no numeric prefixes). Order in the generated `AGENTS.md` follows the folder order in `inputRoots`. `rules/shell-preamble` must stay first and `rules/shell-preamble-reminder` last, after every other source root.
- A new rule folder must be added to `inputRoots`, or it isn't installed.

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

Keep an agent's filename, `name`, title and README examples consistent. A rename
does not remove an old live installation when `delete: false`; document stale
names and never delete or overwrite the user's live copies without approval.
For OpenCode, use `mode: all` when an agent must support both primary selection
and delegation. A prompt describing the current model is not evidence the
harness changed its selected primary agent. Document activation and delegation
separately, including child-model inheritance and permission limitations.

### Syncing a changed skill or agent from a live install

Live copies (e.g. `~/.config/opencode/skills/<name>/`) are plain tool files. Repo copies may carry tool sections the live copy doesn't have. When copying a live file back:

1. Diff the live folder against the repo folder.
2. Take the body and shared fields from the live copy.
3. **Keep the repo's tool sections** (`claudecode:`, `opencode:`, `name`, `targets`).

Files that currently carry tool sections:

| File | Section |
|---|---|
| `skills/report/skills/report/SKILL.md` | `claudecode: allowed-tools` |
| `skills/eli5/skills/eli5/SKILL.md` | `claudecode: allowed-tools` |
| `mcp-servers/exa/skills/code-search/SKILL.md` | `claudecode: context` |
| `agents/second-opinion/subagents/*.md` | `name`, `targets`, `opencode: mode` and `permissions`, `claudecode: tools` |
| `agents/local-model/subagents/local-model.md` | `name`, `targets`, `opencode: mode` |
| `skills/trailofbits/` (38 skills, all 30 agents) | `claudecode:` settings and agent `targets`; listed in its README |
| `agents/security-*/subagents/*.md`, `agents/reverse-engineering/subagents/*.md` (6 agents) | `targets`, `opencode: mode`, `claudecode: model` |
| `skills/distilly/skills/distilly/SKILL.md` | `claudecode: argument-hint, user-invocable, allowed-tools` |

Third-party skills and agents (in `skills/`, `agents/` and `mcp-servers/`) should stay identical to upstream apart from tool sections. Note any other change in the folder's README.

When adding third-party content, record in the folder's README the upstream repo, the path inside it, and the commit you copied from. The update check below depends on that commit.

### Plugins

rulesync installs rules, skills, agents, commands, hooks and MCP servers, not plugins. When adding a plugin:

1. Create `plugins/<plugin>/README.md` with what it does, an **Install** section (the plugin entry or command for each tool it supports), a **Let your agent do it** section, a **Use** section, and its origin.
2. Open the agent section with "Skip this if you installed it by hand", then the exact sentence the user says to their agent, then "The agent follows these steps:". Write the steps so an agent can follow them: ask the user which tools and get approval before editing any tool config; check whether the plugin is already installed; edit only the plugin list, keeping comments and other settings; never add both OpenCode's `plugin` and `plugins` keys; never open credential files; and hand the user any step the agent can't run, such as a slash command.
3. Use the plugin with its defaults. Don't add a rule for it unless the plugin's own documentation tells users to add instructions; if it does, say so in the README and ask the user first. Note any interaction with the rules here (for example, what it commits) in the README's Use section.
4. Add the plugin to `plugins/README.md` and the root README.
5. Plugins install from upstream, so nothing goes in `THIRD_PARTY_LICENSES.md` unless you copy their files here.

### MCP servers

- One `mcp.jsonc` per tool folder; rulesync merges them all.
- Commands are installed programs run by name (e.g. `pmb-mcp`, installed with `uv tool install pmb-ai`). Never use an absolute path.
- Supported per-server fields that carry over to OpenCode, Claude Code and Codex: `command`, `args`, `env`, `cwd`, `timeout`, `url`, `headers`, and `disabled` (written as `enabled: false` for OpenCode and Codex, passed through as `disabled: true` for Claude Code).
- If the MCP server's name changes, warn the user: their OpenCode permission rules match tools by `<server name>_*`.

## Check for updates

Run this check when the user asks to update, upgrade, sync or refresh anything here, and before adding new content (so new and existing copies match their upstreams). Each step that contacts the network needs the user's approval first.

1. **Third-party skills and agents** (`skills/`, and skills under `mcp-servers/`). For each folder, compare the commit recorded in its README with upstream's latest: `git ls-remote <repo> HEAD`. If they differ, clone upstream into `/tmp/opencode`, diff upstream's folder against the repo copy, and show the user what changed before copying anything. Copy only into the folder's inner `skills/` and `subagents/`; its `README.md` and `profile.jsonc` are this repo's and are never overwritten. If upstream's license text changed, update its section in `THIRD_PARTY_LICENSES.md`. Copying follows "Syncing a changed skill or agent" above: keep the repo's tool sections, then record the new commit. If a README has no commit recorded, clone upstream's latest, diff it the same way, and record that commit.
   Some skills aren't files upstream. `mcp-servers/codebase-memory` extracts its skill from the `skill_content` string in the program's `src/cli/cli.c` at the release tag; decode the C string exactly and check the frontmatter parses.
2. **MCP servers installed with uv.** Run `uv tool list --outdated` and report what's behind. Don't upgrade them; give the user `uv tool upgrade --all`.
3. **Container images** (`mcp-servers/*/compose.yaml`). Compare the pinned tag with the project's latest GitHub release. If newer, look up that tag's digest from the registry (for GHCR: get an anonymous pull token from `https://ghcr.io/token?scope=repository:<owner>/<image>:pull`, then read the `docker-content-digest` header of `HEAD https://ghcr.io/v2/<owner>/<image>/manifests/<tag>`), show the user the release notes link, and update tag and digest together.
4. **rulesync.** Compare the version pinned in the README's commands with `npm view rulesync version`. A new version is an upgrade, not a refresh: generate with both versions into separate throwaway home folders (see "Verify before committing"), diff the output, and show the user the differences before changing the pin.
5. **Pinned MCP packages** (`uvx` and `npx` pins in `mcp-servers/*/mcp.jsonc`, such as `freecad-mcp@` and `rea-agents@`). Compare each pin with the package's latest release and update it together with any matching skill or addon the README names.
6. **Plugins** (`plugins/`). Nothing is copied, so there's nothing to diff. Check that each README's install line still matches upstream's install docs.
7. Summarize what's current, what's behind, and what you changed.

Never run an upstream's own installer (`install.sh`, `npx <package>`, plugin marketplaces) to update; copy files as above.

## Keep the credits current

The root `README.md` is a short catalog, not a credits table. Keep its entries,
the component READMEs' Origin sections and `THIRD_PARTY_LICENSES.md` current whenever you:

- add, rename or remove a rule, agent, skill or MCP server, or
- find context files during an authorized inspection of the user's machine that aren't accounted for (for example a skill in `~/.agents/skills/`, `~/.claude/skills/` or `~/.config/opencode/skills/` with no attribution).

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
HOME=/tmp/opencode/rulesync-check npx rulesync@33.0.0 generate --global --features rules,subagents,skills,mcp
```

Leak scan over the files git would commit:

```bash
git ls-files --cached --others --exclude-standard -z -- . ':!AGENTS.md' ':!skills/' \
  | xargs -0 rg -n -i \
      -e '/home/' -e '/run/user/' \
      -e '\bsk-[a-z0-9_-]{16,}' -e 'gh[pousr]_[a-z0-9]{20,}' -e 'xox[abpr]-' -e 'AKIA[0-9A-Z]{16}' \
      -e '"[a-z0-9_-]*(token|secret|password|passwd|api[_-]?key)[a-z0-9_-]*"\s*:\s*"[^${]' \
      -e '[a-z0-9_-]*(token|secret|password|api_key)[a-z0-9_-]*\s*=\s*"[^$]'
```

Expect no output. The patterns catch home paths, common token formats (Anthropic and OpenAI `sk-`, GitHub, Slack, AWS), and any token, secret, password or API key field holding a literal value. `${VAR}` placeholders and `{env:...}` / `{file:...}` references pass. The scan skips this file, which quotes the patterns. It was checked against fake Claude Code, Codex and imported MCP credentials, and caught all of them.

The scan above skips `skills/`, so run it again on any of my own folders there (whose README says "Written for this repo"), replacing the `git ls-files ...` pathspec with those folders, for example `skills/eli5 skills/report skills/package-management`.

Third-party skills are full of documentation placeholders (`api_key="your-api-key"`, `/home/ubuntu`), so they get a narrower scan for real token formats and your own home path:

```bash
git ls-files --cached --others --exclude-standard -z -- skills/ \
  | xargs -0 rg -n \
      -e "/home/$USER" -e "/run/user/$(id -u)" \
      -e '\bsk-[A-Za-z0-9_-]{16,}' -e 'gh[pousr]_[A-Za-z0-9]{20,}' -e 'xox[abpr]-[A-Za-z0-9-]{10,}' -e 'AKIA[0-9A-Z]{16}'
```

Expect no output here either. Placeholders like `sk-...` don't match because the patterns need the length of a real token.

`.gitignore` also blocks common credential files (`.claude.json`, `.credentials.json`, `auth.json`, `.env`, keys) and the `.rulesync/` folder that `import` writes, as a backstop. The `skills/resume-skills` skills contain made-up example emails and phone numbers; those are fine. Commits use the author email `1754228+280Zo@users.noreply.github.com`.
