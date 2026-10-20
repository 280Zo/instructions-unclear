# Security scanning

Two agents, five skills and three commands from Seth Hobson's agent collection, for threat modeling and code scanning.

- Agents: `security-scanning-security-auditor`, `threat-modeling-expert`
- Skills: `attack-tree-construction`, `sast-configuration`, `security-requirement-extraction`, `stride-analysis-patterns`, `threat-mitigation-mapping`
- Commands: `security-sast`, `security-dependencies`, `security-hardening`

This bundle is included in the default global install. Installing it adds
instructions and commands; it does not install scanners or run checks.

## Install

From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode,codexcli --features subagents,skills,commands --input-roots agents/security-scanning
```

Swap `--targets` for your tools. This command does not replace rules or MCP
settings. The repo's default install includes the bundle too. Run the same
command again to update. Global output includes commands for all three targets;
invocation depends on the assistant. Older workspace-profile copies are not
removed automatically, so review them for duplicate agents and commands.

## Tools you need

Threat modeling, attack trees and requirements reviews need no scanner. For
automated checks, install only the tools appropriate to the project:

| Work | Tools and prerequisites |
| --- | --- |
| Multi-language SAST | Semgrep; CodeQL CLI plus its query packs and a supported build toolchain; or SonarQube plus a scanner and running server |
| Python | Python with Bandit and pip-audit; some upstream examples also use Safety, which may need an account or service access |
| JavaScript / TypeScript | Node and the project's package manager; project-local ESLint with reviewed security plugins; npm audit for npm projects |
| Go | Go and gosec |
| Rust | Rust/Cargo and Clippy; dependency checks may use cargo-audit |
| Java / Ruby | The project's JDK/build tools with SpotBugs or PMD; Ruby/Bundler with Brakeman, as applicable |
| Optional hosted checks | Snyk or SonarQube services may need separate setup, accounts and suitable terms |

For standalone Python CLIs, isolated tool installs are an option:

```bash
uv tool install semgrep
uv tool install bandit
uv tool install pip-audit
```

These are separate, user-run installations, not part of rulesync. Keep project
dependencies in the project's existing environment. Get CodeQL and other
non-Python tools through their official distributions; check their license and
access requirements before use. Review upstream setup snippets rather than
blindly running global installs or automated fixes. Some scripts and config
paths in the prompts are examples to create, not files supplied by this bundle.

## Use

Start your tool in the project you want reviewed:

- "Have the threat-modeling expert do a STRIDE pass on the design in `~/code/app/docs/architecture.md`"
- "Build an attack tree for the login flow in `~/code/app`" (`attack-tree-construction`)
- `/security-sast`, `/security-dependencies`, `/security-hardening` (OpenCode, Claude Code)

The commands run scanners and can propose or apply fixes; say what they may touch first. Your installed rules still apply.

## Changes from upstream

- Agent files are in `subagents/`, named after their upstream `name`. The security auditor here has the same prompt as the one in [`security-compliance`](../security-compliance/); both are kept so either folder works on its own.
- Each agent's description is quoted, it gained `targets: ["*"]` and `opencode: mode: subagent`, and `model: opus` moved under `claudecode:`. Prompts, skills and commands are unchanged.
- Plugin manifests aren't copied.

## Origin

[wshobson/agents](https://github.com/wshobson/agents), `plugins/security-scanning`, commit `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, copied 2026-10-14. [MIT](../../THIRD_PARTY_LICENSES.md#wshobsonagents), © 2024 Seth Hobson. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
