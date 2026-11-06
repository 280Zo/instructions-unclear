# Operating Authentik behind the login front end

The guide pages (`docs/guide/`) hold the steps that don't depend on the auth gateway and point
here for the ones that do. Section names below are what the guide cites. The facts the steps rely
on, with their sources, are in `reference.md`.

## Site values

What guide 6.1 asks for, for this module:

| Value | Fills (site file) |
|---|---|
| The login page's name under the domain (the user picks it; `auth` or `login` are common) | `edge.authentik.host` |
| Authentik image: the current release from Authentik's docs, pinned to `YYYY.M` | `edge.authentik.image` |
| Postgres image for Authentik (the official compose file names the major version) | `edge.authentik.postgres_image` |
| UID/GID for the `authentik` account | `edge.authentik.uid/gid` |
| The Postgres user and database names | `edge.authentik.postgres_user`, `edge.authentik.postgres_db` |

An example of this section, with the keys filled in, is `site.example.yaml` in this folder. It also shows the optional `signup`, `people` and `signin_sources` keys (see "People and access").

## The containers

Authentik follows its official compose file: server and worker share `/data` and `/templates` and
get 512 MB of shared memory, the worker also has `/certs` and the blueprints folder (read-only), and
there is no Redis. The server listens only on `127.0.0.1:9000`, for the ingress.

## Secrets on the login VM

Created as in guide 3.8 (hidden prompt, no history); `secrets.md` in the output lists the commands:

