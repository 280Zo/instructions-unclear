# Security

One security bundle owned by this repo: a secure-coding rule, two agents, six skills and four commands for secure coding, security reviews, threat modeling, code and dependency scanning, hardening and compliance checks. It replaces the separate `security-scanning`, `security-compliance`, `secure-coding` and `security-best-practices` folders, whose overlaps and conflicting instructions are resolved here.

`security-threat-model` is deliberately **not** in this bundle. The user keeps it out of the default install, and rulesync can't leave one skill of a bundle out of one group, so it stays its own folder, [`skills/security-threat-model`](../../skills/security-threat-model/), selected by `work` and `infosec`. The `threat-modeling-expert` agent here uses it wherever it's installed.

Installing the bundle adds instructions, agents, skills and commands. It does not install scanners, run checks or authorize changes to a project.

| Item | Kind | Purpose | Origin |
| --- | --- | --- | --- |
| `rules/secure-coding.md` | Rule | The security mistakes AI-written code makes most often, and how to avoid them | Written for this repo |
| `security-auditor` | Agent | DevSecOps, application and cloud security audits; points to `/compliance-check` for framework audits | wshobson/agents |
| `threat-modeling-expert` | Agent | Threat modeling; uses `security-threat-model` as its primary workflow and the four technique skills | wshobson/agents |
| `security-best-practices` | Skill | Default security review and secure-by-default coding for Python, JavaScript/TypeScript and Go, one fix at a time | OpenAI skills |
| `stride-analysis-patterns` | Skill | STRIDE technique | wshobson/agents |
| `attack-tree-construction` | Skill | Attack tree technique | wshobson/agents |
| `threat-mitigation-mapping` | Skill | Mapping threats to controls | wshobson/agents |
| `security-requirement-extraction` | Skill | Turning threats into security requirements | wshobson/agents |
| `sast-configuration` | Skill | SAST tool configuration, custom rules and CI setup | wshobson/agents |
| `/security-sast` | Command | Run and triage SAST scans | wshobson/agents |
| `/security-dependencies` | Command | Dependency vulnerability scans, SBOMs, approval-gated remediation | wshobson/agents |
| `/security-hardening` | Command | Heavy multi-phase hardening run, only when explicitly requested | wshobson/agents |
| `/compliance-check` | Command | GDPR, HIPAA, SOC 2 and PCI-DSS compliance review | wshobson/agents |

## Install

The `default`, `work` and `infosec` groups include `agents/security`; `work` and `infosec` also include `skills/security-threat-model`. See [`groups/README.md`](../../groups/README.md). To install this bundle alone, from the repo root:

```bash
npx rulesync@38.0.0 generate --global --targets opencode,claudecode,codexcli --features subagents,skills,commands --input-roots agents/security
```

> **Warning:** adding `rules` to `--features` (`--features rules,subagents,skills,commands`) replaces your whole global instructions file with this bundle's one rule. Only include `rules` if you also list every other rule root you want, in order (`rules/shell-preamble` first, `rules/shell-preamble-reminder` last). Otherwise use the command above and get the secure-coding rule from a group.

Swap `--targets` for your tools. The command doesn't replace MCP settings. Run it again to update. Global output includes commands for all three targets; invocation depends on the assistant. Copies installed earlier from the old separate folders (for example the `security-scanning-security-auditor` and `security-compliance-security-auditor` agents) are not removed automatically; review them for duplicates.

### Tools you need

Threat modeling, attack trees, requirements reviews and best-practice reviews need no scanner. For automated checks, use the tools the project already has. Anything else is installed only with your approval, following the package-management skill: never globally, and with an exact, reviewed version for any one-off runner.

