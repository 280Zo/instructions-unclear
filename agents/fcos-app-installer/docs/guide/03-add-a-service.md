# 3. Add a service

The core procedure. The result:
- the service's fragments are part of its VM's `config.bu`, so the next rebuild includes it
- the running VM gets the same files now, so only this service starts
- the login front end routes `https://<hostname>.<domain>` to it, behind the login page (or, for a service on its own login, without it)

The VM must already exist ([section 2](02-build-a-vm.md)). The login front end
must exist for 3.9 ([section 6](06-edge-vm.md)). Until it does, stop after 3.8
and reach the service with the break-glass tunnel ([section 8](08-break-glass.md)).

## 3.1 Ask the owner: where it goes

[Questions](questions.md) 5, 6 and 9: which server and which VM (always
asked), and whether it goes behind the login page. A service on its own login
(`login: app-only`, with the reason) and a `hostname` gets an HTTPS address
without the login page; without a `hostname` it gets no address (internal
only, reachable through the break-glass tunnel). Also: which app, and is it
new or does it reuse existing data on the file server (a migration)?

## 3.2 [Agent] Research the app

Load the skill **`researching-apps-for-self-hosting`** and follow it: it says
which facts to find, from which official sources, and how to label a gap.
Write the results, each with its source, into
`<workspace>/services/<svc>/research.md`. What the app prints at start says
what its log will hold: the agent reads logs only through `vmssh.py logs`,
which hides secret-looking text. Then each fact goes into the spec:

| Fact | Goes to (service spec) |
|---|---|
| Image on its official registry, pinned to a major-version tag (never `latest`) | `containers[].image` |
| Each container the app needs (app, worker, database) and their order | `containers[]`, `depends_on` |
| Port each container listens on | `publish` (one container only), `port` |
| Every path it writes: config, data, cache, database | `volumes[]` |
| Database engine and file | `class: local-db`, `engine`, `file` |
| Settings (environment, command) | `env`, `command` |
| Secrets (API keys, passwords, signing keys), and which must stay the same after a rebuild | `secrets[]` (names only), `durable` |
| Whether the image starts as root inside the container | `user_mode` |
| Shared memory or read-only folders the docs ask for | `shm_size_mib`, `read_only` |
| Paths desktop or mobile clients call without a browser | `api_paths` |
| Mail the app sends (reminders, invitations): its mail driver, and the sender address that driver needs | `env` |

If a fact isn't in the official docs, ask (question 14) instead of guessing.

**Apps that send mail.** Nothing here uses an email server (owner decision:
never an email server). Set the app's mail driver to its log driver, so what it
would send is written to its log. Many apps still refuse to build a message
without a sender address: Monica's invitations failed with "An email must have
a From or a Sender header" until `MAIL_FROM_ADDRESS` was set. Give the app a
sender address on the owner's domain (nothing is sent from or to it), and find
in its docs which log file holds the mail. A link in such a mail can be a
credential (an invitation lets someone join): the owner reads it from the log
on the VM, and the agent does not.

