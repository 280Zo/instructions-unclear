# Docker skills (core)

Docker's own skills for everyday container work:

| Skill | For |
|---|---|
| `docker-project-foundations` | Dockerizing a project: Dockerfile, `compose.yaml` and `.dockerignore` |
| `docker-build-strategies` | Writing, reviewing and slimming Dockerfiles: multi-stage builds, layer caching, non-root users |
| `docker-compose-patterns` | Compose stacks: services, health checks, dependency order, volumes, networks, dev overrides |
| `docker-destructive-guardrails` | Says exactly what will be lost and asks before `rm`, `prune`, `rmi` and other irreversible Docker commands |

The four descriptions add about 380 tokens to every request, so they're in `default` and `work`. Docker's Sandboxes and Docker Agent skills are in [`skills/docker-sandboxes-agent`](../docker-sandboxes-agent/), `work` only.

## Install

From the repo root, through the `default` or `work` [install group](../../groups/), or just these skills:

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/docker
```

The skills' `scripts/verify-*.sh` helpers run `docker` and `docker compose` to check your work; `verify-build.sh` builds and tags an image. rulesync installs neither Docker nor Compose. Most guidance also applies to Podman, but Docker wrote and tested it for Docker.

## For agents: install, remove and update

### Install

- The [`default`](../../groups/README.md#default) and [`work`](../../groups/README.md#work) groups install it globally. For this folder alone, use the command under [Install](#install) above.
- rulesync doesn't install Docker or Compose; the `scripts/verify-*.sh` helpers need them. Install them only with approval, following the `package-management` skill.
- To verify, start a new session and confirm the skills list includes all four skill names. Don't run `verify-build.sh` as a test; it builds and tags an image.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `docker-project-foundations`, `docker-build-strategies`, `docker-compose-patterns` and `docker-destructive-guardrails` in each tool's global skills folder; delete them only with approval.

- The seven [`skills/docker-sandboxes-agent`](../docker-sandboxes-agent/) skills point to `docker-destructive-guardrails`. If those are installed, remove both folders together or keep this one.
- If Docker's native plugin or `npx skills add docker/skills` also installed these names, find out which copy belongs to which installer before deleting.
- Docker, Compose, and images or containers the skills helped create stay.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The release tag and commit are under [Origin](#origin). Update this folder and `skills/docker-sandboxes-agent` from the same release, and record the same tag and commit in both READMEs. See the routing bullets below for native plugins and `docker-docs`.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed skill writes Dockerfiles or Compose files. `docker-destructive-guardrails` applies to destructive Docker commands however they're run, including through the [Podman MCP](../../mcp-servers/podman/).
- These four and the seven in `skills/docker-sandboxes-agent` are one upstream collection, split by Docker's own product grouping in `catalog.yaml` so `default` doesn't carry the product-specific descriptions. The other seven point to `docker-destructive-guardrails`, so this folder must be installed wherever that one is. Update both folders from the same release.
- Upstream also ships native plugins for Claude Code, Codex, Cursor, Copilot CLI and Gemini CLI and a `npx skills add docker/skills` installer. Use one installer per tool; don't install the native plugin on top of these copies.
- Upstream's unreleased `docker-docs` skill pairs with Docker's official docs MCP server (`https://ai-backend-service.docker.com/mcp`). It isn't copied because it isn't in a release.
- After a refresh, re-read the descriptions. If one now claims a job another item owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[docker/skills](https://github.com/docker/skills), `skills/` (these four skills, complete), tag v0.3.1, commit `8afc2c6ef4e0ec2ea8e4ba024d0b884ea930b926`, copied 2026-10-24. Unchanged. [Apache 2.0](../../THIRD_PARTY_LICENSES.md#dockerskills), © 2026 Docker, Inc. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
