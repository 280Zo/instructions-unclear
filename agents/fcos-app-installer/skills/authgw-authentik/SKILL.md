---
name: authgw-authentik
description: Authentik as the login page, user directory and per-app access gateway of the login front end on a Fedora CoreOS VM. Use when the user picks Authentik, or asks which login or single sign-on tool to use and the site has no auth gateway yet.
---

# authgw-authentik

Authentik gives every web app one login page, local users and groups, per-app access rules and a
dashboard of apps. A reverse proxy asks it whether to let each request through (forward auth). This
module holds its service spec, its templates and the code that writes its rules files. It names no
site: every value comes from the site file.

## What it provides, needs and pairs with

Read `module.yaml` in this folder, or run `python3 tools/modules.py list --capability auth_gateway`.

- Provides: a forward-auth endpoint, a user directory, groups, per-app access rules, an app
  dashboard, an optional sign-up page and sign-in with an existing account (Google, Apple).
- Needs: an ingress to ask it, and a database (PostgreSQL, run inside this module's own spec).
- Pairs with: `ingress-traefik`, tested.

## Choosing it

Ask the user which auth gateway they want, or recommend from the modules installed: run
`python3 tools/modules.py list` and compare. Record the choice in the site file under
`login_frontend: auth_gateway:`. Nothing here is a default.

## Files

- `spec.yaml`: the service spec (placeholders `<site: ...>` are filled from the site file).
- `templates/`: the per-app rules (a provider and an application, or a dashboard link only) and the outpost binding.
- `operations.md`: the steps that depend on this product (site values, secrets, start and check, first login, recovery, groups and people, applying the login rules). The guide pages hand over to it.
- Code: `tools/authgw/authentik.py`, called by `tools/login_frontend.py`.

To add another auth gateway, follow the module guide (`docs/guide/12-add-a-module.md`).
