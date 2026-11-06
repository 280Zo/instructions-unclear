# 7. Remove a service, roll back the login layer

## 7.1 Remove a service

**[Agent]**, after the user confirms the service name and whether its data
should be kept:

1. Run its backups one last time and confirm the files (section 4).
2. Stop and disable it on its VM:

```fish
# desktop (fish)
set ws <workspace>; set vm <vm>; set svc <svc>; set uid <uid>
python3 tools/vmssh.py run $vm -- "sudo loginctl disable-linger $svc; sudo systemctl stop user@$uid.service"
for f in $ws/vms/$vm/igns/{$svc,$svc-port,$svc-backup-db,$svc-backup-files}.ign
    python3 -c 'import json,sys; s=json.load(open(sys.argv[1])).get("storage",{}); [print(e["path"]) for k in ("files","links") for e in s.get(k,[])]' $f
end > /tmp/opencode/remove-$svc.txt
cat /tmp/opencode/remove-$svc.txt
```

Linger goes first, so systemd doesn't start the user's manager again. The
list holds exactly the files and links this service's fragments wrote (its
Quadlets, network, firewall port, backup units, timer links, dump scripts,
linger file); list
the same fragments as in 3.7. Folders and data are not in it. Check the list:
if any line is an error instead of a path (a fragment name that doesn't
exist), stop and fix the fragment names first. Then remove exactly those files:

```fish
# desktop (fish)
python3 tools/vmssh.py run $vm -- 'xargs -r sudo rm -f -- && sudo systemctl reload nftables' < /tmp/opencode/remove-$svc.txt
```

Ignition also made system units for the service, such as the subordinate-ID pin
`subids-<svc>.service`. They are not files in that list, and a unit left behind
fails at the next boot once the account is gone. Disable and delete them, then
the Quadlet folder if it is empty (`rmdir` refuses otherwise):

```fish
# desktop (fish)
for f in $ws/vms/$vm/igns/{$svc,$svc-port,$svc-backup-db,$svc-backup-files}.ign
    python3 -c 'import json,sys; [print(u["name"]) for u in json.load(open(sys.argv[1])).get("systemd",{}).get("units",[])]' $f
end > /tmp/opencode/remove-$svc-units.txt
cat /tmp/opencode/remove-$svc-units.txt
python3 tools/vmssh.py run $vm -- 'while read -r u; do sudo systemctl disable --now "$u"; sudo rm -f "/etc/systemd/system/$u"; done; sudo systemctl daemon-reload; sudo rmdir /etc/containers/systemd/users/'$uid' 2>/dev/null; true' < /tmp/opencode/remove-$svc-units.txt
```

3. Remove its fragments from `<workspace>/vms/<vm>/` and from `MERGE_ENTRIES`.
   Render `config.bu` and run `bash tools/build-vm.sh <workspace>/vms/<vm>`.
4. Login front end: move the spec out of `<workspace>/services/` (keep it in
   an archive folder), regenerate and push the login front end (section 3.9),
   and delete its leftover route and login-rules files there (each chosen
   module's `operations.md`, "Applying route changes" and "Applying the login
   rules"). In the auth gateway's own interface, delete the application and
   provider: deleting a rules file doesn't delete what it created (its
   `operations.md`, "Removing an app").
5. Data: its folder on the data disk and its file server folders stay until
   the user says to delete them. The service's account stays too; the next rebuild
   drops it. When the user says to delete, it is a manual step (the agent's
   key may be revoked by then): `sudo rm -rf /var/lib/appdata/<svc>` and
   `sudo userdel -r <svc>` on the VM, which also removes the account's home
   folder with its Podman secrets; then check with `getent passwd <svc>` and
   `grep <svc> /etc/subuid /etc/subgid`.
6. **[Manual]** Remove the DNS name if one per service was used
   (router_firewall: `dns_wildcard`), and the file server account if nothing
   else uses it.
7. Update the site file.

## 7.2 Turn off the login for one app

If a client can't work behind the login page even with open paths:

1. Make sure the app's own password is on.
2. In the service's spec set `login: app-only` with the reason, keep its
   `hostname`, regenerate it (section 3.6), regenerate the login front end,
   and push both (section 3.9).
3. Nothing to remove on the login front end (its two files are replaced, see
   3.9). Have the user delete its old provider in the auth gateway's
   interface.

It keeps its HTTPS address, now without the login page: same certificate,
and its port still open only to the login front end. It also stays on the
gateway's dashboard as a link that opens the app. Without a `hostname` it
would get no address at all, and be reachable only through the break-glass
tunnel (section 8).

Note for specs made before this behaviour: a service already on its own login
that still has a `hostname` gets this HTTPS address without the login page at
the next regeneration. Remove the `hostname` if it should have no address.

## 7.3 Remove the whole login layer

If the proxy-and-login approach doesn't work out, each app can be opened
directly on the LAN instead:

1. For every service: in its `<svc>-port` fragment, change `edge_tcp` to
   `lan_tcp`. That opens the port to the LAN instead of only the login front
   end. Push and reload nftables. Gap: the generator always writes `edge_tcp`,
   so this edit has to be repeated after every regeneration until it has an
   option for it.
2. Turn on every app's own password.
3. Stop the ingress and the auth gateway (each module's `operations.md`,
   "Stop it"), and remove their fragments.
4. **[Manual]** Remove the `*.<domain>` DNS entry. Clients then use
   `http://<vm-ip>:<port>`, unencrypted on the LAN; tell the user that this is
   the trade-off.

To return to the login layer, reverse these steps.
