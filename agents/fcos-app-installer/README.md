# fcos-app-installer: an OpenCode agent for Fedora CoreOS services

`fcos-app-installer` is an [OpenCode](https://opencode.ai) agent that builds Fedora
CoreOS virtual machines and adds containerized services to them: rootless
Podman Quadlets, backups by database engine, a firewall per VM, and one login
front end in front of every service (an ingress and an auth gateway you
choose; Traefik with Authentik is the pairing tested so far). It follows the
procedure in `docs/guide/README.md`, asks its questions in plain language
(`docs/guide/questions.md`), and stops for every step on systems it doesn't
touch: your hypervisor's shell, your router, your file server, your DNS
provider, and anything involving a secret.

This README is also installed into the folder you run the agent in, where
`docs/`, `tools/` and the other folders sit beside it. In the repository those
folders are under `toolkit/` (see [Layout](#layout)), so the paths below are
plain text and not links.

## What is fixed and what you choose

A few things are the same for everyone: Fedora CoreOS, Butane and Ignition, systemd, and rootless
Podman run from Quadlets. Two more are built into the generator and the guide, not offered as modules:

- Shared data and backups go over NFS. Every VM mounts a backups share, and an app's large files can
  sit on other NFS shares.
- Databases are SQLite, Postgres or MariaDB, each with its own backup template, or a `custom` engine
  where the spec gives its own dump command. The custom engine is the way to use any other database.

Everything else is a product you choose, and nothing is a default. The hypervisor, the router and
firewall, the file server and the DNS provider each have an adapter skill (`adapter-<product>`). The
login front end's ingress and auth gateway are modules (`ingress-<product>`, `authgw-<product>`). If
the product you use has no adapter or module, the agent builds one with you.

## What it needs

- OpenCode 2.1.3 or newer on your desktop. Start OpenCode in the toolkit's
  folder, the one that holds `tools/`, `AGENTS.md` and `.opencode/`. The agent's
  allow rules, guard rules and rules file are all relative to it, and
  `python3 tools/check_requirements.py` fails when you start anywhere else.
  OpenCode loads the `AGENTS.md` in that folder and in each folder above it
  (searched upward), up to the git root, or up to your home folder when the
  toolkit is under it. Project skills are searched upward too, but only as far
  as the project root (see "OpenCode versions and where it looks" below). Keep the toolkit in
  a folder of its own, outside any other checkout and outside folders that hold
  their own `AGENTS.md` or skills, or those files load into every session.
  The agents' skill and subagent filters were tested on OpenCode 2.1.3.
- Python 3 with PyYAML. (git is optional for the tools: when it is installed,
  they ask it for the checkout around the toolkit; without it they look for a
  `.git` above the toolkit instead. The test suite does need git: some tests
  build a repository or ask git which files a folder publishes.)
- Podman or Docker: the build checks run Butane and Podman's Quadlet generator
  in containers, from the images pinned in `tools/images.env`. You pull them
  once yourself; the tools say the exact command.
- `python3 tools/check_requirements.py` checks all of these and changes nothing.
- A virtualization platform, a router, a file server with NFS, and a DNS
  provider for Let's Encrypt DNS-01 (the adapter's `acme` block gives the
  certificate client's provider code, so any provider the client supports
  works once it has an adapter). Each product has an adapter skill in `.opencode/skills/adapter-<product>/` with
  the steps you do yourself. A product without one gets general steps, and the
  agent can draft an adapter as you go.

### OpenCode versions and where it looks

The agents' skill and subagent filters were tested on OpenCode 2.1.3, so the toolkit needs 2.1.3
or newer; `tools/check_requirements.py` checks it. The toolkit's rules are in the folder's
`AGENTS.md`, so it doesn't depend on the config's instructions list, which OpenCode parsed but
never loaded from 2.0.0 to 2.0.29 (issue 51341); the loader (`configuredSource` in
`packages/core/src/config/plugin/instruction.ts`) arrived in 2.0.30.

A relative instructions pattern, which this toolkit doesn't use, is resolved with
`globUp(pattern, start, root)`: it is globbed in the launch folder and every folder above it up to
the project root (the git root), so it also matches in any enclosing checkout. OpenCode collects
`AGENTS.md` the same way, from the launch folder up to the project root, or up to the home folder
when the launch folder is under it (`stop = FSUtil.contains(home, start) ? home : root`), so a
toolkit under the home folder also loads `~/AGENTS.md` and every `AGENTS.md` in between, git
checkout or not. This was read in OpenCode's source at v2.1.3 and not tested on a live session. OpenCode's Skills docs say project skills are
searched the same way, from the current directory up to the project root, at every level. That is
why the toolkit belongs in a folder of its own.

Sources: https://github.com/anomalyco/opencode/issues/51341 ·
https://github.com/anomalyco/opencode/pull/51422 ·
https://github.com/anomalyco/opencode/blob/v2.0.30/packages/core/src/config/plugin/instruction.ts ·
https://github.com/anomalyco/opencode/blob/v2.0.29/packages/core/src/config/plugin/instruction.ts ·
https://github.com/anomalyco/opencode/blob/v2.1.3/packages/core/src/config/plugin/instruction.ts
(`match`, `projectSource`) · https://opencode.ai/v2/docs/skills/ (Discovery)

## Install

The install has two parts. `install.py` copies the toolkit's own files, and
rulesync writes the agent, its helper, the `/add-service` command, the skills
and the rules. `~/AI/fcos-app-installer` stands for the folder you choose. Make
it a folder of its own, outside any git checkout: a copy inside another
repository would load that repository's own `AGENTS.md` and skills into every
session. The installer refuses the repository it belongs to and warns about any
other checkout.

1. Get the instructions-unclear repository, and run the next two commands from
   its root:

   ```fish
   # desktop (fish)
   git clone https://github.com/280Zo/instructions-unclear.git
   cd instructions-unclear
   ```
2. Copy the toolkit's own files (`tools/`, `templates/`, `docs/`, `tests/` and the
   rest). The first command only lists what it would do; read its list, then
   add `--apply`:

   ```fish
   # desktop (fish), in the repository
   python3 agents/fcos-app-installer/install.py ~/AI/fcos-app-installer
   python3 agents/fcos-app-installer/install.py ~/AI/fcos-app-installer --apply
   ```

   It copies a fixed list of files and never deletes anything. A file on that
   list that already exists and differs is replaced, so a README.md or
   `.gitignore` of yours at the top of the folder, or an edit you made to a
   toolkit file, would be overwritten. The dry run lists each one as "changed".
   Your workspace, rulesync's output and any other file are left alone.
3. Add the agent and the rest with rulesync:

   ```fish
   # desktop (fish), in the repository
   npx rulesync@41.0.0 generate --config groups/fcos_app_installer.jsonc --output-roots ~/AI/fcos-app-installer
   ```

   Only OpenCode enforces the agent's permission list. For another tool, add
   `--targets opencode,claudecode` and keep `opencode` in the list, because the
   tools read the skills where OpenCode keeps them. That tool gets the agent's
   instructions without the guard rails.
4. In the new folder, run the requirement check and the tests. Then run the
   checks in `docs/guide/10-trial-run.md` once to see that OpenCode loads the
   rules, skills and helper agent, and start OpenCode there:

   ```fish
   # desktop (fish)
   cd ~/AI/fcos-app-installer
   python3 tools/check_requirements.py
   python3 -m unittest discover tests
   ```
5. Start with `/add-service <service>`. The agent asks which server and VM. On
   the first run it asks where to keep the workspace (below) and creates it with
   `tools/workspace.py`.

## The workspace: your private files

Everything specific to your setup lives in a folder outside the toolkit's
folder and outside any git checkout that holds it, by default
`~/fcos-workspace`, remembered in `~/.config/fcos-agent/workspace`.
`tools/workspace.py` refuses a folder inside either. It asks git for the
checkout's top level; if git can't answer (not installed, or it refuses a
checkout another user owns), it looks for a `.git` above the toolkit instead.
It guards the nearest checkout: with nested checkouts, a folder in the outer
one but outside the inner one is allowed. A toolkit that is in no checkout is
guarded at its own folder only.

```
<workspace>/
  site.yaml        your servers, network, file server, domain, providers
  secrets/         API token files, mode 600, read only by scripts
  vms/<vm>/        each VM's spec, Butane fragments and Ignition file
  services/<svc>/  each service's spec, research notes, generated files
  adapters-draft/  adapters drafted during runs
```

Start from `site.example.yaml`. Every value there is a placeholder.

## Giving the agent access to your hypervisor

The agent never runs commands on your servers. Where the hypervisor has an API, its adapter has a step
you run yourself, as the server's administrator, that creates a limited token. The token can only see
and manage the VMs in its own pool, use one disk storage and one bridge, and upload config discs. The
agent uses it only through the adapter's tool (`tools/hypervisor.py`, which loads the adapter's code), which has no delete or
disk-swap command; those stay steps you run yourself. The step prints the secret once, and the agent's
next step stores it in `<workspace>/secrets/` from a hidden prompt. When the install is done, the
adapter's teardown step removes the access; the VMs keep running. The adapter's `SKILL.md` lists its
steps (`python3 tools/adapters.py show --role virtualization`).

