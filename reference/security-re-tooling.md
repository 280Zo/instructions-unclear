# Security and reverse-engineering AI integration audit

## Recommendation

Keep REA and the existing specialist agents. ZAP's official MCP serves the web-security role, ReVa supports shared Ghidra projects and radareorg's MCP covers radare2-specific work. The repository now includes their disabled connection templates and the complete IoTHackBot collection with documented safety/portability patches. These are catalog choices for the requested workflows, not instructions to enable every server together.

Written for the repository owner to choose context bundles for the `infosec` and `reverse_engineering` profiles. This is a repository-content recommendation, not an instruction to install or operate tools.

## Scope and evidence

- Research date: October 15, 2026. Primary evidence: upstream documentation, source/package files, license texts, release notes and public GitHub repository metadata. Links in the tables identify the reviewed projects or specific documentation.
- Current metadata was read through GitHub's unauthenticated repository API where available. The shared unauthenticated quota was exhausted; requests stopped rather than using credentials or another route. Missing metrics remain unknown. Some returned push dates were October 16 UTC, beyond the session's October 15 date; those dates are excluded from date-based ranking.
- No analysis tools were installed or runtime-tested. No samples, devices, capture interfaces, targets, credentials or live configurations were accessed. Pinned rulesync was downloaded only into a temporary verification directory. Packaging tests/generation passed; upstream test presence and release notes do not establish a passing native runtime or a security audit.
- Public web documentation can change. Included pins are REA `6.5.0`, IoTHackBot commit `d443c408a9fdd83f97d8c354b9c639afa2251974`, ReVa `v7.3.1`, radare2 MCP `1.8.8` and ZAP MCP `0.4.0`. Component READMEs record exact source commits and applicable licenses. Deferred candidates remain unimported; their versions are research observations, not repository pins.
- Prior handoff claims are superseded where the findings below differ. In particular, MIGINC's fork parent is LaurieWired, not bethington; its installation documentation references bethington. `netwlos` is treated as a likely reference to `netflows`, not as an independently identified tool.

## Selection criteria

Choose a real capability first, then assess licensing, compatibility, supported releases, maintenance evidence, tests and adoption. Official/vendor-maintained integrations take preference when they meet the need. Stars help assess adoption; they do not establish stability, correctness or safety. A recent push alone does not establish substantive maintenance. No numerical stability score is justified by this documentation-only audit.

An AI component means an MCP server, an agent-host plugin, or a usable skill/workflow with its required helpers. A normal SDK plugin, JSON output, contributor `AGENTS.md`, or a CLI that an agent can invoke does not by itself establish a dedicated AI integration.

## Final de-duplicated repository shortlist

### Core content

