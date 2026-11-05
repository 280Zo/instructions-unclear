---
name: adapter-opnsense
description: "Owner steps for OPNsense as the router and firewall of the fcos-app-installer toolkit: reserving a VM's address, pointing every name under the domain at the login front end, and allowing only the traffic a VM needs. Use when the owner's router or firewall is OPNsense."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps from adapter.yaml.
---

# OPNsense (router firewall)

Ask first which DHCP service hands out addresses on the VM's network
(Dnsmasq is the default; KEA, or ISC, which is end-of-life), and whether that
network gives addresses only to reserved MACs.

Traffic rules go on the interface where the traffic enters the router (the
source network's interface), never the destination's. List only the flows
that apply to the machine; traffic within one VLAN needs no rule.

## How to use it

Never write these commands by hand. The shared renderer fills in every value,
refuses values that could change a command, and computes script checksums
itself. List the steps and the values each one needs, then render one step at a
time, with the values in a JSON file in `/tmp/opencode/`:

```fish
# desktop (fish)
python3 tools/adapters.py show --role router_firewall --provider opnsense
python3 tools/adapters.py render --role router_firewall --provider opnsense --step <id> --values /tmp/opencode/<id>.json
```

Show the rendered step to the owner as it is, then wait for what it asks them
to report back. `HOST` is the server's key in the site file, never its display
or node name.

## Steps

| Step | What it does |
|---|---|
| `reserve_ip` | Reserve a VM's address for its MAC |
| `dns_wildcard` | Send every name under the domain to the login front end |
| `allow_flows` | Allow only the traffic a VM needs |

## Official documentation

- https://docs.opnsense.org/manual/dhcp.html
- https://docs.opnsense.org/manual/unbound.html
- https://docs.opnsense.org/manual/firewall.html

Menu names change between versions; when one doesn't match, follow the linked documentation.
