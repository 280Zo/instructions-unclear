# 8. Break-glass access

**[Manual]** These are the user's steps, with their own SSH key; the agent
never runs them.

When the login front end or its auth gateway is down, the services are still running
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

1. SSH from the admin network is allowed on every VM and doesn't involve the auth gateway.
2. SSH connects to the app's port from inside the app's own VM. Traffic from a
   machine to its own address counts as local traffic, which the firewall
   accepts (`iif "lo" accept`).

If only the auth gateway is down and the ingress still runs, apps on their own login keep working at their
normal HTTPS address; apps behind the login page are refused, not let through (expected from how forward
auth works; not tested yet).

For a service that listens on `127.0.0.1` on the login front end itself (the
auth gateway does, on the port its `operations.md` names):

```fish
# desktop (fish)
ssh -N -L <port>:127.0.0.1:<port> <admin>@<login-ip>
```

These tunnels skip the login and HTTPS. Use them to fix things, not as the
normal way in, and close them when done (Ctrl+C).

**Apps that force their own `https://` address.** The tunnel above only works
in a browser for an app that builds its links from the address it is asked on.
Some apps, in production mode, build every link from their own `https://` address:
their login page loads through the tunnel, but signing in redirects to `https://localhost:8080`
and the browser stops with `SSL_ERROR_RX_RECORD_TOO_LONG`. The tunnel still shows that such an app answers
(a status check), and nothing more.

For those apps, and when only the auth gateway is down while the ingress still runs, the way in is the
app's route without the login, edited by hand and put back. The app's own login still protects it. The
ingress module's `operations.md`, "Break-glass: an app's route without the login", has the exact edit
and how to put it back, and what each block must print. If the ingress itself is down, no web address
works; fix it first.

If SSH itself is unreachable, the last way in is the VM's serial console on
the virtualization server, logging in as `<admin>` with its password. **Not
proven yet:** in the first test the serial console stayed silent although the
VM had booted with its console on the serial port (the virtualization
adapter's `reference.md`, "Console on the `proxmoxve` image").
Until that is fixed and tested, don't count on it.

**Providers.** On Proxmox VE the serial console is `qm terminal <vmid>` on the
server (leave with Ctrl+O); see the skill `adapter-proxmox` for the
platform's other manual steps.
