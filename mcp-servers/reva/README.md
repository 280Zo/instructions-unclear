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
npx rulesync@33.0.0 generate --config mcp-servers/reva/profile.jsonc --output-roots ~/AI/reva
```

Never add `--global`. This copies context and a **disabled** connection; it does not install Ghidra or the extension. After separately approving/installing the matching extension, start the project, verify its loopback endpoint and explicitly enable `reva` in the generated project configuration. Default assistant endpoint: `http://127.0.0.1:8080/mcp/message`. Resolve any port conflict in Ghidra and the project connection together.

Do not also install ReVa's native Claude plugin with these same skills. Do not copy upstream's blanket auto-approval suggestion. Keep the server loopback-only; scripting can execute code and annotation tools mutate project state. Restrict scripting or configure supported authentication before any shared-host deployment; this template does not authorize one. Ordinary tool calls should precede arbitrary scripting, and changes need retained evidence/appropriate approval.

## Updating

Update the extension version, skill commit and matching Ghidra requirements together, comparing upstream changes before copying. Preserve all `patterns.md`, `examples.md` and scripting references. Re-run the offline tests and throwaway reverse-engineering generation. No runtime compatibility has been tested by merely generating this config.

## Origin

Skills copied unchanged from [cyberkaida/reverse-engineering-assistant](https://github.com/cyberkaida/reverse-engineering-assistant), `ReVa/skills/`, tag `v7.3.1`, commit `3cb3e65f354cda8d6125ecff654063436a3ab5ab`, October 15, 2026. Apache-2.0, copyright 2023 サイバーカイダ; [upstream license](https://github.com/cyberkaida/reverse-engineering-assistant/blob/v7.3.1/LICENSE), [shipped full text](../../THIRD_PARTY_LICENSES.md#cyberkaidareverse-engineering-assistant). Connection template and README written for this repo by 280Zo. See the [assessment](../../reference/security-re-tooling.md) for alternatives and selection rationale.