| Component | Decision | Repository placement / profile | Reason and boundary |
|---|---|---|---|
| [REA](https://github.com/morluto/rea/blob/rea-agents-6.5.0/README.md) | Keep existing | `mcp-servers/rea/`; reverse_engineering | Broad analysis MCP plus investigation skill. Reuses external native providers, Rizin, Android tools and bounded artifact readers. It does not install every backend or replace live GUI/device integrations. |
| [IoTHackBot](https://github.com/BrownFineSecurity/iothackbot) | Imported with documented safety/portability patches; native runtime not installed/tested | `skills/iothackbot/`; both profiles | [MIT license verified](https://github.com/BrownFineSecurity/iothackbot/blob/master/LICENSE). All 13 upstream skills plus one repo-authored shared-tool skill preserving CLI/config/wordlist assets in generated output. Adds device/console/ONVIF/J-Link workflows. Do not also install its native plugin with duplicate skill names. |
| [Official ZAP MCP add-on](https://www.zaproxy.org/docs/desktop/addons/mcp-integration/) | Disabled template added; host-dependent activation | `mcp-servers/zap/`; infosec | FOSS web-security control: crawling, contexts, alerts, scans and reports. Official in-process add-on, not a generic HTTP proxy wrapper. Requires separately installed ZAP/add-on. |
| Existing RE/security agent bundles | Keep | `agents/reverse-engineering/`, security bundles and Trail of Bits; current profile boundaries | Existing reverse-engineer, firmware-analyst and malware-analyst plus four skills remove the need for new generic personas. Tool mentions in a prompt are not installed integrations. |

### Selected specialist integrations, opt-in rather than concurrent defaults

| Capability | Selected component | Profile and activation | Why this choice |
|---|---|---|---|
| Shared Ghidra GUI/project analysis | [ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) | `mcp-servers/reva/`; reverse_engineering, disabled until matched Ghidra extension is installed | Project/session workflows, annotations/types, multi-program work and Version Tracker/diffing distinguish it from REA's broad provider. Release 7.3.1 has versioned artifacts/signature evidence; six companion skills are included. ReVa is a different project from REA. |
| radare2-native analysis | [radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp) | `mcp-servers/radare2/`; reverse_engineering, disabled opt-in | Maintained organization upstream, releases and documented security fixes; actual r2 ecosystem support. Rizin is a distinct framework. If no r2-specific workflow is wanted, leave this disabled and use REA/Rizin. |

These selections preserve distinct capabilities, not alternate MCP wrappers for the same basic operation. ReVa is selected for project collaboration, not declared universally better than the much more popular LaurieWired integration. radare2 is selected for its separate ecosystem, not as a universally better disassembler.

### Conditional winners, not part of the initial core

| Need | Choose | Why optional / remaining check |
|---|---|---|
| Existing supported Saleae hardware, live acquisition | [Saleae built-in MCP](https://docs.saleae.com/mcp/guides/getting-started) | Vendor integration avoids a third-party wrapper. Proprietary, experimental host; documented Logic MSO support remains forthcoming. Confirm supported device/app version. |
| Analyst-visible JADX project/debugger context | [zinja-coder/jadx-ai-mcp](https://github.com/zinja-coder/jadx-ai-mcp) + [matching server](https://github.com/zinja-coder/jadx-mcp-server) | One paired integration, not two alternatives. Adds GUI context, edits and debugger inspection beyond headless analysis. No claim of complete debugger control. |
| Semantic Android phone UI automation | [mobile-next/mobile-mcp](https://github.com/mobile-next/mobile-mcp) | Accessibility/screenshot interaction complements ADB. Prefer local operation; adds nothing necessary for offline APK analysis. |
| Programmable live HTTP interception/replay beyond ZAP | [snapspecter/mitmproxy-mcp](https://github.com/snapspecter/mitmproxy-mcp) | Proxy lifecycle, modification and replay. Use instead of another mitmproxy adapter. If controlling an already-running flow view is the requirement, assess [lups2000](https://github.com/lups2000/mitmproxy-MCP) instead. |
| Already-licensed IDA, new dedicated IDA integration | [HexRaysSA/ida-mcp](https://github.com/HexRaysSA/ida-mcp) | Official MIT connector, proprietary IDA 9.4+/idalib requirements. Not demonstrated to be a drop-in replacement for REA's existing mrexodia integration. |
| Existing Burp workflow | [PortSwigger official MCP](https://github.com/PortSwigger/mcp-server) | Prefer vendor extension over forks; Burp remains proprietary. Usually an alternative to ZAP, not another default scanner. |

### Evaluation-only or deferred

- [Official angr MCP](https://api.angr.io/en/latest/api/angr.mcp.html): real upstream interface, but documented tools primarily overlap static CFG/decompilation/xrefs and annotations. Do not sell it as an exposed symbolic path-solving API. Defer until a specific angr-backed analysis requirement and compatible release are demonstrated.
- Frida: real complementary runtime instrumentation, but no audited wrapper earns an unconditional winner. Evaluate **one** of [dnakov](https://github.com/dnakov/frida-mcp) (greater adoption, stale activity) or [fuzzmind](https://github.com/fuzzmind/frida-mcp) (explicit Frida 17 bounds, tiny adoption) against the required runtime. Do not import both by default.
- MobSF: useful integrated security analysis, but wrappers differ sharply. [plur1bu5](https://github.com/plur1bu5/mobsf-mcp) has broader static/dynamic coverage; its setup patches host API restrictions. Do not use that setup. [pullkitsan](https://github.com/pullkitsan/mobsf-mcp-server) is narrower static upload/scan. Neither is a core selection without compatibility and setup validation.
- OpenOCD and sigrok live-control wrappers remain evaluation-only; defaults/implementation gaps prevent recommending them as stable safe defaults. No validated dedicated flashrom wrapper was established.
- Moria and Mithril are optional native CLI prerequisites/workflows, not MCP additions. Mithril's content/SBOM/CVE scanning is distinct from extraction; no need to add Moria merely because Mithril is selected.
- Additional general RE skill bundles and generic new analyst agents are unnecessary for the initial selection.

## Complete inventory classification

Repeated tools from the user's categories are merged into one row. Named MCP implementations are reviewed separately in the following section.

### Hosts and primary frameworks

| Entry | AI component / disposition |
|---|---|
| REA / REA MCP | Existing selected MCP, CLI and workflow skill; [pinned README](https://github.com/morluto/rea/blob/rea-agents-6.5.0/README.md). Official name here is Reverse Engineer Anything. |
| ReVa / ReVa MCP / ReVa workflows | Selected optional Ghidra extension/server/workflows as one bundle; [upstream](https://github.com/cyberkaida/reverse-engineering-assistant). Its PyGhidra skills target ReVa sessions, not arbitrary REA sessions. |
| IoTHackBot integrations / skills | Imported whole skill/tool collection with documented safety/portability patches; [upstream](https://github.com/BrownFineSecurity/iothackbot). Claude Code plugin packaging does not make the collection an MCP server. |
| OpenCode | Existing agent host, not an analysis backend. No new RE bundle follows from the name. |
| Anthropic Claude | Model/product family; distinguish Claude Code's local tool access from chat-only use. Host/account choice, not a new RE connector. |
| Exa / Exa MCP / web_fetch_exa | Existing research service/connector/tool in `mcp-servers/exa/`; reuse. Retrieval is not a second MCP server. |

### Binary, mobile and supporting analysis engines

| Tool | AI interface and decision |
|---|---|
| [Ghidra](https://github.com/NationalSecurityAgency/ghidra) | Native host prerequisite. REA baseline; ReVa selected only for the distinct shared project workflow. Do not add all Ghidra servers. |
| [IDA Pro](https://docs.hex-rays.com/core/mcp) | Proprietary host; REA existing integration, optional official MCP. Connector license does not grant an IDA entitlement. |
| [Hopper](https://www.hopperapp.com/) | Proprietary host with built-in MCP; REA provider exists. No extra shmsr wrapper by default. |
| [Rizin](https://github.com/rizinorg/rizin) | REA caller-supplied provider; native prerequisite, no additional baseline server. |
| [radare2](https://github.com/radareorg/radare2) | Distinct r2 framework. Selected optional official-organization MCP. |
| [Cutter](https://github.com/rizinorg/cutter) | Rizin GUI. No dedicated context addition needed; documented Cutter commands do not imply synchronized full GUI control. |
| [RetDec](https://github.com/avast/retdec) | Native decompiler/ordinary integrations; upstream reports limited maintenance. No official AI plugin established; omit default. |
| [JEB](https://www.pnfsoftware.com/jeb/manual/mcp/) | Proprietary host with native GUI/CLI MCP. REA can connect to caller-started service. Prefer native support over extension unless an actual version defect is shown. |
| [JADX](https://github.com/skylot/jadx) | Native CLI/GUI, Apache-2.0. REA headless + IoTHackBot skill; optional Zin paired GUI integration for different capability. |
| [Apktool](https://github.com/iBotPeaches/Apktool) | Native decode/rebuild/smali tool, Apache-2.0. REA/IoTHackBot cover workflow. Separate server duplicates baseline. |
| [angr](https://api.angr.io/en/latest/api/angr.mcp.html) | Actual upstream MCP supports load, CFG, decompile, references and edits. Evaluation-only; no documented general symbolic exploration tool in the reviewed list. |
| [Qiling](https://github.com/qilingframework/qiling) | OS-aware emulation framework. Its IDA plugin is not an AI plugin. Third-party emulation wrappers exist but were not validated enough to select. |
| [Unicorn](https://github.com/unicorn-engine/unicorn) | CPU-emulation library/dependency. No separate MCP justified. |
| [Capstone](https://github.com/capstone-engine/capstone) | Disassembly library/dependency. No separate MCP justified. |
| [FLOSS](https://github.com/mandiant/flare-floss) | Obfuscated-string extraction CLI/JSON and conventional import scripts. Useful native utility; no official AI connector established. |
| [Frida](https://frida.re/docs/android/) | Runtime instrumentation, complementary to static analysis; conditional one-wrapper pilot only. Matching runtime/server or Gadget prerequisites remain separate. |
| IDA Plugins | Unspecified category; request exact plugin, license and capability. Normal IDA plugins are not automatically AI components. |
| [MobSF](https://github.com/MobSF/Mobile-Security-Framework-MobSF) | GPL-3.0 static/dynamic security platform. Community MCPs exist; defer default pending compatibility review. Not merely another Java decompiler. |
| [ADB](https://developer.android.com/tools/adb) | Existing REA device workflows; native transport/CLI prerequisite. Do not confuse shell/install access with semantic UI automation. |
| [scrcpy](https://github.com/Genymobile/scrcpy) | Human-facing mirroring/control application, Apache-2.0. No adapter needed just for mirroring; Mobile Next wins the optional semantic-UI role. Streaming-specific wrappers remain alternatives. |

### Firmware and hardware

| Tool | AI interface and decision |
|---|---|
| [CHIPSEC](https://github.com/chipsec/chipsec) | Native framework; IoTHackBot adds an offline UEFI skill. Hardware-driver access is separate. Imported setup uses `-nl` and user-writable output capture instead of world-writable package directories. |
| [Binwalk](https://github.com/ReFirmLabs/binwalk) | Native firmware identification/extraction; already callable by REA. No extra MCP needed. |
| [Unblob](https://github.com/onekey-sec/unblob) | Native recursive extractor; already callable by REA. Format plugins are not AI plugins. |
| [Firmwalker](https://github.com/craigz28/firmwalker) | Bash searches over extracted firmware, GPL-3.0. No established dedicated AI component; mostly duplicates searchable-file workflows. |
| [FIRMADYNE](https://github.com/firmadyne/firmadyne) | Native firmware emulation research framework. Distinct dynamic capability, substantial isolated-lab setup; not a core AI-context addition. |
| [Moria](https://github.com/nmatt0/moria) | MIT C++ firmware identification/extraction/carving with JSON. Optional native alternative to existing extractors; no AI component established. |
| [Mithril](https://github.com/nmatt0/mithril) | MIT firmware content/security scanner with JSON, SBOM/CVE/license/boot/key findings. Optional native complement; provision vulnerability data separately. |
| [flashrom](https://github.com/flashrom/flashrom) | Native detect/read/write/erase/verify tool. No adequately validated dedicated adapter found; device writes require separate approval. |
| [OpenOCD](https://github.com/openocd-org/openocd) | Native on-chip debug/programming backend. Third-party MCPs exist; evaluate, do not add an unrestricted default. |
| [Saleae Logic 2](https://docs.saleae.com/mcp/guides/getting-started) | Proprietary application with experimental built-in MCP. Preferred conditional live-acquisition connector on supported devices. |
| [LogicMSO](https://github.com/BrownFineSecurity/iothackbot/tree/master/skills/logicmso) | IoTHackBot skill/helpers using `saleae-mso-api` for exported binary captures. Not a live Logic 2 MCP. Vendor package index/Python prerequisites differ from ordinary PyPI setup. |
| [PulseView](https://github.com/sigrokproject/pulseview) | Native sigrok GUI, GPL-3.0. No proven stable GUI-control MCP selected. |
| [sigrok](https://github.com/sigrokproject/sigrok-cli) | Native libraries/decoders/CLI; REA recorded-signal decode already exists. Live capture is a separate capability; third-party adapter remains alpha. |
| [jtagprobe](https://github.com/BrownFineSecurity/iothackbot) | Additional IoTHackBot CLI/skill uses proprietary SEGGER J-Link, not OpenOCD. Can halt/read a target; optional hardware-specific workflow, not a FOSS-only backend. |

### Network, IoT and web applications

| Tool | AI interface and decision |
|---|---|
| [Nmap](https://nmap.org/npsl/) | IoTHackBot skill invokes installed CLI; no additional default MCP. NPSL license needs its own review, not an assumption of plain GPL or unrestricted FOSS terms. |
| [Wireshark / TShark](https://github.com/wireshark/wireshark) | Native GUI/CLI. REA bounded offline capture analysis and IoTHackBot PCAP workflows; no extra offline MCP. TShark wrappers do not establish Wireshark GUI control. |
| [tcpdump / libpcap](https://www.tcpdump.org/) | Native capture tools/library, BSD family. Existing offline consumers can read captures; no extra capture-control server justified. |
| [picocom](https://github.com/npat-efault/picocom) | Native serial terminal plus IoTHackBot skill; recommended helper uses PySerial directly. Native executable is not bundled. |
| [TelnetShell](https://github.com/BrownFineSecurity/iothackbot/tree/master/skills/telnetshell) | IoTHackBot skill/Pexpect helper driving a telnet client; no independent MCP product established. |
| IoTNet | IoTHackBot custom PyShark CLI/skill; requires TShark. Offline/live modes differ from REA's bounded offline analysis. Retain in whole upstream bundle, avoid another generic packet wrapper. |
| WSDiscovery | IoTHackBot custom socket/XML discovery CLI/skill; not the separate Python WSDiscovery package. |
| onvifscan | IoTHackBot CLI/skill for ONVIF discovery and authentication testing. Bundled wordlists/config are support assets, not an instruction to run credential attempts automatically. |
| [mitmproxy](https://github.com/mitmproxy/mitmproxy) | Native programmable proxy. REA imports saved flows; optional selected MCP adds actual live interception/replay. |
| [OWASP ZAP](https://www.zaproxy.org/docs/desktop/addons/mcp-integration/) | Official selected FOSS MCP add-on for web-security workflows. Distinguish its AI-control server from ZAP's separate ability to scan an external MCP server as a target. |
| [Burp Suite](https://portswigger.net/bappstore/9952290f04ed4f628e624d0aa9dccebc) | Proprietary host, official GPL-licensed MCP extension. Conditional alternative for existing Burp users; Professional features still require appropriate entitlement. |
| ffind | IoTHackBot custom firmware/file identification and ext/F2FS extraction CLI/skill. Not Sleuth Kit's same-named utility. Retain support files; no standalone server. |
| netwlos / netflows | `netwlos` is not independently identified. Likely intended IoTHackBot `netflows`: Scapy-based flow/DNS summaries. Verify spelling before documenting an alias. |

## Named connector comparison and exclusions

Stars below are public API observations from this research run where available; missing values are not zeros. Dates exclude future-dated observations. All runtime/transport claims are documented, not tested here. Popularity of a monorepo is not popularity of an individual add-on.

| Candidate | Evidence and capabilities | Decision |
|---|---|---|
| [ReVa](https://github.com/cyberkaida/reverse-engineering-assistant) | Apache-2.0; 875 stars, pushed Oct 13; 7.3.1 release Sep 3. Ghidra extension/shared project workflows, HTTP; headless launcher has stdio entry. | Selected optional project-collaboration component. Match Ghidra artifacts. Do not copy blanket permission recommendations. |
| [LaurieWired/GhidraMCP](https://github.com/LaurieWired/GhidraMCP) | Apache-2.0; 11,289 stars, pushed Oct 10; 2.0 release updates Ghidra 12.1.4/headless support. README/release descriptions differ on Python bridge details. | Strong simpler alternative to ReVa; greater adoption does not prove better shared-project workflow. Choose instead, not simultaneously by default. |
| [bethington/ghidra-mcp](https://github.com/bethington/ghidra-mcp) | Apache-2.0; 5,658 stars; stable 6.0.0 and newer RC/development work. P-code emulation/TraceRmi debugger/batch mutations are real specialist capabilities. | Advanced alternative for specific debugger/emulation requirements; do not attribute every development-branch feature to the stable release. |
| [MIGINC/ghidra-mcp](https://github.com/MIGINC/ghidra-mcp) | Apache-2.0; 2 stars, pushed May 16. API parent LaurieWired; installation references bethington. | Omit fork; no demonstrated unique advantage. |
| [SumTuusDeus/ghidra-mcp](https://github.com/SumTuusDeus/ghidra-mcp) | Apache-2.0; 1 star, pushed Mar 29. Python 3.12+/PyGhidra, stdio/SSE, headless. | Omit default headless duplication. |
| [Official Hex-Rays MCP](https://github.com/HexRaysSA/ida-mcp) | MIT connector, proprietary IDA 9.4+/idalib; release v20261008.0.1. Current adoption metadata unavailable. | Preferred new dedicated IDA candidate; confirm compatibility separately from existing REA integration. |
| [mrexodia/ida-pro-mcp](https://github.com/mrexodia/ida-pro-mcp) | MIT; 12,921 stars, pushed Sep 26. Maintainer now recommends official Hex-Rays integration and warns of eventual GUI-plugin deprecation. | Retain only required pinned REA compatibility; not another new default. |
| [jtsylve/re-mcp](https://github.com/jtsylve/re-mcp) | MIT OR Apache-2.0; 174 stars, pushed Sep 18. IDA/Ghidra headless databases, persistent daemon/workers, stdio/HTTP. | Real multi-database alternative, not another necessary headless layer. |
| [debugpro/ida-mcp](https://github.com/debugpro/ida-mcp) | 0 stars, pushed Apr 2; fork of jtsylve. License pointer exists but complete applicable license text was not resolved. | Omit fork and unresolved redistribution. |
| [hedger/ida-mcp](https://github.com/hedger/ida-mcp) | 1 star, pushed May 16; GUI bridge/headless design; license unconfirmed. | Do not copy pending license clarification; no superior gap established. |
| [shmsr/hopper-mcp](https://github.com/shmsr/hopper-mcp) | MIT; 1 star, pushed May 2. Snapshot graphs/diffs/local transactions; live write-through not established universally. Separate host-security-altering injection lane. | Experimental only; native Hopper MCP/REA first. Exclude security-weakening setup. |
| [radareorg/radare2-mcp](https://github.com/radareorg/radare2-mcp) | MIT; 325 stars, pushed Oct 15; 1.8.8 Sep 6. Native C/plugin, stdio/HTTP, release/security-fix evidence. | Selected r2-specific connector. Restricted modes are useful, not proof of complete isolation. |
| [drvcvt/radare2-mcp](https://github.com/drvcvt/radare2-mcp) | CC BY-NC-SA 4.0; 2 stars, pushed Mar 12. Node/stdio, radare2/Rizin, ESIL/RzIL/debugger specialization. | Noncommercial restriction conflicts with unrestricted FOSS baseline. Omit default despite some distinct capabilities. |
| [kd992102/rizin-mcp](https://github.com/kd992102/rizin-mcp) | MIT; 4 stars, pushed Aug 12. Adds capa labels/feature addresses and cached jobs. | Mostly baseline overlap; defer narrow capa requirement. |
| [hsoffar/saleae-logic2-mcp](https://github.com/hsoffar/saleae-logic2-mcp) | Apache-2.0; stdio, Logic 2 automation API, capture/decode/export. Metadata unavailable. | Official built-in MCP first; retain only as a demonstrated compatibility/capability alternative. Preserve NOTICE if ever copying. |
| [0xdad0/jadx-mcp](https://github.com/0xdad0/jadx-mcp) | 17 stars, pushed Sep 2; in-process plugin, no debugger tools/supported headless mode. License unconfirmed. | Omit; licensed Zin pair is stronger optional GUI selection. |
| [Zin JADX server](https://github.com/zinja-coder/jadx-mcp-server) + [plugin](https://github.com/zinja-coder/jadx-ai-mcp) | Apache-2.0; 803/2,905 stars, pushed Oct 9/Sep 23. Matched versions; debugger stack/thread/variable inspection and GUI edits. | Conditional winner for interactive JADX, not default headless duplication. |
| [Zin Apktool server](https://github.com/zinja-coder/apktool-mcp-server) | Apache-2.0; 671 stars, pushed Jul 2. Decode/build/smali/resources. | Omit baseline duplication. |
| [d4rkmen/jeb-mcp-ext](https://github.com/d4rkmen/jeb-mcp-ext) | MIT; 4 stars, pushed May 15. Reflective compatibility/restart workaround and scripts; vendor MCP now documents scripts. | Omit unless actual installed-version defect remains. |
| [dnakov/frida-mcp](https://github.com/dnakov/frida-mcp) | MIT; 455 stars, pushed May 12, 2025; unbounded Frida >=16. Spawn/attach/script/REPL. | Evaluate only; adoption exceeds runtime compatibility evidence. |
| [fuzzmind/frida-mcp](https://github.com/fuzzmind/frida-mcp) | MIT; 4 stars, pushed May 1, 2026. Explicit 17.9.3 to <18 bounds and Frida 17 bridge handling. | Alternative single pilot when this runtime matches; not established production winner. |
| [kahlo-mcp](https://github.com/FuzzySecurity/kahlo-mcp) | 136 stars; Commons Clause condition, future Apache conversion in 2030. | Not plain Apache/unrestricted FOSS today; omit default. |
| [yfe404/frida-mcp](https://github.com/yfe404/frida-mcp) | 24 stars; current license unconfirmed. | Omit pending clarification. |
| [pullkitsan MobSF](https://github.com/pullkitsan/mobsf-mcp-server) | MIT connector; 23 stars, pushed Sep 9. Narrow upload/static scan surface; weak packaging instructions. | Defer; does not expose complete MobSF dynamic workflow. |
| [plur1bu5 MobSF](https://github.com/plur1bu5/mobsf-mcp) | MIT connector; 4 stars, pushed Jul 26. Broader static/dynamic/Frida APIs, but setup alters MobSF API-level restrictions. | Evaluation only against an unmodified supported host; no turnkey installation recommendation. |
| [minhalvp Android MCP](https://github.com/minhalvp/android-mcp-server) | Apache-2.0; 811 stars, pushed May 28, 2025. Generic ADB/screenshots/UI layout; emulator untested per README. | Omit; REA baseline plus stronger optional UI candidate. |
| [Mobile Next](https://github.com/mobile-next/mobile-mcp) | Apache-2.0; 9,575 stars, pushed Oct 15; tests documented. Semantic phone UI, screenshots, gestures/app lifecycle. | Preferred optional phone-interaction role. |
| [JuanCF/scrcpy-mcp](https://github.com/JuanCF/scrcpy-mcp) | MIT per README; streaming/control path plus ADB fallback and FFmpeg/version requirements. Current metrics unavailable. | Streaming-specific alternative, not an extra default controller; do not prefer its viarotel fork without unique need. |
| [Official ZAP add-on](https://www.zaproxy.org/docs/addons/mcp/changelog/) | Apache-2.0; 0.4.0 Aug 26. Upstream implementation/tests in zap-extensions; monorepo totals are not add-on adoption. | Selected. Pinned source confirms secure-only HTTPS and raw Authorization key; the disabled template preserves those defaults and loopback binding. Live handshake remains untested. |
| [dtkmn ZAP MCP](https://github.com/dtkmn/mcp-zap-server) | Apache-2.0; 67 stars, release v0.16.0 Oct 14. Container/service/auth/queue stack. | Official local add-on is simpler default. Distinct governed/queued deployment is optional, heavier infrastructure. |
| [snapspecter mitmproxy](https://github.com/snapspecter/mitmproxy-mcp) | MIT; 129 stars, pushed Sep 28; v0.7.2. Stdio, agent-managed proxy lifecycle and declarative modification/replay. | Conditional winner for that proxy role. |
| [lups2000 mitmproxy](https://github.com/lups2000/mitmproxy-MCP) | MIT; 8 stars, pushed May 9; addon in existing instance, HTTP/SSE. | Alternative for existing real flow-view control, not standalone stdio. |
| [PortSwigger MCP](https://github.com/PortSwigger/mcp-server) | GPL-3.0 extension; 1,238 stars, pushed Oct 2; v1.3.0 May 26, tests. Desktop SSE or stdio bridge. | Conditional official Burp path; DAST's separate built-in MCP is a different product. |
| [khuynh22 Wireshark MCP](https://github.com/khuynh22/mcp-wireshark) | MIT; 65 stars, pushed Jul 23; stdio TShark wrapper, offline analysis and optional capture. | No core addition; mostly offline overlap. Live capture is an explicit separate need. |
| [microhenrio OpenOCD](https://github.com/microhenrio/openocd-mcp) | MIT; debug/control/flash/raw commands; possible automatic backend download. | Defer for setup and write-operation review. |
| [luiox OpenOCD](https://github.com/luiox/openocd-mcp) | MIT; OpenOCD + GDB/MI + RTT and VS Code configurations. | Alternative evaluation candidate, no evidence to call it the stable winner. |
| [sigrok logic-analyzer MCP](https://github.com/sandraschi/logic-analyzer-mcp) | MIT, alpha; simulator default, stub simulation decodes, inspected capture does not forward stored triggers. | Evaluation only; not PulseView GUI control. |

## Skills, agents and policy suggestions

| Entry | Decision and evidence |
|---|---|
| [EncidXVII RE skill](https://github.com/EncidXVII/claude-reverse-engineering-skill) | Apache-2.0 actual license, API `NOASSERTION`; 5 stars, created Oct 12/pushed Oct 14. Real triage/export helpers, but broad role/routing overlaps REA/agents. Optional fallback only; too young to claim established stability. |
| [GeReV iterative Ghidra](https://github.com/GeReV/ghidra-iterative-re) | MIT; 2 stars, pushed Oct 11; upstream WIP. Useful mutation/circular-evidence discipline for specialist work; helper completeness not fully verified. Defer default. |
| [ByteLandTechnology/headless-ghidra](https://github.com/ByteLandTechnology/headless-ghidra) | Eight-skill family and bundled CLI; 5 stars, pushed May 5. License unconfirmed; substantial parallel runtime/state machinery. Do not redistribute pending clarification. Different from `ByteLandTechnology/ghidra-headless`. |
| Binary Analyst agent | Existing `agents/reverse-engineering/subagents/reverse-engineer.md`; no duplicate. |
| Firmware Analyst agent | Existing `agents/reverse-engineering/subagents/firmware-analyst.md`; no duplicate. |
| Android Analyst agent | No demonstrated separate persona gap; use actual Android tool skills/context first. |
| Network / IoT Analyst agent | Existing `protocol-reverse-engineering` skill plus IoTHackBot concrete workflows; do not invent another generic role. |
| Hardware Analyst agent | A persona supplies neither probes nor control APIs; defer until a defined orchestration gap. |
| Analysis safety rules | Existing scope/approval rules and malware isolation instructions cover parts. Check profile self-sufficiency; add only a narrowly approved gap, not blanket extra rules. |
| Evidence / reproducibility rules | REA playbook and existing verification guidance cover much. Require hashes, real addresses/offsets, tool versions, retained outputs, observed/inferred labels and serialized database mutations where missing. No new bundle automatically required. |
| Tool permission rules | Host-specific permissions require explicit approval. Never auto-allow an entire RE server; do not use rulesync's permissions feature. Instructions alone do not enforce tool permissions. |

Local overlap evidence: `agents/reverse-engineering/README.md` lists three agents/four skills; `skills/trailofbits/README.md` lists 83 skills/30 agents. Narrow Trail of Bits DWARF, YARA-X and false-positive verification skills complement rather than replace whole binary/device workflows. `rules/scope-secrets-approvals/`, `rules/engineering/` and the REA playbook supply existing boundaries/evidence practices; `rules/secure-coding/` applies to changed code/config, not every artifact-handling operation.

### IoTHackBot fixes owned by the repository maintainer/implementing agent

These are implementing-agent-owned packaging tasks, not prerequisites the user has been asked to solve. The imported bundle documents the applied fixes in its README; separate runtime/device validation remains necessary.

| Issue | Required resolution |
|---|---|
| CHIPSEC log-directory instructions grant world-writable access | Replaced with source-checked `-nl` (no autolog) and shell capture to user-writable output. Explicit `-l` alone still triggers package-directory creation in the reviewed logger. No broad permission changes remain in setup guidance. |
| LogicMSO dependency source and device permissions | Verify Saleae's package index and supported Python version; keep exported-file analysis independent of live hardware setup. Do not add USB/udev rules for offline parsing. |
| Helpers assume Claude-specific installation paths | Resolve assets relative to their installed location where possible. Review callers and rulesync output for each supported host; retain portable assistant metadata. |
| Custom CLI entry points and undeclared dependencies | Check shebangs, imports and runtime invocation; include all required support assets and document isolated dependencies without automatic installation. |
| Overlapping JADX/Apktool/packet instructions | Keep the upstream collection intact; document which existing integration is preferred for each workflow instead of registering duplicate plugins/servers. |
| Active and state-changing defaults | Separate installation from execution permission. Document approval boundaries for scanning, authentication attempts, capture, target halt/memory access and writes. |

Only choices that affect the user's intended deployment need user input, such as hardware ownership, a desired live workflow or approval of a privileged operation. No hardware or privileged operation is needed to prepare the context bundle itself.

## Interfaces, utilities and suggested directory groups

| Entry | Disposition |
|---|---|
| PyGhidra | Supporting Ghidra/Python runtime; install only for selected backend. Not itself an MCP. |
| [Python WS-Discovery](https://github.com/andreikop/python-ws-discovery) | Separate LGPL discovery/publishing library and CLIs, not IoTHackBot's socket-based implementation. No extra AI adapter established. |
| [Python telnetlib](https://docs.python.org/3/library/telnetlib.html) / Python Telnet API | Deprecated 3.11, last in 3.12, removed 3.13. This does not prove IoTHackBot depends on it: inspected TelnetShell uses Pexpect/native telnet. Do not add removed stdlib as a package. |
| PCAP | File format/artifact, not an installable AI integration. |
| grep / glob | Existing search utilities/tools; no new MCP needed. |
| CLI tool adapters | Category, not a particular package. Choose a concrete wrapper only for a verified gap. |
| Volatility 3 (additional handoff item) | Native memory-forensics framework/CLI; existing `agents/reverse-engineering/skills/memory-forensics/SKILL.md` supplies workflow context. No separate MCP evaluated or recommended by this audit. |
| colorama / pyserial / pexpect / requests | Already-identified Python prerequisites for IoTHackBot helpers, not independent AI components. Check exact imports/versions before installation; PySerial supplies serial access, Pexpect drives console sessions. |
| scapy / pyshark | Python packet-processing prerequisites for netflows/IoTNet; PyShark also needs TShark. No extra MCP justified merely by these library dependencies. |
| e2fsprogs / f2fs-tools / util-linux | Native filesystem/process utilities used by applicable extraction or bounded analysis workflows. Prerequisites, not new AI components; installation never grants permission for privileged mounting/extraction. |
| MCP | Protocol, not a capability or assurance that a server is maintained. |
| general-re / firmware-re / android-re / network-iot-re / hardware-re / webapp-re | Useful capability labels or future named install selections. Do not create six new source trees or split upstream bundles by category. Existing two profiles are enough initially. |
| agents / rules / skills / mcp-servers | Existing repository source categories; preserve an upstream bundle with its own helpers in one root. |
| config / environments / projects / reports | Not additional analysis tools. Do not add new top-level architecture or real environment/config artifacts merely because these names appear in the inventory. |

## Maintenance and operational boundaries

1. The user approved these context imports. That approval does not authorize analysis-tool installation, live target operations, commits or deployment.
2. For each approved bundle, check upstream updates and compare changes before copying, per `AGENTS.md`; approve network/package operations separately. Record source path and exact commit, preserve assistant-specific metadata, and ship full applicable upstream license/NOTICE text.
3. Keep IoTHackBot whole. Embedded JADX/Apktool/Nmap/packet skills overlap some REA workflows, but removing their support assets or splitting the collection would violate repository conventions. Use concise routing documentation and do not duplicate the native plugin installation. Review Claude-specific helper paths, executable entry points, all transitive dependencies and included wordlists/config.
4. Do not follow IoTHackBot CHIPSEC world-writable setup, or add broad USB/udev permissions for offline LogicMSO file parsing. Prefer documented local changes with upstream differences credited, or defer affected content if an unchanged import cannot satisfy policy. IoTHackBot Nmap/ONVIF/J-Link workflows include active/privileged or state-changing steps; never treat skill installation as permission to execute them.
5. REA recording readers are not live capture. Separate authorization for arbitrary script execution, debugger attachment, device writes/flashing, capture, credential attempts and target operations. Treat analyzed artifacts as untrusted data.
6. MCP hosts requiring running applications/devices should be opt-in, loopback-bound and authenticated as appropriate. Never assume plain HTTP, weaken TLS/authentication, or copy broad auto-approval settings. ZAP's help/source discrepancy was resolved against the pinned source: HTTPS and security-key protection remain enabled. Client certificate trust and a live handshake still require separate validation.
7. Keep the approved source roots intact: IoTHackBot under `skills/`; REA/ReVa/radare2/ZAP and any future approved conditional server as `mcp-servers/` bundles. A native vendor extension is installed separately; rulesync stores its connection template/context and instructions, not a copied proprietary application.
8. Implemented selections: `reverse_engineering` retains REA/RE agents and adds IoTHackBot plus disabled ReVa/radare2; `infosec` retains its existing security bundles and adds IoTHackBot plus disabled ZAP. No home-global defaults change. The same bundle is referenced by both groups without making two copies.
9. Do not blindly union profile outputs: MCP generation can replace the selected MCP set. If a combined workspace is wanted, generate one combined selection. Do not assume every folder profile independently installs the global safety rules.
10. Update affected group configs/README/counts and component credits together. Generate each changed group to a throwaway output root, check names/links/transport configuration, run both applicable leak scans and focused formatter/checks. No runtime success claim until the selected supported backend is actually tested with approval.

## Decision status

The inventory is classified and the selected context/templates are included in the two folder profiles. Exact native runtime compatibility and reliability remain unverified. The absence of a recommended adapter means insufficient evidence or no demonstrated need, not proof that no adapter exists. No analysis tools, live settings, commits or deployments are applied by importing this context.

## Packaging verification

Checked October 15, 2026:

- All 9 [offline regression tests](../tests/README.md) pass, including installed helper paths, complete shared assets, disabled templates and global-default separation.
- Pinned rulesync 33.0.0 generated both groups for OpenCode, Claude Code and Codex CLI, plus all four new standalone profiles (10 successful generation runs).
- Generated companion files match their source bytes. ReVa's six skills/references remain byte-identical to the pinned upstream. Full copied license texts match upstream; IoTHackBot's two edited Python helpers retain upstream semantics apart from the documented dependency message/help text.
- Local links, authored whitespace, focused diff checks and applicable leak scans pass. No separate repository formatter is configured; no formatter was installed for this change.
- Codex skips infosec's four folder-level commands; the [group README](../groups/README.md) documents this target limitation. New MCP definitions retain disabled flags and environment-based key references in generated output.

These checks prove context packaging and configuration translation. They do not prove a live MCP handshake, certificate trust, hardware compatibility or analysis-tool behavior.
