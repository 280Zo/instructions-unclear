# 6. Login front end: ingress, auth gateway, certificates

One VM, on a server that is always on, runs the ingress (the reverse proxy), the auth gateway (the
login) and the certificate for every service. It needs nothing from the file server except a place
for its backups. Build it first; every other service's route lives here.

Which product fills each of the two parts is the user's choice, recorded in the site file under
`login_frontend` (`python3 tools/modules.py list` shows what is installed, and
[section 12](12-add-a-module.md) adds another). This page holds the steps that are the same for any
choice. Each chosen module keeps its own steps in `operations.md` in its skill folder, and this page
says where it hands over.

**Providers.** The modules installed today are `ingress-traefik` and `authgw-authentik`. Their
`operations.md` files hold the Traefik and Authentik steps: site values, secrets, start and check, the
first login, recovery, groups and people, applying route and login-rule changes, and the break-glass
route edit.

## Why one login front end

One central login, plus a way around it in an emergency (break-glass access), is the usual practice.
It is also what this setup does.

**What stops when it's down:** only the way in through the browser at `https://<app>.<domain>`. The
apps keep running on their own VMs with their data untouched. SSH to every VM still works from the
admin network; it doesn't go through the auth gateway. The virtualization server's web interface isn't
behind it either.

**Why not one login per service:** each copy would be another auth gateway with its own database and
updates, so more parts that can fail, not fewer. Each needs roughly 1-2 GB of memory. Each needs its
own admin account and MFA, and one more login system to keep patched, where a central one is a single
place to enforce MFA, lock an account, or see who logged in. And you'd log in to every app separately.

**How it stays reachable:**
1. It runs on a server that is always on.
2. A tested way around it: the SSH tunnel in [section 8](08-break-glass.md) reaches any app directly
   from the admin network, skipping the login page.
3. Apps keep their own login where they have one, so a tunnel still meets a password.
4. The auth gateway's database is backed up nightly like any app's, so a broken VM can be rebuilt with
   the same users and settings.
5. If the admin account itself is locked out, 6.8 points to the gateway's own recovery.

## 6.1 Ask the user

| Value | Fills (site file) |
|---|---|
| Which VM runs it (built in 6.2), on an always-on server | `edge.vm` |
| Email for the certificate authority's notices, if the chosen ingress asks for one (its `operations.md`) | `acme_email` |
| Which ingress and which auth gateway (recommend from the tested pairings, then ask) | `login_frontend.ingress`, `login_frontend.auth_gateway` |
| The chosen modules' own values: the login page's name, images, UIDs/GIDs | each module's `operations.md`, "Site values" |
| Which DNS provider handles the certificate (question 3) | the DNS adapter, which carries the `acme` block the ingress reads |

## 6.2 Build the VM

Follow [section 2](02-build-a-vm.md) on an always-on server. Its fragments also include `edge-ports`
(lets the rootless ingress bind 80 and 443, and opens them to the LAN), and its only NFS share is
`backups`. Two cores, 4 GB of memory, a 20 GB OS disk and a 10 GB data disk are plenty.

