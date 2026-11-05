# fcos-app-installer: an OpenCode agent for Fedora CoreOS services

`fcos-app-installer` is an [OpenCode](https://opencode.ai) agent that builds Fedora
CoreOS virtual machines and adds containerized services to them: rootless
Podman Quadlets, backups by database engine, a firewall per VM, and one login
front end (Traefik + Authentik) in front of every service. It follows the
procedure in [`docs/guide/README.md`](docs/guide/README.md), asks its questions
in plain language ([`docs/guide/questions.md`](docs/guide/questions.md)), and
stops for every step on systems it doesn't touch: your hypervisor's shell, your
router, your file server, your DNS provider, and anything involving a secret.

## What it needs

- OpenCode 2.1.3 or newer on your desktop. Start OpenCode in the toolkit's
  folder, the one that holds `tools/`, `rules/` and `.opencode/`: the agent's
  allow rules, guard rules and rule files are all relative to it, and
  `python3 tools/check_requirements.py` fails when you start anywhere else.
  OpenCode loads the `rules/*.md` glob from `opencode.json`, and any
  `AGENTS.md`, from that folder and every folder above it up to the git root
  (searched upward, see `docs/guide/research-notes.md`), so keep the toolkit in
  a folder of its own, outside any other checkout: otherwise that checkout's own
  `rules/*.md` and `AGENTS.md` files load into every session.
  Earlier 2.0 releases ignore the config's `instructions` list, so the rules in
  `rules/` wouldn't load (fixed in 2.0.30), and the agents' skill and subagent
  filters were tested on 2.1.3.
- Python 3 with PyYAML. (git is optional: when it is installed, the tools ask it
  for the checkout around the toolkit; without it they look for a `.git` above
  the toolkit instead. Nothing else needs it.)
- Podman or Docker: the build checks run Butane and Podman's Quadlet generator
  in containers, from the images pinned in `tools/images.env`. You pull them
  once yourself; the tools say the exact command.
- `python3 tools/check_requirements.py` checks all of these and changes nothing.
- A virtualization platform, a router, a file server with NFS, and a DNS
  provider for Let's Encrypt DNS-01 (DuckDNS only today: the login front end's
  Traefik settings name it; another provider needs that changed). Each has an adapter
  skill in `.opencode/skills/adapter-<product>/` with the steps you do yourself; a product without one gets
  general steps, and the agent can draft an adapter as you go.

## Install

1. Clone this repository and start OpenCode in the toolkit's folder inside it
   (the one holding `tools/`).
2. The agent and its command live in `.opencode/` (`agents/fcos-app-installer.md`,
   `commands/add-service.md`); OpenCode picks them up from the folder it is
   started in.
3. Run the checks in [`docs/guide/10-trial-run.md`](docs/guide/10-trial-run.md)
   once: the tests, then that OpenCode loads the rules, skills and helper agent.
4. Start with `/add-service <service>`; the agent asks which server and VM. On the first run it asks where
   to keep the workspace (below) and creates it with `tools/workspace.py`.

## The workspace: your private files

Everything specific to your setup lives in a folder **outside** the toolkit's
folder and outside any git checkout that holds it, by default
`~/fcos-workspace`, remembered in `~/.config/fcos-agent/workspace`.
`tools/workspace.py` refuses a folder inside either. It asks git for the
checkout's top level; if git can't answer (not installed, or it refuses a
checkout another user owns), it looks for a `.git` above the toolkit instead.
A toolkit that is in no checkout is guarded at its own folder only.

```
<workspace>/
  site.yaml        your servers, network, file server, domain, providers
  secrets/         API token files, mode 600, read only by scripts
  vms/<vm>/        each VM's spec, Butane fragments and Ignition file
  services/<svc>/  each service's spec, research notes, generated files
  adapters-draft/  adapters drafted during runs
```

Start from [`site.example.yaml`](site.example.yaml). Every value there is a
placeholder.

## Giving the agent access to your hypervisor

The agent never runs commands on your servers. For Proxmox VE you run one
script as root on each server, after checking its checksum:
`.opencode/skills/adapter-proxmox/scripts/setup-agent-access.sh --storage <id> --bridge <name> --iso-storage <id>`
(run it with `--check` first). It creates a pool, a limited role, a user and a
token. The token can only see and manage VMs in its pool, use one disk
storage, one bridge, and upload config discs. `tools/pve.py`, the only way
the agent uses it, has no delete or disk-swap command; those stay steps you
run yourself. The
script prints the secret once; the agent's next step stores it in
`<workspace>/secrets/` from a hidden prompt. The agent uses it only through
`tools/pve.py`. When the install is done, `teardown-agent-access.sh
--move-to backrooms --create-pool` moves the VMs into pool `backrooms`, then
removes the access and the agent's pool; the VMs keep running.

On a VM the agent never uses your SSH key. It makes its own setup key
(`tools/vmssh.py`), you add it beside yours, and it is revoked when the
services work; only your key remains.

The agent's permissions are guard rails, not a wall: it runs as your user, so
a command written to get around them (a script it writes and then runs) could
reach anything you can, including your SSH key, your ssh-agent and
`secrets/`. They stop the ordinary ways in, and the agent is told never to
try the others. For a hard boundary, run the agent as a separate user or in a
container that can't read those.

Three things that keep those guard rails working:

- **Pick the `fcos-app-installer` agent** in this folder. OpenCode's own
  `build` agent sees the same tools and skills but none of this agent's
  rules, so it would run or edit things this agent may not.
