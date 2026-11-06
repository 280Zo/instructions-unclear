# 3. Add a service

The core procedure. The result:
- the service's fragments are part of its VM's `config.bu`, so the next rebuild includes it
- the running VM gets the same files now, so only this service starts
- the login front end routes `https://<hostname>.<domain>` to it, behind the login page (or, for a service on its own login, without it)

The VM must already exist ([section 2](02-build-a-vm.md)). The login front end
must exist for 3.9 ([section 6](06-edge-vm.md)). Until it does, stop after 3.8
and reach the service with the break-glass tunnel ([section 8](08-break-glass.md)).

## 3.1 Ask the user: where it goes

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

**Apps that send mail.** Nothing here uses an email server. Set the app's mail driver to its log driver,
so what it would send is written to its log. Many apps still refuse to build a message
without a sender address ("An email must have a From or a Sender header") until its
sender setting is set, for example `MAIL_FROM_ADDRESS`. Give the app a
sender address on the user's domain (nothing is sent from or to it), and find
in its docs which log file holds the mail. A link in such a mail can be a
credential (an invitation lets someone join): the user reads it from the log
on the VM, and the agent does not.

**Ask who may open it** (apps behind the login page). An auth gateway may let every user open an app
that has no group, so ask which groups get it (for example `family`, `guests`) and put them in
`groups:`. The login front end's rules create each group if it's missing and bind it to the app. Tell
the user to add themselves (and anyone else) to the group in the gateway's own interface, or they lose
access too. An app on its own login can't take `groups:`: its route skips the login page. Also ask
whether anyone new needs an account for it: they go into the site file's `people:` (guide 6.10). The
gateway's details (how the groups and bindings behave, what to do when a group is removed) are in its
`operations.md`, "Who may open an app".

**The app's dashboard section and logo.** The gateway's dashboard may list apps under section headings.
Propose a section from what the app is for (a relationship manager: `Relationships`), reuse an
existing section when the app fits one, ask the user, and put it in `section:`. For the logo, find it
in the app's official repository or website (an SVG or PNG the project publishes), save it as
`<workspace>/services/<svc>/<file>`, show it to the user, and use it as `icon:` once they confirm; the
user may give their own file instead. The login front end stores it on the VM and the gateway serves it
itself, so no browser fetches it from the internet. How the gateway shows both is in its `operations.md`,
"The dashboard section and the logo".

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

## 3.4 Ask the user: identity and naming

[Questions](questions.md) 10, 11 and 15: paths that skip the login page,
the UID/GID (matching the file server account when it uses NFS), and the
secrets the user keeps. Hostname defaults to the service name.

## 3.5 [Manual] File server: account and folders

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
set ws <workspace>; set svc <svc>
python3 tools/check_workspace.py $ws; and python3 tools/gen_service.py $ws/services/$svc/service.yaml $ws/site.yaml $ws/services/$svc; and bash tools/build-vm.sh $ws/services/$svc/rendered
```

`check_workspace.py` refuses a name, UID, GID, web name or port (on the same
VM) that another service or the login front end already uses. Each clash is
one line; pick a free value with the user (UID/GID: [question](questions.md)
11) and run it again. The generator refuses the whole spec if anything is
wrong, and writes nothing. Expected: `build-vm: all checks passed`. It writes, under
`<workspace>/services/<svc>/rendered/`:

| File | What |
|---|---|
| `<svc>.bu` | the user, its folders, one Quadlet per container and the private network |
| `<svc>-port.bu` | the firewall port, open only to the login front end (not for loopback services) |
| `<svc>-backup-<container>.bu` | the database backup, by engine |
| `<svc>-backup-files.bu` | the files backup of its `local` data |
| `files/route-<svc>.yml`, the login-rules file `files/app-<svc>.*` | the route and login rules, placed on the login front end in 3.9 |

and `<workspace>/services/<svc>/secrets.md`, which lists each secret's name,
who uses it, whether it must be kept, and the exact command to create it, and
`<workspace>/services/<svc>/ids.md`: the UID, GID, the subordinate ID ranges
pinned from them at boot (`subids-<svc>.service`, so they never depend on the
order apps were created), and how a container user maps to a file owner on
disk. Tell the user to keep a copy with their notes.

Copy the fragments and their `files/` into `<workspace>/vms/<vm>/`, add each
fragment to `MERGE_ENTRIES` in `values/config.values`, render `config.bu`
again, and run `bash tools/build-vm.sh <workspace>/vms/<vm>`.

## 3.7 [Agent] Push to the running VM

Convert the service's fragments into one script, copy it, and run it. The
script creates exactly what Ignition would create. List every fragment by name
(no wildcards). If any fragment is refused, the tool prints nothing and exits
non-zero, and nothing is pushed.

List exactly the fragments 3.6 generated for this service, by name (shown for
a service with a `db` container that has a database and some `local` data):

```fish
# desktop (fish)
set ws <workspace>; set vm <vm>; set svc <svc>
rm -f /tmp/opencode/apply-$svc.sh
python3 tools/ign_to_script.py $ws/vms/$vm/igns/{$svc,$svc-port,$svc-backup-db,$svc-backup-files}.ign > /tmp/opencode/apply-$svc.sh; and python3 tools/vmssh.py run $vm -- 'f=$(mktemp) && cat > "$f" && sudo bash "$f"; rc=$?; rm -f "$f"; exit $rc' < /tmp/opencode/apply-$svc.sh; and python3 tools/vmssh.py run $vm -- "sudo loginctl enable-linger $svc; sudo systemctl start user@\$(id -u $svc).service; sudo systemctl reload nftables; sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user daemon-reload"; or echo "STOP: push failed, nothing more was run"
```

The push creates missing folders with their mode and owner, but leaves a
folder that already exists as it is (`kept:`), as Ignition does: an app may
have taken it over, such as a database's data folder. A changed mode or owner
on an existing folder therefore needs a rebuild (section 5), or ask the
user. Files under `/usr/local` go through FCOS's own `/usr/local` link; any
other symlink on the way stops the push.

`loginctl enable-linger` starts the service user's systemd now (the linger
file alone only takes effect at the next boot). The containers then fail and
retry until their secrets exist (3.8). That's expected.

`systemctl reload nftables` reloads only the host firewall's own table; the
base config overrides the stock reload, which would also wipe Podman's rules.

## 3.8 [Manual] Secrets, then start

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
containers and the backup timers that 3.6 generated (shown for a service with `db`, `app` and `cron` containers):

```fish
# desktop (fish)
set vm <vm>; set svc <svc>
python3 tools/vmssh.py run $vm -- "sudo -u $svc XDG_RUNTIME_DIR=/run/user/\$(id -u $svc) systemctl --user start $svc-db.service $svc-app.service $svc-cron.service $svc-backup-db.timer $svc-backup-files.timer"
```

## 3.9 [Agent] Login front end: route and login rules

For services behind the login page, and services on their own login that
have a `hostname` (an HTTPS route without the login page). Regenerate the
whole login front end from every service spec, so its routes and application list
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
`rendered/login-frontend.bu` places the ingress's settings, every route, every
app's login rules and the gateway's application list. Each app's rules are
applied before the list that names it where the gateway applies its rules in no
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

Then apply the change with each chosen module's `operations.md`:

- The ingress ("Applying route changes"): remove the route files the new set no longer contains (a
  removed service, or one switched to its own login), because Ignition never deletes files, and
  restart it if its static settings changed too.
- The auth gateway ("Applying the login rules"): remove the rules files the new set no longer
  contains, make the gateway apply the rules, and check that every rules file was applied.

Tell the user which files were removed. What a removed rules file created in the gateway is not
deleted with it: the user removes that in the gateway's own interface, as the module says.

## 3.10 [Agent] Verify

Run each check and report its result to the user:

```fish
# desktop (fish)
set vm <vm>; set ip 192.0.2.30; set svc <svc>; set port 8110; set host <svc>.example.org
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
| Units active, logs clean | `active`, no errors in the last 30 lines. Some apps print generated credentials at first start (an app may print an OAuth client secret), so logs are read only with `vmssh.py logs`, which hides anything that looks like a secret (`[hidden]`); `vmssh.py run` refuses `journalctl`, `podman logs`, log files, environments and secret stores. If a secret reaches the agent anyway, it stops and tells the user to rotate it. |
| Port from another LAN machine (the desktop) | `refused` or `timeout` (any status code means the port is open to the LAN: fail) |
| Port from the login front end | an HTTP status from the app |
| `https://<host>/` | `302` to `https://<login host>/...`; for a service on its own login, the app's own page or login (no redirect to the login page) |
| An open path | the app's own response (often `401` without its password), not a redirect |
| Backup | a new timestamped file in `backups/<vm>/<svc>/` |
| Certificate | the browser shows a valid `*.<domain>` certificate |

