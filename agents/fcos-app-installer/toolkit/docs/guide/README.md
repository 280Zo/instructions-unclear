# Adding services to Fedora CoreOS machines

This guide is the procedure for building Fedora CoreOS (FCOS) virtual machines
and adding services to them. A person can follow it by hand, and the
`fcos-app-installer` agent follows it step by step. Verified facts and their sources:
[`research-notes.md`](research-notes.md). The questions the agent asks, in
order and in plain language: [`questions.md`](questions.md).

**Private data stays out of this repository.** Every real value (names,
addresses, domains, users, servers) lives only in the private workspace, a
folder outside the repository (`<workspace>/site.yaml`, `<workspace>/vms/`,
`<workspace>/services/`). Secret values live only in Podman secrets on the
machines, in `<workspace>/secrets/` files that only scripts read, and in the
owner's password manager. Commands and examples here use placeholders:
`192.0.2.x` addresses, `example.duckdns.org`, `<admin>`, `<workspace>`.
`python3 tools/publish_check.py` runs before every commit and fails on any
workspace value or anything that looks like private data.

## Roles and providers

The setup has a few roles, and the owner picks a product for each:

| Role | Does |
|---|---|
| virtualization | runs the machines; may offer an API the agent can use with a limited token |
| router and firewall | hands out reserved addresses, local DNS (one wildcard name), traffic between networks |
| file server | shared folders over NFS, one account per service, a backups share |
| DNS for certificates | lets the login front end prove it owns the domain (Let's Encrypt DNS-01) |
| login front end | built by the agent: Traefik and Authentik on one always-on machine |

Each product has an adapter: its owner steps, with every value filled in,
what the agent may do through an API, and links to its official docs. A
product without an adapter gets the general steps from the skill `adapter-generic`,
and the agent offers to draft an adapter from what the owner actually did
(the `adapter-drafter` subagent, with `tools/adapters.py draft`). Each adapter is
a skill, `.opencode/skills/adapter-<product>/`: `SKILL.md` says what the product is and when
to use it, `adapter.yaml` holds the steps, `scripts/` its host scripts, and
`tools/adapters.py` is the one renderer for all of them.

**Providers.** Adapter skills exist for Proxmox VE (`adapter-proxmox`, with its
host scripts and API access through `tools/pve.py`), OPNsense
(`adapter-opnsense`), TrueNAS (`adapter-truenas`) and DuckDNS
(`adapter-duckdns`). Pages in this guide name the
adapter step to show, for example "virtualization: `create_api_access`".

## Running it with the agent

In OpenCode, started in the toolkit's folder (the one holding `tools/`), run
`/add-service <service>` (the agent asks which server and VM). The
`fcos-app-installer` agent reads this guide and the workspace, asks the questions in
`questions.md`, and does every **[Agent]** step itself. It stops for **[Owner]**
steps, missing values, the 5 GB rule, images that start as root, failed checks,
anything irreversible, and commits.

## Pages

1. [Host setup](01-host-setup.md): once per virtualization server
2. [Build a VM](02-build-a-vm.md)
3. [Add a service](03-add-a-service.md): the core procedure
4. [Databases and backups](04-databases-and-backups.md)
5. [Rebuild a VM](05-rebuild-a-vm.md) while keeping its data disk
6. [Login front end](06-edge-vm.md): Traefik, Authentik, certificates
7. [Remove a service, roll back the login layer](07-remove-and-rollback.md)
8. [Break-glass access](08-break-glass.md)
9. [Admin commands](09-admin-commands.md)
10. [Trial run after installing](10-trial-run.md): the checks only a live OpenCode can show
11. [Move and update](11-move-and-update.md): another computer, a newer toolkit, a service's new release line

## Conventions

Run every desktop command in this guide (`python3 tools/...`) from the
toolkit's folder, the one holding `tools/`: the commands are relative to it.

Every action is tagged with who does it. **[Owner]** steps happen on systems
the agent never touches: the virtualization server's shell, the router, the
file server, the DNS provider, remote-access consoles, and anything involving
a secret value. The agent shows them from the adapter, with every value filled
in, says which machine and shell each command runs in, lists what to report
back, and waits. **[Agent]** steps happen on the desktop, in the workspace, on
the machines over SSH, and through `tools/pve.py`.

Each code block starts with a comment naming the machine and shell:
`# desktop (fish)`, `# vm ai (bash, <admin>)`. Desktop commands are fish syntax;
commands on a server or a machine are bash.

## How it works

**Butane files are the source of truth, and changes also go live.** Each VM
has a folder `<workspace>/vms/<vm>/` with its Butane fragments: base config,
one per NFS share, the firewall, and one set per service. `config.bu` merges
them into the VM's Ignition file. Adding a service adds its fragments, rebuilds
the Ignition file, and pushes the same contents to the running VM with
`tools/ign_to_script.py`, so the running VM matches what a rebuild produces.

**Services are generated from a spec.** `<workspace>/services/<svc>/service.yaml`
describes the containers, storage, secrets and login
([`schemas/service.schema.md`](../../schemas/service.schema.md)).
`tools/gen_service.py` turns it into Quadlets, Butane fragments, backups, a
firewall port, and the route and login rules. The login front end is generated
the same way from `specs/login-frontend/` by `tools/login_frontend.py`.

**Several servers, never clustered.** Each server is an entry under `hosts` in
the site file, with its own storage, network and limits. One marked as not
always on is sometimes switched off, with everything on it. The login front end
goes on an always-on server. Every VM procedure starts by asking which server.

**Storage classes.** Every path a container uses has one class:

| Class | Lives in | Use for |
|---|---|---|
| `nfs` | `/var/mnt/<share>/...` | Project files and bulk data |
| `local` | `/var/lib/appdata/<service>/...` (data disk) | State that must survive rebuilds and must not depend on the file server |
| `local-db` | `/var/lib/appdata/<service>/db/<container>` (data disk) | SQLite, Postgres, MariaDB. Never on NFS |

Every VM has two disks. The OS disk is replaced on every rebuild. The data disk
(label `appdata`) is kept. Backups copy `local` and `local-db` data to the file
server when it's up, and skip quietly when it isn't.

**The 5 GB rule.** A service's `local` and `local-db` data may go on the data
disk without asking when it's expected to stay at or under 5 GB. Above that the
agent stops and asks: grow the data disk, or store on NFS and record the risk
in the service's accepted risks (for a database, saying plainly that it can
corrupt).

