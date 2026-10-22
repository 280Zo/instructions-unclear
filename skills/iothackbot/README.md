# IoTHackBot

[IoTHackBot](https://github.com/BrownFineSecurity/iothackbot) is an IoT security toolkit with 13 Claude Code skills and shared Python/CLI/config/wordlist resources. `upstream/` is the complete upstream tree, unchanged, including its plugin manifests and supporting files. It is **not a rulesync source root**.

## Install

Prefer the [upstream setup and plugin procedure](upstream/README.md#installation). After reviewing dependencies and operations, Claude Code can load the complete local tree from the repo root:

```bash
claude --plugin-dir ./skills/iothackbot/upstream
```

Upstream also documents persistent local-marketplace installation. Its CLI helpers require a separately approved environment and the upstream `bin/` on that environment's PATH. Merely loading the plugin does not install dependencies, native tools, drivers or hardware access. The upstream documentation includes privileged commands and dependency examples; do not run them automatically or weaken device/filesystem permissions. Apply your host's scope, permission and package-management rules.

No upstream OpenCode integration is documented or claimed here. OpenCode's former flattened copy and repo-authored `iothackbot-tools` router are no longer generated. Do not recreate path rewrites merely to simulate native support. If you need OpenCode support, demonstrate the specific host/resource failure and approve a separate integration design first.

## Verified ownership and migration

In an isolated, network-disabled Claude Code 2.1.296 environment, native validation passed, direct loading discovered all 13 skills, and the local marketplace installed successfully. Subsequent generation of the reduced infosec and reverse-engineering groups left all native plugin files unchanged. This verifies packaging and discovery, not operation against devices or installation of dependencies.

The previous local safety/portability edits, Python formatting changes and helper router were removed in favor of faithful upstream content. Upstream examples retain Claude-specific paths and runtime assumptions; native loading does not prove every example works on every host. Review them before execution. Nothing in this refresh authorizes probing, credential attempts, capture, device access or writes.

Existing live extracted skills are not removed by `delete: false`. Before activating the native plugin, review and explicitly approve removing stale copies of the 13 named skills and `iothackbot-tools` from the intended assistant. Do not install both owners simultaneously. This refresh changes only repository files.

## Use

Ask for APK/firmware analysis, recorded packet/capture inspection, or a specifically authorized console/device workflow. Dependencies include the selected Java/native tool, packet or serial libraries, and proprietary SEGGER J-Link or Saleae components where named. Choose only what the task needs. See [upstream usage](upstream/README.md#usage) and the [tooling assessment](../../reference/security-re-tooling.md).

## Updating

Compare the recorded revision with upstream, review the complete tree, then replace `upstream/` faithfully. Validate native plugin loading and subsequent rulesync coexistence in isolation before deleting an existing working integration. Keep this wrapper and the consolidated license notice current.

## Origin

[BrownFineSecurity/iothackbot](https://github.com/BrownFineSecurity/iothackbot), complete tree at commit `d443c408a9fdd83f97d8c354b9c639afa2251974`, copied October 20, 2026. MIT, © 2025 iothackbot contributors; [full notice](../../THIRD_PARTY_LICENSES.md#brownfinesecurityiothackbot), also preserved in `upstream/LICENSE`. Wrapper written for this repo by 280Zo.
