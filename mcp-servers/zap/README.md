# ZAP MCP

The [official ZAP MCP Integration add-on](https://www.zaproxy.org/docs/desktop/addons/mcp-integration/) exposes web-security contexts, crawling, scan status, alerts, history and reports. This is a control interface to your own ZAP, not the separate feature for scanning another MCP server.

## Tools you need

- A compatible ZAP installation and its official **MCP Integration 0.4.0** add-on, plus the add-on's required automation/commonlib/network/passive-scan/report components. Browser-backed AJAX crawling has additional runtime prerequisites.
- A local running ZAP with MCP enabled, a trusted HTTPS certificate for the selected endpoint and its security-key protection retained.
- `ZAP_MCP_SECURITY_KEY` provided through your local runtime environment. It must match ZAP's configured MCP key; never paste its value into this repository, chat, a shell-history command or a generated settings file. The template contains only an environment placeholder.

Install ZAP/add-ons through the [official distribution](https://www.zaproxy.org/download/) after separate approval. This repo does not download or start ZAP or scan a target.

## Install and activate

From the repo root, use the [infosec group](../../groups/README.md#infosec) (folder-scoped), the [work group](../../groups/README.md#work) (home folder; the connection is still written disabled), or this folder alone:

```bash
npx rulesync@41.0.0 generate --config mcp-servers/zap/profile.jsonc --output-roots ~/AI/zap
```

Never add `--global` to this single-folder command; through `work` or `default` it reaches your home-folder MCP list instead, still disabled. In `default`, only the OpenCode [`security` agent](../../agents/security/) may use its tools. The connection is disabled either way. In ZAP, enable MCP on loopback, retain secure-only and security-key protection, and verify the HTTPS listener/certificate. In your client, use its documented certificate-trust configuration; do not disable TLS verification or switch off server protections to obtain a connection. Then explicitly enable `zap` in the generated project configuration.

The source-checked endpoint is `https://localhost:8282` with the **raw key** in `Authorization`, not `Bearer <key>`. The pinned handler accepts JSON-RPC POST and GET event-stream requests on its listener; a guessed `/sse` or `/mcp` suffix is unnecessary. Adjust the hostname/port only to match your separately configured listener and trusted certificate.

The upstream help's plain-HTTP example conflicts with the pinned secure-only default. This template follows the source: `McpParam` defaults port 8282, `secureOnly=true` and security-key protection enabled; `McpHttpMessageHandler` rejects insecure requests and compares the Authorization value directly. No live handshake has been run by generating this template.

Starting a spider, authentication flow or scan requires explicit target scope and approval. Do not expose the listener externally or grant blanket tool permissions. Enabling the server does not authorize active testing.

## Updating

Compare the add-on's release/source before changing the pin; verify listener, TLS, header and dependency behavior again. Generate both isolated ZAP and infosec selections into temporary output roots. Keep the key placeholder and disabled default.

## For agents: install, remove and update

### Install

- It's in the `infosec` folder group and the `work` home-folder group, or installs alone as a folder profile with the command in [Install and activate](#install-and-activate). It's written switched off either way.
- ZAP, the MCP Integration 0.4.0 add-on and its dependencies, and a trusted HTTPS certificate are prerequisites rulesync doesn't install; see [Tools you need](#tools-you-need). The user sets `ZAP_MCP_SECURITY_KEY` in their runtime environment. Never ask for, read or print its value.
- Leave the connection off unless the user asks for it, and turn it on only after their ZAP listener is set up as described above.
- To verify, once it's on, check that `zap` connects and its tools are listed. Don't start a spider, scan or authentication flow as a test.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `zap` entry from the MCP list it was written to (the chosen folder, or the home folder for `work`), because each run replaces that list. For a folder install, deleting the generated files in the folder also works, with approval.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- If the user installed it through `work` and syncs a native V2 config without the `mcp` feature, remove the `zap` entry from `mcp.servers` by hand, keeping every other setting.
- ZAP, its add-ons, certificates and sessions stay. Never remove them without the user's explicit approval. The MCP security key is the user's to rotate or remove in ZAP.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Updating](#updating). The pin is add-on 0.4.0, recorded in the `mcp.jsonc` comment and [Origin](#origin) (tag `mcp-v0.4.0`); change both together and recheck the endpoint and header in `mcp.jsonc`.

## Origin

Template and README written for this repo by 280Zo. Primary source: [zaproxy/zap-extensions](https://github.com/zaproxy/zap-extensions), `addOns/mcp/`, tag `mcp-v0.4.0`, commit `03a03eb34db2c4ccec61c2a434d6fab298311a25`, inspected October 15, 2026. No upstream Java code or binaries copied. ZAP source is Apache-2.0, copyright 2026 The ZAP Development Team; [upstream license](https://github.com/zaproxy/zap-extensions/blob/mcp-v0.4.0/LICENSE).