**Rootless.** Each service runs as its own Linux user with a fixed UID/GID
(matching its file server account when it uses NFS), under rootless Podman
Quadlets with all capabilities dropped and no new privileges. `map-user`
containers keep the user's IDs; `root-start` images (that start as root inside
the container) get only the capabilities the spec lists, and no NFS volumes.

**One login front end.** One always-on VM runs Traefik and Authentik for every
service (section 6 explains why one, and how to get in when it's down). Every
name under the domain points at it. Traefik serves HTTPS with one wildcard
certificate and asks Authentik to log the user in, then forwards to the
service's VM. Each service VM's firewall accepts the service port only from
the login front end. Clients that can't do a web login use the paths the spec
lists as open, protected by the app's own password.

## Who does what

| The owner | The agent |
|---|---|
| Virtualization server: runs the setup script and the delete/rebuild commands from the adapter | Creates, starts and checks VMs with `tools/pve.py` and the limited token |
| Router: address reservations, the DNS wildcard, traffic rules between networks | Writes the specs, generates and builds every file, runs the checks |
| File server: accounts, groups, exports, folders | Pushes changes to running VMs over SSH as `<admin>` and starts services |
| Secret values: entered at hidden prompts, kept in the password manager | Lists secret names only; never sees a value |

## Tools in this repo

| Tool | Does |
|---|---|
| `tools/workspace.py` | Creates and finds the workspace; reads earlier installs |
| `tools/pve.py` | The only way the agent talks to the virtualization API: `check`, `list`, `create [--dry-run]`, `start`, `status`. Reads the token itself; refuses VMs outside its pool |
| `tools/gen_service.py <service.yaml> <site.yaml> <out>` | Generates every file for one service from its spec |
| `tools/login_frontend.py <site.yaml> <out> [<service.yaml>...]` | Generates the login front end and every route and login rule |
| `tools/adapters.py` | Loads adapters, renders owner steps, drafts new adapters |
| `tools/render.py <template> <values>` | Fills `{{KEY}}` placeholders for the base templates |
| `tools/build-vm.sh <folder>` | Butane strict on every fragment, `nft -c` on the firewall, Quadlet dry run, secret scan |
| `tools/ign_to_script.py <fragment.ign>...` | Turns fragments into one idempotent script for the running VM |
| `tools/vmssh.py` | The agent's own SSH key for a VM: `keygen`, `trust`, `run`, `logs` (the only way it reads a log), `revoke`. Output passes through `tools/redact.py`, which hides secret-looking text |
| `tools/http_check.py [--timeout N] <url>` | Prints a URL's status code (and redirect), or `refused`; verifies TLS, sends no data, writes nothing |
| `tools/install_notes.py <workspace> [--note "..."]` | Writes `<workspace>/AGENTS.md`: what the install has and how a new service hooks in; keeps hand-added notes |
| `tools/publish_check.py` | Run before every commit |
| `tools/validate.sh tests/fixtures/<x>.values` | Builds every template and every generated fixture with test values |
| `python3 -m unittest discover tests` | All tests |
