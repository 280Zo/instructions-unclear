---
name: hypervisor-proxmox
description: "Manual steps and agent access for Proxmox VE as the virtualization server of the fcos-app-installer toolkit: downloading the Fedora CoreOS image, giving the agent a pool-scoped API token and storing it, describing the host (read-only discovery), config-disc fallback, rebuilding an OS disk, deleting a VM, and removing the agent's access. Use when the user's VMs run on Proxmox VE."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps from adapter.yaml.
---

# Proxmox VE (virtualization)

The agent itself only uses `tools/hypervisor.py` (check, list, create, start,
status) with the token. Everything that needs root on the host, or deletes,
is a manual step from this skill. The host scripts the user runs are in
`scripts/` (`lib.sh`, `setup-agent-access.sh`, `discover-host.sh`,
`teardown-agent-access.sh`); the renderer puts their checksums in the steps. `site.example.yaml` in this
folder shows the `hosts` section of the site file with every key the scripts and `tools/virtualization/proxmox.py` read.

Order of a first install: `discover_host`, `download_image`,
`create_api_access`, then `store_api_token` as its own step right after a new
token is created. If the check says the token already exists and the
workspace has no copy of its secret, show `rotate_api_token` as its own step
instead of applying, then `store_api_token`; never show the two together. At
the end: `teardown_api_access` (the VMs move into pool `backrooms`), then the
user deletes the token file.

## How to use it

Never write these commands by hand. The shared renderer fills in every value,
refuses values that could change a command, and computes script checksums
itself. List the steps and the values each one needs, then render one step at a
time, with the values in a JSON file in `/tmp/opencode/`:

```fish
# desktop (fish)
python3 tools/adapters.py show --role virtualization --provider proxmox
python3 tools/adapters.py render --role virtualization --provider proxmox --step <id> --values /tmp/opencode/<id>.json
```

Show the rendered step to the user as it is, then wait for what it asks them
to report back. `HOST` is the server's key in the site file, never its display
or node name.

## Steps

| Step | What it does |
|---|---|
| `download_image` | Download the current Fedora CoreOS image to the server |
| `create_api_access` | Give the agent its limited Proxmox token on the server |
| `rotate_api_token` | Replace an existing token whose secret the workspace doesn't have |
| `store_api_token` | Store that token on the user's desktop, from a hidden prompt |
| `discover_host` | Describe the server for the agent (read-only) |
| `teardown_api_access` | Remove the agent's Proxmox access (VMs move to pool `backrooms`) |
| `copy_ignition_snippet` | Give a VM its Ignition file as a snippet (fallback) |
| `rebuild_os_disk` | Replace a VM's OS disk, keep its data disk |
| `remove_vm` | Delete a VM and its disks |

## Official documentation

- https://pve.proxmox.com/pve-docs/qm.1.html
- https://pve.proxmox.com/pve-docs/pveum.1.html
- https://pve.proxmox.com/pve-docs/api-viewer/
- https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/provisioning-proxmoxve.adoc
- https://pve.proxmox.com/pve-docs/chapter-qm.html

Menu names change between versions; when one doesn't match, follow the linked documentation.
