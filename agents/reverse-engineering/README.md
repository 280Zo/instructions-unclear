# Reverse engineering

Three agents and four skills from Seth Hobson's agent collection, for binary, firmware and malware analysis.

- Agents: `reverse-engineer`, `firmware-analyst`, `malware-analyst`
- Skills: `binary-analysis-patterns`, `anti-reversing-techniques`, `memory-forensics`, `protocol-reverse-engineering`

From this repo it's a **profile**: it installs into one folder you choose, not your home folder. It pairs well with the [REA profile](../../mcp-servers/rea/) in the same folder.

## Install

From the repo root:

```bash
mkdir -p ~/re
npx rulesync@33.0.0 generate --config agents/reverse-engineering/profile.jsonc --output-roots ~/re --targets opencode,claudecode,codexcli
```

Swap `--targets` for your tools. Never add `--global`. Run the same command again to update.

The agents and skills describe tools (Ghidra, IDA, radare2, Volatility and others) but don't install them.

## Use

Start your tool in the profile folder and point it at what you're analyzing by path:

- "Have the reverse engineer work out what `~/samples/tool.bin` does"
- "Ask the firmware analyst to map out the filesystem in `~/firmware/router.img`"
- "Use `protocol-reverse-engineering` on the capture in `~/captures/device.pcap`"

## Changes from upstream

- Agent files are in `subagents/`, named after their upstream `name`.
- Each agent's description is quoted, it gained `targets: ["*"]` and `opencode: mode: subagent`, and `model: opus` moved under `claudecode:`. Prompts and skills are unchanged.
- Plugin manifests aren't copied.

## Origin

[wshobson/agents](https://github.com/wshobson/agents), `plugins/reverse-engineering`, commit `46891e7e60da0e52baf1050b7b6391b64e84c6d9`, copied 2026-10-14. [MIT](../../THIRD_PARTY_LICENSES.md#wshobsonagents), © 2024 Seth Hobson. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
