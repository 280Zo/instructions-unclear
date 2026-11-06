---
name: permission-tuning
description: Use when OpenCode permission prompts keep recurring or a new category of prompt appears, or before changing permission rules, policies, saved "Always" approvals, or the shell-habit rules in AGENTS.md. Security first, then fewer prompts, with per-project isolation.
---

# Permission tuning (OpenCode V2)

Priorities, in order: (1) security, (2) per-project isolation, (3) fewer prompts. Security wins any conflict. Read this file and the project's notes from earlier tuning rounds (evidence, decisions, test log), then act. Don't make the user re-explain the history.

## Verified facts (OpenCode V2; do not re-derive)
* Rules are an ordered list; last match wins; `*` matches anything including `/`; a trailing ` *` also matches the bare command. Shell rules match the raw subcommand text.
* A leading `VAR=val` defeats BOTH allow and deny matching. Agents must not prefix commands (use `python3 -B`).
* A project `opencode.jsonc` allow beats the global `* ask`. In testing it also beat a global rule `deny`; the docs document only policies as holding against a repo's config.
* "Allow always" saves a durable, project-scoped allow in SQLite. It overrides `ask`, never `deny`. Subagents in the same project share it. The prompt proposes broad prefixes (`python3 *`); never recommend clicking it.
* Policies (`tool.use`, resource `<action>:<pattern>`) run after rules and saved approvals. They cannot ask. Invalid statements are dropped with only a log warning (fail open): always test canaries.
* Shell file access is checked only against shell rules; `read`/`edit`/`external_directory` govern file tools. Shell redirects (`>`) skip `edit` rules.
* Allowlists are conveniences, not boundaries (wrappers, interpreters, parser differentials). The real boundary is an OS sandbox.
* `opencode mcp list` is unreliable. Use `/mcps` or the server log (`server=<name>`). Agents cannot see prompts; the user must report them.
* Where a policy `edit:*opencode.json*` is installed, agents cannot edit any `opencode.json(c)`. Give the user exact before/after snippets and have them edit by hand in `vim`. Keep a backup of the config before any change.

## Workflow
1. **Gather evidence.** Screenshots or the prompt list: project, subagent or not, full command text including prefixes and pipes. List that project's saved approvals (below).
2. **Classify.** Which subcommand actually triggered the prompt? Pipe pieces (`tail`, `rg`) are usually already allowed. Categories: read-only, pure filter, test runner, repo script, scratch op, git local write, container, network, interpreter or heredoc, wrapper.
3. **Root cause first.** Env prefix? Wrapper? A saved approval that cannot match? An agent habit (shell instead of `read`/`edit`)?
4. **Lowest-risk fix, in order:** (a) change the agent habit in AGENTS.md; (b) narrow global allow for read-only or pure commands; (c) per-project `opencode.jsonc` allow for a NAMED entrypoint in a trusted repo; (d) policy deny for anything that must hold regardless of approvals; (e) sandbox the harness.
5. **Safe-to-allow test.** A command may be allowlisted only if it cannot (i) run arbitrary code, (ii) write outside its scope (check `-o`, `--output`, `-i`, `>`), (iii) reach the network, (iv) read secrets, (v) launch another command.
6. **Never allowlist:** interpreters with free arguments (`python3 *`, `node *`, `bash *`, `sh *`, `fish *`), wrappers (`env`, `xargs`, `time`, `nice`; `timeout` only with a fixed duration AND fixed runner), `rm *`, `curl *`, `tee *`, `chmod *`, `docker run *`, `edit *`, `cp`/`mv`/`tar`/`git archive` with wildcard destinations, agent-written scripts in `/tmp`. Test runners (`python3 -m unittest *`) execute repo code: trusted repos only, say so.
7. **Review gate.** Send the proposal plus evidence to the `evaluator` and `security` agents (read-only). Fix findings. Show the exact diff.
8. **Offline check.** If the user keeps a corpus of commands with expected outcomes and a test that models documented matching, add the new commands there and run it. It models documented matching only, so it never replaces step 9.
9. **Apply with approval.** If a policy blocks agents from editing `opencode.json(c)`, the user applies rule changes by hand; policies and rules go before the final `edit:*opencode.json*` statement. Check the server log (`~/.local/share/opencode/log/opencode.log`) for dropped statements, then run canaries.
10. **Record** the decision and test results in memory and in the project's notes, if the user keeps them.

## Live-test protocol
Announce the exact command at the END of a turn: "On the next turn I'm going to run `X`. Please choose Allow once if prompted. Afterward I'll ask whether you were prompted." Run it next turn, one command per turn, then ask. Never ask for "Always". Deterministic denial tests can be batched (a denial is visible in the result). For "should not prompt" checks, batch them and ask one question. Operational steps (listing, deleting, copying) need no prompt question. Clean up anything you create.

## Saved approvals (audit and prune)
```
opencode api get "/api/permission/saved?projectID=<id>" | jq '.data | map({id, action, resource})'
opencode api delete /api/permission/saved/<id>
```
Project IDs map to folders in the `project` table of `~/.local/share/opencode/opencode.db` (read-only `sqlite3 -readonly`; the shell rule asks). Flag broad rows: `bash/sh/fish/python*/node *`, `rm *`, `env/xargs/curl/tee/chmod *`, `edit *`, `docker run/build/create *`, `git commit/push *`, `cp/mv/sd/sed/awk/find *`, `external_directory /tmp/*`. NEVER delete without per-row user approval (show the rows on an approval page first). Do not edit the SQLite file.

## Repo scripts
Allow only named, version-controlled entrypoints, per project, in repos the user owns or has reviewed. A repo config can grant itself permissions: before opening an unfamiliar repo inspect `opencode.json*`, `.opencode/` and AGENTS.md. Never allow agent-written scripts.

## Sources
OpenCode V2 permissions, policies and config docs: https://opencode.ai/v2/docs/permissions and https://opencode.ai/v2/docs/.
