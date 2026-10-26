# security-threat-model

Repository-grounded AppSec threat modeling: trust boundaries, assets, attacker capabilities, abuse paths and mitigations. Included in `infosec`, `work` and `default`. In OpenCode's `default` install, only the [`security` agent](../../agents/security/) can load it.

## Install

Use the [infosec group](../../groups/README.md#infosec), or install this skill alone into a chosen folder, from the repo root:

```bash
mkdir -p ~/AI/threat-model
npx rulesync@41.0.0 generate --features skills --input-roots skills/security-threat-model --output-roots ~/AI/threat-model
```

Never add `--global` to that folder-scoped command. The full references and interface assets are included. No scanner, dependencies or MCP services are installed.

## Use and boundaries

Use when explicitly asking for repository/path threat modeling or abuse-path enumeration. It is not a generic architecture-review trigger. The skill asks for material service assumptions to be confirmed before its final report and grounds claims in source evidence. It writes a Markdown threat model; source access or installation alone does not authorize probing, target operations or remediation. Context packaging tests do not establish a completed security assessment.

Use one installation owner per destination. The legacy upstream installer defaults to `~/.codex/skills`, whereas rulesync 38's global Codex output uses `~/.agents/skills`; choose an explicit matching destination where needed and review duplicate owners rather than automatically removing live files.

## For agents: install, remove and update

To install, use the `infosec` group (folder), the `default` or `work` group (home folder), or the folder command above. It needs no other software. To verify, start a new session in the install location and check that `security-threat-model` is listed among the skills. Don't run a threat model as a test.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `security-threat-model` skill folder behind; delete it with approval. Threat model reports it already wrote are the user's files and stay unless the user asks. If the user keeps `rules/routing`, its line still names this skill, so tell them.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The pinned commit is in [Updating and origin](#updating-and-origin); the update bullets in the next section say what to recheck.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "**Security**: threat model → `security-threat-model`".
- It does not own security review or secure-by-default help (`security-best-practices`), scanner setup and SAST runs (`/security-sast`, `sast-configuration`), dependency risk (`/security-dependencies`), compliance (`/compliance-check`) or multi-phase hardening (`/security-hardening`, only when asked for by name).
- Why: on 2026-10-21 the user replaced the per-skill rules with one routing rule because several skills' descriptions and rules claimed the same jobs. Here, this skill overlapped with the `threat-modeling-expert` agent and the STRIDE and attack-tree skills in [`agents/security`](../../agents/security/). The rule names this skill as the threat-model owner, and `threat-modeling-expert` uses it as its primary workflow, with the technique skills inside it.
- It stays its own folder, not inside `agents/security`, because the user keeps it out of the `default` install and rulesync can't leave one skill of a bundle out of one group. `work` and `infosec` select it. Don't move or copy it into `agents/security`.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and triggers. If it now claims a job another item owns, or drops one it owned, update `rules/routing`, this section and the `agents/security` README in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/.curated/security-threat-model/` from [OpenAI's skills repository](https://github.com/openai/skills), pinned to `49f948faa9258a0c61caceaf225e179651397431`, imported October 20, 2026. Upstream is deprecated. Its installer was verified in isolation before import; compare full references/assets and regenerate affected selections when reviewing a new revision.

Publisher: OpenAI. Apache-2.0; the license retains unfilled copyright-example boilerplate, not a named holder. Original [LICENSE.txt](skills/security-threat-model/LICENSE.txt) and [consolidated terms](../../THIRD_PARTY_LICENSES.md#openaiskills) are retained. Wrapper written for this repo by 280Zo.
