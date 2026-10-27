# REA

[REA (Reverse Engineer Anything)](https://github.com/morluto/rea) lets your agent take apart software you don't have the source for: Electron and JavaScript apps, .NET programs, websites, Android APKs and native binaries. You ask a question about a program ("how does this app export data?"), the agent runs REA's tools on it, and answers with evidence: the entry points, calls and files involved, with locations you can check.

From this repo, REA is a **profile**: it lives in one folder you choose. Start your coding tool in that folder and REA's tools and instructions are there. Start it anywhere else and REA isn't loaded at all, so it costs nothing in your everyday sessions.

| File                                | What it is                                                                                           |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `mcp.jsonc`                         | The `rea` MCP server, run as `npx -y rea-agents@6.7.0 mcp`                                           |
| `skills/reverse-engineer-anything/` | REA's investigation playbook: which tool to run for which kind of target, and how to report findings |
| `profile.jsonc`                     | Installs both into your chosen folder                                                                |

## Install

1. Have Node.js 22.19+, 24.11+ or 26+. The first start downloads `rea-agents`, so it's slower than later ones.

2. From the repo root, install into the folder you'll work in:

   ```bash
   mkdir -p ~/AI/reverse_engineering/rea
   npx rulesync@41.0.0 generate --config mcp-servers/rea/profile.jsonc --output-roots ~/AI/reverse_engineering/rea --targets claudecode,codexcli,opencode
   ```

   Swap `--targets` for the tools you use. Never add `--global`: that would put REA in every session.

Additional requirements depend on the selected workflow; the npm package is not a complete backend installation:

| Target                             | Needs                                                                             |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| Native binaries                    | Ghidra 12.1.x (set `GHIDRA_INSTALL_DIR` before starting your tool), IDA or Hopper |
| Android, firmware, packet captures | The tools in [REA's list](https://github.com/morluto/rea#what-you-can-analyze)    |
| JavaScript and Electron, on Linux  | A procps-compatible `ps` on your `PATH` (most distributions have it)              |
| Browser-backed website work | The selected release's browser prerequisites and approval for any browser download or page visit |

## For agents: install, remove and update

### Install

This is a folder profile, also in the [reverse-engineering group](../../groups/README.md#reverse_engineering); use the command in [Install](#install) and never `--global`. The `rea` connection is written switched on. Node.js and any backend in the table above are prerequisites rulesync doesn't install; `GHIDRA_INSTALL_DIR` is set by the user in the launch environment.

Start in this repo and ask:

> Follow `mcp-servers/rea/README.md` to install the backend I choose and test the folder-scoped REA connection with a harmless local fixture. Show the plan and ask before installation or configuration changes.

Follow the [shared backend installation procedure](../../agents/reverse-engineering/README.md#for-agents-installing-and-verifying-backends), including its approvals, verification and rollback requirements. Use the reviewed REA **6.7.0** baseline above; setup examples from upstream main or the copied skill may describe a newer release. Inspect the installed release's documented options before using them. Do not upgrade REA, Node or a backend as an incidental repair.

1. Select the workflow before installing anything. Check Node/npm and, on Linux where required, procps-compatible `ps`. Separate missing MCP registration, client permission, process startup and missing native backend failures. Static JavaScript or managed-code work does not justify installing Ghidra. Website/browser work has its own browser prerequisites; do not assume native analysis setup supplies them.
2. Read [upstream installation and readiness guidance](https://github.com/morluto/rea/blob/main/docs/installation.md), checking it against the recorded release. Check the [native provider guide](https://github.com/morluto/rea/blob/main/docs/native-investigation.md) or the target-specific guide linked from upstream's [requirements table](https://github.com/morluto/rea#what-you-can-analyze). Show the exact package/backend installation and registration changes for approval; a diagnostics command using `npx` can itself download software.
3. Reuse the profile's pinned MCP registration and complete skill. Do not run the upstream global `setup` merely to install a missing backend: it can register another MCP server and replace workflow instructions. If setup is genuinely required, review its supported dry run, clients, paths and skill replacements first and obtain approval for that scope. Do not use global registration for this folder profile.
4. Install only the selected backend and prerequisites using its official supported procedure. For Ghidra, use the reviewed **12.1.x** compatibility baseline and its required full JDK; do not guess the Java major version or substitute another Ghidra release. Verify installation and the release's documented headless launcher. For the test, set `GHIDRA_INSTALL_DIR` only to the approved Ghidra installation root in the assistant launch environment; `JAVA_HOME` or persistent shell/service changes need review too. For IDA/Hopper, have the user supply and activate the correct licensed edition; verify REA supports that edition/platform and do not bypass activation or install a trial automatically.
5. For Android, firmware or recorded-network work, choose only the bring-your-own tools in the release's corresponding guide (for example JADX plus its JDK, an approved firmware unpacker, or TShark). Check their OS/version requirements and use the shared workflow's isolated install and fixture tests. A native decompiler is not a substitute for those tools. REA's optional Rizin backend and the separate radare2 MCP are different integrations; do not install one to fix the other.
6. Generate context into the agreed folder from this repo using the command above or the combined reverse-engineering group. Inspect any pre-existing project config before overwriting it. Restart/reconnect only with approval, from that folder, after prerequisites and environment are ready. Startup can acquire the pinned npm package; approval to copy skills is not approval to download it.
7. Smoke test in stages: confirm `rea` connects and the intended skill/tools appear; then, with fixture approval, use static inspection on a tiny self-authored JavaScript tree. For a requested native backend, separately inspect a benign compiled fixture without executing it, and verify the known symbol/string through REA. Use the connected server's actual tool schema; do not assume a tool described on main exists in 6.7.0. Test outside the profile in a fresh session to confirm REA is absent unless another approved global integration supplies it.
8. Report registration, catalog discovery and each selected backend's fixture result separately. List skipped backends as not installed/not tested, not failures requiring automatic installation. Retain the commands, versions, sources, created files and rollback plan from the shared procedure. Do not proceed from the smoke test to a user target without its own scope approval.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component), including its note on folder groups. As [Updating](#updating) says, removing the profile means deleting the folder you installed it into, with approval and only if nothing else lives there. Otherwise regenerate that folder without this one, which replaces its MCP list and drops `rea`.
- `delete: false` leaves the `reverse-engineer-anything` skill folder behind in that folder's skills directory. Delete it only with approval, and only if no other installed folder provides it.
- The cached `rea-agents` package in `~/.npm/_npx`, Node.js, Ghidra, IDA, Hopper and other backends stay, along with saved evidence and snapshots. Never remove them without the user's explicit approval. If someone ran `npx rea-agents setup`, its global registration is upstream's; use upstream's documented removal rather than deleting files by guesswork.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The pin is `rea-agents@6.7.0` in `mcp.jsonc`; change it together with the copied skill, the tag and commit in [Origin](#origin), and the [license section](../../THIRD_PARTY_LICENSES.md#morlutorea) if upstream's license changed.

## Use

The [reverse-engineering group](../../groups/README.md#reverse_engineering) adds the RE agents and ReVa skills plus disabled ReVa/radare2 connections. IoTHackBot is now a separately installed native plugin, not generated by that group.

```bash
cd ~/AI/reverse_engineering/rea
opencode        # or claude, codex
```

Then ask about a target by its absolute path. Some starting points:

- "Look at `/Applications/Notion.app` and find how it exports data. Show the entry points, calls and dependencies involved, with source locations."
- "What network endpoints does `/opt/someapp` call, and with what payloads?"
- "Inspect `https://example.com` and explain how its search box gets results."
- "Open `/path/app.apk` and list the permissions it uses and where."

The agent picks the right REA tool from its playbook, runs it, and cites what it found. In OpenCode, `/mcps` should show `rea` connected and `/skills` should show `reverse-engineer-anything`. Your usual MCP servers stay available in that folder too, because OpenCode adds the folder's config to your global one. I tested that OpenCode's config includes `rea` inside the folder and not outside it.

Don't run `npx rea-agents setup`: it installs REA into your global config, which turns it on everywhere.

## Updating

REA releases often. Update the skill and the server version together:

1. Copy `.agents/skills/reverse-engineer-anything/` from the new release's tag (`rea-agents-X.Y.Z`) over `skills/reverse-engineer-anything/` here, and record the tag and commit under "Origin".
2. Change `rea-agents@6.7.0` in `mcp.jsonc` to the same version.
3. Run the install command again.

"Check for updates" in [`AGENTS.md`](../../AGENTS.md) does the comparison for you. To remove REA, delete the folder you installed it into; the only other trace is the cached package in `~/.npm/_npx`.

Release 6.7.0 includes result-contract changes introduced in 6.6/6.7. Saved Evidence and snapshots from older releases may need regeneration; Android version codes are now strings. Review the [release notes](https://github.com/morluto/rea/releases/tag/rea-agents-6.7.0) before changing a working environment. Nothing here migrates evidence or upgrades a live server.

## Responsible use

Only analyze software you own or are authorized to examine, for lawful purposes such as research, interoperability and preservation. See REA's [DISCLAIMER.md](https://github.com/morluto/rea/blob/main/DISCLAIMER.md).

## Origin

[morluto/rea](https://github.com/morluto/rea), skill from `.agents/skills/reverse-engineer-anything/` at tag `rea-agents-6.7.0` (commit `27dc42d10249f0410904a75c0997842eb03b931c`), copied 2026-10-20. Unchanged. Other upstream skills concern development of REA itself and are not included. [MIT](../../THIRD_PARTY_LICENSES.md#morlutorea), © 2026 morluto.
