# Facts the Proxmox adapter relies on

Each fact comes from the official source linked under it, not from memory. Re-check a fact when its source changes, and add a new one here, with its link, when you start relying on it.

## The FCOS image for Proxmox

Current stable `proxmoxve` image: 44.20260928.3.2, format `qcow2.xz`.

Source: https://builds.coreos.fedoraproject.org/streams/stable.json

## Guest agent and shutdown

The templates leave the guest agent off (`--agent 0`). Proxmox shuts a VM down through ACPI, which FCOS handles. (FCOS does not ship `qemu-guest-agent`; see the guide's FCOS facts.)

Source: the FCOS package lock linked in the guide's FCOS facts

## Replace `scsi0`, keep `scsi1`

`qm set <id> --delete scsi0` makes the old disk `unused0`. `qm disk unlink <id> --idlist unused0` removes it. `qm set <id> --scsi0 <storage>:0,import-from=<path-to-qcow2>,iothread=1,discard=on` imports the new image. Then `qm resize <id> scsi0 <size>` and `qm set <id> --boot order=scsi0`. `scsi1` is never named, so it stays attached

Source: https://pve.proxmox.com/pve-docs/qm.1.html · https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/provisioning-proxmoxve.adoc

## Uploading a config ISO through the API

`POST /nodes/{node}/storage/{storage}/upload`, multipart/form-data: text field `content` = `iso` (enum `iso`, `vztmpl`, `import`) and the file as the part named `filename` (the API normalizes the name). Returns a task id. Needs **`Datastore.AllocateTemplate`** on `/storage/{storage}`. Listing the ISOs already there (`GET .../content?content=iso`) needs `Datastore.Audit` or `Datastore.AllocateSpace` there. `GET /access/permissions?path=/storage/<id>` shows the token's effective privileges.

Source: https://pve.proxmox.com/pve-docs/api-viewer/ (data file `apidoc.js`, paths `/nodes/{node}/storage/{storage}/upload`, `.../content`, `/access/permissions`)

## Ignition from an uploaded NoCloud ISO; VM creation with the pool-scoped token (tested on Proxmox VE 9.2 with the FCOS stable `proxmoxve` image 44.x)

**Works.** A `cidata` ISO (`user-data` = Ignition JSON, empty `meta-data`) on `ide2` as a CD-ROM is read on first boot (`ignition.platform.id=proxmoxve`; Afterburn mounts it): the user, SSH key and files were created. `POST /nodes/{node}/qemu` with `scsi0: <storage>:0,import-from=<iso-storage>:import/<image>.qcow2` succeeded with only the token's rights (role on the pool, `PVEDatastoreUser` on the disk storage, `Datastore.AllocateTemplate Datastore.Audit` on the ISO/import storage, `SDN.Use` on the bridge). On 9.2, `GET /cluster/resources` omits a guest's `pool` field for a caller without **`Pool.Audit`** on that pool, so `tools/virtualization/proxmox.py` reads membership from `GET /pools?poolid=<pool>` (needs `Pool.Audit`, read-only). The Proxmox adapter's default Ignition delivery is therefore the uploaded ISO

Source: Tested on a real Proxmox node · https://pve.proxmox.com/pve-docs/api-viewer/ (`/nodes/{node}/qemu`, `/pools`) · https://pve.proxmox.com/pve-docs/pveum.1.html (privileges)

## Console on the `proxmoxve` image

Image defaults: kernel `console=tty0 console=ttyS0,115200n8` (ttyS0 is the interactive console) and GRUB on serial; Fedora's Proxmox guide uses `--serial0 socket --vga serial0` and `qm terminal`. Confirmed on the VM (`/proc/cmdline`, `serial-getty@ttyS0` active). On the test node `qm terminal <id>` stayed silent even with Enter; SSH is the working way in

Source: https://github.com/coreos/fedora-coreos-config/blob/testing-devel/platforms.yaml · https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/provisioning-proxmoxve.adoc · https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/emergency-shell.adoc

## Hostname with the ISO delivery

With an empty `meta-data`, nothing sets a name: the VM came up as `localhost`. With `/etc/hostname` written by Ignition (as the base template does), the VM booted normally (`systemctl is-system-running` = `running`, no emergency shell) and used that name. A forum report says a Butane-written `/etc/hostname` drops FCOS into the emergency shell when Proxmox's own cloud-init drive supplies the VM name; that path (snippet + cloud-init drive) was **not tested** and is not the default

Source: Tested on a real Proxmox node

## An address reservation before first start

A VLAN whose DHCP serves only reserved MACs needs the reservation before first start; the MAC is known only after the VM is created, so the order is create (stopped), reserve, start.

Source: Tested on a real Proxmox node

## Teardown: pools

A Proxmox resource pool is a set of VMs, containers and storages, useful for permission handling. The teardown script moves the agent's VMs into a pool the user names and creates it with `--create-pool` (its own usage text; run on a real server, both servers).

Source: https://pve.proxmox.com/pve-docs/chapter-pveum.html (Resource Pools) · `.opencode/skills/adapter-proxmox/scripts/teardown-agent-access.sh`
