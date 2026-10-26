# ReVa

[ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) connects an assistant to shared Ghidra programs/projects, annotations, types and comparison workflows. It is distinct from [REA](../rea/), which remains the broad default analysis interface. This bundle contains a disabled assistant-mode HTTP connection and all six upstream companion skills/references.

| Skill | Purpose |
|---|---|
| `binary-triage` | Initial binary inventory |
| `deep-analysis` | Extended investigation |
| `ctf-crypto`, `ctf-pwn`, `ctf-rev` | Specialist challenge workflows |
| `pyghidra-scripting` | ReVa-hosted Python scripting, not standalone PyGhidra |

## Tools you need

- Ghidra 12+ with the **ReVa v7.3.1 extension built for your exact Ghidra version**. Use the [tagged release](https://github.com/cyberkaida/reverse-engineering-assistant/releases/tag/v7.3.1), not an arbitrary latest build. If no matching asset exists, stop and assess a supported version rather than guessing compatibility.
- A running Ghidra project with ReVa enabled in both the Project and Code Browser plugin configuration, as the [tagged README](https://github.com/cyberkaida/reverse-engineering-assistant/blob/v7.3.1/README.md#installation) describes.
- For `run-script`, Ghidra must run under PyGhidra; ordinary `ghidraRun` does not expose that scripting runtime. Python/JDK prerequisites follow the selected Ghidra release. Other ReVa functions do not imply full scripting support.

## Install and activate

From the repo root, use the [reverse-engineering group](../../groups/README.md#reverse_engineering), or this component alone:

```bash
npx rulesync@41.0.0 generate --config mcp-servers/reva/profile.jsonc --output-roots ~/AI/reva
```

Never add `--global`. This copies context and a **disabled** connection; it does not install Ghidra or the extension. After separately approving/installing the matching extension, start the project, verify its loopback endpoint and explicitly enable `reva` in the generated project configuration. Default assistant endpoint: `http://127.0.0.1:8080/mcp/message`. Resolve any port conflict in Ghidra and the project connection together.

Do not also install ReVa's native Claude plugin with these same skills. Do not copy upstream's blanket auto-approval suggestion. Keep the server loopback-only; scripting can execute code and annotation tools mutate project state. Restrict scripting or configure supported authentication before any shared-host deployment; this template does not authorize one. Ordinary tool calls should precede arbitrary scripting, and changes need retained evidence/appropriate approval.

## For agents: install, remove and update

### Install

This is a folder profile, also in the [reverse-engineering group](../../groups/README.md#reverse_engineering); use the command in [Install and activate](#install-and-activate) and never `--global`. OpenCode's `default` group also installs it, switched off, where only the [`reverse-engineering` agent](../../agents/reverse-engineering/) may use its tools. The `reva` connection is written switched off. Ghidra, the matching ReVa extension and, for scripting, PyGhidra are prerequisites rulesync doesn't install (see [Tools you need](#tools-you-need)).

Follow the [shared backend installation procedure](../../agents/reverse-engineering/README.md#for-agents-installing-and-verifying-backends). Ask whether ordinary project access or PyGhidra scripting is required; do not install the scripting stack for an ordinary read-only check.

1. Inspect the existing Ghidra/JDK installation and extension versions. Select the exact Ghidra build, **ReVa v7.3.1** matching asset and, if requested, PyGhidra requirements from the tagged instructions above. If there is no matching asset, stop. Show official download/build commands, installation paths and required runtime changes for approval; verify published checksums/signatures when available.
2. Back up approved plugin settings. Install the extension through Ghidra's supported mechanism, then enable the Project and Code Browser plugins as documented. Hand interactive GUI/license steps to the user when automation is unavailable. Do not remove working extensions or install duplicate companion skills.
3. With approval, create a disposable project containing a benign fixture, start the loopback-only server and check the intended port is free. Explicitly approve enabling the assistant connection; preserve other MCP entries and permissions. Do not bind it to a public interface to work around a connection problem.
4. Smoke test the MCP catalog and a read-only operation on the fixture using the installed server's schema. Record the Ghidra and extension versions and observed result. Scripting remains untested unless separately requested; if it is requested, test only a reviewed harmless script in the disposable PyGhidra project. Do not modify a real project or run arbitrary scripts as an installation check.
5. Follow the shared handoff/rollback checklist. Remove or stop only this test's approved resources; keep the connection disabled if setup is incomplete. Generation, connection, ordinary project access and scripting are separate verification results.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component), including its note on folder groups. Regenerating the folder without this one removes the `reva` entry from that folder's MCP list, because each run replaces it. Otherwise, with approval, delete the generated files in the folder, or the whole folder if nothing else lives there.
- `delete: false` leaves six skill folders behind in that folder's skills directory: `binary-triage`, `deep-analysis`, `ctf-crypto`, `ctf-pwn`, `ctf-rev` and `pyghidra-scripting`. Delete them only with approval, and only if no other installed folder provides them.
- Ghidra, the ReVa extension and its plugin settings, PyGhidra, and the user's Ghidra projects stay. Never remove or change them without the user's explicit approval; use the shared handoff/rollback checklist if they ask.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The pin is ReVa v7.3.1, recorded in this README, the `mcp.jsonc` comment and [Origin](#origin). Change it together with the six copied skills, the Ghidra requirements, and the [license section](../../THIRD_PARTY_LICENSES.md#cyberkaidareverse-engineering-assistant) if upstream's license changed.

## Updating

Update the extension version, skill commit and matching Ghidra requirements together, comparing upstream changes before copying. Preserve all `patterns.md`, `examples.md` and scripting references. Re-run the offline tests and throwaway reverse-engineering generation. No runtime compatibility has been tested by merely generating this config.

Checked October 20, 2026: v7.3.1 remains the latest release and all six copied skill payloads match the audited upstream development tree. The verified release baseline below is retained; unrelated later repository commits are not a reason to relabel the copied source.

## Origin

Skills copied unchanged from [cyberkaida/reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant), `ReVa/skills/`, tag `v7.3.1`, commit `3cb3e65f354cda8d6125ecff654063436a3ab5ab`, October 15, 2026. Apache-2.0, copyright 2023 サイバーカイダ; [upstream license](https://github.com/cyberkaida/reverse-engineering-assistant/blob/v7.3.1/LICENSE), [shipped full text](../../THIRD_PARTY_LICENSES.md#cyberkaidareverse-engineering-assistant). Connection template and README written for this repo by 280Zo.