**Ask who may open it** (apps behind the login page). Authentik lets every
user open an app that has no bindings, so ask which groups get it (for
example `family`, `guests`) and put them in `groups:`. The login front end's
rules file `access.yaml` creates each group if it's missing (the one place
that does) and binds it to the app. Tell the owner to
add themselves (and anyone else) to the group in Authentik's admin interface
(**Directory → Groups**), or they lose access too. Group names are lowercase;
if the owner already has a group with capital letters, a new lowercase one is
made beside it. Removing a group from `groups:` later doesn't remove its old
binding; the owner deletes it under the application's **Policy / Group / User
Bindings**. Such an app also refuses everyone until its group bindings exist (a
`deny-until-bound` policy); that relies on the application's policy engine
mode staying **any** (Authentik's default): switching it to **all** in the
admin interface would lock everyone out. An app on its own login can't take `groups:`: its route skips the
login page, so a binding would only hide its dashboard link. Also ask whether
anyone new needs an account for it: they go into the site file's `people:`
(guide 6.10).

**The app's dashboard section.** Authentik's dashboard lists apps under
section headings, all on one page: each application's `group` becomes a
heading over its apps (authentik's `web/src/user/LibraryPage/ApplicationList.ts`).
Propose a section from what the app is for (Monica, a relationship manager:
`Relationships`), reuse an existing section when the app fits one, ask the
owner, and put it in `section:`. Apps with the same section are listed
together; without one, an app is listed under "Ungrouped".

**The app's logo.** Find it in the app's official repository or website (an
SVG or PNG the project publishes), save it as
`<workspace>/services/<svc>/<file>`, show it to the owner, and use it as
`icon:` once they confirm; the owner may give their own file instead. The
login front end stores it on the VM and Authentik serves it itself, so no
browser fetches it from the internet
([File picker values](https://docs.goauthentik.io/customize/file-picker/)).

## 3.3 [Agent] Classify storage and apply the 5 GB rule

For each path:
- A database (SQLite, Postgres, MariaDB) → `local-db`. Never NFS.
- State the app needs while the file server is off, or small config → `local`.
- Project files, media, large data → `nfs` under `/var/mnt/<share>/...`.

Add up the expected size of `local` and `local-db`. **At 5 GB or less**,
continue. **Over 5 GB**, stop and ask (question 12): grow the VM's data disk,
or store it on NFS with the risk recorded as an accepted risk that starts with
`over the 5 GB rule:` and gives the reason and date. For a database, say
plainly that it can corrupt on NFS.

Images that start as root inside the container (question 13) use
`user_mode: root-start` with only the capabilities their docs need, from
`CHOWN DAC_OVERRIDE FOWNER SETUID SETGID NET_BIND_SERVICE`. They can't use
NFS volumes, and can't share a folder with a `map-user` container.

## 3.4 Ask the owner: identity and naming

[Questions](questions.md) 10, 11 and 15: paths that skip the login page,
the UID/GID (matching the file server account when it uses NFS), and the
secrets the owner keeps. Hostname defaults to the service name.

## 3.5 [Owner] File server: account and folders

Only for services that use NFS or back up to the file server. The agent
writes the spec and runs the generator first (3.6), then shows the one table
in `<workspace>/services/<svc>/file-server.md`: every folder to make, with its
user, group and mode. Below it, once, the adapter's how-to for the product:
**file_server: `service_user`** and **file_server: `backup_folder`**.

Report back: done, and the exact paths.

## 3.6 [Agent] Write the spec and generate

Write `<workspace>/services/<svc>/service.yaml`
([field reference](../../schemas/service.schema.md)), then:

```fish
# desktop (fish)
set ws <workspace>; set svc monica
python3 tools/check_workspace.py $ws; and python3 tools/gen_service.py $ws/services/$svc/service.yaml $ws/site.yaml $ws/services/$svc; and bash tools/build-vm.sh $ws/services/$svc/rendered
```

`check_workspace.py` refuses a name, UID, GID, web name or port (on the same
VM) that another service or the login front end already uses. Each clash is
one line; pick a free value with the owner (UID/GID: [question](questions.md)
11) and run it again. The generator refuses the whole spec if anything is
wrong, and writes nothing. Expected: `build-vm: all checks passed`. It writes, under
`<workspace>/services/<svc>/rendered/`:

| File | What |
|---|---|
| `<svc>.bu` | the user, its folders, one Quadlet per container and the private network |
| `<svc>-port.bu` | the firewall port, open only to the login front end (not for loopback services) |
| `<svc>-backup-<container>.bu` | the database backup, by engine |
| `<svc>-backup-files.bu` | the files backup of its `local` data |
| `files/route-<svc>.yml`, `files/app-<svc>.blueprint.yaml` | the route and login rules, placed on the login front end in 3.9 |

and `<workspace>/services/<svc>/secrets.md`, which lists each secret's name,
who uses it, whether it must be kept, and the exact command to create it, and
`<workspace>/services/<svc>/ids.md`: the UID, GID, the subordinate ID ranges
pinned from them at boot (`subids-<svc>.service`, so they never depend on the
order apps were created), and how a container user maps to a file owner on
disk. Tell the owner to keep a copy with their notes.

Copy the fragments and their `files/` into `<workspace>/vms/<vm>/`, add each
fragment to `MERGE_ENTRIES` in `values/config.values`, render `config.bu`
again, and run `bash tools/build-vm.sh <workspace>/vms/<vm>`.

## 3.7 [Agent] Push to the running VM

Convert the service's fragments into one script, copy it, and run it. The
script creates exactly what Ignition would create. List every fragment by name
(no wildcards). If any fragment is refused, the tool prints nothing and exits
non-zero, and nothing is pushed.

List exactly the fragments 3.6 generated for this service, by name (Monica
shown: a `db` container with a database and some `local` data):

```fish
# desktop (fish)
set ws <workspace>; set vm apps; set svc monica
rm -f /tmp/opencode/apply-$svc.sh
python3 tools/ign_to_script.py $ws/vms/$vm/igns/{$svc,$svc-port,$svc-backup-db,$svc-backup-files}.ign > /tmp/opencode/apply-$svc.sh; and python3 tools/vmssh.py run $vm -- 'f=$(mktemp) && cat > "$f" && sudo bash "$f"; rc=$?; rm -f "$f"; exit $rc' < /tmp/opencode/apply-$svc.sh; and python3 tools/vmssh.py run $vm -- "sudo loginctl enable-linger $svc; sudo systemctl start user@\$(id -u $svc).service; sudo systemctl reload nftables; sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user daemon-reload"; or echo "STOP: push failed, nothing more was run"
```

The push creates missing folders with their mode and owner, but leaves a
folder that already exists as it is (`kept:`), as Ignition does: an app may
have taken it over, such as a database's data folder. A changed mode or owner
on an existing folder therefore needs a rebuild (section 5), or ask the
owner. Files under `/usr/local` go through FCOS's own `/usr/local` link; any
other symlink on the way stops the push.

`loginctl enable-linger` starts the service user's systemd now (the linger
file alone only takes effect at the next boot). The containers then fail and
retry until their secrets exist (3.8). That's expected.

`systemctl reload nftables` reloads only the host firewall's own table; the
base config overrides the stock reload, which would also wipe Podman's rules.

## 3.8 [Owner] Secrets, then start

The agent shows the table at the top of `secrets.md` (secret, used by, what
to enter, keep it), then the commands. For each secret, on the VM, as the service user. The value is
read from a hidden prompt, so it never appears on screen, in shell history,
or in any file. Keep every value that must be kept in your password manager:
Podman secrets live on the OS disk and are gone after a rebuild, and some
values (database passwords, signing keys) must be re-entered exactly as
before, because data on the kept data disk depends on them.

```bash
# vm <vm> (bash, <admin>)
cd /
read -rs -p "value for <secret-name>: " v; echo
printf %s "$v" | sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman secret create <secret-name> -
unset v
sudo -u <svc> XDG_RUNTIME_DIR=/run/user/<uid> podman secret ls
```

Report back: the secret names now listed. Then **[Agent]** starts the
containers and the backup timers that 3.6 generated (Monica shown):

```fish
# desktop (fish)
set vm apps; set svc monica
python3 tools/vmssh.py run $vm -- "sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user start $svc-db.service $svc-app.service $svc-cron.service $svc-backup-db.timer $svc-backup-files.timer"
```

## 3.9 [Agent] Login front end: route and login rules

For services behind the login page, and services on their own login that
have a `hostname` (an HTTPS route without the login page). Regenerate the
whole login front end from every service spec, so its routes and outpost list
always match:

```fish
# desktop (fish)
set ws <workspace>
python3 tools/login_frontend.py $ws/site.yaml $ws/login-frontend $ws/services/*/service.yaml
bash tools/build-vm.sh $ws/login-frontend/rendered
```

The output goes to `<workspace>/login-frontend/`, outside every VM folder, so
a VM build never picks up a second copy. It refuses clashing web names and
route names, and services bound to loopback on another VM.
`rendered/login-frontend.bu` places Traefik's settings, every route, every
app's login rules and the outpost list. Each app's rules are applied before
the outpost list that names it, because Authentik applies blueprints in no
fixed order.

Copy `rendered/login-frontend.bu` and all of `rendered/files/` into the login
front end VM's folder (replacing the old copies), build it, and push only
`login-frontend` (it places files; there is no account to start):

```fish
# desktop (fish)
set ws <workspace>; set vm <login-vm>
rm -f /tmp/opencode/apply-login-frontend.sh
python3 tools/ign_to_script.py $ws/vms/$vm/igns/login-frontend.ign > /tmp/opencode/apply-login-frontend.sh; and python3 tools/vmssh.py run $vm -- 'f=$(mktemp) && cat > "$f" && sudo bash "$f"; rc=$?; rm -f "$f"; exit $rc' < /tmp/opencode/apply-login-frontend.sh; or echo "STOP: push failed"
```

Then remove route and login-rule
files the new set no longer contains (a removed service, or one switched to
its own login): Ignition never deletes files, so the push leaves them behind.
These folders belong to the `traefik` and `authentik` accounts, so the
commands use `sudo`:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- 'sudo ls /var/lib/appdata/traefik/dynamic/ /var/lib/appdata/authentik/blueprints/'
# a service removed, or on its own login without a hostname: route and blueprint go
set gone oldsvc
python3 tools/vmssh.py run <login-vm> -- "sudo rm -f /var/lib/appdata/traefik/dynamic/$gone.yml /var/lib/appdata/authentik/blueprints/app-$gone.yaml"
```

A service switched between the login page and its own login (keeping its
`hostname`) needs no removal: both its files keep their names and are
replaced by the push (open route plus dashboard link, or the reverse).

Tell the owner which ones were removed. Deleting or replacing a blueprint file
doesn't delete what it created: for a removed service the owner deletes its
application and its provider (if it has one) in Authentik's admin interface; for a service
switched to its own login, only its old provider (the dashboard link sets the
application's provider to none).

Traefik reloads route files on change. If its static settings
(`traefik.yml`) changed too, restart it:
`python3 tools/vmssh.py run <login-vm> -- "sudo -u traefik XDG_RUNTIME_DIR=/run/user/\$(id -u traefik) systemctl --user restart traefik-traefik.service"`.
Then make Authentik apply its login rules. Its file watcher reacts only to
new and modified files; the push replaces each file by renaming a copy into
place, so the automatic apply races the push and may wait for the hourly
rescan. Restarting the worker rescans every rules file at startup, registers
new ones and applies changed ones (the login page itself stays up). The
check then runs inside the worker: it waits (up to 5 minutes) until each
rules file's record says `successful` for the file as it is now, because
Authentik records an invalid file only there, never in its log. The VM
hashes the files itself and passes the hashes in: a `podman exec` process
lacks the worker's extra group and can't list the rules folder:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- 'cd / && u=authentik && r=/run/user/$(id -u $u) && sudo -u $u XDG_RUNTIME_DIR=$r systemctl --user restart authentik-worker.service && for i in $(seq 30); do sudo -u $u XDG_RUNTIME_DIR=$r podman exec authentik-worker true 2>/dev/null && break; sleep 5; done && { printf "EXPECTED = {"; for f in $(sudo find /var/lib/appdata/authentik/blueprints -maxdepth 1 -name "*.yaml" | sort); do printf "\"custom/%s\": \"%s\", " "$(basename "$f")" "$(sudo sha512sum "$f" | cut -d" " -f1)"; done; echo "}"; cat; } | sudo -u $u XDG_RUNTIME_DIR=$r podman exec -i authentik-worker sh -c "exec ak shell -c \"\$(cat)\""' < tools/authentik_rules_status.py
```

Expected: one `ok` line per rules file and exit status 0. If a file reports
`error`, restart the worker and run the check once more before treating it
as a failure: a rules file that applies another one first can fail when the
other wasn't registered yet at that moment. Any `pending` or
`error` line after 5 minutes is a failure: the owner opens **System →
Blueprints** in Authentik's admin interface, where the failed file's entry
shows why. Each open path must be a valid regex; Authentik skips a pattern it
can't compile, which leaves that path behind the login.

## 3.10 [Agent] Verify

Run each check and report its result to the owner:

```fish
# desktop (fish)
set vm apps; set ip 192.0.2.30; set svc monica; set port 8110; set host monica.example.duckdns.org
python3 tools/vmssh.py run $vm -- "sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user is-active $svc-app.service"
python3 tools/vmssh.py logs $vm $svc-app.service -n 30
python3 tools/http_check.py --timeout 3 http://$ip:$port/
python3 tools/vmssh.py run <login-vm> -- "curl -s -o /dev/null -w '%{http_code}\n' http://$ip:$port/"
python3 tools/http_check.py https://$host/
python3 tools/http_check.py https://$host/<an open path>
python3 tools/vmssh.py run $vm -- "sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user start $svc-backup-files.service; sudo -u $svc ls -l /var/mnt/backups/<vm>/$svc/"
```

| Check | Expected |
|---|---|
| Units active, logs clean | `active`, no errors in the last 30 lines. Some apps print generated credentials at first start (Monica prints an OAuth client secret), so logs are read only with `vmssh.py logs`, which hides anything that looks like a secret (`[hidden]`); `vmssh.py run` refuses `journalctl`, `podman logs`, log files, environments and secret stores. If a secret reaches the agent anyway, it stops and tells the owner to rotate it. |
| Port from another LAN machine (the desktop) | `refused` or `timeout` (any status code means the port is open to the LAN: fail) |
| Port from the login front end | an HTTP status from the app |
| `https://<host>/` | `302` to `https://<login host>/...`; for a service on its own login, the app's own page or login (no redirect to the login page) |
| An open path | the app's own response (often `401` without its password), not a redirect |
| Backup | a new timestamped file in `backups/<vm>/<svc>/` |
| Certificate | the browser shows a valid `*.<domain>` certificate |

When every check passes and the owner has no more work for the agent on this
VM, revoke the agent's setup key (2.7). It removes the key's file on the VM,
proves the agent can no longer log in, then deletes the key in the workspace;
only the owner's key remains:

```fish
# desktop (fish)
python3 tools/vmssh.py revoke $vm
```

The final report says it was revoked, and how the owner can confirm it: on
the VM, `ls ~/.ssh/authorized_keys.d/` lists no `fcos-agent` file. If a check
fails and the owner wants to stop, the agent revokes it anyway; the next run
makes a new one.

## 3.11 [Agent] Record it

Update the site file and the spec with the final values and any accepted
risks. Tell the owner which checks passed, which failed, and which couldn't be
run and why.

Then rebuild the install's notes, `<workspace>/AGENTS.md`: what exists (VMs,
login front end, services, groups, sections, numbers in use, secret names) and
how a new service hooks into it. The next run reads it first. Anything a spec
can't hold (an app without single sign-on shared by invitation, a quirk found
while setting it up) goes in as a one-line note, which every rebuild keeps:

```fish
# desktop (fish)
python3 tools/install_notes.py <workspace>
python3 tools/install_notes.py <workspace> --note "<one line>"
```

## 3.12 Temporary API access to an app (when needed)

When an app must be configured through its own API (settings, users inside
the app), the agent gets temporary access and gives it back:

1. **[Owner]** Create a time-limited admin token in the app, as its
   official docs describe (the agent gives the exact steps), then store it:
   the agent prints the command with `python3 tools/appapi.py store-step
   <svc>` (a hidden prompt; the token goes into `<workspace>/secrets/`,
   which the agent can't read). The command shows the app's address and
   stores it with the token: check it is your app's own address, because
   the token is only ever sent there.
2. **[Agent]** Calls the app's API with `python3 tools/appapi.py call <svc>
   <METHOD> <path> [--data <json file>]`: HTTPS with a verified certificate,
   only the app's `api_paths` behind the login page, and the token never
   printed.
3. **[Agent]** When done: `python3 tools/appapi.py forget <svc>` deletes the
   local copy. **[Owner]** Delete the token in the app itself; the final
   report says where.
