# 6. Login front end: Traefik, Authentik, certificates

One VM, on a server that is always on, runs the proxy (Traefik), the login
(Authentik) and the certificate for every service. It needs nothing from the
file server except a place for its backups. Build it first; every other
service's route lives here.

## Why one login front end

One central login, plus a way around it in an emergency (break-glass access),
is the usual practice. It is also what this setup does.

**What stops when it's down:** only the way in through the browser at
`https://<app>.<domain>`. The apps keep running on their own VMs with their
data untouched. SSH to every VM still works from the admin network; it doesn't
go through Authentik. The virtualization server's web interface isn't behind
it either.

**Why not one login per service:** each copy would be another Authentik with
its own database and updates, so more parts that can fail, not fewer. Each
needs roughly 1-2 GB of memory. Each needs its own admin account and MFA, and
one more login system to keep patched, where a central one is a single place to
enforce MFA, lock an account, or see who logged in. And you'd log in to every
app separately.

**How it stays reachable:**
1. It runs on a server that is always on.
2. A tested way around it: the SSH tunnel in [section 8](08-break-glass.md)
   reaches any app directly from the admin network, skipping the login page.
3. Apps keep their own login where they have one, so a tunnel still meets a
   password.
4. Authentik's database is backed up nightly like any app's, so a broken VM
   can be rebuilt with the same users and settings.
5. If the admin account itself is locked out, 6.8 gives Authentik's own
   recovery key.

## 6.1 Ask the owner

| Value | Fills (site file) |
|---|---|
| Which VM runs it (built in 6.2), on an always-on server | `edge.vm` |
| Email for Let's Encrypt notices | `acme_email` |
| The login page's name under the domain (default `auth`) | `edge.authentik.host` |
| Authentik image: the current release from Authentik's docs, pinned to `YYYY.M` | `edge.authentik.image` |
| Postgres image for Authentik (the official compose file names the major version) | `edge.authentik.postgres_image` |
| UIDs/GIDs for the `traefik` and `authentik` accounts | `edge.traefik.uid/gid`, `edge.authentik.uid/gid` |
| Which DNS provider handles the certificate (question 3; only one is wired today, see 6.3) | the DNS adapter |

## 6.2 Build the VM

Follow [section 2](02-build-a-vm.md) on an always-on server. Its fragments
also include `edge-ports` (lets rootless Traefik bind 80 and 443, and opens
them to the LAN), and its only NFS share is `backups`. Two cores, 4 GB of
memory, a 20 GB OS disk and a 10 GB data disk are plenty.

**[Owner]** Traefik and Authentik write their backups to the backups share as
their own accounts, so the file server needs those accounts and folders, the
same as any service (section 3.5): adapter steps **file_server: `service_user`**
and **file_server: `backup_folder`**, once for `traefik` and once for
`authentik`, with the UIDs/GIDs from 6.1. Without them the nightly backups
fail, and Authentik's database backup is what a rebuild relies on.

Report back: done, and the exact paths.

## 6.3 [Agent] Generate the login front end

```fish
# desktop (fish)
set ws <workspace>
python3 tools/login_frontend.py $ws/site.yaml $ws/login-frontend $ws/services/*/service.yaml
bash tools/build-vm.sh $ws/login-frontend/rendered
```

With no service yet, leave out the service specs; the outpost list is then
empty. The output goes to `<workspace>/login-frontend/`, outside every VM
folder. It holds Traefik and Authentik as ordinary services (from
`specs/login-frontend/`) and `login-frontend.bu` with Traefik's settings, the
login middleware, every route and login rule, and the outpost list. Copy the
fragments and `files/` into `<workspace>/vms/<vm>/`, add them to
`MERGE_ENTRIES`, render `config.bu`, and build the VM folder.

**Providers.** The certificate step is wired for DuckDNS only today:
`templates/edge/traefik.yml.tmpl` names the `duckdns` provider and
`specs/login-frontend/traefik.yaml` the secret `duckdns_token`
(the skill `adapter-duckdns`). Another DNS provider needs those
two changed first; that is a known gap.

Authentik follows its official compose file: server and worker share `/data`
and `/templates` and get 512 MB of shared memory, the worker also has `/certs`
and the blueprints folder (read-only), and there is no Redis. The server
listens only on `127.0.0.1:9000`, for Traefik.

## 6.4 [Owner] Certificate token and DNS

1. Adapter step **dns_certificates: `api_token`**. The agent never sees the token.
2. Adapter step **router_firewall: `dns_wildcard`**: every name under the
   domain points at this VM, or one name per service if the wildcard doesn't
   work.

Report back: done, and the check's output.

## 6.5 [Owner] Secrets on this VM

Three secrets, created as in section 3.8 (hidden prompt, no history);
`secrets.md` in the output lists the commands:

