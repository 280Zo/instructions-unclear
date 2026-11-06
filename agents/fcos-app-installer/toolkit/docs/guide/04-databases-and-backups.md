# 4. Databases and backups

Any service whose spec has a `local-db` volume follows this page. That covers
SQLite in WAL mode, Postgres and MariaDB, plus a `custom` engine
with its own dump command.

## Why databases stay off NFS

SQLite's documentation says WAL mode doesn't work over a network filesystem,
because WAL needs shared memory between the processes using the database.
Postgres and MariaDB on NFS have similar locking and caching risks. A dropped
NFS connection can corrupt any of them. So the database lives on the VM's data
disk, and the file server gets copies. The only exception is an accepted risk
the owner agreed to under the 5 GB rule.

## The process

1. **Keep the database on the data disk**, under
   `/var/lib/appdata/<svc>/db/<container>/`. The container mounts it with `:z`.
2. **Back it up while it runs**, one backup unit per database volume, chosen
   by `engine` (`tools/gen_service.py` writes `<svc>-backup-<container>.bu`):
   - `sqlite`: Python's `sqlite3` online backup API in the official
     `python:3-alpine` image. The copy is consistent and includes changes
     still in the WAL file; copying the file with `cp` could catch it halfway
     through a write. FCOS has no `sqlite3` binary, which is why it uses Python.
   - `postgres`: `pg_dump -Fc` inside the running database container through
     `podman exec`, with the user and database from its `POSTGRES_USER` and
     `POSTGRES_DB`.
   - `mariadb` (or `mysql` for MariaDB images): `mariadb-dump
     --single-transaction` inside the container, with its own `MARIADB_*`
     settings.
   - `custom`: the one-line dump command from the spec.
3. **Write to the file server** at `/var/mnt/backups/<vm>/<svc>/`, with a UTC
   timestamp in the name. Each run keeps the newest `keep` files.
4. **Skip when the file server or the data disk is missing.** Each backup runs
   `ExecCondition=/usr/local/bin/require-mounts /var/mnt/backups /var/lib/appdata`.
   When either isn't really mounted, systemd marks the run as skipped, not
   failed, and logs `require-mounts: <path> is not mounted`. Checking the data
   disk too means a missing disk can never produce an empty backup that would
   push good ones out of the rotation.
   `Persistent=true` on the timer runs a missed backup at the next boot.
5. **The virtualization server's own backups** of the data disk (section 1.5)
   are the copy that works while the file server is away.
6. **Before any rebuild**: stop the service, run its backup by hand, confirm
   the new file exists, then rebuild. Rebuilds keep the data disk, so the
   database should never need restoring; the backup covers mistakes.

