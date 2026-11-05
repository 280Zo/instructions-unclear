# 2. Build a VM

Builds a new FCOS VM with the base config, its NFS shares and the firewall.
No services yet; those come from [section 3](03-add-a-service.md). Host setup
([section 1](01-host-setup.md)) must be done on the target server.

## 2.1 Ask the owner

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

## 2.2 [Owner] File server: allow the VM on each export

For each share: adapter step **file_server: `nfs_export`**. The VM's own
folder in the backups share comes with its first service
(file_server: `backup_folder`, section 3.5).

Report back: done, plus any export path that differs from the site file.

## 2.3 [Agent] Write the VM spec

`<workspace>/vms/<vm>/vm.yaml`, every value from the site file and the
owner's answers, none assumed.

**Every VM setting is decided, never left to a default.** Research the
server's facts (discovery: CPU and its flags, NUMA nodes, disk type, memory
free with every guest running, other VMs' start order) and the official
guidance (the virtualization platform's VM documentation, the FCOS guide for
that platform, each app's requirements). Then fill `settings:` with every
setting below, each with the value to use, why, and the source. The
platform's tool refuses a spec where one is missing, unexplained or out of
range, and its dry run prints them all as a table. Show that table to the
owner; the values are used unless the owner changes them.

**Providers.** For Proxmox VE the settings below are what `tools/pve.py`
checks and sends; the official sources are the Proxmox VE VM chapter and the
FCOS Proxmox guide, linked in the Proxmox adapter skill (`adapter-proxmox`).

```yaml
name: <vm>
host: <host>
vmid: <vmid>
cores: 2
ram_mib: 3072
os_disk_gib: 30
data_disk_gib: 10
storage: <disk storage>
bridge: <bridge>
vlan_tag: <vlan or null>
mtu: <mtu or null>
image_volume: <iso storage>:import/<image file>
ignition:
  method: nocloud-iso   # the adapter's default; snippet is the fallback
settings:               # each one: {use: <value>, why: <one line>, source: <doc or discovery>}
  cpu: {use: host, why: "one server, no live migration; exact host CPU and flags", source: "platform VM docs"}
  cpu_flags: {use: [], why: "type host already passes every host flag", source: "platform VM docs"}
  sockets: {use: 1, why: "host has one socket", source: "discovery"}
  numa: {use: false, why: "host has one NUMA node", source: "discovery; platform VM docs"}
  cpuunits: {use: 100, why: "equal CPU share with the other VMs", source: "platform VM docs"}
  cpulimit: {use: 0, why: "no cap", source: "platform VM docs"}
  balloon: {use: "on", why: "keep the device with no minimum; fixed size, use reported", source: "platform VM docs"}
  allow_ksm: {use: true, why: "shares identical pages on a small host", source: "platform VM docs"}
  bios: {use: seabios, why: "OVMF mainly for PCIe passthrough", source: "platform VM docs"}
  machine: {use: pc, why: "Q35 mainly for PCIe passthrough; newest machine version at each start, fine for Linux", source: "platform VM docs"}
  disk_cache: {use: none, why: "balance of safety and speed", source: "platform VM docs"}
  disk_aio: {use: io_uring, why: "the platform's default", source: "platform VM docs"}
  discard: {use: true, why: "thin storage gets freed space back", source: "platform VM docs"}
  ssd: {use: true, why: "the disk under the storage is an SSD", source: "discovery (ROTA 0)"}
  nic_model: {use: virtio, why: "best performance, lowest overhead", source: "platform VM docs"}
  nic_queues: {use: 2, why: "multiqueue equal to the vCPUs", source: "platform VM docs"}
  nic_firewall: {use: false, why: "the VM's own nftables filters", source: "base template"}
  rng: {use: urandom, why: "avoids entropy starvation at boot", source: "platform VM docs"}
  tablet: {use: false, why: "serial console, no VNC mouse", source: "platform VM docs"}
  hotplug: {use: "network,disk,usb", why: "the platform's default", source: "platform VM docs"}
  startup_order: {use: null, why: "starts after VMs that have an order (the router: owner step); setting one needs Sys.Modify on the whole server", source: "platform VM docs; qemu-server permission check"}
  startup_up: {use: null, why: "no extra delay needed", source: "platform VM docs"}
  onboot: {use: true, why: "starts with the server", source: "owner"}
  protection: {use: true, why: "no accidental deletion", source: "platform VM docs"}
  agent: {use: false, why: "no guest agent in FCOS yet", source: "FCOS package list"}
  watchdog: {use: none, why: "nothing in the VM would feed it", source: "platform VM docs"}
  acpi: {use: true, why: "clean shutdown", source: "platform VM docs"}
  kvm: {use: true, why: "hardware virtualization", source: "platform VM docs"}
  localtime: {use: false, why: "Linux keeps UTC", source: "platform VM docs"}
  tags: {use: [fcos-agent], why: "easy to spot", source: "owner"}
  description: {use: "<what this VM runs>", why: "easy to spot", source: "owner"}
```

If a VM must start after another one on the server (the router that serves
its address, the file server), give that one a start order (for example 1,
with a startup delay) as an owner step in the platform's web interface. The
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
`<vm>.ign`, which is where `tools/pve.py` looks for it.

## 2.5 [Agent] Create the VM, stopped

```fish
# desktop (fish)
python3 tools/pve.py create <workspace>/vms/<vm>/vm.yaml --host <host> --workspace <workspace> --dry-run
```

Before anything is sent (dry run included), `pve.py` reads the server's
network list and refuses a bridge other than the host's `bridge` (the token's
permissions refuse it too; an optional `forbidden_bridges` list is honored but
never asked), a VLAN on a bridge that isn't VLAN-aware or doesn't allow it,
and a network card MTU above the bridge's. A bridge that doesn't report
which VLANs it allows only gives a warning: tell the owner, who checks it on
the server. A refusal goes to the owner as it is; never change the owner's
network to get past it.

