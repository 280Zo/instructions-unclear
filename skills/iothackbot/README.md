# IoTHackBot

[IoTHackBot](https://github.com/BrownFineSecurity/iothackbot) is an IoT security toolkit with 13 Claude Code skills and shared Python/CLI/config/wordlist resources. `upstream/` is the complete upstream tree, unchanged, including its plugin manifests and supporting files. It is **not a rulesync source root**.

## Install

Prefer the [upstream setup and plugin procedure](upstream/README.md#installation). After reviewing dependencies and operations, Claude Code can load the complete local tree from the repo root:

```bash
claude --plugin-dir ./skills/iothackbot/upstream
```

Upstream also documents persistent local-marketplace installation. Its CLI helpers require a separately approved environment and the upstream `bin/` on that environment's PATH. Merely loading the plugin does not install dependencies, native tools, drivers or hardware access. The upstream documentation includes privileged commands and dependency examples; do not run them automatically or weaken device/filesystem permissions. Apply your host's scope, permission and package-management rules.

No upstream OpenCode integration is documented or claimed here. Do not recreate path rewrites merely to simulate native support. If you need OpenCode support, demonstrate the specific host/resource failure and approve a separate integration design first.

## Verified ownership

In an isolated, network-disabled Claude Code 2.1.296 environment, native validation passed, direct loading discovered all 13 skills, and the local marketplace installed successfully. Subsequent generation of the reduced infosec and reverse-engineering groups left all native plugin files unchanged. This verifies packaging and discovery, not operation against devices or installation of dependencies.

Upstream examples retain Claude-specific paths and runtime assumptions; native loading does not prove every example works on every host. Review them before execution. Nothing here authorizes probing, credential attempts, capture, device access or writes.

Don't install the native plugin and extracted copies of its 13 skills in the same assistant.

## Use

Ask for APK/firmware analysis, recorded packet/capture inspection, or a specifically authorized console/device workflow. Dependencies include the selected Java/native tool, packet or serial libraries, and proprietary SEGGER J-Link or Saleae components where named. Choose only what the task needs. See [upstream usage](upstream/README.md#usage).

## Updating

Compare the recorded revision with upstream, review the complete tree, then replace `upstream/` faithfully. Validate native plugin loading and subsequent rulesync coexistence in isolation before deleting an existing working integration. Keep this wrapper and the consolidated license notice current.

## For agents: install, remove and update

To install, use the native plugin procedure in [Install](#install). No group includes it, and rulesync never installs it. It is documented for Claude Code only. Get approval before editing `~/.claude/settings.json` or installing any dependency from [Use](#use). To verify, start Claude Code with the plugin loaded and check that the 13 skills are listed. Don't run them against a device, network or capture as a test.

To remove, use the same mechanism that installed it. For `--plugin-dir`, stop passing the flag. For the local marketplace, with approval remove the `iothackbot` entry under `enabledPlugins` and the `iothackbot-local` entry under `extraKnownMarketplaces` that upstream's option 2 added, keep every other setting, and restart Claude Code. Never delete files in this repo's `upstream/` to uninstall it. Old extracted copies from before the native plugin (`apktool`, `chipsec`, `ffind`, `iotnet`, `jadx`, `jtagprobe`, `logicmso`, `netflows`, `nmap`, `onvifscan`, `picocom`, `telnetshell`, `wsdiscovery` and `iothackbot-tools`) are removed as [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component) describes, with approval. Python environments, native tools, drivers and vendor software stay unless the user asks.

To update, follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The copied commit is in [Origin](#origin).

## Origin

[BrownFineSecurity/iothackbot](https://github.com/BrownFineSecurity/iothackbot), complete tree at commit `d443c408a9fdd83f97d8c354b9c639afa2251974`, copied October 20, 2026. MIT, © 2025 iothackbot contributors; [full notice](../../THIRD_PARTY_LICENSES.md#brownfinesecurityiothackbot), also preserved in `upstream/LICENSE`. Wrapper written for this repo by 280Zo.
