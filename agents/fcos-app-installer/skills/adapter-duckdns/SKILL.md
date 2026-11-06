---
name: adapter-duckdns
description: "Owner steps for DuckDNS as the DNS provider that proves the domain for the login front end's wildcard certificate (Let's Encrypt DNS-01 through Traefik and lego). Use when the owner's domain is a DuckDNS subdomain."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps from adapter.yaml.
---

# DuckDNS (dns certificates)

DuckDNS holds one TXT record at a time, so the login front end asks for one
wildcard certificate (`*.<domain>`) and never adds extra names. The token is a
secret: the owner stores it on the VM from a hidden prompt.

## How to use it

Never write these commands by hand. The shared renderer fills in every value,
refuses values that could change a command, and computes script checksums
itself. List the steps and the values each one needs, then render one step at a
time, with the values in a JSON file in `/tmp/opencode/`:

```fish
# desktop (fish)
python3 tools/adapters.py show --role dns_certificates --provider duckdns
python3 tools/adapters.py render --role dns_certificates --provider duckdns --step <id> --values /tmp/opencode/<id>.json
```

Show the rendered step to the owner as it is, then wait for what it asks them
to report back. `HOST` is the server's key in the site file, never its display
or node name.

## Steps

| Step | What it does |
|---|---|
| `api_token` | Copy your DuckDNS token for the domain |
| `acme_provider` | The certificate client's DuckDNS provider (nothing to do) |

## Official documentation

- https://go-acme.github.io/lego/dns/duckdns/
- https://doc.traefik.io/traefik/reference/install-configuration/tls/certificate-resolvers/acme/

Menu names change between versions; when one doesn't match, follow the linked documentation.
