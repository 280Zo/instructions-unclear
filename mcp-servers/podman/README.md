# Podman MCP (Podman and Docker)

[manusa/podman-mcp-server](https://github.com/manusa/podman-mcp-server) lets an assistant list, inspect, run, stop and remove containers, and list, pull, build, push and remove images, on **Podman or Docker**. It also lists networks and volumes. It talks to the Podman socket API when one is available and otherwise falls back to the `podman` or `docker` CLI.

It's a community server, not part of the Podman project. Neither Podman nor Docker publishes an official MCP server for local containers; Docker's official servers cover Docker Hub, its docs and its MCP Gateway. This one was chosen on 2026-10-24 over [ckreiling/mcp-server-docker](https://github.com/ckreiling/mcp-server-docker), which is more popular but Docker-only and hasn't had owner activity since 2025-06.

## Install

It's in the `default` and `work` [install groups](../../groups/), **switched off**. To add just this server, from the repo root:

```bash
npx rulesync@41.0.0 generate --global --features mcp --input-roots mcp-servers/podman
```

That replaces your tool's whole MCP list with this one server, so normally use a group or your `rulesync.local.jsonc` list instead.

### What it needs

- Node.js with `npx`. The first start downloads `podman-mcp-server@0.0.15` from npm.
- Podman or Docker. For the Podman API, the user socket must be running (`systemctl --user enable --now podman.socket` on Linux); otherwise it uses the CLI.

### Turn it on

In OpenCode, set `"enabled": true` on the `podman` entry in `opencode.jsonc` (or turn it on from `/mcps`), then restart. In Claude Code, remove `"disabled": true`. It has no credentials to configure.

## Use

- "List my running containers and show the logs for `web`"
- "Build `./Containerfile` as `myapp:dev`"
- "Which images are taking space?"

`container_remove`, `image_remove` and `image_push` change state. Your permission settings decide whether those calls are asked about; the server itself doesn't ask.

## For agents: install, remove and update

### Install

It's in the `default` and `work` groups, written switched off. See [Install](#install) for the single-folder command and [What it needs](#what-it-needs) for prerequisites rulesync doesn't install.

1. Keep it disabled unless the user asks to turn it on. Never enable it to make a test pass.
2. Before enabling, check that `podman` or `docker` is installed and which one the user wants. Don't start the Podman socket or change services without approval.
3. To verify, enable it in a new session and call `container_list` and `image_list` only. Don't run, remove or push anything as a smoke test.
4. Not in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed tool competes for local container control. Writing Dockerfiles and Compose files is the `docker` skills' job; destructive commands follow `docker-destructive-guardrails`.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `podman` MCP entry, because each run replaces the whole MCP list.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- If the user syncs a native V2 config without the `mcp` feature, remove the `podman` entry from `mcp.servers` by hand, keeping every other setting.
- Podman or Docker, the Podman socket service, the cached `podman-mcp-server` npm package, and every container and image stay. Never remove or stop them without the user's explicit approval.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The pin is `podman-mcp-server@0.0.15` in `mcp.jsonc`; change it together with the versions in this README.

## Updating

Compare the pin with `npm view podman-mcp-server version` and read the [release notes](https://github.com/manusa/podman-mcp-server/releases). Check for new tools that change state, then update `mcp.jsonc` and this README together.

## Origin

Connection template written for this repo by 280Zo, based on [manusa/podman-mcp-server](https://github.com/manusa/podman-mcp-server) v0.0.15 (npm `podman-mcp-server@0.0.15`, published 2026-02-27), checked 2026-10-24. No upstream files are copied here. Upstream is [Apache 2.0](https://github.com/manusa/podman-mcp-server/blob/main/LICENSE), by Marc Nuri (manusa).