When every check passes and the user has no more work for the agent on this
VM, revoke the agent's setup key (2.7). It removes the key's file on the VM,
proves the agent can no longer log in, then deletes the key in the workspace;
only the user's key remains:

```fish
# desktop (fish)
python3 tools/vmssh.py revoke $vm
```

The final report says it was revoked, and how the user can confirm it: on
the VM, `ls ~/.ssh/authorized_keys.d/` lists no `fcos-agent` file. If a check
fails and the user wants to stop, the agent revokes it anyway; the next run
makes a new one.

## 3.11 [Agent] Record it

Update the site file and the spec with the final values and any accepted
risks. Tell the user which checks passed, which failed, and which couldn't be
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

1. **[Manual]** Create a time-limited admin token in the app, as its
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
   local copy. **[Manual]** Delete the token in the app itself; the final
   report says where.

## 3.13 Facts the service files rely on

Each fact comes from the official source linked under it, not from memory. Re-check one when its source changes.

### Rootless Quadlet path and linger

Quadlets for a non-root user can live in `/etc/containers/systemd/users/${UID}/`. Linger comes from an empty file at `/var/lib/systemd/linger/<user>`, written by Butane. The installed Podman is 5.8.9

Source: https://github.com/containers/podman/blob/main/docs/source/markdown/podman-systemd.unit.5.md · https://github.com/coreos/fedora-coreos-docs/blob/main/modules/ROOT/pages/tutorial-user-systemd-unit-on-boot.adoc

### subuid/subgid for Ignition users

Created automatically for normal users. Users created with `system: true` get **none**, which breaks rootless Podman. Service users are therefore normal users with fixed `uid`, not `system: true`. First-boot checks confirm `/etc/subuid`

Source: https://github.com/coreos/fedora-coreos-tracker/issues/472

### How the templates handle rootless services

These are design choices, not facts from a source.

- **Container auto-update:** the system `podman-auto-update.timer` updates only root's containers, so
  rootless containers need the user-level `podman-auto-update.timer`. The base config enables it for
  all users through `/etc/systemd/user/timers.target.wants/` and sets its schedule with a drop-in
  under `/etc/systemd/user/podman-auto-update.timer.d/`.
- **"Won't start if storage is missing":** a user systemd manager can't order itself after the
  system's `.mount` units, so `RequiresMountsFor=` isn't reliable there. Each Quadlet runs
  `ExecStartPre=/usr/bin/mountpoint -q <mount-root>` for every mount root it uses. Accessing an
  automount point triggers the NFS mount, and if the mount fails the service fails. Rootful
  exceptions also add `RequiresMountsFor=`.
