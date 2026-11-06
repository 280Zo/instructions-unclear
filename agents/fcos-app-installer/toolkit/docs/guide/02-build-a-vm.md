# 2. Build a VM

Builds a new FCOS VM with the base config, its NFS shares and the firewall.
No services yet; those come from [section 3](03-add-a-service.md). Host setup
([section 1](01-host-setup.md)) must be done on the target server.

## 2.1 Ask the user

[Questions](questions.md) 5 to 8: which server (always asked), a new machine,
its size, disks and network (with options from the server's discovery output),
and the address to reserve. Then the shares it mounts.

| Value | Fills |
|---|---|
| VM name (lowercase letters, digits, hyphens) | `vms[].name` in the site file, the VM spec |
| An unused VM ID | VM spec `vmid` |
| Cores, memory, OS disk, data disk (the sum of its services' local data plus headroom) | VM spec |
| Disk storage, bridge, VLAN, MTU, SSD emulation, ballooning | VM spec |
| The address to reserve | `vms[].ip` |
| NFS shares and their export paths (always a `backups` share) | `vms[].nfs_shares` |

Any site value still marked ASK is asked now.

## 2.2 [Manual] File server: allow the VM on each export

For each share: adapter step **file_server: `nfs_export`**. The VM's own
folder in the backups share comes with its first service
(file_server: `backup_folder`, section 3.5).

Report back: done, plus any export path that differs from the site file.

## 2.3 [Agent] Write the VM spec

`<workspace>/vms/<vm>/vm.yaml`, every value from the site file and the
user's answers, none assumed. Its fields (the VM ID, the image, the disks, the
network, the platform settings) belong to the hypervisor adapter's tool: the
adapter's `vm.example.yaml` lists every one, and the tool refuses a spec that
leaves one out.

**Every VM setting is decided, never left to a default.** Research the
server's facts (discovery: CPU and its flags, NUMA nodes, disk type, memory
free with every guest running, other VMs' start order) and the official
guidance (the virtualization platform's VM documentation, the FCOS guide for
that platform, each app's requirements). Then fill `settings:` with every
setting in the adapter's example, each with the value to use, why, and the
source. The platform's tool refuses a spec where one is missing, unexplained or
out of range, and its dry run prints them all as a table. Show that table to
the user; the values are used unless the user changes them.

**Providers.** For Proxmox VE the example is `vm.example.yaml` in the skill
`hypervisor-proxmox`; `tools/hypervisor.py` checks and sends those settings,
and the official sources are the Proxmox VE VM chapter and the FCOS Proxmox
guide, linked in that skill.

If a VM must start after another one on the server (the router that serves
its address, the file server), give that one a start order (for example 1,
with a startup delay) as a manual step in the platform's web interface. The
agent's VMs keep no start order: VMs without one start after those that have
one, and setting it needs a right on the whole server that the agent's
access deliberately doesn't have (the tool refuses it before sending
anything).

## 2.4 [Agent] Render the base fragments and build

Each fragment gets a flat `KEY=value` file in `<workspace>/vms/<vm>/values/`,
built from the site file. Never a secret value: `tools/render.py` refuses keys
ending in `_TOKEN`, `_PASSWORD`, `_SECRET` or `_KEY` that have a value.

| Fragment | Template | Rendered as |
|---|---|---|
| base | `templates/base/base-config.bu.tmpl` | `base-config.bu` |
| firewall | `templates/base/firewall.bu.tmpl` | `firewall.bu` |
| one per NFS share | `templates/base/nfs-share.bu.tmpl` | `nfs-<share>.bu` |
| shared groups (if a service uses one) | `templates/base/shared-group.bu.tmpl` | `group-<name>.bu` |
| login front end VM only | `templates/base/edge-ports.bu.tmpl` | `edge-ports.bu` |
| top level | `templates/base/config.bu.tmpl` | `config.bu` |

`MERGE_ENTRIES` in `config.values` lists one `      - local: igns/<fragment>.ign`
line per fragment (the file name without `.bu`), `base-config` first: Ignition
creates users in that order, and the admin account must come before any app's
account to get user number 1000 or 1001 (`build-vm.sh` refuses another order).

```fish
# desktop (fish)
set ws <workspace>; set vm apps
mkdir -p $ws/vms/$vm/values $ws/vms/$vm/files
python3 tools/render.py templates/base/base-config.bu.tmpl $ws/vms/$vm/values/base-config.values > $ws/vms/$vm/base-config.bu
python3 tools/render.py templates/base/firewall.bu.tmpl $ws/vms/$vm/values/firewall.values > $ws/vms/$vm/firewall.bu
for share in backups
    python3 tools/render.py templates/base/nfs-share.bu.tmpl $ws/vms/$vm/values/nfs-$share.values > $ws/vms/$vm/nfs-$share.bu
end
python3 tools/render.py templates/base/config.bu.tmpl $ws/vms/$vm/values/config.values > $ws/vms/$vm/config.bu
bash tools/build-vm.sh $ws/vms/$vm
```

Expected: every line `ok`, ending with `build-vm: all checks passed`. Any
`FAIL` stops the procedure. The Ignition file goes next to the spec as
`<vm>.ign`, which is where `tools/hypervisor.py` looks for it.

## 2.5 [Agent] Create the VM, stopped

```fish
# desktop (fish)
python3 tools/hypervisor.py create <workspace>/vms/<vm>/vm.yaml --host <host> --workspace <workspace> --dry-run
```

Before anything is sent (dry run included), the adapter's tool checks the
VM's network against the server's and refuses what the server or the user's
network would reject. A check it can't make only gives a warning: tell the
user, who checks it on the server. A refusal goes to the user as it is; never
change the user's network to get past it.

**Providers.** The Proxmox VE tool (`hypervisor-proxmox`) reads the server's
network list and refuses a bridge other than the host's `bridge` (the token's
permissions refuse it too; an optional `forbidden_bridges` list is honored but
never asked), a VLAN on a bridge that isn't VLAN-aware or doesn't allow it,
and a network card MTU above the bridge's. A bridge that doesn't report
which VLANs it allows only gives a warning.

