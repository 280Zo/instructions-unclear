# 1. Host setup (once per virtualization server)

Do this once on every server listed under `hosts` in the site file. Every
step that runs on the server is **[Owner]**: the agent never runs commands
there. The agent shows each step from the virtualization adapter with the
server's values filled in.

**Providers.** For Proxmox VE the steps are in the skill `adapter-proxmox` (`.opencode/skills/adapter-proxmox/`);
the setup and teardown scripts are in its `scripts/` and the agent
uses the token through `tools/hypervisor.py`. For another platform the agent shows
the general steps from the skill `adapter-generic`.

## 1.1 Ask the owner, from what the server shows

Never assume a network, storage or hardware value. The owner runs the
read-only discovery script (adapter step **virtualization: `discover_host`**,
the discovery script in the virtualization adapter skill), which saves the server's facts as
`<workspace>/hosts/<host>/discovery.txt`; the agent reads that file and asks
one question at a time with options taken from it ([questions](questions.md),
5 and 7). Run it again after the server's hardware, storage or network
changes. For another platform the agent gives read-only commands instead and
the owner pastes their output.

| Value | Fills (site file) |
|---|---|
| The name the owner uses for the server, and its node name | `hosts.<host>.name`, `.node` |
| Its address for the API, and the API's CA certificate | `hosts.<host>.address`, `.ca_file` |
| Always running, or sometimes switched off | `hosts.<host>.always_on` |
| VM disk storage | `hosts.<host>.storage` |
| Storage for config discs and images, and its import folder | `hosts.<host>.iso_storage` |
| Network bridge, VLAN, MTU (never the WAN bridge) | `hosts.<host>.bridge`, VM specs |
| CPU, memory and disk type (decides cores, RAM, SSD emulation, ballooning) | VM specs |

## 1.2 [Owner] Download the Fedora CoreOS image

Adapter step **virtualization: `download_image`**. It downloads the stable
image for the platform from the official stream metadata, checks its SHA-256,
and stops (deleting the file) if it doesn't match. Repeat before each rebuild,
so VMs start from a current image.

Report back: the checksum line and the image file name.

## 1.3 [Owner] Give the agent a limited token

Adapter step **virtualization: `create_api_access`**. The owner copies the
host scripts to the server, checks their SHA-256 (`tools/adapters.py` fills
them in, and the agent's own folder, from where the agent is installed; they
are never typed in by hand), runs the setup script in check mode, then for
real. The
token can only see and manage VMs in its own pool, use one disk storage, one
network bridge, and upload config discs to one storage. It cannot delete VMs
or disks.

When the token is new, the script prints its secret once, and nothing to run.
The agent then shows the next step on its own, **virtualization:
`store_api_token`**: a desktop command that stores the secret in
`<workspace>/secrets/` from a hidden prompt. The secret never goes into the
chat, and the agent never reads the file; only `tools/hypervisor.py` does.

Report back: the checksum lines, the check's output, the apply's output
without the secret.

## 1.4 [Agent] Check the token

```fish
# desktop (fish)
python3 tools/hypervisor.py check --host <host> --workspace <workspace>
```

Expected: the API version, and the token's rights on exactly its pool, its
storages and its bridge. Anything more or less: stop and report it.

## 1.5 Local backups of VM disks

Every VM's data disk holds state that must survive the file server being off,
so each server backs its VMs up to its own storage, on a schedule outside the
update window. The OS disk is rebuilt from config anyway and can be left out.
How to set it up is in the virtualization platform's own docs (the adapter
links them).

## 1.6 When the install is done

**[Owner]** Adapter step **virtualization: `teardown_api_access`**. It moves
the agent's VMs into pool `backrooms` (always this
pool, so nothing is asked; they keep running, the script creates the pool when
it doesn't exist, and a pool is only a label for a set of VMs), then removes
the agent's pool, the token, its user, roles and grants. Run the check first. Afterwards delete
the token file in `<workspace>/secrets/`. The next install runs the setup
script again for a fresh token.
