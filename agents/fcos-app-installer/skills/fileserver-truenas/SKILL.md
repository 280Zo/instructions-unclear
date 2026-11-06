---
name: fileserver-truenas
description: "Manual steps for TrueNAS as the file server of the fcos-app-installer toolkit: letting a VM mount an NFS share, creating a service's user and folders, and creating its backup folder. Use when the user's file server or NAS is TrueNAS."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps from adapter.yaml.
---

# TrueNAS (file server)

The VM sends numbers, so UIDs and GIDs must match; names on the file
server don't matter. Show the service's generated `file-server.md` table
(folder, user, group, mode) first, then these how-to steps once. A VM's
backup folder is mode 0755 and not group-writable; each service's own backup
folder is 0750, owned by its UID and GID.

## How to use it

Never write these commands by hand. The shared renderer fills in every value,
refuses values that could change a command, and computes script checksums
itself. List the steps and the values each one needs, then render one step at a
time, with the values in a JSON file in `/tmp/opencode/`:

```fish
# desktop (fish)
python3 tools/adapters.py show --role file_server --provider truenas
python3 tools/adapters.py render --role file_server --provider truenas --step <id> --values /tmp/opencode/<id>.json
```

Show the rendered step to the user as it is, then wait for what it asks them
to report back. `HOST` is the server's key in the site file, never its display
or node name.

## Steps

| Step | What it does |
|---|---|
| `nfs_export` | Let a VM mount an NFS share |
| `service_user` | Create a service's NAS user and folders |
| `backup_folder` | Create a service's backup folder |

## Official documentation

- https://www.truenas.com/docs/scale/shares/nfs/addingnfsshares/
- https://www.truenas.com/docs/scale/26/credentials/users/manageusers/

Menu names change between versions; when one doesn't match, follow the linked documentation.