On a VM the agent never uses your SSH key. It makes its own setup key
(`tools/vmssh.py`), you add it beside yours, and it is revoked when the
services work; only your key remains.

The agent's permissions are guard rails, not a wall: it runs as your user, so
a command written to get around them (a script it writes and then runs) could
reach anything you can, including your SSH key, your ssh-agent and
`secrets/`. They stop the ordinary ways in, and the agent is told never to
try the others. For a hard boundary, run the agent as a separate user or in a
container that can't read those.

Three habits keep those guard rails working:

- Pick the `fcos-app-installer` agent in this folder. OpenCode's own `build`
  agent sees the same tools and skills but none of this agent's rules, so it
  would run or edit things this agent may not. (The `default` group's
  restrictions for `build` hide this agent's skills from it, but they don't
  add this agent's guard rails.)
- Answer an approval with "Allow once". "Allow always" saves the command's
  pattern for the whole project (OpenCode's Permissions docs), so later
  commands that merely start the same way stop asking. A configured deny still
  wins, but the asks you rely on disappear. "Reject" also cancels every other
  request waiting at that moment.
- The workspace rule is broad on purpose: the agent may work in any folder whose
  path contains "fcos-" without asking. Keep that
  word for install folders such as `~/fcos-<place>/` and don't use it
  for unrelated folders. `secrets/` inside such a folder stays off limits.

The agent starts only its own `adapter-drafter` helper. A subagent runs with
its own permissions, not the starter's, so any other agent it started could
read `secrets/` or run commands the installer is denied. The folder holds no
other agent.

Its MCP filter is a deny list. The agent's file names each server it blocks, and
only Exa is left open for research. A server you add later is allowed until
someone names it there, and `agents/generate.py` and its tests in the
repository need the same change. Skills and subagents are allow lists.

## The login front end and getting in when it's down

One login front end (an ingress and an auth gateway) sits in front of every
app: you log in once, and the gateway's dashboard lists your apps. Each app's port only
accepts connections from the login front end (apps bound to loopback open no
port at all). If the login front end is down, the apps keep running, and you
reach any of them through an SSH tunnel:

```fish
# desktop (fish)
ssh -N -L 8080:<vm-ip>:<port> <admin>@<vm-ip>
```

1. You SSH from your desktop into the app's own VM. SSH from the admin
   network is allowed on every VM and doesn't involve the auth gateway.
2. SSH then connects to the app's port from inside that VM. Traffic from a
   machine to its own address counts as local traffic, which the firewall
   accepts (`iif "lo" accept`). So the tunnel reaches the app even though the
   port refuses every other machine.
3. You open `http://localhost:8080` on your desktop.

The tunnel skips the login page and HTTPS; use it to fix things and close it
when done. Details, and the fallback when SSH is down too:
`docs/guide/08-break-glass.md`.

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
   notes first, and write what changed and its link on the guide page that relies
   on it (for the Butane spec, section 2.8 of `docs/guide/02-build-a-vm.md`).
3. Change the pin in `tools/images.env` (tag and digest, as the check shows
   them on quay.io), test-first: a test for any change in behavior, then
   `python3 -m unittest discover tests`, both fixture validations and
   `python3 tools/publish_check.py`. Pull the new image yourself; the tools
   say the exact command.
4. Run the trial in `docs/guide/10-trial-run.md` on a VM that doesn't matter.
   Only then go back to the task.

### For the agent

At the start of every run, right after the workspace question, run
`python3 tools/check_updates.py`. If it reports an update, show its table and
offer to run the steps above first; never change a pin without the user's
yes, and the user approves each commit and pulls the image. If the check
can't run (no network), say so and carry on with the current pins.

## Changing a host script

You run the adapters' host scripts as root, after checking the checksum a step
shows. A step takes that checksum from the script itself, so the tools also
compare every script with `host-scripts.sha256`, a list the agent's rules keep
it from editing: the list sits outside the skills, edits to it are denied, and
so is any shell command that contains its name, its extension (`.sha25`) or the
word `host-script`. A spelling that avoids all three, such as `host-s*` or
`host-'scripts'.sha'256'`, is expanded by the shell after the rules have matched
and gets through. This is a guard rail like the rest of the agent's
permissions, not a wall: the agent runs as your user, so a command written to
get around the rules could still rewrite the file. For a hard boundary run the agent as a separate user. A script whose hash
differs from the list, or that the list does not hold, stops its step with a
message, and only scripts an adapter declares in its `scripts:` list are
pinned. The list takes one `sha256sum` line per script, no blank lines or
comments.

After you change a script on purpose, read the change first (for example with
`diff` against the same script in the instructions-unclear repository, or
`git diff` if you keep the toolkit in a checkout), then rewrite the list
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
It checks every file in the folder, with no exemptions. It scans the toolkit's
own folder only, or the one folder you pass as an argument (pass a checkout's
top level to scan all of it). Run it in the folder you installed the toolkit
into. In the repository the skills sit at `skills/`, not `.opencode/skills/`,
so it can't find the adapters and reports product names such as an adapter's name
from your workspace as hits. Its last line says how
it found the files: `git list` (git's list for the folder, ignored files
excluded) or `walked` (every file in a plain copy, or when git can't answer;
git's own folder, Python caches and links are skipped, and git-ignored files are
read). A file it can't read is reported as a hit, and a scan that finds no file
at all is an error, not a pass.

## Layout

| Folder | Holds |
|---|---|
| `.opencode/` | the agents (`fcos-app-installer`, the main one for Fedora CoreOS; `adapter-drafter`, its helper that drafts adapters) and the `/add-service` command, written by rulesync |
| `.opencode/skills/` | skills: one adapter per provider (its manual steps, notes and host scripts), the generic fallback, `researching-apps-for-self-hosting`, and one module per product the login front end can use (`ingress-*`, `authgw-*`): its data, spec, templates and `operations.md` (the steps that depend on the product). List them with `python3 tools/modules.py list` |
| `host-scripts.sha256` | the pinned checksum of every host script; the agent's rules keep it from editing this file |
| `AGENTS.md` | rules that don't depend on the OS: how manual steps are given, how secrets and private values are handled; written by rulesync |
| `docs/guide/` | the procedure, provider-neutral |
| `schemas/` | the service spec's field reference |
| `templates/` | Butane and Quadlet building blocks |
| `tools/` | the desktop-side tools |
| `tests/` | tests, including the publish and wording checks |

In the repository (`agents/fcos-app-installer/`), the same pieces are kept as
rulesync sources and the toolkit's own files:

| Folder or file | Holds |
|---|---|
| `subagents/`, `commands/`, `skills/`, `rules/` | the sources rulesync turns into `.opencode/agents/`, `.opencode/commands/`, `.opencode/skills/` and `AGENTS.md` |
| `toolkit/` | the toolkit's own files: `tools/`, `templates/`, `docs/`, `schemas/`, `specs/`, `tests/`, `site.example.yaml`, `host-scripts.sha256` |
| `install.py` | places `toolkit/` and this README into the folder you run the toolkit in |
| `profile.jsonc` | the profile for rulesync; `groups/fcos_app_installer.jsonc` is the install group |

## For agents: install, remove and update

Install. Follow [Install](#install) with the user's folder, and ask before each
step: the installer copies files and rulesync writes the agent files, so both
change the user's disk. Run the dry run first and show the user its list,
especially any "changed" line, since those files get replaced. The group installs
the installer agent, `adapter-drafter`, the `/add-service` command, 8 skills and
3 rules, and writes no MCP settings, so it can't replace the user's MCP list. It
is not part of the `default` group; it needs `--output-roots`, never `--global`.
To verify, ask the user to start OpenCode in the new folder, pick
`fcos-app-installer`, and work through `docs/guide/10-trial-run.md`. Its checks
show that the rules, skills and helper agent load.

Remove. The install wrote only into the folder it was installed to, so delete
that folder, with the user's approval. Two things live outside it and belong to
the user: the workspace (their private values and `secrets/`) and the
remembered path `~/.config/fcos-agent/workspace`. Leave both unless the user
asks, and never open `secrets/`. The hypervisor user and token and the VM
setup keys that runs create are not in the folder either; the teardown steps
in the guide remove them (`teardown-agent-access.sh`), so tell the user if they
are still in place. rulesync uses `delete: false`, so regenerating after a
change to the repository never removes an old agent, skill or command file;
delete stale names yourself, with approval, from `.opencode/agents/`,
`.opencode/commands/` and `.opencode/skills/`.

Update. The toolkit has no upstream. It is written for this repo, so edit the
files under `agents/fcos-app-installer/` in the repository. Keep the tool
sections in `subagents/*.md` and `commands/add-service.md` (`name`, `targets`
and `opencode:`, listed in the repo's `AGENTS.md`). The agent's permission list
is hand-written, so don't try to generate it; `agents/generate.py` reads it for
the agent map. After a change, run `python3 -m unittest discover -s tests` in
the repository, then `check_fcos_app_installer.py` from the repository's
`tests/` folder with the path of the rulesync CLI. That check installs into a
new folder and runs the toolkit's whole suite there. To update an installed
folder, run `install.py` again (it lists what changes), then the rulesync
command. The pinned Butane and Podman images are updated by hand (see
[Updating](#updating)). When you add or rename a folder here, update
`groups/README.md` and the catalog READMEs, and run `python3 agents/generate.py`.

## Origin

Written for this repo by 280Zo, under the repository's MIT license. It has no
upstream to check. The agent's closing "How to work" section is the shared
one from `agents/generate.py`, adapted from OpenCode v2.1.3 (MIT, © 2025
opencode). The license text is in the repository's `THIRD_PARTY_LICENSES.md`.