| Work | Tools and prerequisites |
| --- | --- |
| Multi-language SAST | Semgrep; CodeQL CLI plus its query packs and a supported build toolchain; or SonarQube plus a scanner and running server |
| Python | Python with Bandit and pip-audit; some upstream examples also use Safety, which may need an account or service access |
| JavaScript / TypeScript | Node and the project's package manager; project-local ESLint with reviewed security plugins; npm audit for npm projects |
| Go | Go, gosec and govulncheck |
| Rust | Rust/Cargo and Clippy; dependency checks may use cargo-audit |
| Java / Ruby | The project's JDK/build tools with SpotBugs or PMD; Ruby/Bundler with Brakeman, as applicable |
| Optional hosted checks | Snyk or SonarQube services may need separate setup, accounts and suitable terms |
| Active testing | OWASP ZAP (for example through the [ZAP MCP server](../../mcp-servers/zap/)); needs an explicit target scope and your approval first |

Get CodeQL and other non-Python tools through their official distributions; check their license and access requirements. Some scripts and config paths in the prompts (`scripts/run-sast.sh`, `scripts/compliance/*`, `automated-dependency-update.sh`) are examples to create, not files supplied by this bundle.

## Use

Start your tool in the project you want reviewed:

- "Do a security best-practices review of `~/code/app`" (`security-best-practices`, the default review)
- "Threat model `~/code/app/api`" (`security-threat-model`, where installed; the `threat-modeling-expert` agent follows the same workflow)
- "Build an attack tree for the login flow in `~/code/app`" (`attack-tree-construction`)
- "Set up Semgrep in CI for this repo" (`sast-configuration`)
- "Use the security auditor to list the evidence we'd need for a SOC 2 review"
- `/security-sast`, `/security-dependencies`, `/compliance-check`
- `/security-hardening` only when you want the full multi-phase run; it writes its state to `.security-hardening/` inside the current project

The commands report findings first. Fixes, dependency updates, installs, CI changes, commits, deployments and active testing all wait for your approval. Your installed rules still apply.

## Why this bundle exists

On October 21, 2026 the user decided to merge the overlapping security folders into one bundle owned by this repo. It removed:

- **Duplicate auditors:** `security-scanning-security-auditor` and `security-compliance-security-auditor` had the same prompt. Now there is one `security-auditor`.
- **Two threat-model workflows:** the `threat-modeling-expert` agent's own steps and the `security-threat-model` skill. The agent now uses the skill as its primary repo-grounded workflow and the four technique skills inside it.
- **Two SAST guides:** `/security-sast` now runs and triages scans and points to `sast-configuration` for tool setup and CI.
- **Two compliance paths:** the auditor points to `/compliance-check` for framework audits.
- **Two review modes:** `security-best-practices` is the default review; `/security-hardening` runs only when explicitly requested.
- **Install conflicts:** global and unpinned installs (`pip install`, `npm install -g`, `go install …@latest`, `cargo install`, `gh extension install`) contradicted the package-management rules.
- **Automatic changes:** `npm audit fix && npm update`, `pip-audit --fix` and the auto-update script ran without approval.
- **TLS/HSTS disagreement:** the secure-coding rule said default to TLS, `security-best-practices` said don't report missing TLS and avoid HSTS, and the auditor listed HSTS without caveats.
- **Commit instructions** that didn't follow the repo's commit-approval protocol, an unscoped "search online", Claude-only tool names in `/security-hardening`, an ungated penetration-testing step, and references to files that don't exist.

## Changes from upstream

Supporting files not listed here are byte-identical to their sources.

**`rules/secure-coding.md`** (repo-authored, from `rules/secure-coding/`)

- TLS line: TLS is the default for production and deployed configuration; local development without TLS is not a finding; HSTS only as a deliberate deployment decision with its lock-in risk explained.

**`subagents/security-auditor.md`** (from `security-scanning-security-auditor.md`; the compliance copy was identical apart from `name`)

- `name` changed to `security-auditor`. Repo tool sections kept: quoted description, `targets: ["*"]`, `opencode: mode: subagent`, `claudecode: model: opus`.
- Security headers line: HSTS only as a deliberate deployment decision; missing TLS in local development is not a finding.
- Compliance section: new "Framework audits" line pointing to `/compliance-check`.
- Behavioral traits: active testing (DAST, penetration tests, ZAP) only against explicitly scoped and approved targets.

