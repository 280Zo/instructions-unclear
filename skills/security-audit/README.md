# security-audit

Cloudflare's multi-phase security audit: reconnaissance, coverage-led hunting with isolated subagents, adversarial validation of every candidate, schema-checked `findings.json`, independent record verification and a target-neutral report. Included in `default` and `work`. In OpenCode's `default` install, only the [`security` agent](../../agents/security/) can load it.

## Install

The [`default`](../../groups/README.md#default) and [`work`](../../groups/README.md#work) groups install it into your home folder. To install this skill alone into a folder, from the repo root:

```bash
mkdir -p ~/AI/security-audit
npx rulesync@43.12.0 generate --features skills --input-roots skills/security-audit --output-roots ~/AI/security-audit
```

Never add `--global` to that folder-scoped command. The whole upstream skill folder is included: `SKILL.md`, the phase and attack-class companion files, `report-schema.json` and the two validators with their tests.

### What it needs

- Node.js, to run `validate-findings.cjs` and `validate-coverage-ledger.cjs`. They have no dependencies.
- An assistant that can start parallel subagents. In OpenCode the `security` agent runs the skill's `general` role as `general` and its `research` role (reconnaissance, coverage critics and final record verifiers, which mainly read source) as `explore`.
- An OS-enforced sandbox (no network, allowlisted environment, read-only target, resource limits) before it runs any target code. Without one, the skill doesn't execute target code and keeps the lead as `needs_validation`. Nothing here installs a sandbox.

## Use and boundaries

Ask for a full audit of a codebase: "security audit `~/code/app`", "find vulnerabilities in `./src`", "pen-test this codebase, output to `~/audits/app`". The skill has two modes. Guidance mode (security questions, focused checks) writes no files. Full audit mode runs all six phases and writes its artifacts to `~/security-audit-skill/<repo>/run-<N>` unless you name another directory. Your installed rules still apply, so the agent asks before writing outside the current project when you didn't name the path.

The skill reads source and never modifies target source; it writes inside the target only to an output folder you pick there that version control ignores. Its own rules forbid installing dependencies, probing deployed or shared systems and spending paid quota. Installing it doesn't authorize an audit of any target.

For how it compares with the other security skills and commands, see [Which one to use](../../agents/security/README.md#which-one-to-use).

A full run starts many subagents, so it costs far more than a normal review. Name a budget (a maximum number of agent runs) or the `quick` profile for a cheaper first pass.

## For agents: install, remove and update

To install, use the `default` or `work` group, or the folder command above. Check that Node.js is on `PATH` for the validators; don't install it without the user's approval and the package-management skill. To verify, start a new session in the install location and check that `security-audit` is listed among the skills. Don't run an audit as a test. A harmless check is running the validators' own tests from the installed skill folder: `node validate-findings.test.cjs` and `node validate-coverage-ledger.test.cjs`. They create and remove folders in the system temporary directory and start `node` and `mkfifo` child processes; nothing else is touched.

To remove, follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves the `security-audit` skill folder behind; delete it with approval. Audit runs it already wrote under `~/security-audit-skill/` or elsewhere are the user's files and stay unless the user asks. If the user keeps `rules/routing`, its line still names this skill, so tell them.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates). The pinned commit is in [Updating and origin](#updating-and-origin); the update bullets in the next section say what to recheck.

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "codebase security audit, vulnerability hunt or pen-test of code → `security-audit`".
- It does not own security review or secure-by-default help (`security-best-practices`), threat models (`security-threat-model`), scanner setup and SAST runs (`sast-configuration`, `/security-sast`), dependency risk (`/security-dependencies`), compliance, DevSecOps and cloud-posture audits (`/compliance-check`, the `security-auditor` agent) or multi-phase hardening with fixes (`/security-hardening`, only when asked for by name).
- Why: upstream's description also claims "security questions" and "focused reviews", which `security-best-practices` owns here. The routing rule narrows it to audits, vulnerability hunts and pen-tests of code. The `security` agent's instructions send those to this skill and send compliance, DevSecOps and cloud-posture audits to `security-auditor`. The [Which one to use](../../agents/security/README.md#which-one-to-use) table also puts infrastructure-as-code in the repo here.
- It stays its own folder, not inside `agents/security`, so it keeps its upstream tree unchanged and other tools can install it alone. In OpenCode `default` it's in the `audit` bundle in [`agents/generate.py`](../../agents/generate.py), which only the `security` agent allows.
- On upstream updates, don't edit the upstream skill text to change routing, and don't add a per-skill routing rule to this folder.
- After a refresh, re-read the new `description` and companion file list. If it now claims a job another item owns, or drops one it owned, update `rules/routing`, this section and the `agents/security` README in the same change and tell the user.

## Updating and origin

Complete unchanged `skills/security-audit/` from [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill), pinned to `c1c8a8c1471069fb0e188eeaff69b8e8db6564a8`, imported 2026-11-23. Upstream documents only the generic Skills CLI (`npx skills add … --skill security-audit`) as its installer, and the repo has nothing outside this folder except its README and [LICENSE](https://github.com/cloudflare/security-audit-skill/blob/c1c8a8c1471069fb0e188eeaff69b8e8db6564a8/LICENSE) (no hooks or plugin manifest), so rulesync distributes the same files. The Skills CLI itself wasn't run.

MIT, © 2025-2026 Cloudflare, Inc. Full text in [`THIRD_PARTY_LICENSES.md`](../../THIRD_PARTY_LICENSES.md#cloudflaresecurity-audit-skill). Wrapper written for this repo by 280Zo.
