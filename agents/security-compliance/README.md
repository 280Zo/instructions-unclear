# Security compliance

One agent, `security-compliance-security-auditor`, and one command, `compliance-check`, from Seth Hobson's agent collection: DevSecOps, compliance frameworks (GDPR, HIPAA, SOC 2) and audit evidence.

This bundle is included in the default global install. Installing the context
files does not run a scan, install tools or authorize changes to a project.

## Install

From the repo root:

```bash
npx rulesync@33.0.0 generate --global --targets opencode,claudecode,codexcli --features subagents,commands --input-roots agents/security-compliance
```

Swap `--targets` for your tools. The command installs just this bundle without
replacing rules or MCP settings. The repo's default install includes it too.
Run the same command again to update. Commands are included in global output
for OpenCode, Claude Code and Codex; invocation depends on the assistant.

Older workspace-profile copies are not removed automatically. If you used one,
review that workspace for duplicate agents and commands after installing globally.

## Use

Start your tool in the project you want reviewed:

- "Use the security auditor to list the evidence we'd need for a SOC 2 review of `~/code/app`"
- `/compliance-check` (OpenCode, Claude Code)

The command can run checks and propose changes; say what it may touch first. Your installed rules still apply.

## Tools you need

No scanner is required to discuss compliance requirements or assemble an
evidence checklist. Automated evidence collection needs the relevant project's
runtime, test tools and any scanners you choose. The prompt contains example
code, not a preinstalled audit application. Installing this bundle does not
establish compliance or replace a qualified compliance review.

## Changes from upstream

- The agent file is in `subagents/`, named after its upstream `name`.
- Its description is quoted, it gained `targets: ["*"]` and `opencode: mode: subagent`, and `model: opus` moved under `claudecode:`. The prompt and the command are unchanged.
- Plugin manifests aren't copied.

## Origin

[wshobson/agents](https://github.com/wshobson/agents), `plugins/security-compliance`, commit `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, copied 2026-10-14. [MIT](../../THIRD_PARTY_LICENSES.md#wshobsonagents), © 2024 Seth Hobson. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