Show the user the dry run's exact steps (upload the config disc, create the
VM in the agent's pool with protection on, grow the OS disk) and ask before
running it without `--dry-run`. The VM is created stopped, and `hypervisor.py`
prints its network card's `MAC address:` for 2.6 (`hypervisor.py status` shows it
again).

## 2.6 [Manual] Router: reserve the address

Adapter step **router_firewall: `reserve_ip`**, after the VM is created and
before its first start. On a network that only serves reserved MAC addresses
the VM gets no address at all without it. If the VM sits on a different
network from the file server or the login front end, also
**router_firewall: `allow_flows`**.

Report back: done, and the reserved address if it differs.

**[Manual] The desktop's route to the VM, when needed.** The agent runs on the
user's desktop, so it checks the desktop's own networks first (read-only):
`ip -4 -br addr`. If the desktop has an address on the VM's network that is
not one of the VM's SSH or web sources, it reaches the VM directly from that
address and the VM's firewall drops it. The user then adds a permanent route
for the VM's address through the router, on a desktop network the VM does
allow (with the router's pass rule for SSH and the web from there). Every
value is filled in; the router's address on that network is asked if the
site file doesn't hold it:

```fish
# desktop (fish)
set conn (nmcli -g GENERAL.CONNECTION device show <allowed-interface>)
sudo nmcli connection modify "$conn" +ipv4.routes "<vm-ip>/32 <router-ip-on-that-network>"
sudo nmcli device reapply <allowed-interface>
ip route get <vm-ip>
```

`device reapply` applies the saved route without taking the interface down.
This assumes NetworkManager on the desktop.

Report back: the first line of `ip route get`, which shows
`via <router-ip-on-that-network>`.

## 2.7 [Agent] Start and check the first boot

The agent never uses the user's SSH key. It works on the VM with its own
setup key, which the user adds beside theirs and which is revoked when the
services work (3.10). The private key stays in the workspace's `secrets/`
folder; `tools/vmssh.py` runs ssh with only that key (no ssh config, no
ssh-agent).

1. Start the VM and make the key:

   ```fish
   # desktop (fish)
   python3 tools/hypervisor.py start <vmid> --host <host> --workspace <workspace>
   python3 tools/vmssh.py keygen <vm> --workspace <workspace>
   ```

2. **[Manual]** The key command prints the manual step, with the public key
   filled in: log in with your own key and put it in its own file,
   `~/.ssh/authorized_keys.d/fcos-agent`, then print the VM's host key
   fingerprint. The block checks the machine's name first and stops with
   `STOP: this is not <vm>` anywhere else, so pasting it on the wrong machine
   (another VM, or the hypervisor) changes nothing. Report back the
   fingerprint line.

3. Pin the VM's host key, then check the first boot:

   ```fish
   # desktop (fish)
   python3 tools/vmssh.py trust <vm> --fingerprint <SHA256:...> --workspace <workspace>
   python3 tools/vmssh.py run <vm> --workspace <workspace> -- 'hostnamectl hostname; getenforce; findmnt -n /var/lib/appdata; ls -l /dev/disk/by-id/ | grep drive-scsi1; systemctl is-enabled nftables podman-auto-update.timer zincati; sudo nft list set inet host_filter edge_tcp; systemctl --failed --no-legend'
   python3 tools/vmssh.py run <vm> --workspace <workspace> -- 'for m in /var/mnt/*; do /usr/local/bin/require-mounts $m && echo "$m mounted"; done'
   ```

The later pages write `python3 tools/vmssh.py run <vm> -- '...'` for the same
call; add `--workspace <workspace>` before `--` when no workspace is
remembered.

Expected:
- hostname is `<vm>` and SELinux is `Enforcing`
- `/var/lib/appdata` is mounted (xfs, label `appdata`)
- a `scsi-0QEMU_QEMU_HARDDISK_drive-scsi1` link exists
- all three units are `enabled`, and no unit has failed
- `edge_tcp` exists (empty until services are added)
- every NFS share prints `mounted`

FCOS updates itself (Zincati) and reboots inside the update window; that is
expected.

**If SSH doesn't answer:** first check the address reservation (2.6).
`tools/hypervisor.py status` shows whether the VM is running. The user can see in
the virtualization platform's own view whether it has read from its disks and
sent network traffic; a VM that read hundreds of MB and sent packets has
booted. The serial console is not a proven fallback yet (see
[section 8](08-break-glass.md)).

**If `/var/lib/appdata` isn't mounted,** Ignition didn't find the data disk
under `/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1`. Check the
`by-id` name on the VM, fix the device path in the base template, and rebuild
([section 5](05-rebuild-a-vm.md)).

## 2.8 Facts the base configuration relies on

Each fact comes from the official source linked under it, not from memory. Re-check one when its source changes.

### Latest stable Butane FCOS spec

`version: 1.7.0` (emits Ignition spec 3.6.0). Ignition 2.26.0 marked 3.6.0 stable. FCOS stable ships Ignition 2.27.0.

Source: https://github.com/coreos/butane/blob/main/docs/specs.md · https://github.com/coreos/ignition/blob/main/docs/release-notes.md

### `qemu-guest-agent` in FCOS

**Not shipped** (absent from the FCOS package lock). Layering packages with rpm-ostree is avoided.

Source: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/manifest-lock.x86_64.json

### Firewall on FCOS

`nftables` and `iptables-nft` ship; `firewalld` does not. `nftables.service` runs `nft -f /etc/sysconfig/nftables.conf`. It's disabled by default; Butane enables it

Source: the FCOS package lock (above) · https://src.fedoraproject.org/rpms/nftables/blob/rawhide/f/nftables.service

### sudo on FCOS

`/etc/sudoers.d/coreos-sudo-group`: `%sudo ALL=(ALL) NOPASSWD: ALL`. `wheel` uses Fedora's stock rule. Users in `sudo` get non-interactive sudo, so no sudoers drop-in is needed

Source: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/overlay.d/05core/etc/sudoers.d/coreos-sudo-group · https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/authentication.adoc

### Automatic updates

Zincati is active by default: FCOS updates itself and reboots.

Source: https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/auto-updates.adoc

### The keys Ignition writes

Ignition writes the user's SSH key to `~/.ssh/authorized_keys.d/ignition`, so that file in a key listing is the user's, not the agent's.

Source: https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/authentication.adoc