Show the owner the dry run's exact steps (upload the config disc, create the
VM in the agent's pool with protection on, grow the OS disk) and ask before
running it without `--dry-run`. The VM is created stopped, and `pve.py`
prints its network card's `MAC address:` for 2.6 (`pve.py status` shows it
again).

## 2.6 [Owner] Router: reserve the address

Adapter step **router_firewall: `reserve_ip`**, after the VM is created and
before its first start. On a network that only serves reserved MAC addresses
the VM gets no address at all without it. If the VM sits on a different
network from the file server or the login front end, also
**router_firewall: `allow_flows`**.

Report back: done, and the reserved address if it differs.

**[Owner] The desktop's route to the VM, when needed.** The agent runs on the
owner's desktop, so it checks the desktop's own networks first (read-only):
`ip -4 -br addr`. If the desktop has an address on the VM's network that is
not one of the VM's SSH or web sources, it reaches the VM directly from that
address and the VM's firewall drops it. The owner then adds a permanent route
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

The agent never uses the owner's SSH key. It works on the VM with its own
setup key, which the owner adds beside theirs and which is revoked when the
services work (3.10). The private key stays in the workspace's `secrets/`
folder; `tools/vmssh.py` runs ssh with only that key (no ssh config, no
ssh-agent).

1. Start the VM and make the key:

   ```fish
   # desktop (fish)
   python3 tools/pve.py start <vmid> --host <host> --workspace <workspace>
   python3 tools/vmssh.py keygen <vm> --workspace <workspace>
   ```

2. **[Owner]** The key command prints the owner step, with the public key
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
`tools/pve.py status` shows whether the VM is running. The owner can see in
the virtualization platform's own view whether it has read from its disks and
sent network traffic; a VM that read hundreds of MB and sent packets has
booted. The serial console is not a proven fallback yet (see
[section 8](08-break-glass.md)).

**If `/var/lib/appdata` isn't mounted,** Ignition didn't find the data disk
under `/dev/disk/by-id/scsi-0QEMU_QEMU_HARDDISK_drive-scsi1`. Check the
`by-id` name on the VM, fix the device path in the base template, and rebuild
([section 5](05-rebuild-a-vm.md)).
