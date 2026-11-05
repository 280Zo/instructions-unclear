# 8. Break-glass access

**[Owner]** These are the owner's steps, with their own SSH key; the agent
never runs them.

When the login front end or Authentik is down, the services are still running
on their VMs; only the way in is gone. Their ports refuse every machine except
the login front end, but SSH from the admin LAN still works, so tunnel through
it. Test these steps once after the login front end is built, so they are known
to work before they are needed.

```fish
# desktop (fish)
ssh -N -L 8080:<vm-ip>:<port> <admin>@<vm-ip>
```

Then open `http://localhost:8080` on the desktop. Why it works even though the
port refuses every machine except the login front end:

1. SSH from the admin network is allowed on every VM and doesn't involve Authentik.
2. SSH connects to the app's port from inside the app's own VM. Traffic from a
   machine to its own address counts as local traffic, which the firewall
   accepts (`iif "lo" accept`).

If only Authentik is down and Traefik still runs, apps on their own login keep
working at their normal HTTPS address; apps behind the login page are refused,
not let through (expected from how forward auth works; not tested yet).

For a service that listens on `127.0.0.1` on the login front end itself (such
as Authentik):

```fish
# desktop (fish)
ssh -N -L 9000:127.0.0.1:9000 <admin>@<login-ip>
```

These tunnels skip the login and HTTPS. Use them to fix things, not as the
normal way in, and close them when done (Ctrl+C).

**Apps that force their own `https://` address.** The tunnel above only works
in a browser for an app that builds its links from the address it is asked on.
Monica, in production mode, builds every link from its own `https://` address:
tested on a real install, its login page loaded through the tunnel, but signing
in redirected to `https://localhost:8080` and Firefox stopped with
`SSL_ERROR_RX_RECORD_TOO_LONG`. The tunnel still shows that such an app answers
(a status check), and nothing more.

For those apps, and when only Authentik is down while Traefik still runs, the
way in is the app's route without the login, edited by hand and put back. The
app's own login still protects it. Tested end to end on a real install: the
address answered with the app's own page instead of a redirect, signing in
worked, and after the restore the redirect to the login page was back. In the
generated route file (`dynamic/<svc>.yml` on the login front end VM), the login
is the single line `middlewares: [authentik]` on the app's router. Take a copy
outside the watched folder, remove the line, and Traefik reloads the file by
itself (Monica shown; each block stops by itself on any other machine):

```bash
# vm <login-vm> (bash, <admin>): run this ONLY on <login-vm>
if [ "$(hostnamectl hostname)" = "<login-vm>" ]; then
  cd /
  sudo cp -p /var/lib/appdata/traefik/dynamic/monica.yml /var/lib/appdata/traefik/monica.yml.login
  sudo sed -i '/^\s*middlewares: \[authentik\]\s*$/d' /var/lib/appdata/traefik/dynamic/monica.yml
  echo "login lines left in the route: $(sudo grep -c 'middlewares: \[authentik\]' /var/lib/appdata/traefik/dynamic/monica.yml)"
else
  echo "STOP: this is not <login-vm>, it is $(hostnamectl hostname); nothing was changed"
fi
```

Put it back as soon as you are done. Regenerating and pushing the login front
end (guide 3.9) also restores it:

```bash
# vm <login-vm> (bash, <admin>): run this ONLY on <login-vm>
if [ "$(hostnamectl hostname)" = "<login-vm>" ]; then
  cd /
  sudo cp -p /var/lib/appdata/traefik/monica.yml.login /var/lib/appdata/traefik/dynamic/monica.yml
  sudo rm -f /var/lib/appdata/traefik/monica.yml.login
  echo "login lines in the route: $(sudo grep -c 'middlewares: \[authentik\]' /var/lib/appdata/traefik/dynamic/monica.yml)"
else
  echo "STOP: this is not <login-vm>, it is $(hostnamectl hostname); nothing was changed"
fi
```

The first block must print `0` and the second `1`. If Traefik itself is down,
no web address works; fix Traefik first.

If SSH itself is unreachable, the last way in is the VM's serial console on
the virtualization server, logging in as `<admin>` with its password. **Not
proven yet:** in the first test the serial console stayed silent although the
VM had booted with its console on the serial port (research notes row 13).
Until that is fixed and tested, don't count on it.

**Providers.** On Proxmox VE the serial console is `qm terminal <vmid>` on the
server (leave with Ctrl+O); see the skill `adapter-proxmox` for the
platform's other owner steps.
