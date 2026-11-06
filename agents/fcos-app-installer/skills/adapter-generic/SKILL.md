---
name: adapter-generic
description: "Provider-neutral owner steps for the fcos-app-installer toolkit's roles (virtualization, router and firewall, file server, DNS for certificates). Use when the owner's product for a role has no adapter skill of its own; afterwards offer to draft one."
license: MIT
compatibility: Needs the fcos-app-installer toolkit; tools/adapters.py renders the steps from adapter.yaml.
---

# General steps for any product

`tools/adapters.py` falls back to these steps by itself when no
`adapter-<provider>` skill exists, and marks the adapter as generic. Say so to
the owner: the steps describe what to achieve, not where it is in their
product's menus. Look up the product's official documentation for each step.

When the install is done, offer to draft an adapter skill for the product from
what the owner actually did: hand it to the `adapter-drafter` subagent, which
writes `<workspace>/adapters-draft/adapter-<provider>/` for review.

## How to use it

Never write these commands by hand. The shared renderer fills in every value,
refuses values that could change a command, and computes script checksums
itself. List the steps and the values each one needs, then render one step at a
time, with the values in a JSON file in `/tmp/opencode/`:

```fish
# desktop (fish)
python3 tools/adapters.py show --role <role> --provider <product>
python3 tools/adapters.py render --role <role> --provider <product> --step <id> --values /tmp/opencode/<id>.json
```

Show the rendered step to the owner as it is, then wait for what it asks them
to report back. `HOST` is the server's key in the site file, never its display
or node name.

## Steps per role

| Role | Steps |
|---|---|
| virtualization | `download_image`, `copy_ignition_snippet`, `rebuild_os_disk`, `create_api_access` |
| router firewall | `reserve_ip`, `dns_wildcard`, `allow_flows` |
| file server | `nfs_export`, `service_user`, `backup_folder` |
| dns certificates | `api_token`, `acme_provider` |

A DNS adapter also carries an `acme` block (the certificate client's provider code, the variable the
token goes in, the secret's name). An adapter drafted for an earlier version names its second step
`traefik_provider`: rename it `acme_provider` and add the block, or the check reports the role's
steps as missing.
