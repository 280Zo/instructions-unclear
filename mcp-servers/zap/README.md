# ZAP MCP

The [official ZAP MCP Integration add-on](https://www.zaproxy.org/docs/desktop/addons/mcp-integration/) exposes web-security contexts, crawling, scan status, alerts, history and reports. This is a control interface to your own ZAP, not the separate feature for scanning another MCP server.

## Tools you need

- A compatible ZAP installation and its official **MCP Integration 0.4.0** add-on, plus the add-on's required automation/commonlib/network/passive-scan/report components. Browser-backed AJAX crawling has additional runtime prerequisites.
- A local running ZAP with MCP enabled, a trusted HTTPS certificate for the selected endpoint and its security-key protection retained.
- `ZAP_MCP_SECURITY_KEY` provided through your local runtime environment. It must match ZAP's configured MCP key; never paste its value into this repository, chat, a shell-history command or a generated settings file. The template contains only an environment placeholder.

Install ZAP/add-ons through the [official distribution](https://www.zaproxy.org/download/) after separate approval. This repo does not download or start ZAP or scan a target.

## Install and activate

From the repo root, use the [infosec group](../../groups/README.md#infosec), or:

```bash
npx rulesync@33.0.0 generate --config mcp-servers/zap/profile.jsonc --output-roots ~/AI/zap
```

Never add `--global`. The connection is disabled. In ZAP, enable MCP on loopback, retain secure-only and security-key protection, and verify the HTTPS listener/certificate. In your client, use its documented certificate-trust configuration; do not disable TLS verification or switch off server protections to obtain a connection. Then explicitly enable `zap` in the generated project configuration.

The source-checked endpoint is `https://localhost:8282` with the **raw key** in `Authorization`, not `Bearer <key>`. The pinned handler accepts JSON-RPC POST and GET event-stream requests on its listener; a guessed `/sse` or `/mcp` suffix is unnecessary. Adjust the hostname/port only to match your separately configured listener and trusted certificate.

The upstream help's plain-HTTP example conflicts with the pinned secure-only default. This template follows the source: `McpParam` defaults port 8282, `secureOnly=true` and security-key protection enabled; `McpHttpMessageHandler` rejects insecure requests and compares the Authorization value directly. No live handshake has been run by generating this template.

Starting a spider, authentication flow or scan requires explicit target scope and approval. Do not expose the listener externally or grant blanket tool permissions. Enabling the server does not authorize active testing.

## Updating

Compare the add-on's release/source before changing the pin; verify listener, TLS, header and dependency behavior again. Generate both isolated ZAP and infosec selections into temporary output roots. Keep the key placeholder and disabled default.

## Origin

Template and README written for this repo by 280Zo. Primary source: [zaproxy/zap-extensions](https://github.com/zaproxy/zap-extensions), `addOns/mcp/`, tag `mcp-v0.4.0`, commit `03a03eb34db2c4ccec61c2a434d6fab298311a25`, inspected October 15, 2026. No upstream Java code or binaries copied. ZAP source is Apache-2.0, copyright 2026 The ZAP Development Team; [upstream license](https://github.com/zaproxy/zap-extensions/blob/mcp-v0.4.0/LICENSE). See the [assessment](../../reference/security-re-tooling.md) for selection rationale.