| Secret | Account | Value |
|---|---|---|
| `duckdns_token` | `traefik` | the DNS provider's token |
| `authentik_secret_key` | `authentik` | a new random value, 60+ characters |
| `authentik_pg_password` | `authentik` | a new random value, 32 to 99 characters (Postgres doesn't support longer) |

Generate the two random values in your password manager (no spaces), save
them there, then paste each one at the hidden prompt.

The VM already starts Traefik and Authentik at boot. Until their secrets
exist, they fail (Traefik's log says `no such secret`) and retry every 30
seconds until the secrets are there (`RestartSec=30` in the container
template); that's expected, and they come up on their own once you've created
them.

They must be kept. Postgres stores its password in the database on the data
disk at first start, and Authentik signs sessions and data with the secret key.
After a rebuild the secrets are created again with these same values
(section 5.3); a new random value would lock Authentik out of its own
database.

## 6.6 [Agent] Start and check

```fish
# desktop (fish)
set vm <login-vm>
python3 tools/vmssh.py run $vm -- 'sudo -u traefik XDG_RUNTIME_DIR=/run/user/$(id -u traefik) systemctl --user start traefik-traefik.service traefik-backup-files.timer; sudo -u authentik XDG_RUNTIME_DIR=/run/user/$(id -u authentik) systemctl --user start authentik-postgres.service authentik-server.service authentik-worker.service authentik-backup-postgres.timer authentik-backup-files.timer'
python3 tools/vmssh.py logs $vm traefik-traefik.service -n 40 | grep -iE "acme|certificate|error"
python3 tools/http_check.py https://<login host>/
```

Expected:
- Traefik's log shows the certificate for `*.<domain>` being obtained (the DNS
  check waits 60 s, so the first one takes a minute or two)
- `<login host>` (the site file's `edge.authentik.host`, for example `login.<domain>`) answers `200`, or `302` with its login flow (a TLS error means the certificate isn't valid yet)
- the browser shows a valid certificate, and the login page loads fully

Since 2026.8, Authentik only trusts forwarded headers from its trusted proxy
networks; the defaults include `127.0.0.0/8` and the private ranges. If the
page loads endlessly or complains about HTTP vs HTTPS, check
`AUTHENTIK_LISTEN__TRUSTED_PROXY_CIDRS` against the address Traefik connects
from (research notes row 16).

## 6.7 [Owner] First Authentik login

1. Open `https://<login host>/if/flow/initial-setup/` and set the admin email
   and password. Keep them in your password manager.
2. Turn on MFA for the admin, in the **user** interface (not the admin
   interface): click the **gear icon** at the top right, open the
   **Credentials** tab, then **MFA Devices** → **Enroll**. Add a WebAuthn
   device (a passkey) or a TOTP device, and also **Static tokens** (six
   single-use backup codes for your password manager)
   ([User interface overview](https://docs.goauthentik.io/users-sources/user/user-interface/)).
3. **Applications → Outposts → authentik Embedded Outpost** (admin
   interface): check that `authentik_host` is `https://<login host>`.

## 6.8 Admin recovery

If the admin can't log in any more (a broken flow, lost MFA), Authentik
creates a one-time recovery link, valid for the number of minutes given
(Authentik's troubleshooting docs, "I can't log in to authentik"; they show it
for Docker Compose and Kubernetes, here it runs in the worker container):

```bash
# vm <login front end vm> (bash, <admin>)
cd /
sudo -u authentik XDG_RUNTIME_DIR=/run/user/<uid> podman exec -it authentik-worker ak create_recovery_key 10 <admin user>
```

The link gives whoever has it direct access: open it right away, don't store
it. If the login page itself isn't reachable, open the link through the
tunnel to `127.0.0.1:9000` (section 8).

## 6.9 Check the login wall end to end

Add one test service through [section 3](03-add-a-service.md) (a tiny
`docker.io/traefik/whoami` works). Then confirm:
- `https://whoami.<domain>/` redirects to the Authentik login
- after login, the page shows `X-authentik-username` in the request headers

Remove the test service afterward ([section 7](07-remove-and-rollback.md)).

## 6.10 People and access

Everyone signs in to the login page with a local account: no email, and
nothing here talks to the outside. Groups decide which apps
each person gets:

- `guests`: the default group. Anyone who can reach the login page (your
  home networks and Tailscale) can create their own account on its **Sign
  up** link and lands here, with only the apps whose `groups:` list `guests`.
- `family`: the household. The owner moves a person here (or adds more apps
  per person) in Authentik's admin interface: the person's **Groups** tab.

Each app behind the login page lists the groups that may open it (guide
3.2). A person in none of them is refused with "Permission denied".

**[Agent]** The sign-up page comes from the site file; it is Authentik's own
example flow `flows-enrollment-2-stage.yaml` without the email field
(username, password, name), adding new accounts to the group
(`create_users_group`) and linking the page from the sign-in page
(`enrollment_flow`). With `approve: true` new accounts start disabled until
the owner turns them on (`create_users_as_inactive`):

```yaml
signup: {group: guests}
```

The owner can also have the agent create an account in advance, under
`people:` (username, display name, groups), never a password or an email:

```yaml
people:
  - {username: sam, name: "Sam Example", groups: [family]}
```

Then regenerate and push the login front end (guide 3.9). Its rules file
`access.yaml` creates the groups, each listed person once (later group
changes the owner makes in the admin interface stay) and the app bindings; a
separate `signup.yaml` creates the sign-up page and the sign-in sources, so a
problem there never undoes who may open which app. Until `access.yaml` has
bound an app's groups, that app refuses everyone.

Sign-up passwords must be at least 12 characters and not easy to guess
(Authentik's password policy, checked on the VM; nothing is sent outside).
New accounts are ordinary users who can change their own password in the
user interface.

**Turning sign-up off again:** remove `signup:` from the site file and push;
then, because Authentik keeps what a rules file created, the owner opens the
admin interface, **Flows and Stages → Stages →
default-authentication-identification**, clears **Enrollment flow** (and any
sources under **Sources**), and deletes the `signup` flow. The sign-in
stage's sources are replaced by the ones the site file lists; sources added
there by hand would be removed.

**[Owner]** For an account made in advance, set its password: in the admin
interface, **Directory → Users**, click the person's name, **Reset
password**
([Manage users](https://docs.goauthentik.io/users-sources/user/user_basic_operations/)).
Give it to them in person; they can change it in the user interface. Keep the
admin's own MFA on.

### Sign in with an existing account (Google, Apple)

People can also sign up and sign in with an account they already have. Their
browser goes to the provider and back; the VM checks the result with the
provider over HTTPS. Nothing sends mail. New people land in the sign-up group,
like the sign-up page.

**[Owner]** Register the login page once with each provider; the agent gives
each value filled in (`<login host>` is the site file's
`edge.authentik.host`):

- **Google** ([authentik guide](https://docs.goauthentik.io/users-sources/sources/social-logins/google/cloud/);
  console names from Google's [Manage OAuth Clients](https://support.google.com/cloud/answer/15549257)):
  open the **Google Auth Platform** in the Google Cloud console and create a
  project when asked. Register the app when asked (**Get started**): app name,
  your support email, audience **External**, your contact email. Under
  **Branding**, add the authorized domain `<domain>`. Under **Clients**,
  **Create client** of type **Web application** with the authorized redirect
  URI `https://<login host>/source/oauth/callback/google/`. The client secret
  is shown only once, at creation: save it with the client ID in the password
  manager. Keep the default scopes only: for name, email and profile, Google
  needs no test-user list and no verification, and shows no warning
  ([Manage App Audience](https://support.google.com/cloud/answer/15549945)).
  Report back the **client ID**; the client secret goes into the VM later.
- **Apple** ([authentik guide](https://docs.goauthentik.io/users-sources/sources/social-logins/apple/);
  needs an Apple developer account): register an App ID with *Sign In with
  Apple*, a Services ID configured with the domain `<login host>` and the
  return URL `https://<login host>/source/oauth/callback/apple/`, and a key
  for *Sign in with Apple*; download the key file. Report back the Services
  ID, the Team ID and the Key ID.

**[Agent]** Put the non-secret identifiers in the site file, regenerate and
push the login front end (guide 3.9):

```yaml
signin_sources:
  google: {client_id: "<client ID>"}
  apple: {client_id: "<services ID>;<team ID>;<key ID>"}
```

**[Owner]** Create the secrets on the VM with the commands in the login
front end's `secrets.md`: `authentik_google_secret` from a hidden prompt, and
`authentik_apple_key` from the key file (copy it to `/dev/shm` on the VM,
which lives in memory, not on the VM's disk; the command loads it and removes
the copy). Keep both in your password manager. Then the
agent restarts the worker and runs the rules check (guide 3.9).

### Users' pictures

Authentik shows each person's picture by its **Avatars** system setting
(default `gravatar,initials`: the VM asks gravatar.com for a picture by a
SHA-256 hash of the email address and browsers then load it from there, else
initials; [System settings](https://docs.goauthentik.io/sys-mgmt/settings/),
`authentik/lib/avatars.py`).
Ask the owner which they want; changing it is an owner step in the admin
interface (**System → Settings → Avatars**, e.g. `initials` for no outside
lookup). Uploaded pictures aren't offered: Authentik has no upload page of its
own, and a picture stored on the user would end up in the ID token, which the
outpost's sign-out puts into its redirect address (`id_token_hint`,
`internal/outpost/proxyv2/application/application.go`).
