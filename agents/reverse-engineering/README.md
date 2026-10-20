# Reverse engineering

Three agents and four skills from Seth Hobson's agent collection, for binary, firmware and malware analysis.

- Agents: `reverse-engineer`, `firmware-analyst`, `malware-analyst`
- Skills: `binary-analysis-patterns`, `anti-reversing-techniques`, `memory-forensics`, `protocol-reverse-engineering`

From this repo it's a **profile**: it installs into one folder you choose, not your home folder. It pairs well with the [REA profile](../../mcp-servers/rea/) in the same folder.

## Install

From the repo root:

```bash
mkdir -p ~/reverse_engineering/re
npx rulesync@33.0.0 generate --config agents/reverse-engineering/profile.jsonc --output-roots ~/reverse_engineering/re --targets opencode,claudecode,codexcli
```

Swap `--targets` for your tools. Never add `--global`. Run the same command again to update.

## Tools you need

The profile installs instructions only. Choose tools for the artifact you are
authorized to examine; you do not need everything below for every task.

| Work | Tools and prerequisites |
| --- | --- |
| Static binary analysis | A disassembler/decompiler such as Ghidra, radare2, IDA Pro or Binary Ninja. Ghidra also needs the Java version required by its release; commercial tools need their own licenses |
| Debugging | GDB or LLDB on supported systems; x64dbg for Windows. Attach permissions and target access are separate from this profile |
| Memory forensics | Volatility 3, Python and suitable OS symbols; an already-acquired memory image. Memory acquisition tools/drivers are a separate privileged setup |
| Protocol analysis | Wireshark or TShark and an authorized capture file. Live capture needs separate interface permissions and scope approval |
| Firmware | Binwalk or other chosen unpackers plus their extraction dependencies; architecture-specific tools as needed |
| Advanced analysis | Optional angr, Unicorn, Frida or QEMU when the selected workflow calls for them; use an isolated environment and their supported versions |

Install these from their official distributions or your OS package manager.
Some Python CLIs can use isolated tool environments, for example:

```bash
uv tool install volatility3
```

That installs the analysis CLI, not capture drivers, symbols or target access.
The [REA setup](../../mcp-servers/rea/#install) has its own runtime/backend
requirements if you also want its MCP integration. Nothing here runs tools or
analyzes an artifact merely by being installed.

The [tooling assessment](../../reference/security-re-tooling.md) covers the full categorized inventory, AI interfaces and overlap with these agents. The [reverse-engineering group](../../groups/README.md#reverse_engineering) also includes IoTHackBot and ReVa skills plus disabled ReVa/radare2 connections; this agent-only profile does not install those extras.

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
