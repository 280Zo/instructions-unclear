# 5. Rebuild a VM

A rebuild replaces the OS disk with a fresh FCOS image and boots it with the
current Ignition file. The data disk stays attached and is never wiped: the
base config sets `wipe_filesystem: false`, and every file Butane writes onto it
uses `overwrite: true`, so Ignition rewrites config files there without failing
on files that already exist.

Use it for OS-level changes (base config, firewall, users), for recovery, or to
pick up a change that can't be pushed live.

## 5.1 [Agent] Prepare

1. Rebuild the Ignition file: `bash tools/build-vm.sh <workspace>/vms/<vm>`. Expected: all checks pass.
2. Build the new config disc from it under a **new, dated name**, because the
   VM's current disc `fcos-<vm>-ign.iso` is still attached and is never
   overwritten:
   `bash tools/make_cidata_iso.sh <workspace>/vms/<vm>/<vm>.ign <workspace>/vms/<vm>/fcos-<vm>-ign-<YYYYMMDD>.iso`.
   Gap: `tools/hypervisor.py` uploads a config disc only when it creates a VM. Until
   it can upload one for an existing VM, the owner uploads that file to the
   VM's ISO storage, keeping its name, in the server's web interface. The
   rebuild step refuses a disc that is already attached, then attaches the new
   one. The old disc stays on the storage until the owner removes it from the
   ISO storage's content list in the web interface, once the rebuilt VM runs.
3. Tell the owner which services will be down, and for roughly how long (a few minutes).
4. Back up every database now and confirm the files exist:

```fish
# desktop (fish)
set vm apps
python3 tools/vmssh.py run $vm -- 'for u in /var/lib/systemd/linger/*; do s=$(basename $u); sudo -u $s XDG_RUNTIME_DIR=/run/user/$(id -u $s) systemctl --user list-unit-files "$s-backup*.service" --no-legend; done'
python3 tools/vmssh.py run $vm -- "sudo -u <svc> XDG_RUNTIME_DIR=/run/user/\$(id -u <svc>) systemctl --user start <svc>-backup-<container>.service; sudo -u <svc> ls -lt /var/mnt/backups/<vm>/<svc>/ | head -n 3"
```

If the file server is off, the backup skips. Then ask the owner to run the
virtualization server's backup of the VM now.

5. Stop the services cleanly so databases close:

```fish
# desktop (fish)
python3 tools/vmssh.py run $vm -- 'for u in /var/lib/systemd/linger/*; do s=$(basename $u); sudo systemctl stop user@$(id -u $s).service; done'
```

## 5.2 [Owner] Swap the OS disk

First download a current image (virtualization: `download_image`) and note
its file name. Then adapter step **virtualization: `rebuild_os_disk`**. It
runs as one strict script that first checks the VM's ID belongs to the VM's
name, that the data disk is there and that the image exists, and stops at the
first failed check. It detaches the old OS disk, deletes only that disk,
imports the new image, attaches the new config disc and starts the VM.

Report back: the whole output, or the STOP line.

## 5.3 [Agent] Check

1. The VM's SSH host key changed, and the new OS disk no longer has the
   agent's setup key. If the workspace still holds one for this VM, run
   `python3 tools/vmssh.py reinstall <vm>`: it drops the old pinned host key
   and prints the owner step for the same key again. Otherwise make a new one
   with `keygen` (section 2.7). Then `trust` with the new fingerprint the owner
   reports. The owner's own `ssh` also warns about the changed host key; on
   the desktop they remove the old entry with `ssh-keygen -R <vm-ip>`.
2. Run the first-boot checks (section 2.7).
3. Confirm the data survived: `python3 tools/vmssh.py run <vm> -- 'sudo ls -la /var/lib/appdata/*/'` shows the existing folders and files.
4. Podman secrets live in each service user's home on the OS disk, so they are gone after a rebuild. The owner creates them again (section 3.8) with the same values from the password manager. A database password or signing key must be the same value, because the data on the kept data disk still expects it. Then the agent starts the services.
   If a database password is lost, set a new one inside the database first (Postgres: `sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman exec -i <svc>-<container> psql -U <pg user> -d <pg db> -c "ALTER ROLE <pg user> PASSWORD '<new>'"`, with the Postgres user and database from the service's spec or the site file, then keep `<new>` in the password manager and create it as the secret).
5. Run each service's verification checklist (section 3.10).