- **Answer an approval with "Allow once".** "Allow always" saves the command's
  pattern for the whole project (OpenCode's Permissions docs), so later
  commands that merely start the same way stop asking. A configured deny
  still wins, but the asks you rely on disappear. "Reject" also cancels every
  other request waiting at that moment.
- **The workspace rule is broad on purpose.** The agent may work in any folder
  whose path contains "fcos-" without asking (owner decision, 2026-10-31), so
  keep that word for install folders such as `~/fcos-installs/<place>/`, and
  don't use it for unrelated folders. `secrets/` inside it stays off limits.

## The login front end and getting in when it's down

One login front end (Traefik and Authentik) sits in front of every app: you
log in once, and Authentik's dashboard lists your apps. Each app's port only
accepts connections from the login front end (apps bound to loopback open no
port at all). If the login front end is down,
the apps keep running, and you reach any of them through an SSH tunnel:

```fish
# desktop (fish)
ssh -N -L 8080:<vm-ip>:<port> <admin>@<vm-ip>
```

1. You SSH from your desktop into the **app's own VM**. SSH from the admin
   network is allowed on every VM and doesn't involve Authentik.
2. SSH then connects to the app's port from inside that VM. Traffic from a
   machine to its own address counts as local traffic, which the firewall
   accepts (`iif "lo" accept`). So the tunnel reaches the app even though the
   port refuses every other machine.
3. You open `http://localhost:8080` on your desktop.

The tunnel skips the login page and HTTPS; use it to fix things and close it
when done. Details, and the fallback when SSH is down too:
[`docs/guide/08-break-glass.md`](docs/guide/08-break-glass.md).

## Updating

The services on your VMs update themselves: every container has
`AutoUpdate=registry`, and each VM's update timer pulls fixes within the
image's tag. What doesn't update itself is the toolkit's own desktop-side
images, pinned by tag and digest in `tools/images.env`: Butane (which writes
every VM's boot config) and Podman (which checks the firewall and the
container files). Nothing pulls them for you.

### For a person

1. Check, before you start a task: `python3 tools/check_updates.py`. It reads
   quay.io's public tag list and changes nothing. "up to date" means you're
   done.
2. For a newer release or a rebuilt tag, read the image's official release
   notes first, and write what changed and its link into
   `docs/guide/research-notes.md`.
3. Change the pin in `tools/images.env` (tag and digest, as the check shows
   them on quay.io), test-first: a test for any change in behavior, then
   `python3 -m unittest discover tests`, both fixture validations and
   `python3 tools/publish_check.py`. Pull the new image yourself; the tools
   say the exact command.
4. Review it the way this toolkit was built: a fresh reviewer for each
   commit, then a whole-branch review.
5. Run the trial in `docs/guide/10-trial-run.md` on a VM that doesn't matter.
   Only then go back to the task.

### For the agent

At the start of every run, right after the workspace question, run
`python3 tools/check_updates.py`. If it reports an update, show its table and
offer to run the steps above first; never change a pin without the owner's
yes, and the owner approves each commit and pulls the image. If the check
can't run (no network), say so and carry on with the current pins.

## Changing a host script

You run the adapters' host scripts as root, after checking the checksum a step
shows. A step takes that checksum from the script itself, so the tools also
compare every script with `host-scripts.sha256`, a list the agent's rules keep
it from editing: the list sits outside the skills, edits to it are denied, and
so is any shell command that names it, its extension or the word `host-script`
(quoted, globbed and variable spellings of the name included). This is a guard
rail like the rest of the agent's permissions, not a wall: the agent runs as
your user, so a command written to get around the rules could still rewrite the
file. For a hard boundary run the agent as a separate user. A script whose hash
differs from the list, or that the list does not hold, stops its step with a
message, and only scripts an adapter declares in its `scripts:` list are
pinned. The list takes one `sha256sum` line per script, no blank lines or
comments.

After you change a script on purpose, read the change first (for example with
`git diff` in the checkout you keep the toolkit in), then rewrite the list
yourself from the skills folder (`.opencode/skills`) and check it:

```fish
# desktop (fish)
cd .opencode/skills
sha256sum adapter-*/scripts/* > ../../host-scripts.sha256
sha256sum -c ../../host-scripts.sha256
```

## Publishing

This repository is meant to be shared. Real values never go into it: before
every commit, run

```fish
# desktop (fish)
python3 tools/publish_check.py
python3 -m unittest discover tests
```

`publish_check.py` fails on any value from your workspace, any private
address, real domain or email, SSH key, password hash or secret-looking value.
It scans the toolkit's own folder only, or the one folder you pass as an
argument (pass a checkout's top level to scan all of it). Its last line says how
it found the files: `git list` (git's list for the folder, ignored files
excluded) or `walked` (every file in a plain copy, or when git can't answer;
git's own folder, Python caches and links are skipped, and git-ignored files are
read). A file it can't read is reported as a hit, and a scan that finds no file
at all is an error, not a pass.

## Layout

| Folder | Holds |
|---|---|
| `.opencode/` | the agents (`fcos-app-installer`, the main one for Fedora CoreOS; `adapter-drafter`, its helper that drafts adapters), the `/add-service` command, and `opencode.json`, which loads `rules/` |
| `.opencode/skills/` | skills: one adapter per provider (its owner steps, notes and host scripts), the generic fallback, and `researching-apps-for-self-hosting` |
| `host-scripts.sha256` | the pinned checksum of every host script; the agent's rules keep it from editing this file |
| `rules/` | rules that don't depend on the OS: how owner steps are given, how secrets and private values are handled |
| `docs/guide/` | the procedure, provider-neutral |
| `schemas/` | the service spec's field reference |
| `specs/login-frontend/` | Traefik and Authentik as service specs |
| `templates/` | Butane and Quadlet building blocks |
| `tools/` | the desktop-side tools |
| `tests/` | tests, including the publish and wording checks |
