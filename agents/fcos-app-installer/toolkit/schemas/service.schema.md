# Service spec (`service.yaml`) field reference

One file per service, kept in the workspace (`services/<name>/service.yaml`).
`python3 tools/gen_service.py service.yaml site.yaml <out-dir>` checks it and
writes the Quadlets, Butane fragments and `secrets.md`. Nothing is written
unless the whole spec is valid. Unknown fields are errors.

Host network values (VM address, bridge, VLAN) and storage never appear here
and are never defaulted: they come from `site.yaml`, and a missing one is an
error that names it.

## Service

| Field | Required | Meaning |
|---|---|---|
| `name` | yes | Lowercase letters, digits, hyphens; starts with a letter; at most 31. Also the Linux user and the folder under the data disk. |
| `vm` | yes | A VM listed in `site.yaml` (`vms`). |
| `uid` | yes | 1000-24608 (the IDs whose pinned container ID ranges fit below the IDs systemd reserves). Must match the file server user if the service uses NFS. Unique across the workspace (`tools/check_workspace.py`). |
| `gid` | no | Defaults to `uid`. Same range and uniqueness as `uid`. |
| `extra_groups` | no | Shared groups the user joins (names only). |
| `title`, `description` | no | Plain text. `title` defaults to `name`. |
| `login` | yes | `gateway` (route and rules behind the login page) or `app-only` (needs `login_reason`, one sentence; with a `hostname` it gets an HTTPS route without the login page and a dashboard link on the auth gateway, without one no route). |
| `hostname` | with `gateway`; optional with `app-only` | One name under the site domain (no dots). Needs a container that publishes. |
| `api_paths` | no | Regular expressions for paths clients call directly (skip the login). Must compile. |
| `port` | with a publisher | Host port, 1024-65535. |
| `bind` | no | `vm_ip` (default; the VM's address from `site.yaml`) or `loopback` (`127.0.0.1`, no firewall port). |
| `containers` | yes | One or more containers, below. |
| `secrets` | if any container uses one | `{name, durable, source}` per secret. |
| `backups` | no | `{schedule, keep}`. `schedule`: `daily`, `weekly` (Sunday) or an `OnCalendar` time; the time of day comes from `site.yaml` `backups.oncalendar`. `keep` falls back to `site.yaml` `backups.keep`. |
| `accepted_risks` | no | Sentences that waive a check. A sentence must **start** with the phrase, a colon and a reason (case doesn't matter): `over the 5 GB rule: ...` waives the size rule; `no backups: ...` waives the missing backup share. Free text, so accented letters are allowed (like `description` and `login_reason`); every other field is ASCII only. |

## Container

| Field | Meaning |
|---|---|
| `name` | Same rules as the service name. Not `files`, `network` or starting with `backup`. The container is `<service>-<name>`. |
| `image` | `registry/name:tag`, pinned to a version, never `latest`; `@sha256:` digest optional after the tag. |
| `user_mode` | `map-user`: `UserNS=keep-id`, no added capabilities, may use NFS. `root-start`: for images that start as root and drop privileges; no `UserNS=`, `DropCapability=ALL` plus only the listed `add_capabilities` (from `CHOWN DAC_OVERRIDE FOWNER SETUID SETGID NET_BIND_SERVICE`), no NFS volumes. Containers sharing a `local` folder must use the same `user_mode`. |
| `add_capabilities` | `root-start` only. |
| `publish` | Container port. At most one container in the service. |
| `command` | List of arguments (`Exec=`). |
| `shm_size_mib` | Optional: size of `/dev/shm` in MiB (`ShmSize=`), 1-65536, when the app's official docs ask for it. |
| `depends_on` | Container names; becomes `Requires=` and `After=`. No cycles. |
| `env` | `{NAME: value}`. Names `[A-Z_][A-Z0-9_]*`; one-line values. Secret-looking values are refused. |
| `secrets` | `{ENV: secret_name}` or a list of `{env, name}`. |
| `network` | `private` (default: the service's `.network`; containers reach each other as `<service>-<container>`) or `host`. Host is only for the login front end's proxy; it cannot publish. |
| `volumes` | List, below. |

Every container also gets `NoNewPrivileges=true`, `DropCapability=ALL`,
`AutoUpdate=registry` and a mount check before start.

## Volume

| Field | Meaning |
|---|---|
| `path` | Container path: absolute, normalized, no `..`, spaces or colons. No volume may sit inside another. |
| `read_only` | Optional `true` for `local` and `nfs`: mounted read-only (`:ro,z`, NFS `:ro`). Not for `local-db`. |
| `class` | `local` (data disk, backed up as files), `local-db` (data disk, backed up by `engine`), `nfs`. |
| `expected_gib` | Required for `local` and `local-db`. Shared folders count once; the total above 5 GB is refused. |
| `name` | `local` only: folder name; defaults to the path with `/` replaced by `-`. A folder shared by two containers uses the same name or path. |
| `host` | `nfs` only: `/var/mnt/<share>/...`; the share must be listed for the VM in `site.yaml`. No label option is added. |
| `engine` | `local-db` only: `sqlite` (needs `file`), `postgres` (`pg_dump -Fc`, user and database from `POSTGRES_USER` and `POSTGRES_DB`), `mariadb` or `mysql` (`mariadb-dump --single-transaction` inside the container with its own `MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`; the official `mysql` image has neither the tool nor those variables, so use `custom` for it), `custom` (needs `command`: one line that prints the dump). One `local-db` volume per container. |

## Secret

| Field | Meaning |
|---|---|
| `name` | Lowercase letters, digits, underscores. Every secret must be used, and every used one declared. |
| `durable` | `true` for values data depends on (database passwords, signing keys). `secrets.md` marks it: save the value in your password manager; a rebuild must re-enter the same value. |
| `value` | What the owner enters, on one line, as the app's docs describe it (e.g. `base64:` followed by 32 random bytes in base64). Shown in `secrets.md`'s table; default "a long random value, no spaces". Never a value itself. |
| `source` | `generate` (random, on the VM, never shown) or `prompt` (hidden prompt). Default `generate`, or `prompt` when `durable`; a durable secret can't be `generate`. |

## Output

`<out>/rendered/files/<service>-<container>.container`, `<service>.network`,
`<out>/rendered/<service>.bu`, `<service>-port.bu` (unless `bind: loopback`),
`<service>-backup-<container>.bu` per `local-db` volume,
`<service>-backup-files.bu` if any `local` volume, `<service>-route.bu` plus
route and gateway rules files when `login: gateway`, `<out>/secrets.md` (a table of the secrets, then
the commands), `<out>/ids.md`, `<out>/backups.md` (what is backed up, when, where, how to restore) and
`<out>/file-server.md` (one table of the folders to make on the
file server: user, group, mode).