**`subagents/threat-modeling-expert.md`**

- Workflow: uses the `security-threat-model` skill as the primary workflow for repositories, drawing on `stride-analysis-patterns`, `attack-tree-construction`, `threat-mitigation-mapping` and `security-requirement-extraction`; the original eight steps remain for design-only work.
- Fallback: if `security-threat-model` isn't installed (the default install leaves it out), the agent says so and uses the original steps, grounded in repo evidence.

**`commands/security-sast.md`**

- Replaced the dangling `security-secrets.md` / `security-owasp.md` / `security-api.md` line with a pointer to the `sast-configuration` skill for configuration and CI.
- New "Installing tools" section: project tooling first, package-management skill, ask before installing, never global, pinned one-off runners.
- `pip install bandit`, `npm install --save-dev …` and `pip install semgrep` lines replaced with comments naming the packages and the approval requirement.
- CI/CD section: note that the examples are proposals needing approval, and that before adoption tools are pinned exactly, action tags are replaced with commit SHAs and the project's own frozen install is used; GitHub Actions and GitLab examples pin `<exact-version>` placeholders, and ESLint comes from `npm ci` instead of `npm install -g`.
- Best practice 10 re-pins tools with approval; "Related Tools" now lists bundle items instead of missing files.

**`commands/security-dependencies.md`**

- New "Ground rules" section: tooling and install policy; remediation is reported, proposed and applied only after approval, with no blanket upgrades.
- `automation_scripts` marked as proposed commands to run only after approval (commands kept).
- CI example: marked as a proposal needing approval, with action tags to replace by commit SHAs before adoption; `pip install` and `go install` pinned to `<exact-version>` placeholders.
- "Automated Updates": approval gate and targeted-update preference added above the script (script kept); `npx npm-check-updates` pinned to `<exact-version>`.
- Best practices: staged updates and backup branches now need approval.
- "Tool Installation" install commands replaced with a table of the same tools plus the install policy.
- Usage example comment "Auto-fix vulnerabilities" now "Apply approved fixes"; closing line says "user-approved remediation".

**`commands/security-hardening.md`**

- Rules: `.security-hardening/` is written inside the current project only; checkpoints "ask the user and wait" instead of `AskUserQuestion`; dispatch `security-auditor`, `threat-modeling-expert` or a general-purpose subagent instead of `subagent_type`; no `EnterPlanMode` mention.
- New rules 7–9: only when explicitly requested (default review is `security-best-practices`); installs, commits and deployment policy; active testing needs explicit scope and approval, including ZAP MCP scans.
- Every `Task` / `subagent_type` block now names the agent (`security-scanning-security-auditor` → `security-auditor`).
- Step 2 prompt: follow `security-threat-model` with `stride-analysis-patterns` and `attack-tree-construction`, or the agent's own workflow when that skill isn't installed.
- Step 11: scope and approval gate before any active testing, with a non-active fallback and the approved scope passed to the agent.
- Step 12 prompt: uses `/compliance-check`'s framework method.
- Next steps: production deployment only when the user explicitly requests it.

**`commands/compliance-check.md`**

- `configure_tls` example: comment that HSTS is a deliberate deployment decision.
- Automated compliance checks: note that CI changes need approval, `scripts/compliance/*` are examples to create, and `license-checker` is used only if present or approved.

**`skills/sast-configuration/SKILL.md`**

- Basic setup: tooling and install policy paragraph; `pip install semgrep` and `gh extension install github/gh-codeql` removed (Semgrep, SonarQube and CodeQL commands kept, with approval notes).
- Custom rule example: missing `references/semgrep-rules.md` replaced by a pointer to `/security-sast`'s custom rules.
- `scripts/run-sast.sh` marked as an example for the project to create.
- Related skills: `/security-sast` runs scans; this skill covers configuration and CI.

