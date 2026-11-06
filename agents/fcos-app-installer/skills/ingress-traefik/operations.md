# Operating Traefik as the login front end's ingress

The guide pages (`docs/guide/`) hold the steps that don't depend on the ingress and point here for
the ones that do. Section names below are what the guide cites. The facts the steps rely on, with
their sources, are in `reference.md`.

## Site values

| Value | Fills (site file) |
|---|---|
| UID/GID for the `traefik` account | `edge.traefik.uid/gid` |
| Email for Let's Encrypt notices | `acme_email` |

## Ports and the VM

The login front end VM's fragments include `edge-ports`: it lets the rootless Traefik bind 80 and 443
and opens them to the LAN. Traefik writes its backups to the backups share as the `traefik` account,
so the file server needs that account and its folder like any service (guide 3.5): adapter steps
**file_server: `service_user`** and **file_server: `backup_folder`**, with the UID/GID from the site
file.

## The certificate and the DNS provider

Traefik gets one wildcard certificate for `*.<domain>` by ACME DNS-01. Which DNS provider it asks is
not written in this module: `traefik.yml` takes the certificate client's provider code from the `acme`
block of the DNS adapter the site names (`roles.dns_certificates.provider`), and the token's secret
name and variable from the same block (`python3 tools/adapters.py show --role dns_certificates`). A
provider without an adapter needs one with that block first (`skills/adapter-generic`). The provider's
own limits (for example how many TXT records it holds at once) are in that block's `notes`, which the
generated `traefik.yml` repeats in a comment.

The DNS check waits 60 s, so the first certificate takes a minute or two.

## Secrets on the login VM

Created as in guide 3.8 (hidden prompt, no history); `secrets.md` in the output lists the commands:

| Secret | Account | Value |
|---|---|---|
| the DNS adapter's `acme` `store_as` name | `traefik` | the DNS provider's token |

The VM already starts Traefik at boot. Until its secret exists it fails (its log says `no such
secret`) and retries every 30 seconds (`RestartSec=30` in the container template); that's expected,
and it comes up on its own once the secret is created.

## Start and check

```fish
# desktop (fish)
set vm <login-vm>
python3 tools/vmssh.py run $vm -- 'sudo -u traefik XDG_RUNTIME_DIR=/run/user/$(id -u traefik) systemctl --user start traefik-traefik.service traefik-backup-files.timer'
python3 tools/vmssh.py logs $vm traefik-traefik.service -n 40 | grep -iE "acme|certificate|error"
```

Expected: the log shows the certificate for `*.<domain>` being obtained. A TLS error on the login
page means the certificate isn't valid yet.

## Applying route changes

After the files are pushed (guide 3.9), remove the route files the new set no longer contains: a
removed service, or one switched to its own login without a hostname. Ignition never deletes files, so
the push leaves them behind. The folder belongs to the `traefik` account, so the commands use `sudo`:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- 'sudo ls /var/lib/appdata/traefik/dynamic/'
set gone oldsvc
python3 tools/vmssh.py run <login-vm> -- "sudo rm -f /var/lib/appdata/traefik/dynamic/$gone.yml"
```

A service switched between the login page and its own login (keeping its `hostname`) needs no
removal: its route keeps its name and is replaced by the push.

Traefik reloads route files on change. If its static settings (`traefik.yml`) changed too, restart it:

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- "sudo -u traefik XDG_RUNTIME_DIR=/run/user/\$(id -u traefik) systemctl --user restart traefik-traefik.service"
```

## Stop it

```fish
# desktop (fish)
python3 tools/vmssh.py run <login-vm> -- "sudo -u traefik XDG_RUNTIME_DIR=/run/user/\$(id -u traefik) systemctl --user stop traefik-traefik.service"
```

## Break-glass: an app's route without the login

For an app that forces its own `https://` address, and when only the auth gateway is down while Traefik
still runs, the way in is the app's route without the login, edited by hand and put back. The app's own
login still protects it. Tested end to end on a real install (Authentik as the gateway): the address
answered with the app's own page instead of a redirect, signing in worked, and after the restore the
redirect to the login page was back. In the generated route file (`dynamic/<svc>.yml` on the login
front end VM), the login is the single line `middlewares: [authentik]` on the app's router (the
middleware's name comes from the gateway's glue file, `templates/gateways/authgw-authentik/`). Take a
copy outside the watched folder, remove the line, and Traefik reloads the file by itself (each block
stops by itself on any other machine):

```bash
# vm <login-vm> (bash, <admin>): run this ONLY on <login-vm>
if [ "$(hostnamectl hostname)" = "<login-vm>" ]; then
  cd /
  sudo cp -p /var/lib/appdata/traefik/dynamic/<svc>.yml /var/lib/appdata/traefik/<svc>.yml.login
  sudo sed -i '/^\s*middlewares: \[authentik\]\s*$/d' /var/lib/appdata/traefik/dynamic/<svc>.yml
  echo "login lines left in the route: $(sudo grep -c 'middlewares: \[authentik\]' /var/lib/appdata/traefik/dynamic/<svc>.yml)"
else
  echo "STOP: this is not <login-vm>, it is $(hostnamectl hostname); nothing was changed"
fi
```

Put it back as soon as you are done. Regenerating and pushing the login front end (guide 3.9) also
restores it:

```bash
# vm <login-vm> (bash, <admin>): run this ONLY on <login-vm>
if [ "$(hostnamectl hostname)" = "<login-vm>" ]; then
  cd /
  sudo cp -p /var/lib/appdata/traefik/<svc>.yml.login /var/lib/appdata/traefik/dynamic/<svc>.yml
  sudo rm -f /var/lib/appdata/traefik/<svc>.yml.login
  echo "login lines in the route: $(sudo grep -c 'middlewares: \[authentik\]' /var/lib/appdata/traefik/dynamic/<svc>.yml)"
else
  echo "STOP: this is not <login-vm>, it is $(hostnamectl hostname); nothing was changed"
fi
```

The first block must print `0` and the second `1`. If Traefik itself is down, no web address works;
fix Traefik first.
