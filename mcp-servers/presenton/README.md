# Presenton

[Presenton](https://github.com/presenton/presenton) makes presentations you can edit in PowerPoint or import into Google Slides. It runs in Docker on your machine, and your coding tool talks to it through its MCP server.

| File | What it is |
|---|---|
| `mcp.jsonc` | Becomes a `presenton` MCP server at `http://localhost:5001/mcp`, installed switched off |
| `compose.yaml` | Runs Presenton in Docker, pinned to one release |
| `.env.example` | The settings Presenton needs. Copy it to `.env`, which git ignores |

You need Docker with the Compose plugin. The MCP server only exists in the Docker version; Presenton's desktop app doesn't have one.

## Setup

From this folder:

1. Copy the settings file and fill it in: an admin username and password, your text provider (`LLM`) with its key and model, and optionally an image provider.

   ```bash
   cp .env.example .env
   ```

   Provider names and variables are in [Presenton's environment variable reference](https://docs.presenton.ai/hosting/environment-variables).

2. Start it. The first start downloads the image.

   ```bash
   docker compose up -d
   ```

3. Open `http://localhost:5001`, sign in, and generate a small test presentation.
4. In **Admin → API keys**, create a key and export it where your coding tool starts:

   ```bash
   export PRESENTON_API_KEY=paste-your-presenton-key-here
   ```

   The key is never written into any file. The generated config only refers to `PRESENTON_API_KEY`.

5. Add `mcp-servers/presenton` to `inputRoots` in your `rulesync.local.jsonc` (see the [root README](../../README.md#install)) and run your install command with `--features mcp` included. rulesync replaces your tool's whole MCP server list, so keep your other server folders in that list too.

What `compose.yaml` sets up:

- **Port:** `5001` on this machine only (`127.0.0.1`), so nothing else on your network can reach it. The web app, its API and the MCP server all use it.
- **Data:** presentations, settings, the admin account and the database live in a Docker volume named `presenton_presenton_data`, which survives stopping, removing and upgrading the container.
- **Restarts:** none. It runs only when you start it.
- **Privacy:** `.env.example` turns off Presenton's anonymous usage tracking and image generation. Turn image generation back on in `.env` if you want pictures in your slides.

## Use

The MCP server is installed switched off, so your coding tool doesn't report a failed connection while Presenton is stopped. Each time you want a deck:

1. `docker start presenton`
2. Turn the server on in your tool. In OpenCode, set `"enabled": true` on `presenton` in `opencode.jsonc`.
3. Ask for it: "make a 10-slide PowerPoint on our Q3 results from `notes.md`", or `/report … as PowerPoint` to get an evidence-backed deck from the `report` skill.
4. The deck appears in Presenton's dashboard at `http://localhost:5001`, where you can edit it and export PowerPoint or PDF. For Google Slides, import the `.pptx` (File → Import slides).
5. When you're done, turn the server off again and run `docker stop presenton`.

rulesync writes the switch in each tool's own form: `"disabled": true` for OpenCode V2 and `enabled = false` for Codex. For Claude Code it passes `"disabled": true` through as written. I haven't confirmed Claude Code honors that key, so it may show Presenton as a failed server while the container is stopped. Tools that have no per-server on/off switch don't get this server at all; rulesync skips it for them with a warning.

## Upgrading

`compose.yaml` pins `v0.9.11-beta` by its digest, so the image never changes unless you change it. To upgrade, pick a release from [Presenton's releases](https://github.com/presenton/presenton/releases), replace both the tag and the `sha256:` digest in `compose.yaml` (the image's page on GitHub's package registry lists the digest), then from this folder:

```bash
docker compose up -d
```

Your data stays in the volume. The "Check for updates" steps in [`AGENTS.md`](../../AGENTS.md) look up the newest release and its digest for you.

## For agents: install, remove and update

### Install

- It's in the `default` and `work` [install groups](../../groups/README.md), written switched off. Follow [Setup](#setup) above. In `default`, the OpenCode `build`, `plan`, `general` and [`design`](../../agents/design/) agents may use its tools.
- It needs Docker with the Compose plugin. The user fills in `.env` (admin login, text provider and key) and sets `PRESENTON_API_KEY` where their tool starts. Never ask for, read or print those values. The first `docker compose up -d` downloads the pinned image, so get approval first.
- Leave the connection off unless the user asks for it. They turn it on as [Use](#use) describes, after `docker start presenton`.
- To verify, once it's on, check that `presenton` connects and its tools are listed. A test deck is the user's step in Setup; don't generate decks as a smoke test without approval, because generation calls the user's paid provider.

### Remove

- Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). Regenerating without this folder removes the `presenton` MCP entry, because each run replaces the whole MCP list.
- This folder ships no skills, agents or commands, so `delete: false` leaves nothing of this repo's behind.
- If the user syncs a native V2 config without the `mcp` feature, remove the `presenton` entry from `mcp.servers` by hand, keeping every other setting.
- The `presenton` container, its image and the `presenton_presenton_data` volume (all the user's decks, settings and admin account) stay. Never stop, remove or prune them without the user's explicit approval. The user's `.env` stays too.
- The Presenton API key and provider keys are the user's to revoke, in Presenton's **Admin → API keys** and at each provider.

### Update

- Follow [Check for updates](../../AGENTS.md#check-for-updates) and [Upgrading](#upgrading). The pin is the image tag and `sha256:` digest in `compose.yaml`; change both together, along with the version in this README.
- Then follow the update bullets in [For agents: routing and updates](#for-agents-routing-and-updates).

## For agents: routing and updates

- Role in [`rules/routing`](../../rules/routing/rules/routing.md): "An editable `.pptx` uses the Presenton MCP when it is enabled, otherwise `documents`." Presenton is first choice for editable decks, but use it only when the user has started it and turned the server on; never enable it yourself.
- It does not own browser decks (`frontend-slides`), slides inside a page (`visual-explainer`) or other Office and PDF files (`documents`).
- Why: on 2026-10-21 the user replaced the per-skill routing rules with one routing rule because several items claimed the same jobs. Slides were claimed by four: Presenton, `documents`, `frontend-slides` and `visual-explainer`.
- This folder has no skill or rule, so routing for it lives only in `rules/routing`. Don't add a rule here.
- When upgrading the pinned image, check the release notes for new output types or MCP tools. If Presenton now covers a job another item owns, update `rules/routing` and this section in the same change and tell the user.

## Credits

Presenton is by the Presenton team, licensed [Apache 2.0](https://github.com/presenton/presenton/blob/main/LICENSE) (the license file names no copyright holder). This folder contains no Presenton code: only the connection entry, a compose file that runs their published image, and an example settings file using their documented variables.
