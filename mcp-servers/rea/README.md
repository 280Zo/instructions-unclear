# REA

[REA (Reverse Engineer Anything)](https://github.com/morluto/rea) lets your agent take apart software you don't have the source for: Electron and JavaScript apps, .NET programs, websites, Android APKs and native binaries. You ask a question about a program ("how does this app export data?"), the agent runs REA's tools on it, and answers with evidence: the entry points, calls and files involved, with locations you can check.

From this repo, REA is a **profile**: it lives in one folder you choose. Start your coding tool in that folder and REA's tools and instructions are there. Start it anywhere else and REA isn't loaded at all, so it costs nothing in your everyday sessions.

| File | What it is |
|---|---|
| `mcp.jsonc` | The `rea` MCP server, run as `npx -y rea-agents@6.5.0 mcp` |
| `skills/reverse-engineer-anything/` | REA's investigation playbook: which tool to run for which kind of target, and how to report findings |
| `profile.jsonc` | Installs both into your chosen folder |

## Install

1. Have Node.js 22.19+, 24.11+ or 26+. The first start downloads `rea-agents`, so it's slower than later ones.
2. From the repo root, install into the folder you'll work in:

   ```bash
   mkdir -p ~/rea
   npx rulesync@33.0.0 generate --config mcp-servers/rea/profile.jsonc --output-roots ~/rea --targets claudecode,codexcli,opencode
   ```

   Swap `--targets` for the tools you use. Never add `--global`: that would put REA in every session.

That's enough for JavaScript, Electron, .NET and websites. Other targets need extra tools installed separately:

| Target | Needs |
|---|---|
| Native binaries | Ghidra 12.1.x (set `GHIDRA_INSTALL_DIR` before starting your tool), IDA or Hopper |
| Android, firmware, packet captures | The tools in [REA's list](https://github.com/morluto/rea#what-you-can-analyze) |
| JavaScript and Electron, on Linux | A procps-compatible `ps` on your `PATH` (most distributions have it) |

## Use

```bash
cd ~/rea
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
2. Change `rea-agents@6.5.0` in `mcp.jsonc` to the same version.
3. Run the install command again.

"Check for updates" in [`AGENTS.md`](../../AGENTS.md) does the comparison for you. To remove REA, delete the folder you installed it into; the only other trace is the cached package in `~/.npm/_npx`.

## Responsible use

Only analyze software you own or are authorized to examine, for lawful purposes such as research, interoperability and preservation. See REA's [DISCLAIMER.md](https://github.com/morluto/rea/blob/main/DISCLAIMER.md).

## Origin

[morluto/rea](https://github.com/morluto/rea), skill from `.agents/skills/reverse-engineer-anything/` at tag `rea-agents-6.5.0` (commit `3b79af28e80785afce9f5998d8f03289402a1847`), copied 2026-10-14. Unchanged. REA's three other skills are for developing REA itself and aren't included. [MIT](../../THIRD_PARTY_LICENSES.md#morlutorea), © 2026 morluto.
