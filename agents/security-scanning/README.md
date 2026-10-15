# Security scanning

Two agents, five skills and three commands from Seth Hobson's agent collection, for threat modeling and code scanning.

- Agents: `security-scanning-security-auditor`, `threat-modeling-expert`
- Skills: `attack-tree-construction`, `sast-configuration`, `security-requirement-extraction`, `stride-analysis-patterns`, `threat-mitigation-mapping`
- Commands: `security-sast`, `security-dependencies`, `security-hardening`

From this repo it's a **profile**: it installs into one folder you choose, not your home folder.

## Install

From the repo root:

```bash
mkdir -p ~/security
npx rulesync@33.0.0 generate --config agents/security-scanning/profile.jsonc --output-roots ~/security --targets opencode,claudecode,codexcli
```

Swap `--targets` for your tools. Never add `--global`. Run the same command again to update. Codex gets the agents and skills but not the commands: rulesync 33.0.0 only writes Codex commands globally.

Scanners such as Semgrep aren't installed by this; each skill and command names what it needs.

## Use

Start your tool in the profile folder and point it at the code by path:

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
