# 12. Add a module for another tool

A module teaches the toolkit one product. The login front end uses two kinds: an ingress (a reverse
proxy) and an auth gateway (a login and single sign-on service). Each is a skill folder, one per
product, so only the ones a site chose are loaded. Nothing is a default: the site file names its
choice, and the agent asks the user, or recommends from `python3 tools/modules.py list`.

Build a module only when the user wants a product the list doesn't have. The user's own working
setup (their values, their rendered files, what they verified on their machines) stays in their
workspace. A module holds only what any user of that product needs: a template, a spec, a guide and
the facts behind them.

## 12.1 What a module is

A folder in the skills folder, named `<prefix>-<product>`: `ingress-<product>` or
`authgw-<product>`.

| File | Holds |
|---|---|
| `SKILL.md` | `name` (the folder name) and a `description` that says what the product is and starts its "when" with "Use when". The body says what it provides, needs and pairs with, and how to choose it. |
| `module.yaml` | `capability` (`ingress` or `auth_gateway`), `product`, `summary`, `provides`, `needs`, `pairs_with`, `spec`, `code`, optional `notes`. |
| `spec.yaml` | The product as a normal service spec (`schemas/service.schema.md`). Values that come from the site are written `<site: a.b.c>`. No real values. |
| `templates/` | The files the product needs, with `{{PLACEHOLDERS}}`. |
| `operations.md` | The steps that depend on the product, which the guide pages (6, 3.9, 7, 8) hand over to. For an ingress: "Site values", "Ports and the VM", "The certificate and the DNS provider", "Secrets on the login VM", "Start and check", "Applying route changes", "Stop it" and "Break-glass: an app's route without the login". For an auth gateway: "Site values", "The containers", "Secrets on the login VM", "Start and check", "First login", "Admin recovery", "End-to-end check", "Who may open an app", "The dashboard section and the logo", "Applying the login rules", "Removing an app", "People and access", "Upgrading", "Stop it" and "Restoring the database". |
| `site.example.yaml` | The module's section of the site file, under `edge`, named after its service, with example values. The leak scanner counts these values as public, so a user's own matching values are not flagged. |
| `reference.md` | Optional. Facts the templates rely on, each with its source link and no date. |

`pairs_with` lists other modules with `module`, `tested` (true only if the pairing was built and
worked on a real install) and `how` (one sentence). A pairing that nobody has tested is
`tested: false` or left out. It can still have glue, marked experimental, so someone can try it; the
generator then prints a note that the pairing is untested. Without glue it stops with an error.
Tight coupling goes here, in data, so the agent can recommend without forcing one choice.

## 12.2 The code

Python lives in `tools/ingress/<product>.py` or `tools/authgw/<product>.py`, because the agent runs
`python3 tools/*`. `module.yaml` names it as `code: ingress.<product>`. The generic tools
(`tools/login_frontend.py`, `tools/gen_service.py`) call these functions and name no product. A test
(`tests/test_modules.py`) fails if they do.

An ingress module provides: `check_site(site)` (raises `SpecError` for a site key it needs and finds missing or
wrong, such as the address a certificate authority writes to; the generic tools check no product's keys),
`route_name_problem(name)`, `check_spec(spec, reserved_paths, errors)`,
`redirect_blocks(svc, host, redirects)`, `route_text(kind, gateway, values)` and
`place(site, spec, gateway, gateway_values, routes, acme)`. `gateway` is the auth gateway module's
name, `gateway_values` what that module's `forward_auth_values(site)` returned, and `acme` the
certificate data the DNS adapter carries. The glue for a gateway is a folder
`templates/gateways/<gateway module>/` with `middleware.yml.tmpl` and `route.yml.tmpl`.

An auth gateway module provides: `reserved_route_names()`, `reserved_route_suffix()`,
`reserved_paths()`, `forward_auth_values(site)`, `host_label(site, domain)`, `check_spec(spec, errors)`,
`binding_text(spec, values, kind)`, `settings(site)`, `prepare_spec(spec, config)` and
`place(site, spec, config, routed, bindings, icon_dirs)`.

Read the two existing modules' code before writing a third; the contract is what they do.

## 12.3 How to add one

1. Ask the user which product and why. Read the product's official documentation (not memory), and
   write the facts you rely on, with their links, into the module's `reference.md`.
2. Copy the closest existing module's folder and code, rename it, and change what the product needs.
   Keep every site-specific value a `<site: ...>` placeholder.
3. Write the tests first: a module test like `tests/test_modules.py` (the layout, the pairings), and
   generator tests like `tests/test_login_frontend.py` run against the fixtures in `tests/fixtures/`.
4. Generate with the fixture site and run `bash tools/validate.sh tests/fixtures/edge.values`, then the
   whole suite (`python3 -m unittest discover tests`).
5. Add the skill's name pattern to the agent's skill allow-list if its prefix is new, and add its
   folder to the FCOS skills count tests.
6. Mark the pairing `tested: true` only after the user has built it on a real install and told you
   it worked. Until then it is `tested: false`, and any glue is experimental.

## 12.4 An adapter with a tool

An adapter is a system the user runs by hand. When that system has an API the agent can use with a
limited token, the adapter may also ship a tool. Only the virtualization role has one today. The
adapter names it in `adapter.yaml`: `code: virtualization.<provider>`, a file in
`tools/virtualization/` named like the provider (dashes become underscores). The agent never runs that
file. It runs `python3 tools/hypervisor.py <verb> ...`, which reads `roles.virtualization.provider` from
the site file, loads the adapter's code and hands it the arguments unchanged. The code must define
`VERBS = ("check", "list", "create", "start", "status")` and `main(argv)`; `tools/hypervisor.py` refuses
an adapter whose code doesn't, and `tools/adapters.py` checks the `code:` name. The verbs are all the
agent can do through the API: nothing that deletes or needs root, because those stay manual steps in the
adapter. A hypervisor without an API has no `code:`, and `hypervisor.py` says it has no tool.

What the adapter defines besides the verbs, because the generic tools and the guide leave it to the tool:

- **The VM spec.** The fields of `<workspace>/vms/<vm>/vm.yaml` are the tool's own. The adapter's
  `vm.example.yaml` lists every one. `create` must refuse a spec where a setting is missing, unexplained or
  out of range, and `--dry-run` must print the whole plan (the guide has the user review it) before
  anything is sent.
- **The server's section of the site file.** The keys under `hosts.<host>` are the tool's own, shown in the
  adapter's `site.example.yaml`. The generic tools read only `name` and `always_on`.
- **The token.** The adapter's `store_api_token` step writes the token to `<workspace>/secrets/` from a
  hidden prompt, together with the address of the server, and the tool sends the token only to the address
  stored with the token, never to one from the site file (the agent may edit that file). `teardown_api_access`
  removes the access when the install is done. An adapter with a tool must define both steps, besides the
  role's own; `tools/adapters.py` refuses one that doesn't.

The module goes in the repository. What the user's own install looks like stays in their workspace.
