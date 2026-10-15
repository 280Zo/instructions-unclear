# Security compliance

One agent, `security-compliance-security-auditor`, and one command, `compliance-check`, from Seth Hobson's agent collection: DevSecOps, compliance frameworks (GDPR, HIPAA, SOC 2) and audit evidence.

From this repo it's a **profile**: it installs into one folder you choose, not your home folder.

## Install

From the repo root:

```bash
mkdir -p ~/security
npx rulesync@33.0.0 generate --config agents/security-compliance/profile.jsonc --output-roots ~/security --targets opencode,claudecode,codexcli
```

Swap `--targets` for your tools. Never add `--global`. Run the same command again to update. Codex gets the agent but not the command: rulesync 33.0.0 only writes Codex commands globally.

## Use

Start your tool in the profile folder and point it at the code by path:

- "Use the security auditor to list the evidence we'd need for a SOC 2 review of `~/code/app`"
- `/compliance-check` (OpenCode, Claude Code)

The command can run checks and propose changes; say what it may touch first. Your installed rules still apply.

## Changes from upstream

- The agent file is in `subagents/`, named after its upstream `name`.
- Its description is quoted, it gained `targets: ["*"]` and `opencode: mode: subagent`, and `model: opus` moved under `claudecode:`. The prompt and the command are unchanged.
- Plugin manifests aren't copied.

## Origin

[wshobson/agents](https://github.com/wshobson/agents), `plugins/security-compliance`, commit `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, copied 2026-10-14. [MIT](../../THIRD_PARTY_LICENSES.md#wshobsonagents), © 2024 Seth Hobson. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