`local` data (files on the data disk that aren't a database) gets a files
backup: `<svc>-backup-files.bu`, a tarball of `/var/lib/appdata/<svc>/`
without `db/`, made with `podman unshare` so files owned by sub-IDs are
readable.

## Check a backup

```fish
# desktop (fish)
set vm <vm>; set svc <svc>; set ctr db
python3 tools/vmssh.py run $vm -- "sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user start $svc-backup-$ctr.service; sudo -u $svc ls -lt /var/mnt/backups/<vm>/$svc/ | head"
python3 tools/vmssh.py logs $vm $svc-backup-$ctr.service -n 20
```

Expected: the run finishes without errors and a new file is at the top of the
list. With the file server off, the journal shows the skip message instead.

## Restore (only if the data disk is lost)

Restore from the newest virtualization-server backup of the VM first; it
brings the whole data disk back. Use the file server's copies only if that
fails.

SQLite:

```bash
# vm <vm> (bash, <admin>)
sudo systemctl --user -M <svc>@ stop <svc>-<container>.service
sudo -u <svc> ls -t /var/mnt/backups/<vm>/<svc>/ | grep '\.sqlite$' | head -n 1
sudo -u <svc> cp /var/mnt/backups/<vm>/<svc>/<newest>.sqlite /var/lib/appdata/<svc>/db/<container>/<db-file>
sudo -u <svc> rm -f /var/lib/appdata/<svc>/db/<container>/<db-file>-wal /var/lib/appdata/<svc>/db/<container>/<db-file>-shm
sudo systemctl --user -M <svc>@ start <svc>-<container>.service
```

Postgres (the database must exist and be empty; `<pg user>` and `<pg db>` are its Postgres user and
database from the service's spec or the site file; `<app units>` are the units that use the database,
not the database's own):

```bash
# vm <vm> (bash, <admin>)
sudo systemctl --user -M <svc>@ stop <app units>
sudo -u <svc> ls -t /var/mnt/backups/<vm>/<svc>/ | grep '\.dump$' | head -n 1
sudo -u <svc> cat /var/mnt/backups/<vm>/<svc>/<newest>.dump | sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman exec -i <svc>-<container> \
    pg_restore --clean --if-exists -U <pg user> -d <pg db>
sudo systemctl --user -M <svc>@ start <app units>
```

For the login front end's auth gateway the units and names are in its `operations.md`, "Restoring the
database".

MariaDB. The dump has a `DROP TABLE IF EXISTS` before every
table and no `CREATE DATABASE` (`mariadb-dump` enables `--opt` by default;
checked in a real dump), so loading it into the existing database replaces its
tables. Loading it into a live database is **not tested** here; the throwaway
test below is.

```bash
# vm <vm> (bash, <admin>)
cd /
U="sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid>"
$U systemctl --user stop <svc>-app.service <svc>-cron.service
f=$(sudo -u <svc> ls -1t /var/mnt/backups/<vm>/<svc>/ | grep '^db-.*\.sql\.gz$' | head -n 1); echo "$f"
sudo -u <svc> gunzip -c /var/mnt/backups/<vm>/<svc>/$f | $U podman exec -i <svc>-db sh -c 'mariadb "-u$MARIADB_USER" "-p$MARIADB_PASSWORD" "$MARIADB_DATABASE"'
$U systemctl --user start <svc>-app.service <svc>-cron.service
```

Then run the service's verification checklist (section 3.10).

## Test a restore

Proves a backup restores, without touching anything live. Run it once after a
database service's first backups, and again after big changes. It starts a
throwaway MariaDB from the same image the service uses, with no network and its
data in memory (`--tmpfs`), loads the newest dump, and compares counts with the
live database. It prints counts and file names only, never rows, so nothing
personal reaches the agent.

```bash
# vm <vm> (bash, <admin>)
cd /
U="sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid>"
dir=/var/mnt/backups/<vm>/<svc>
trap '$U podman rm -f restore-test >/dev/null 2>&1' EXIT
$U systemctl --user start <svc>-backup-<ctr>.service <svc>-backup-files.service
db=$(sudo -u <svc> ls -1t $dir | grep '^db-.*\.sql\.gz$' | head -n 1)
files=$(sudo -u <svc> ls -1t $dir | grep '^files-.*\.tar\.gz$' | head -n 1)
sudo -u <svc> gzip -t $dir/$db && sudo -u <svc> gzip -t $dir/$files && echo "both archives are intact"
$U podman run -d --name restore-test --network none --tmpfs /var/lib/mysql \
  -e MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1 -e MARIADB_DATABASE=<database> <the service's MariaDB image> >/dev/null
for i in $(seq 60); do $U podman logs restore-test 2>&1 | grep -q "init process done" && break; sleep 2; done
for i in $(seq 60); do $U podman exec restore-test mariadb-admin ping --silent 2>/dev/null && break; sleep 2; done
sudo -u <svc> gunzip -c $dir/$db | $U podman exec -i restore-test mariadb -uroot <database>
q="select count(*) from information_schema.tables where table_schema='<database>'; select count(*) from <a main table>;"
$U podman exec restore-test mariadb -uroot <database> -N -e "$q"
$U podman exec <svc>-<ctr> sh -c 'mariadb "-u$MARIADB_USER" "-p$MARIADB_PASSWORD" "$MARIADB_DATABASE" -N -e "$0"' "$q"
sudo -u <svc> tar -tzf $dir/$files | wc -l
```

The loop waits for the image's line `MariaDB init process done` (its entrypoint
starts a temporary server first and stops it; loading before that line hits the
temporary server). The two count lines must be equal. The run removes the
throwaway container when it ends. The files archive of a service can hold
credentials, such as an app's own key files and its logs, so keep its folder on
the file server readable by the service's account only (mode 0750 or 0700).

## How SQLite backups run

This is a design choice, not a fact from a source. FCOS doesn't ship `sqlite3`, and app images may
not include it. SQLite backups run Python's `sqlite3.Connection.backup()` (the online backup API) in
the official `docker.io/library/python:3-alpine` image, mounting the database read-write and the
file-server folder.

## Facts the restore test relies on

Each fact comes from the official source linked under it, not from memory. Re-check one when its source changes.

### MariaDB restore and its test (MariaDB 11 image, on a real install)

The image needs one of `MARIADB_RANDOM_ROOT_PASSWORD`, `MARIADB_ROOT_PASSWORD`, `MARIADB_ROOT_PASSWORD_HASH` or `MARIADB_ALLOW_EMPTY_ROOT_PASSWORD` (the empty one is fine for a throwaway with no network). The entrypoint starts a temporary server for initialization and logs `MariaDB init process done. Ready for start up.` when it stops it. `mariadb-dump` enables `--opt` by default; the real dump had a `DROP TABLE IF EXISTS` per table (95) and no `CREATE DATABASE`. Loading that dump into a throwaway server restored the same counts as the live database. Loading into a live database was not tested

Source: https://raw.githubusercontent.com/docker-library/docs/master/mariadb/README.md · https://raw.githubusercontent.com/MariaDB/mariadb-docker/master/docker-entrypoint.sh · https://mariadb.com/docs/server/clients-and-utilities/backup-restore-and-import-clients/mariadb-dump
