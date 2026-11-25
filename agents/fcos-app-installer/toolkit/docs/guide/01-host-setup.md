# 1. Host setup (once per virtualization server)

Do this once on every server listed under `hosts` in the site file. Every
step that runs on the server is **[Manual]**: the agent never runs commands
there. The agent shows each step from the virtualization adapter with the
server's values filled in.

**Providers.** For Proxmox VE the steps are in the skill `hypervisor-proxmox` (`.opencode/skills/hypervisor-proxmox/`);
the setup and teardown scripts are in its `scripts/` and the agent
uses the token through `tools/hypervisor.py`. For another platform the agent shows
the general steps from the skill `adapter-generic`.

## 1.1 Ask the user, from what the server shows

Never assume a network, storage or hardware value. The user runs the
read-only discovery script (adapter step **virtualization: `discover_host`**,
the discovery script in the virtualization adapter skill), which saves the server's facts as
`<workspace>/hosts/<host>/discovery.txt`; the agent reads that file and asks
one question at a time with options taken from it ([questions](questions.md),
5 and 7). Run it again after the server's hardware, storage or network
changes. For another platform the agent gives read-only commands instead and
the user pastes their output.

| Value | Fills (site file) |
|---|---|
| The name the user uses for the server, and its node name | `hosts.<host>.name`, `.node` |
| Its address for the API, and the API's CA certificate | `hosts.<host>.address`, `.ca_file` |
| Always running, or sometimes switched off | `hosts.<host>.always_on` |
| VM disk storage | `hosts.<host>.storage` |
| Storage for config discs and images, and its import folder | `hosts.<host>.iso_storage` |
| Network bridge, VLAN, MTU (never the WAN bridge) | `hosts.<host>.bridge`, VM specs |
| CPU, memory and disk type (decides cores, RAM, SSD emulation, ballooning) | VM specs |

## 1.2 [Manual] Download the Fedora CoreOS image

Adapter step **virtualization: `download_image`**. It downloads the stable
image for the platform from the official stream metadata, checks its SHA-256,
and stops (deleting the file) if it doesn't match. Repeat before each rebuild,
so VMs start from a current image.

Report back: the checksum line and the image file name.

## 1.3 [Manual] Give the agent a limited token

Adapter step **virtualization: `create_api_access`**. The user copies the
host scripts to the server, checks their SHA-256 (`tools/adapters.py` fills
them in, and the agent's own folder, from where the agent is installed; they
are never typed in by hand), runs the setup script in check mode, then for
real. The
token can only see and manage VMs in its own pool, use one disk storage, one
network bridge, and upload config discs to one storage. It cannot delete VMs
or disks.

If the check says the token already exists and the workspace has no copy of its
secret, the agent does not apply. It shows **virtualization: `rotate_api_token`**
as a step of its own, never in the same message: it replaces the token, so the
old one, and any other workspace's copy of it, stops working.

When the token is new, the script prints its secret once, and nothing to run.
The agent then shows the next step on its own, **virtualization:
`store_api_token`**: a desktop command that stores the secret in
`<workspace>/secrets/` from a hidden prompt, together with the address of the
server (and the certificate authority's file, if you have your own). The token
is sent only to the address stored with it, so check that address in the
command before you run it; a different address in the site file is refused. The
secret never goes into the chat, and the agent never reads the file; only
`tools/hypervisor.py` does.

Report back: the checksum lines, the check's output, the apply's output
without the secret.

## 1.4 [Agent] Check the token

```fish
# desktop (fish)
python3 tools/hypervisor.py check --host <host> --workspace <workspace>
```

Expected: the API version, and the token's rights on exactly its pool, its
storages and its bridge. Anything more or less: stop and report it.

## 1.5 Backups of VM disks

Each service backs up its own data by itself: database copies and a files
archive on the file server (section 4). When the file server is off, those
wait. A backup of the whole VM data disk, made by the virtualization server,
covers the data disk even then.

Many platforms write a whole-disk backup as a full copy every time: each run
writes the entire disk, and every copy you keep is another entire disk, so the
space needed grows fast. The agent therefore doesn't propose it by default. It proposes
one when you want a copy that survives the file server being off or lost, and
then says what it costs in space. The OS disk is rebuilt from config anyway
and can be left out.

Where the copy goes matters more than how often. Never put it on the same disk
as the VMs it protects: on a server that has only one disk, one failure would
take the VMs and their backups together. Use another disk, the file server or
another machine.

Where the platform offers them, two ways cost less space: a backup server that
stores each piece of data once (deduplicated), so a new copy adds only what
changed; and replication of the data disk to a second server, which after the
first full copy sends only the changes and keeps a copy for the case that a
server fails. Replication copies a deletion or a damaged file too, so it
protects against a failed server, not against a mistake. How to set a backup up is in the virtualization platform's own
docs (the adapter links them).

**Providers.** For Proxmox VE (`hypervisor-proxmox`), its backups are always
full backups. Proxmox Backup Server stores deduplicated chunks, and its docs
recommend it on a dedicated host, with an NFS server as the alternative.
Replication needs a second node and local ZFS storage. The sources are in the
adapter's `reference.md`, "Whole-disk backups".

## 1.6 When the install is done

**[Manual]** Adapter step **virtualization: `teardown_api_access`**. It removes
the agent's access: the token, its user, roles and grants. The VMs keep
running, and nothing is asked. Run the check first. Afterwards delete the token
file in `<workspace>/secrets/`. The next install runs the setup script again
for a fresh token.

**Providers.** For Proxmox VE (`hypervisor-proxmox`) the teardown first moves the
agent's VMs into pool `backrooms` (always this pool; the script creates it when
it doesn't exist, and a pool is only a label for a set of VMs), then removes the
agent's own pool.