**[Manual]** The ingress and the auth gateway write their backups to the backups share as their own
accounts, so the file server needs those accounts and folders, the same as any service (section 3.5):
adapter steps **file_server: `service_user`** and **file_server: `backup_folder`**, once for each of the
two accounts (their names are the chosen modules' keys under `edge` in the site file), with the
UIDs/GIDs from 6.1. Without them the nightly backups fail, and the auth gateway's database backup is
what a rebuild relies on.

Report back: done, and the exact paths.

## 6.3 [Agent] Generate the login front end

```fish
# desktop (fish)
set ws <workspace>
python3 tools/login_frontend.py $ws/site.yaml $ws/login-frontend $ws/services/*/service.yaml
bash tools/build-vm.sh $ws/login-frontend/rendered
```

With no service yet, leave out the service specs; the gateway's list of applications is then empty.
The output goes to `<workspace>/login-frontend/`, outside every VM folder. It holds the ingress and the
auth gateway as ordinary services (from the chosen modules' specs) and `login-frontend.bu` with the
ingress's settings, the login middleware, every route and login rule, and the gateway's application
list. If the pairing of the two modules isn't marked tested, the generator prints a note saying so; tell
the user. Copy the fragments and `files/` into `<workspace>/vms/<vm>/`, add them to `MERGE_ENTRIES`,
render `config.bu`, and build the VM folder.

The certificate step needs the DNS adapter's `acme` block: the generator stops with the fix when the
site names no DNS provider, or one whose adapter has no such block.

The ingress's `operations.md` ("Ports and the VM") says what its VM needs, and the auth gateway's ("The containers") how its containers are set up.

## 6.4 [Manual] Certificate token and DNS

1. Adapter step **dns_certificates: `api_token`**. The agent never sees the token.
2. Adapter step **router_firewall: `dns_wildcard`**: every name under the domain points at this VM, or
   one name per service if the wildcard doesn't work.

Report back: done, and the check's output.

## 6.5 [Manual] Secrets on this VM

Created as in section 3.8 (hidden prompt, no history); `secrets.md` in the output lists the commands.
They are the DNS provider's token for the ingress, and the secrets of the auth gateway: each module's
`operations.md` ("Secrets on the login VM") says what each one is and what value to give it.

The VM already starts the ingress and the auth gateway at boot. Until their secrets exist, they fail
and retry every 30 seconds (`RestartSec=30` in the container template); that's expected, and they come
up on their own once you've created them.

Some of them must be kept. A database stores its password at first start on the data disk, and a
signing key signs sessions and data. After a rebuild the secrets are created again with these same
values (section 5.3); a new random value would lock the gateway out of its own database. Generate
random values in your password manager, save them there, then paste each one at the hidden prompt.

## 6.6 [Agent] Start and check

Run each module's "Start and check" (`operations.md`), the ingress first. Then:

```fish
# desktop (fish)
python3 tools/http_check.py https://<login host>/
```

Expected:
- the ingress's log shows the certificate for `*.<domain>` being obtained (the DNS check waits 60 s,
  so the first one takes a minute or two)
- `<login host>` (the auth gateway's `host` in the site file, for example `login.<domain>`) answers
  `200`, or `302` with its login flow (a TLS error means the certificate isn't valid yet)
- the browser shows a valid certificate, and the login page loads fully

If the page loads endlessly or complains about HTTP vs HTTPS, the gateway doesn't trust the address the
ingress connects from; its `operations.md` says which setting to check.

## 6.7 [Manual] First login to the auth gateway

The first admin account and its MFA are set up in the gateway's own interface: its `operations.md`,
"First login". Keep the admin email and password in your password manager.

## 6.8 Admin recovery

If the admin can't log in any more (a broken flow, lost MFA), the gateway's own recovery applies: its
`operations.md`, "Admin recovery". The link or key it creates gives whoever has it direct access: use it
right away, don't store it. If the login page itself isn't reachable, reach the gateway through the
tunnel in [section 8](08-break-glass.md).

## 6.9 Check the login wall end to end

Add one test service through [section 3](03-add-a-service.md): a tiny image that prints the request
headers. Then confirm:
- `https://<test>.<domain>/` redirects to the login page
- after login, the page shows the user's name in the request headers (the header's name is in the
  gateway's `operations.md`, "End-to-end check")

Remove the test service afterward ([section 7](07-remove-and-rollback.md)).

**Providers.** `docker.io/traefik/whoami` is such an image and works with any `ingress-*` module.

## 6.10 People and access

Everyone signs in to the login page with a local account: no email, and nothing here talks to the
outside. Groups decide which apps each person gets. Each app behind the login page lists the groups
that may open it (guide 3.2); a person in none of them is refused.

The site file can also hold a sign-up group (people create their own account on the login page), accounts
made in advance (`people:`: username, display name, groups, never a password or an email) and sign-in
with an existing account from another provider (`signin_sources:`, non-secret identifiers only). What
each of these does, the manual steps in the gateway's own interface, and how to turn sign-up off again are
in its `operations.md`, "People and access". After a change to the site file, regenerate and push the
login front end (guide 3.9).
