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
| `reference.md` | Optional. Facts the templates rely on, each with its source link and no date. |

`pairs_with` lists other modules with `module`, `tested` (true only if the pairing was built and
worked on a real install) and `how` (one sentence). A product pairing that nobody has tested stays
out of the list or is `tested: false`; the tools refuse an untested pairing's glue because none
exists. Tight coupling goes here, in data, so the agent can recommend without forcing one choice.

## 12.2 The code

Python lives in `tools/ingress/<product>.py` or `tools/authgw/<product>.py`, because the agent runs
`python3 tools/*`. `module.yaml` names it as `code: ingress.<product>`. The generic tools
(`tools/login_frontend.py`, `tools/gen_service.py`) call these functions and name no product. A test
(`tests/test_modules.py`) fails if they do.

An ingress module provides: `route_name_problem(name)`, `check_spec(spec, reserved_paths, errors)`,
`redirect_blocks(svc, host, redirects)`, `route_text(kind, gateway_module, values)` and
`place(site, spec, gateway_module, gateway_values, routes)`. The glue for each tested gateway is a
folder `templates/gateways/<gateway module>/` with `middleware.yml.tmpl` and `route.yml.tmpl`.

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
   it worked. Until then it is `tested: false` and carries no glue.

The module goes in the repository. What the user's own install looks like stays in their workspace.