| Secret | Account | Value |
|---|---|---|
| `authentik_secret_key` | `authentik` | a new random value, 60+ characters |
| `authentik_pg_password` | `authentik` | a new random value, 32 to 99 characters (Postgres doesn't support longer) |

Generate the two random values in your password manager (no spaces), save them there, then paste each
one at the hidden prompt.

They must be kept. Postgres stores its password in the database on the data disk at first start, and
Authentik signs sessions and data with the secret key. After a rebuild the secrets are created again
with these same values (guide 5.3); a new random value would lock Authentik out of its own database.

## Start and check

```fish
# desktop (fish)
set vm <login-vm>
python3 tools/vmssh.py run $vm -- 'sudo -u authentik XDG_RUNTIME_DIR=/run/user/$(id -u authentik) systemctl --user start authentik-postgres.service authentik-server.service authentik-worker.service authentik-backup-postgres.timer authentik-backup-files.timer'
python3 tools/http_check.py https://<login host>/
```

Expected: `<login host>` (the site file's `edge.authentik.host`, for example `login.<domain>`) answers
`200`, or `302` with its login flow (a TLS error means the certificate isn't valid yet), and the
browser shows a valid certificate and the login page loads fully.

Since 2026.8, Authentik only trusts forwarded headers from its trusted proxy networks; the defaults
include `127.0.0.0/8` and the private ranges. If the page loads endlessly or complains about HTTP vs
HTTPS, check `AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` against the address the ingress connects from
(`reference.md`, "Authentik facts used by the login front end").

## First login

**[Owner]**

1. Open `https://<login host>/if/flow/initial-setup/` and set the admin email and password. Keep them
   in your password manager.
2. Turn on MFA for the admin, in the **user** interface (not the admin interface): click the **gear
   icon** at the top right, open the **Credentials** tab, then **MFA Devices** → **Enroll**. Add a
   WebAuthn device (a passkey) or a TOTP device, and also **Static tokens** (six single-use backup
   codes for your password manager)
   ([User interface overview](https://docs.goauthentik.io/users-sources/user/user-interface/)).
3. **Applications → Outposts → authentik Embedded Outpost** (admin interface): check that
   `authentik_host` is `https://<login host>`.

## Admin recovery

If the admin can't log in any more (a broken flow, lost MFA), Authentik creates a one-time recovery
link, valid for the number of minutes given (Authentik's troubleshooting docs, "I can't log in to
authentik"; they show it for Docker Compose and Kubernetes, here it runs in the worker container):

```bash
# vm <login front end vm> (bash, <admin>)
cd /
sudo -u authentik XDG_RUNTIME_DIR=/run/user/<uid> podman exec -it authentik-worker ak create_recovery_key 10 <admin user>
```

The link gives whoever has it direct access: open it right away, don't store it. If the login page
itself isn't reachable, open the link through the tunnel to `127.0.0.1:9000` (guide 8).

## End-to-end check

With the test service from guide 6.9 added: `https://<test>.<domain>/` redirects to the Authentik
login, and after login the page shows `X-authentik-username` in the request headers.

## Who may open an app

Authentik lets every user open an app that has no bindings, so ask which groups get it (for example
`family`, `guests`) and put them in `groups:`. The login front end's rules file `access.yaml` creates
each group if it's missing (the one place that does) and binds it to the app. Tell the owner to add
themselves (and anyone else) to the group in Authentik's admin interface (**Directory → Groups**), or
they lose access too. Group names are lowercase; if the owner already has a group with capital
letters, a new lowercase one is made beside it. Removing a group from `groups:` later doesn't remove
its old binding; the owner deletes it under the application's **Policy / Group / User Bindings**. Such
an app also refuses everyone until its group bindings exist (a `deny-until-bound` policy); that relies
on the application's policy engine mode staying **any** (Authentik's default): switching it to **all**
in the admin interface would lock everyone out. An app on its own login can't take `groups:`: its
route skips the login page, so a binding would only hide its dashboard link. Also ask whether anyone
new needs an account for it: they go into the site file's `people:` (People and access, below).

## The dashboard section and the logo

Authentik's dashboard lists apps under section headings, all on one page: each application's `group`
becomes a heading over its apps (authentik's `web/src/user/LibraryPage/ApplicationList.ts`). Propose a
section from what the app is for (Monica, a relationship manager: `Relationships`), reuse an existing
section when the app fits one, ask the owner, and put it in `section:`. Apps with the same section
are listed together; without one, an app is listed under "Ungrouped".

The logo comes from the app's official repository or website (an SVG or PNG the project publishes);
save it as `<workspace>/services/<svc>/<file>`, show it to the owner, and use it as `icon:` once they
confirm. The login front end stores it on the VM and Authentik serves it itself, so no browser fetches
it from the internet
([File picker values](https://docs.goauthentik.io/customize/file-picker/)).

## Applying the login rules

After the files are pushed (guide 3.9), remove the rules files the new set no longer contains: a
removed service, or one switched to its own login. Ignition never deletes files, so the push leaves
them behind. The folder belongs to the `authentik` account, so the commands use `sudo`:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- 'sudo ls /var/lib/appdata/authentik/blueprints/'
# a service removed, or on its own login without a hostname: its rules file goes
set gone oldsvc
python3 tools/vmssh.py run <login-vm> -- "sudo rm -f /var/lib/appdata/authentik/blueprints/app-$gone.yaml"
```

A service switched between the login page and its own login (keeping its `hostname`) needs no
removal: its file keeps its name and is replaced by the push (dashboard link with or without the
login).

Deleting or replacing a blueprint file doesn't delete what it created: for a removed service the owner
deletes its application and its provider (if it has one) in Authentik's admin interface; for a service
switched to its own login, only its old provider (the dashboard link sets the application's provider to
none).

Then make Authentik apply its login rules. Its file watcher reacts only to new and modified files; the
push replaces each file by renaming a copy into place, so the automatic apply races the push and may
wait for the hourly rescan. Restarting the worker rescans every rules file at startup, registers new
ones and applies changed ones (the login page itself stays up). The check then runs inside the worker:
it waits (up to 5 minutes) until each rules file's record says `successful` for the file as it is now,
because Authentik records an invalid file only there, never in its log. The VM hashes the files itself
and passes the hashes in: a `podman exec` process lacks the worker's extra group and can't list the
rules folder:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- 'cd / && u=authentik && r=/run/user/$(id -u $u) && sudo -u $u XDG_RUNTIME_DIR=$r systemctl --user restart authentik-worker.service && for i in $(seq 30); do sudo -u $u XDG_RUNTIME_DIR=$r podman exec authentik-worker true 2>/dev/null && break; sleep 5; done && { printf "EXPECTED = {"; for f in $(sudo find /var/lib/appdata/authentik/blueprints -maxdepth 1 -name "*.yaml" | sort); do printf "\"custom/%s\": \"%s\", " "$(basename "$f")" "$(sudo sha512sum "$f" | cut -d" " -f1)"; done; echo "}"; cat; } | sudo -u $u XDG_RUNTIME_DIR=$r podman exec -i authentik-worker sh -c "exec ak shell -c \"\$(cat)\""' < tools/authgw/authentik_rules_status.py
```

Expected: one `ok` line per rules file and exit status 0. If a file reports `error`, restart the worker
and run the check once more before treating it as a failure: a rules file that applies another one
first can fail when the other wasn't registered yet at that moment. Any `pending` or `error` line after
5 minutes is a failure: the owner opens **System → Blueprints** in Authentik's admin interface, where
the failed file's entry shows why. Each open path must be a valid regex; Authentik skips a pattern it
can't compile, which leaves that path behind the login.

## Removing an app

After the guide's steps (7.1, the service's units and its login front end files), the owner deletes the
application and provider in Authentik's admin interface: deleting a blueprint file doesn't delete what
it created. For a service moved to its own login, only its old provider.

## People and access

Everyone signs in to the login page with a local account: no email, and nothing here talks to the
outside. Groups decide which apps each person gets:

- `guests`: the default group. Anyone who can reach the login page (your home networks and Tailscale)
  can create their own account on its **Sign up** link and lands here, with only the apps whose
  `groups:` list `guests`.
- `family`: the household. The owner moves a person here (or adds more apps per person) in Authentik's
  admin interface: the person's **Groups** tab.

Each app behind the login page lists the groups that may open it (guide 3.2). A person in none of them
is refused with "Permission denied".

**[Agent]** The sign-up page comes from the site file; it is Authentik's own example flow
`flows-enrollment-2-stage.yaml` without the email field (username, password, name), adding new accounts
to the group (`create_users_group`) and linking the page from the sign-in page (`enrollment_flow`).
With `approve: true` new accounts start disabled until the owner turns them on
(`create_users_as_inactive`):

```yaml
signup: {group: guests}
```

The owner can also have the agent create an account in advance, under `people:` (username, display
name, groups), never a password or an email:

```yaml
people:
  - {username: sam, name: "Sam Example", groups: [family]}
```

Then regenerate and push the login front end (guide 3.9). Its rules file `access.yaml` creates the
groups, each listed person once (later group changes the owner makes in the admin interface stay) and
the app bindings; a separate `signup.yaml` creates the sign-up page and the sign-in sources, so a
problem there never undoes who may open which app. Until `access.yaml` has bound an app's groups, that
app refuses everyone.

Sign-up passwords must be at least 12 characters and not easy to guess (Authentik's password policy,
checked on the VM; nothing is sent outside). New accounts are ordinary users who can change their own
password in the user interface.

**Turning sign-up off again:** remove `signup:` from the site file and push; then, because Authentik
keeps what a rules file created, the owner opens the admin interface, **Flows and Stages → Stages →
default-authentication-identification**, clears **Enrollment flow** (and any sources under
**Sources**), and deletes the `signup` flow. The sign-in stage's sources are replaced by the ones the
site file lists; sources added there by hand would be removed.

**[Owner]** For an account made in advance, set its password: in the admin interface, **Directory →
Users**, click the person's name, **Reset password**
([Manage users](https://docs.goauthentik.io/users-sources/user/user_basic_operations/)). Give it to
them in person; they can change it in the user interface. Keep the admin's own MFA on.

### Sign in with an existing account (Google, Apple)

People can also sign up and sign in with an account they already have. Their browser goes to the
provider and back; the VM checks the result with the provider over HTTPS. Nothing sends mail. New
people land in the sign-up group, like the sign-up page.

**[Owner]** Register the login page once with each provider; the agent gives each value filled in
(`<login host>` is the site file's `edge.authentik.host`):

- **Google** ([authentik guide](https://docs.goauthentik.io/users-sources/sources/social-logins/google/cloud/);
  console names from Google's [Manage OAuth Clients](https://support.google.com/cloud/answer/15549257)):
  open the **Google Auth Platform** in the Google Cloud console and create a project when asked.
  Register the app when asked (**Get started**): app name, your support email, audience **External**,
  your contact email. Under **Branding**, add the authorized domain `<domain>`. Under **Clients**,
  **Create client** of type **Web application** with the authorized redirect URI
  `https://<login host>/source/oauth/callback/google/`. The client secret is shown only once, at
  creation: save it with the client ID in the password manager. Keep the default scopes only: for name,
  email and profile, Google needs no test-user list and no verification, and shows no warning
  ([Manage App Audience](https://support.google.com/cloud/answer/15549945)). Report back the **client
  ID**; the client secret goes into the VM later.
- **Apple** ([authentik guide](https://docs.goauthentik.io/users-sources/sources/social-logins/apple/);
  needs an Apple developer account): register an App ID with *Sign In with Apple*, a Services ID
  configured with the domain `<login host>` and the return URL
  `https://<login host>/source/oauth/callback/apple/`, and a key for *Sign in with Apple*; download the
  key file. Report back the Services ID, the Team ID and the Key ID.

**[Agent]** Put the non-secret identifiers in the site file, regenerate and push the login front end
(guide 3.9):

```yaml
signin_sources:
  google: {client_id: "<client ID>"}
  apple: {client_id: "<services ID>;<team ID>;<key ID>"}
```

**[Owner]** Create the secrets on the VM with the commands in the login front end's `secrets.md`:
`authentik_google_secret` from a hidden prompt, and `authentik_apple_key` from the key file (copy it
to `/dev/shm` on the VM, which lives in memory, not on the VM's disk; the command loads it and removes
the copy). Keep both in your password manager. Then the agent restarts the worker and runs the rules
check (Applying the login rules, above).

### Users' pictures

Authentik shows each person's picture by its **Avatars** system setting (default `gravatar,initials`:
the VM asks gravatar.com for a picture by a SHA-256 hash of the email address and browsers then load it
from there, else initials; [System settings](https://docs.goauthentik.io/sys-mgmt/settings/),
`authentik/lib/avatars.py`). Ask the owner which they want; changing it is an owner step in the admin
interface (**System → Settings → Avatars**, e.g. `initials` for no outside lookup). Uploaded pictures
aren't offered: Authentik has no upload page of its own, and a picture stored on the user would end up
in the ID token, which the outpost's sign-out puts into its redirect address (`id_token_hint`,
`internal/outpost/proxyv2/application/application.go`).

## Upgrading

Back up the database first (the nightly backup counts; check that it is recent), read the release notes
for every release line in between, and move one release line at a time: the upgrade must follow the
sequence of releases, going to the latest patch of each `major.minor` before the next one, for example
`2025.2.x`, then `2025.4.x`, then `2025.6.x`. Authentik does not support downgrading, so the backup is the
way back. The server and all outposts must be on the same version. Change `edge.authentik.image`, then
follow guide 11. The source is in `reference.md`, "Upgrading Authentik".

## Stop it

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- "sudo -u authentik XDG_RUNTIME_DIR=/run/user/\$(id -u authentik) systemctl --user stop authentik-server.service authentik-worker.service authentik-postgres.service"
```

## Restoring the database

The guide's Postgres restore (guide 4) with Authentik's names: the account and folder are `authentik`,
the database container is `authentik-postgres`, and the units that use the database are
`authentik-server.service authentik-worker.service`. `<pg user>` and `<pg db>` are
`edge.authentik.postgres_user` and `edge.authentik.postgres_db` in the site file, when set.

```bash
# vm <login front end vm> (bash, <admin>)
sudo systemctl --user -M authentik@ stop authentik-server.service authentik-worker.service
sudo -u authentik ls -t /var/mnt/backups/<vm>/authentik/ | grep '\.dump$' | head -n 1
sudo -u authentik cat /var/mnt/backups/<vm>/authentik/<newest>.dump | sudo -u authentik XDG_RUNTIME_DIR=/run/user/<uid> podman exec -i authentik-postgres \
    pg_restore --clean --if-exists -U <pg user> -d <pg db>
sudo systemctl --user -M authentik@ start authentik-server.service authentik-worker.service
```

If the database password is lost, set a new one inside the database first (guide 5.3, with `<svc>` = `authentik` and `<container>` = `postgres`), then keep the
new value in the password manager and create it as the secret `authentik_pg_password`.

## If only Authentik is down

While the ingress still runs, apps on their own login keep working at their normal HTTPS address; apps
behind the login page are refused, not let through (expected from how forward auth works; not tested
yet). The way in for an app behind the login page is the ingress module's break-glass route edit
(`skills/ingress-traefik/operations.md`), or the tunnel to `127.0.0.1:9000` to reach Authentik itself
(guide 8).