**`skills/security-best-practices/SKILL.md`** (OpenAI, Apache-2.0; change notice at the end of the file)

- "search online" now follows the web-research rule (Exa search, official sources first).
- Report mode: this is the default review; `/security-hardening` only on explicit request.
- Commits: only with explicit approval of the exact command, message and files.
- TLS note: production defaults to TLS; missing TLS in local development or testing isn't a finding; HSTS only as a deliberate deployment decision with its lock-in risk explained.

`security-threat-model` isn't copied into this bundle (see the top of this README); it stays unchanged in `skills/security-threat-model/`. Plugin manifests aren't copied.

## For agents: maintaining this bundle

This bundle is **owned by this repo**. Don't overwrite it with a blind upstream copy, and don't replace the files above with upstream versions.

Upstreams and baselines:

| Upstream | Path | Baseline |
| --- | --- | --- |
| [wshobson/agents](https://github.com/wshobson/agents) | `plugins/security-scanning`, `plugins/security-compliance` | Payload copied at `46891e7e60da0e52baf1050b7b6391b64e84c6d9`; verified unchanged at `0874a27b17a22e2b7c2e2bcd725768e0803cad06` on October 20, 2026 |
| [openai/skills](https://github.com/openai/skills) | `skills/.curated/security-best-practices` | `49f948faa9258a0c61caceaf225e179651397431`; the repo is deprecated, so updates are unlikely. `security-threat-model` from the same source is maintained in its own folder |
| This repo | `rules/secure-coding.md` | Written for this repo from the OpenSSF guide |

To check for updates (ask the user before any network access):

1. `git ls-remote <upstream> HEAD` and compare with the baseline above.
2. If it differs, clone upstream into `/tmp/opencode` and diff the upstream payload between the baseline commit and the new commit. Diff upstream against upstream, not against these owned files.
3. Show the user what changed. Port relevant changes by hand into the owned files, keeping every conflict resolution listed in "Changes from upstream" (install policy, approval-gated remediation, TLS/HSTS wording, commit protocol, web-research rule, host-neutral agent names, active-testing scope gate, no dangling references, routing between items).
4. Files listed as unchanged may be copied from upstream byte for byte; keep their modes.
5. Update the baseline commits here and "Changes from upstream", and keep the license notices: the change comment at the end of each modified OpenAI file (update its description), each OpenAI `LICENSE.txt`, and the sections in `THIRD_PARTY_LICENSES.md`.

Don't:

- re-add the old separate folders (`agents/security-scanning`, `agents/security-compliance`, `rules/secure-coding`, `skills/security-best-practices`) or a second security auditor;
- copy `security-threat-model` into this bundle, which would put it back in the default install;
- rename skills (`name` must stay unique across the repo).

Keep routing consistent with the repo's routing rule (`rules/routing`): a threat model goes to `security-threat-model` (and `threat-modeling-expert` uses it), and the default security review goes to `security-best-practices`. `/security-hardening` is used only on explicit request.

## Origin

Assembled and edited for this repo by 280Zo on October 21, 2026.

- Agents, commands and the five technique/SAST skills: [wshobson/agents](https://github.com/wshobson/agents) `plugins/security-scanning` and `plugins/security-compliance`. [MIT](../../THIRD_PARTY_LICENSES.md#wshobsonagents), © 2024 Seth Hobson.
- `security-best-practices`: [openai/skills](https://github.com/openai/skills) at `49f948faa9258a0c61caceaf225e179651397431`. Publisher: OpenAI. [Apache-2.0](../../THIRD_PARTY_LICENSES.md#openaiskills); the license retains unfilled copyright-example boilerplate, not a named holder. Each skill's original `LICENSE.txt` is kept in its folder.
- `rules/secure-coding.md`: Written for this repo, based on OpenSSF's [Security-Focused Guide for AI Code Assistant Instructions](https://best.openssf.org/Security-Focused-Guide-for-AI-Code-Assistant-Instructions.html) (2025).
