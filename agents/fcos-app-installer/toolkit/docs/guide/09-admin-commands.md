# 9. Admin commands

**[Owner]** These are the owner's commands, with their own SSH key; the agent
reaches a VM only through `tools/vmssh.py` (section 2.7).

Adapted from the owner's FCOS notes for rootless services. Every service runs under
its own user, so most commands name that user. `<svc>` is the service user,
`<uid>` its UID, `<ctr>` one of its containers: each container is the unit
`<svc>-<ctr>.service` and the container `<svc>-<ctr>`.

## Log in

```fish
# desktop (fish)
ssh <admin>@<vm-ip>
```

After a rebuild the host key changes: `ssh-keygen -R <vm-ip>`, then log in again.

## Service status and logs

```bash
# vm <vm> (bash, <admin>)
sudo systemctl --user -M <svc>@ status '<svc>-*.service'
sudo systemctl --user -M <svc>@ restart <svc>-<ctr>.service
sudo journalctl _SYSTEMD_USER_UNIT=<svc>-<ctr>.service -f
sudo systemctl --user -M <svc>@ list-timers
```

## Containers

```bash
# vm <vm> (bash, <admin>)
cd /
sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman ps
sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman logs -f <svc>-<ctr>
sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman exec -it <svc>-<ctr> /bin/sh
sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman auto-update --dry-run
```

## Storage and mounts

```bash
# vm <vm> (bash, <admin>)
findmnt /var/lib/appdata
/usr/local/bin/require-mounts /var/lib/appdata /var/mnt/<share> && echo ok
df -h /var/lib/appdata
```

## Firewall

```bash
# vm <vm> (bash, <admin>)
sudo nft list table inet host_filter
sudo systemctl reload nftables
```

## OS updates

FCOS updates itself with Zincati and reboots only inside the window in
`/etc/zincati/config.d/55-updates-strategy.toml`.

```bash
# vm <vm> (bash, <admin>)
sudo systemctl status zincati
rpm-ostree status          # two deployments = an update is staged for the next window
sudo rpm-ostree rollback   # boot back into the previous version (then reboot)
```

## SELinux denials

```bash
# vm <vm> (bash, <admin>)
sudo ausearch -m avc -ts recent
```

A denial on an NFS path usually means `virt_use_nfs` is off
(`getsebool virt_use_nfs`) or someone added `:Z`/`:z` to an NFS volume.
