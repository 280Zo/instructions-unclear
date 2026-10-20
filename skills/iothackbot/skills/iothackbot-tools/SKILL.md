---
name: iothackbot-tools
description: Locate and run the packaged IoTHackBot CLI helpers and support assets used by its firmware, network, ONVIF, UART and telnet skills. Load before using an IoTHackBot custom command or resolving a companion helper path.
---

# IoTHackBot shared tools

Written for this repo. The adjacent `bin/`, `tools/`, `config/` and `wordlists/` are the upstream toolkit, kept together so their relative references work after rulesync installs this skill.

## Resolve paths before execution

Use the actual base directory reported when this skill is loaded. Set `IOTHACKBOT_ROOT` to that directory, not the repository root and not a guessed assistant-specific installation path. If the host does not report the base directory, locate this exact installed `SKILL.md` first and verify its adjacent assets. Do not search credential/configuration files to find it.

For a custom CLI, use the selected Python interpreter explicitly, for example:

```bash
python "$IOTHACKBOT_ROOT/bin/netflows" --help
```

Use the same pattern for `ffind`, `iotnet`, `jtagprobe`, `onvifscan` and `wsdiscovery`. Do not fall through to an unrelated same-named command on PATH, especially Sleuth Kit's `ffind`. Explicit Python invocation avoids the upstream wrappers' system-Python shebangs and does not require adding anything to PATH.

For serial, telnet and LogicMSO helpers, locate the sibling skill's installed base directory and use its adjacent scripts. In those skills and references, set `PICOCOM_SKILL_DIR`, `TELNETSHELL_SKILL_DIR` or `LOGICMSO_SKILL_DIR` to the verified installed directory before using examples. These are non-secret path variables. Quote helper/script paths, including paths containing spaces; use a shell array rather than an unquoted `HELPER` command string when adapting multi-step examples.

## Scope and prerequisites

Installation grants no permission to operate a target. Confirm scope and approval before active discovery, authentication attempts, capture, console commands, target halt/memory access or writes. Begin with authorized offline artifacts when possible. Never change device permissions, install dependencies, start privileged capture or run broad scan defaults merely because a skill shows an example.

Use an existing isolated Python environment whose dependencies match the selected workflow. `iotnet` needs PyShark and TShark; `netflows` needs Scapy; console helpers need PySerial/Pexpect; ONVIF tooling uses Requests; other helpers use colorama and native filesystem utilities. The component README lists the full prerequisites. Do not auto-install them.

Use REA for its existing headless Android and bounded artifact analysis unless the user specifically needs an IoTHackBot CLI workflow. Use native installed Nmap/Apktool/JADX/CHIPSEC only for the selected task. Do not install IoTHackBot's native Claude plugin as well as this rulesync collection: it would duplicate the skill names.
