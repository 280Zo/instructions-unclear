# Docker Sandboxes and Docker Agent skills

Docker's skills for two newer Docker products:

| Skill | For |
|---|---|
| `docker-sandboxes-lifecycle` | Creating, reattaching, listing and removing `sbx` sandboxes that run coding agents in microVMs |
| `docker-sandboxes-network-credentials` | Sandbox network egress policy and credentials |
| `docker-sandboxes-env` (experimental) | Declarative `sbxenv.yaml` sandbox environments |
| `docker-sandboxes-kits` (experimental) | Authoring, packaging and signing sandbox kits |
| `docker-agent-config` | Writing `agent.yaml` for Docker Agent (`cagent`) |
| `docker-agent-run` | Running Docker Agent: safety modes, `--sandbox`, worktrees, troubleshooting |
| `docker-agent-deploy` | Serving, sharing and evaluating Docker Agents |

They only help if you use `sbx` or Docker Agent, and their descriptions add about 850 tokens to every request, so they're in the `work` group only.

## Install

From the repo root, through the `work` [install group](../../groups/), or with the core folder (these skills point to its `docker-destructive-guardrails`):

```bash
npx rulesync@41.0.0 generate --global --targets opencode,claudecode --features skills --input-roots skills/docker skills/docker-sandboxes-agent
```

The skills need the standalone `sbx` CLI or the `docker agent` CLI plugin (Docker Desktop 4.63+); rulesync installs neither.

## For agents: install, remove and update

### Install

- The [`work` group](../../groups/README.md#work) installs it globally, together with [`skills/docker`](../docker/). For these folders alone, use the command under [Install](#install) above, which installs both.
- rulesync doesn't install the `sbx` CLI or the `docker agent` plugin (Docker Desktop 4.63+). Install them only with approval, following the `package-management` skill.
- To verify, start a new session and confirm the skills list includes `docker-sandboxes-lifecycle`, `docker-agent-run` and `docker-destructive-guardrails`. Don't create a sandbox or run an agent as a test.

### Remove

Follow [Removing or replacing a component](../../AGENTS.md#removing-or-replacing-a-component). `delete: false` leaves `docker-sandboxes-lifecycle`, `docker-sandboxes-network-credentials`, `docker-sandboxes-env`, `docker-sandboxes-kits`, `docker-agent-config`, `docker-agent-run` and `docker-agent-deploy` in each tool's global skills folder; delete them only with approval.

- Removing this folder alone is fine; keep `skills/docker` if the user still wants the core skills. Don't delete `docker-destructive-guardrails` as part of this folder, since it belongs to `skills/docker`.
- If Docker's native plugin or `npx skills add docker/skills` also installed these names, find out which copy belongs to which installer before deleting.
- `sbx`, Docker Agent, sandboxes, kits, `sbxenv.yaml` and `agent.yaml` files stay.

### Update

Follow [Check for updates](../../AGENTS.md#check-for-updates). The release tag and commit are under [Origin](#origin). Update this folder and `skills/docker` from the same release, and record the same tag and commit in both READMEs.

## For agents: routing and updates

- Not in [`rules/routing`](../../rules/routing/rules/routing.md): no other installed skill covers `sbx` or Docker Agent.
- This folder and [`skills/docker`](../docker/) are one upstream collection, split by Docker's product grouping (user decision, 2026-10-24). Always install it with `skills/docker`, and update both from the same release. See that README for the native-plugin and `docker-docs` notes.
- After a refresh, re-read the descriptions. If one now claims a job another item owns, update `rules/routing` and this section in the same change and tell the user.

## Origin

[docker/skills](https://github.com/docker/skills), `skills/` (these seven skills, complete), tag v0.3.1, commit `8afc2c6ef4e0ec2ea8e4ba024d0b884ea930b926`, copied 2026-10-24. Unchanged. [Apache 2.0](../../THIRD_PARTY_LICENSES.md#dockerskills), © 2026 Docker, Inc. Updates: see "Check for updates" in [`AGENTS.md`](../../AGENTS.md).
