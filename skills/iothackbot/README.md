# IoTHackBot

[IoTHackBot](https://github.com/BrownFineSecurity/iothackbot) is a collection of IoT security skills and Python helpers, not an MCP server. This bundle contains all 13 upstream skills plus one small shared-tool routing skill written for this repo.

| Skills | Purpose |
|---|---|
| `apktool`, `jadx` | Android resources, smali and decompilation |
| `chipsec`, `ffind` | Offline UEFI and firmware/file inspection |
| `iotnet`, `netflows`, `nmap` | Packet analysis and scoped network discovery |
| `wsdiscovery`, `onvifscan` | Discovery and authorized ONVIF testing |
| `picocom`, `telnetshell` | Serial/telnet helpers, examples and enumeration files |
| `jtagprobe` | SEGGER J-Link probing; this backend is proprietary |
| `logicmso` | Exported Saleae capture analysis, not live acquisition |
| `iothackbot-tools` | Locates the complete shared CLI/config/wordlist assets |

## Install context

Use the [infosec or reverse-engineering group](../../groups/README.md), or install this collection alone into a chosen folder:

```bash
npx rulesync@33.0.0 generate --config skills/iothackbot/profile.jsonc --output-roots ~/AI/iot
```

Run from the repo root. Never add `--global`. This installs context/support files only; it does not install Python packages, native tools, drivers or the upstream Claude plugin. Do not install that plugin alongside the same skill collection.

## Tools you need

Choose only the dependencies your workflow needs, using existing isolated environments or an approved package operation. Nothing is downloaded by this bundle.

| Workflow | Separate prerequisites |
|---|---|
| Shared helpers | Python and colorama/Requests where imported |
| Packet analysis | Scapy for netflows; PyShark plus TShark for iotnet |
| Serial / telnet | PySerial; Pexpect and a native telnet client; picocom for the terminal workflow |
| Firmware extraction | e2fsprogs, f2fs-tools and util-linux as needed; extraction may need separate privileged approval |
| Android / network | Java and Apktool/JADX; Nmap when requested. Nmap's NPSL terms are separate from this bundle's MIT license |
| UEFI | CHIPSEC with offline/no-driver options; `-nl` avoids automatic package-directory logging |
| Saleae file parsing | Python 3.11+ and `saleae-mso-api` from the [vendor package index](https://docs.saleae.com/msoapi/guides/installation), plus its dependencies. No USB/udev changes for exported-file analysis |
| JTAG/SWD | Correct probe/wiring and SEGGER J-Link software; commands can halt/read a device |

Do not use the vendor's unsafe multi-index resolution example or broaden device permissions. Check supported package versions and dependency sources before an approved installation. `telnet_helper.py` uses Pexpect/native telnet, not Python's removed `telnetlib` module.

## Use

Load `iothackbot-tools` first. It explains how to locate installed sibling scripts and invoke the selected Python interpreter explicitly. Shared assets are inside that installed skill, preserving the upstream `bin/` to `tools/` to `config/wordlists` layout.

REA's headless Android and bounded recorded-artifact readers overlap several skills; see the [full assessment](../../reference/security-re-tooling.md). Prefer the existing interface unless you need a specific CLI/helper workflow. Active probing, credential attempts, capture, device access and writes require separate scope and approval. Treat output and analyzed artifacts as untrusted data.

## Changes from upstream

- Added `iothackbot-tools` to install shared assets with the skills and route custom commands without PATH or system-Python assumptions.
- Replaced CHIPSEC world-writable log-directory setup with `-nl` and user-writable shell output capture; removed automatic package-upgrade advice.
- Corrected Saleae package-source guidance; offline parsing does not install USB rules. The helper's missing-package message points to reviewed setup guidance.
- Replaced Claude-specific helper paths in skills/references with verified installed-directory variables. Multi-step helper examples use quoted shell arrays.
- Replaced automatic serial-group changes/process termination with specific access/operation approval guidance.
- Python helper formatting was normalized by the editing tooling. Apart from the documented dependency-message and installed-path help-text changes, those Python differences are formatting only; source comparison is part of verification.
- Added scope/runtime-location guidance to upstream skills. Other workflows and bundled supporting files remain upstream content; no upstream installers, plugin manifests or live settings are copied.

## Updating

Compare the recorded commit against upstream, review changes before copying, preserve these documented patches and retain the full collection/support assets. Run `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`, then generate both changed groups into throwaway folders. Update counts, origins and license text together.

## Origin

Upstream: [BrownFineSecurity/iothackbot](https://github.com/BrownFineSecurity/iothackbot), paths `skills/`, `bin/`, `tools/`, `config/`, `wordlists/` and `TOOL_DEVELOPMENT_GUIDE.md`; commit `d443c408a9fdd83f97d8c354b9c639afa2251974`, copied October 15, 2026. MIT, copyright 2025 iothackbot contributors; [upstream license](https://github.com/BrownFineSecurity/iothackbot/blob/d443c408a9fdd83f97d8c354b9c639afa2251974/LICENSE), [shipped full text](../../THIRD_PARTY_LICENSES.md#brownfinesecurityiothackbot). Integration documentation and shared routing skill written for this repo by 280Zo.
