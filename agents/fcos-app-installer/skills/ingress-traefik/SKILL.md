---
name: ingress-traefik
description: Traefik as the reverse proxy and TLS front door of the login front end on a Fedora CoreOS VM. Use when the user picks Traefik, or asks which reverse proxy to use and the site has no ingress yet.
---

# ingress-traefik

Traefik is a reverse proxy. On the login front end VM it ends TLS with one wildcard certificate and
sends each service's web name to the service. This module holds its service spec, its templates and
the code that writes its files. It names no site: every value comes from the site file.

## What it provides, needs and pairs with

Read `module.yaml` in this folder, or run `python3 tools/modules.py list --capability ingress`.

- Provides: TLS termination, host-based routing, and a forward-auth client.
- Needs: the ACME DNS-01 data of the site's DNS provider (the `dns_certificates` adapter), and an
  auth gateway for any service behind the login page.
- Pairs with: `authgw-authentik`, tested. Other auth gateways support the same forward-auth
  pattern, but this module has glue only for the pairings it lists. Glue for a pairing marked
  `tested: false` is experimental.

## Choosing it

Ask the user which ingress they want, or recommend from the modules installed: run
`python3 tools/modules.py list` and compare. Record the choice in the site file under
`login_frontend: ingress:`. Nothing here is a default.

## Files

- `spec.yaml`: the service spec (placeholders `<site: ...>` are filled from the site file).
- In this folder's `templates` folder: `traefik.yml.tmpl` (the static settings) and `route-open.yml.tmpl` (a route with no login in front).
- In `templates/gateways`, one folder per auth gateway this module has been tested with: the forward-auth middleware and the route behind it.
- `operations.md`: the steps that depend on this product (site values, the certificate, secrets, start and check, applying route changes, the break-glass route edit). The guide pages hand over to it.
- Code: `tools/ingress/traefik.py`, called by `tools/login_frontend.py`.

## An install built before the glue file was renamed

The shared forward-auth file is `00-<auth gateway module>.yml` (here `00-authgw-authentik.yml`) in
Traefik's dynamic folder. An install built earlier has the same file as `00-authentik.yml`. A rebuild
or an update of the login front end writes the new name and leaves the old one, and both define the
same middleware and service names. After pushing the login front end, the user deletes the old file:
`sudo rm /var/lib/appdata/traefik/dynamic/00-authentik.yml` on the login VM. Traefik reads the folder
live, so no restart is needed.

To add another ingress or another pairing, follow the module guide (`docs/guide/12-add-a-module.md`).
