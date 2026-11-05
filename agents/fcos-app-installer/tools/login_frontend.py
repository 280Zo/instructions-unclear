#!/usr/bin/env python3
"""Generate the login front end (Traefik + Authentik) for its VM.

Usage: login_frontend.py <site.yaml> <out-dir> [<service.yaml> ...]

The two parts are normal service specs, specs/login-frontend/traefik.yaml and
authentik.yaml. Values written there as "<site: a.b.c>" come from the site
file; a missing one is an error that names it. Both are built with
gen_service.generate into <out-dir>/rendered/, like any service. On top, this
writes the login front end's own files and one Butane fragment,
rendered/login-frontend.bu, that places them in the folders the containers
mount (overwrite: true, so a rebuild rewrites them):

  traefik config/traefik.yml       static settings (wildcard certificate)
  traefik dynamic/00-authentik.yml forward-auth middleware, route to Authentik
  traefik dynamic/<svc>.yml        one route per routed service (through the
                                   login page, or open for own-login services)
  authentik blueprints/app-<svc>.yaml        provider + application (login page),
                                             or a dashboard link only (own login)
  authentik blueprints/outpost-providers.yaml binds them all to the outpost

Every service spec given is validated in full. Services behind the login page
(login authentik) get a route through the login middleware, login rules and an
outpost entry; services on their own login with a hostname get an HTTPS route
without the login page and a dashboard link (an application with no
provider, never on the outpost); the rest get no route. secrets.md lists the secrets of
both parts.
"""

import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_service import (APPDATA, icon_ref, DOMAIN, HOST_LABEL, SpecError, _fill, _plain, _vm_entry,  # noqa: E402
                         _volume_host, _write_all, generate, has_route, route_texts, validate_spec)

SPECS = Path(__file__).resolve().parent.parent / "specs" / "login-frontend"
PLACEHOLDER = re.compile(r"<site: ([a-z_]+(?:\.[a-z_]+)*)>")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
RESERVED_ROUTE_NAMES = {"authentik-server", "authentik-outpost"}


def _site_value(site: dict, dotted: str):
    node = site
    for key in dotted.split("."):
        if not isinstance(node, dict) or node.get(key) is None:
            raise SpecError(f"site.yaml: {dotted} is missing (the login front end needs it)")
        node = node[key]
    return node


def _filled(node, site: dict):
    if isinstance(node, dict):
        return {k: _filled(v, site) for k, v in node.items()}
    if isinstance(node, list):
        return [_filled(v, site) for v in node]
    if isinstance(node, str):
        match = PLACEHOLDER.fullmatch(node)
        if match:
            return _site_value(site, match.group(1))
        if "<site:" in node:
            raise SpecError(f"login front end spec: malformed placeholder {node!r}")
    return node


def frontend_specs(site: dict) -> tuple[dict, dict]:
    """The Traefik and Authentik specs with every <site: ...> value filled in."""
    import yaml
    specs = []
    for name in ("traefik", "authentik"):
        spec = yaml.safe_load((SPECS / f"{name}.yaml").read_text(encoding="utf-8"))
        specs.append(_filled(spec, site))
    return specs[0], specs[1]


def _folder(spec: dict, container_path: str) -> str:
    """The VM folder behind the volume mounted at container_path."""
    for ctr in spec["containers"]:
        for vol in ctr.get("volumes") or []:
            if vol["path"] == container_path:
                return _volume_host(spec["name"], ctr["name"], vol)
    raise SpecError(f"login front end spec {spec['name']}: no volume at {container_path}")


def _check_site(site: dict) -> tuple[str, str]:
    """(edge vm name, authentik host); errors name the site field."""
    edge_vm = _site_value(site, "edge.vm")
    if _vm_entry(site, edge_vm) is None:
        raise SpecError(f"site.yaml: edge.vm {edge_vm!r} is not listed in vms")
    domain = _site_value(site, "domain")
    if not (_plain(domain) and DOMAIN.fullmatch(domain)):
        raise SpecError("site.yaml: domain is invalid")
    email = _site_value(site, "acme_email")
    if not (_plain(email) and EMAIL.fullmatch(email)):
        raise SpecError("site.yaml: acme_email must be an email address")
    host = _site_value(site, "edge.authentik.host")
    label, _, rest = host.partition(".") if isinstance(host, str) else ("", "", "")
    if not (_plain(host) and HOST_LABEL.fullmatch(label) and rest == domain):
        raise SpecError("site.yaml: edge.authentik.host must be one name directly under the domain "
                        "(the certificate covers only *.<domain>)")
    return edge_vm, label


def _routed(site: dict, services: list, edge_vm: str, auth_label: str) -> list[dict]:
    errors, routed, hostnames, names = [], [], {}, set()
    for spec in services:
        name = spec.get("name") if isinstance(spec, dict) else None
        problems = validate_spec(spec, site)
        if problems:
            errors += [f"service {name!r}: {p}" for p in problems]
            continue
        if name in names or name in ("traefik", "authentik"):
            errors.append(f"service {name!r}: the name is used twice or by the login front end")
        names.add(name)
        if not has_route(spec):
            continue
        # Traefik router/service names: 00-authentik.yml defines authentik-server
        # and authentik-outpost, and each login-page route adds <svc>-outpost
        # (open routes don't, but a later switch to the login page would). A
        # name defined twice would break the shared login routes for every app.
        if name in RESERVED_ROUTE_NAMES or name.endswith("-outpost") or re.search(r"-redirect-[0-9]+$", name):
            errors.append(f"service {name!r}: this name clashes with the login front end's route names "
                          "(authentik-server, authentik-outpost, <name>-outpost, <name>-redirect-<n>); pick another")
        if spec.get("bind", "vm_ip") == "loopback" and spec["vm"] != edge_vm:
            errors.append(f"service {name!r}: bind loopback is only reachable on the login front end VM "
                          f"({edge_vm}); use vm_ip")
        hostname = spec["hostname"]
        if hostname == auth_label:
            errors.append(f"service {name!r}: hostname {hostname!r} is the login page's own name")
        elif hostname in hostnames:
            errors.append(f"service {name!r}: hostname {hostname!r} is already used by {hostnames[hostname]!r}")
        hostnames[hostname] = name
        routed.append(spec)
    if errors:
        raise SpecError("\n".join(errors))
    return sorted(routed, key=lambda s: s["name"])


PERSON = re.compile(r"[a-z][a-z0-9._-]{0,62}")
GROUP_NAME = re.compile(r"[a-z][a-z0-9-]{0,62}")
RESERVED_USERS = {"akadmin"}


def _people(site: dict) -> list[dict]:
    """site.yaml people: local Authentik users (owner, 2026-11-02: no email, no self sign-up).
    Each {username, name, groups}; passwords are set by the owner in Authentik."""
    people = site.get("people")
    if people is None:
        return []
    errors, seen = [], set()
    if not isinstance(people, list):
        raise SpecError("site.yaml: people must be a list of {username, name, groups}")
    for n, person in enumerate(people):
        where = f"site.yaml people[{n}]"
        if not isinstance(person, dict) or set(person) != {"username", "name", "groups"}:
            errors.append(f"{where}: needs exactly username, name and groups (no password or email: "
                          "the owner sets the password in Authentik)")
            continue
        user, name, groups = person["username"], person["name"], person["groups"]
        if not (isinstance(user, str) and PERSON.fullmatch(user)) or user in RESERVED_USERS or user.startswith("ak-"):
            errors.append(f"{where}: username must be lowercase letters, digits, . _ - (not akadmin or ak-...)")
        elif user in seen:
            errors.append(f"{where}: username {user!r} is listed twice")
        seen.add(user)
        if not (isinstance(name, str) and 0 < len(name) <= 100 and name.isprintable()):
            errors.append(f"{where}: name must be one line of at most 100 characters")
        if not (isinstance(groups, list) and len(set(groups)) == len(groups)
                and all(isinstance(g, str) and GROUP_NAME.fullmatch(g) for g in groups)):
            errors.append(f"{where}: groups must be a list of different lowercase group names")
    if errors:
        raise SpecError("\n".join(errors))
    return people


def _signup(site: dict) -> dict | None:
    """site.yaml signup: {group, approve?}: a sign-up page for anyone who can reach the login page
    (owner, 2026-11-03), no email; new accounts land in `group`, inactive until approved if approve."""
    signup = site.get("signup")
    if signup is None:
        return None
    if (not isinstance(signup, dict) or not set(signup) <= {"group", "approve"}
            or not (isinstance(signup.get("group"), str) and GROUP_NAME.fullmatch(signup["group"]))
            or not isinstance(signup.get("approve", False), bool)):
        raise SpecError("site.yaml: signup must be {group: <lowercase group>, approve: true|false (optional)}")
    return signup


# Sign in with an existing account (owner, 2026-11-03). The client id is not secret; the
# secret reaches the worker as an environment variable from a Podman secret (!Env).
SOURCE_TYPES = {
    "google": {"secret": "authentik_google_secret", "env": "SOURCE_GOOGLE_SECRET", "how": "prompt",
               "client": re.compile(r"[A-Za-z0-9._-]{1,200}"), "label": "Google"},
    # Apple: <services id>;<team id>;<key id> (authentik docs, social-logins/apple).
    "apple": {"secret": "authentik_apple_key", "env": "SOURCE_APPLE_KEY", "how": "file",
              "client": re.compile(r"[A-Za-z0-9.-]{1,150};[A-Z0-9]{10};[A-Z0-9]{10}"), "label": "Apple"},
}


def _sources(site: dict, signup: dict | None) -> dict:
    sources = site.get("signin_sources")
    if sources is None:
        return {}
    ok = isinstance(sources, dict) and sources and all(
        kind in SOURCE_TYPES and isinstance(conf, dict) and set(conf) == {"client_id"}
        and isinstance(conf["client_id"], str) and SOURCE_TYPES[kind]["client"].fullmatch(conf["client_id"])
        for kind, conf in sources.items())
    if not ok:
        raise SpecError("site.yaml: signin_sources must map google and/or apple to {client_id} "
                        "(Apple: <services id>;<team id>;<key id>); never a secret")
    if not signup:
        raise SpecError("site.yaml: signin_sources needs signup: {group: ...} (the group new people land in)")
    return sources


def _source_entries(sources: dict, signup: dict) -> list[str]:
    """Authentik's default source enrollment flow (ask a username only if the provider gave none,
    only inside a source sign-in), adding new people to the sign-up group; then each source."""
    out = ["  - model: authentik_flows.flow", "    id: signup-source-flow", "    identifiers:",
           "      slug: signup-source", "    attrs:", "      name: Sign up with an existing account",
           "      title: Choose a username", "      designation: enrollment", "      authentication: none",
           "  - model: authentik_stages_prompt.prompt", "    id: signup-source-field-username", "    identifiers:",
           "      name: signup-source-field-username", "    attrs:", "      field_key: username",
           '      label: "Username"', "      type: username", "      required: true", '      placeholder: "Username"',
           "      placeholder_expression: false", "      order: 100",
           "  - model: authentik_policies_expression.expressionpolicy", "    id: signup-source-if-username",
           "    identifiers:", "      name: signup-source-if-username", "    attrs:",
           "      expression: return 'username' not in context.get('prompt_data', {})",
           "  - model: authentik_policies_expression.expressionpolicy", "    id: signup-source-if-sso",
           "    identifiers:", "      name: signup-source-if-sso", "    attrs:", "      expression: return ak_is_sso_flow",
           "  - model: authentik_stages_prompt.promptstage", "    id: signup-source-prompt", "    identifiers:",
           "      name: signup-source-prompt", "    attrs:", "      fields: [!KeyOf signup-source-field-username]",
           "  - model: authentik_stages_user_write.userwritestage", "    id: signup-source-write", "    identifiers:",
           "      name: signup-source-write", "    attrs:", "      user_creation_mode: always_create",
           f"      create_users_as_inactive: {'true' if signup.get('approve') else 'false'}",
           f'      create_users_group: !Find [authentik_core.group, [name, "{signup["group"]}"]]',
           "      user_type: internal",
           "  - model: authentik_stages_user_login.userloginstage", "    id: signup-source-login", "    identifiers:",
           "      name: signup-source-login",
           "  - model: authentik_flows.flowstagebinding", "    id: signup-source-prompt-binding", "    identifiers:",
           "      target: !KeyOf signup-source-flow", "      stage: !KeyOf signup-source-prompt", "      order: 0",
           "    attrs:", "      re_evaluate_policies: true"]
    for order, stage in ((1, "signup-source-write"), (2, "signup-source-login")):
        out += ["  - model: authentik_flows.flowstagebinding", "    identifiers:",
                "      target: !KeyOf signup-source-flow", f"      stage: !KeyOf {stage}", f"      order: {order}"]
    out += ["  - model: authentik_policies.policybinding", "    identifiers:", "      target: !KeyOf signup-source-flow",
            "      policy: !KeyOf signup-source-if-sso", "      order: 0",
            "  - model: authentik_policies.policybinding", "    identifiers:",
            "      target: !KeyOf signup-source-prompt-binding", "      policy: !KeyOf signup-source-if-username",
            "      order: 0"]
    for kind, conf in sources.items():
        info = SOURCE_TYPES[kind]
        out += ["  - model: authentik_sources_oauth.oauthsource", f"    id: source-{kind}", "    identifiers:",
                f"      slug: {kind}", "    attrs:", f'      name: "{info["label"]}"', f"      provider_type: {kind}",
                f'      consumer_key: "{conf["client_id"]}"', f"      consumer_secret: !Env {info['env']}",
                "      authentication_flow: !Find [authentik_flows.flow, [slug, default-source-authentication]]",
                "      enrollment_flow: !KeyOf signup-source-flow"]
    return out


def _signup_entries(signup: dict) -> list[str]:
    """Authentik's example flows-enrollment-2-stage.yaml without the email field, with the
    default group (user_write create_users_group) and the link on the sign-in page."""
    out = ["  - model: authentik_flows.flow", "    id: signup-flow", "    identifiers:", "      slug: signup",
           "    attrs:", "      name: Sign up", "      title: Create your account", "      designation: enrollment",
           "      authentication: require_unauthenticated"]
    prompts = (("username", "Username", "username", 0), ("password", "Password", "password", 1),
               ("password_repeat", "Password (repeat)", "password", 2), ("name", "Your name", "text", 0))
    for key, label, kind, order in prompts:
        out += ["  - model: authentik_stages_prompt.prompt", f"    id: signup-field-{key}", "    identifiers:",
                f"      name: signup-field-{key}", "    attrs:", f"      field_key: {key}", f'      label: "{label}"',
                f"      type: {kind}", "      required: true", f'      placeholder: "{label}"',
                "      placeholder_expression: false", f"      order: {order}"]
    # Anyone may sign up, so a weak password is refused (checked locally: never sent outside).
    out += ["  - model: authentik_policies_password.passwordpolicy", "    id: signup-password-policy",
            "    identifiers:", "      name: signup-password-policy", "    attrs:",
            "      check_static_rules: true", "      length_min: 12", "      check_zxcvbn: true",
            "      zxcvbn_score_threshold: 2", "      check_have_i_been_pwned: false",
            '      error_message: "Use at least 12 characters, and nothing easy to guess."']
    out += ["  - model: authentik_stages_prompt.promptstage", "    id: signup-prompt-first", "    identifiers:",
            "      name: signup-prompt-first", "    attrs:", "      fields: [!KeyOf signup-field-username, "
            "!KeyOf signup-field-password, !KeyOf signup-field-password_repeat]",
            "      validation_policies: [!KeyOf signup-password-policy]",
            "  - model: authentik_stages_prompt.promptstage", "    id: signup-prompt-second", "    identifiers:",
            "      name: signup-prompt-second", "    attrs:", "      fields: [!KeyOf signup-field-name]",
            "  - model: authentik_stages_user_write.userwritestage", "    id: signup-write", "    identifiers:",
            "      name: signup-write", "    attrs:", "      user_creation_mode: always_create",
            f"      create_users_as_inactive: {'true' if signup.get('approve') else 'false'}",
            f'      create_users_group: !Find [authentik_core.group, [name, "{signup["group"]}"]]',
            "      user_type: internal",
            "  - model: authentik_stages_user_login.userloginstage", "    id: signup-login", "    identifiers:",
            "      name: signup-login"]
    for order, stage in ((10, "signup-prompt-first"), (11, "signup-prompt-second"), (20, "signup-write"),
                         (100, "signup-login")):
        out += ["  - model: authentik_flows.flowstagebinding", "    identifiers:", "      target: !KeyOf signup-flow",
                f"      stage: !KeyOf {stage}", f"      order: {order}"]
    # Only the link is added to the default sign-in stage; its other settings stay.
    return out


def _identification_entry(signup: dict, sources: dict) -> list[str]:
    # Only the sign-up link and the source buttons are set on the default sign-in stage.
    out = ["  - model: authentik_stages_identification.identificationstage", "    identifiers:",
           "      name: default-authentication-identification", "    attrs:",
           # Required on every update by its serializer; the values of Authentik's default flow
           # (blueprints/default/flow-default-authentication-flow.yaml).
           "      user_fields: [email, username]",
           "      enrollment_flow: !KeyOf signup-flow"]
    if sources:
        out.append("      sources: [" + ", ".join(f"!KeyOf source-{k}" for k in sources) + "]")
    return out


def _signup_blueprint(signup: dict, sources: dict) -> str:
    """The sign-up page and sign-in sources, apart from access.yaml: a failure here (a secret
    not created yet) must never roll back the app bindings (review 2026-11-03)."""
    out = ["# Sign-up page and sign-in with an existing account. Written by tools/login_frontend.py.",
           "# access.yaml (groups) is applied first.", "version: 1", "metadata:", "  name: signup",
           "  labels:", '    blueprints.goauthentik.io/instantiate: "true"', "entries:",
           "  - model: authentik_blueprints.metaapplyblueprint", "    attrs:", "      identifiers:",
           '        name: "access"', "      required: true"]
    out += _signup_entries(signup)
    if sources:
        out += _source_entries(sources, signup)
    out += _identification_entry(signup, sources)
    return "\n".join(out) + "\n"


def _access_blueprint(people: list[dict], routed: list[dict], signup: dict | None = None,
                      sources: dict | None = None) -> str:
    """The one rules file that creates groups (from people and every app's groups), the
    people, and each app's group bindings. Each app's own rules are applied first
    (metaapplyblueprint, required), so its application exists before it is bound."""
    bound = [s for s in routed if s.get("groups") and s["login"] == "authentik"]
    groups = sorted({g for p in people for g in p["groups"]} | {g for s in bound for g in s["groups"]}
                    | ({signup["group"]} if signup else set()))
    out = ["# Groups, local people and app access in Authentik (site.yaml people, each app's groups).",
           "# Written by tools/login_frontend.py. Users are created once (state: created): later group",
           "# changes made in the admin interface stay. No passwords: the owner sets each one in Authentik.",
           "version: 1", "metadata:", "  name: access",
           "  labels:", '    blueprints.goauthentik.io/instantiate: "true"', "entries:"]
    for spec in bound:
        out += ["  - model: authentik_blueprints.metaapplyblueprint", "    attrs:", "      identifiers:",
                f'        name: "app-{spec["name"]}"', "      required: true"]
    for group in groups:
        out += ["  - model: authentik_core.group", f"    id: group-{group}", "    identifiers:",
                f'      name: "{group}"']
    for person in people:
        member = ", ".join(f"!KeyOf group-{g}" for g in person["groups"])
        out += ["  - model: authentik_core.user", "    state: created", "    identifiers:",
                f'      username: "{person["username"]}"', "    attrs:",
                f"      name: {json.dumps(person['name'], ensure_ascii=False)}", "      type: internal",
                "      path: users", f"      groups: [{member}]"]
    for spec in bound:
        # Found by app + group, so the owner's own bindings and the other groups are left alone.
        for order, group in enumerate(spec["groups"]):
            out += ["  - model: authentik_policies.policybinding", "    identifiers:",
                    f'      target: !Find [authentik_core.application, [slug, "{spec["name"]}"]]',
                    f"      group: !KeyOf group-{group}", "    attrs:", f"      order: {order}"]
    return "\n".join(out) + "\n"


# An SVG served from the login page's own address must not carry script.
SVG_SCRIPT = re.compile(r"<script|\bon[a-z]+\s*=|javascript:|<foreignObject", re.I)

def _dir_entry(path: str, uid: int, gid: int) -> str:
    return (f"    - path: {path}\n      mode: 0750\n"
            f"      user:\n        id: {uid}\n      group:\n        id: {gid}")


def _file_entry(path: str, local: str, uid: int, gid: int) -> str:
    return (f"    - path: {path}\n      mode: 0640\n      overwrite: true\n"
            f"      user:\n        id: {uid}\n      group:\n        id: {gid}\n"
            f"      contents:\n        local: {local}")


def generate_login_frontend(site: dict, services: list, out, icon_dirs: dict | None = None) -> list[Path]:
    edge_vm, auth_label = _check_site(site)
    people = _people(site)
    traefik, authentik = frontend_specs(site)
    signup = _signup(site)
    sources = _sources(site, signup)
    for kind in sources:
        info = SOURCE_TYPES[kind]
        worker = next(c for c in authentik["containers"] if c["name"] == "worker")
        worker.setdefault("secrets", []).append({"env": info["env"], "name": info["secret"]})
        authentik.setdefault("secrets", []).append({"name": info["secret"], "durable": True, "source": info["how"]})
    # Check both parts before writing anything, so a bad site value can't leave
    # a half-updated folder (new Traefik files next to old Authentik ones).
    problems = [f"login front end {s['name']}: {p}" for s in (traefik, authentik) for p in validate_spec(s, site)]
    if problems:
        raise SpecError("\n".join(problems))
    routed = _routed(site, services, edge_vm, auth_label)
    out = Path(out)
    # Build both parts like any service; keep both secret lists.
    written, secrets = [], []
    for spec in (traefik, authentik):
        written += generate(copy.deepcopy(spec), site, out)
        secrets.append((out / "secrets.md").read_text(encoding="utf-8"))

    t_uid, t_gid = traefik["uid"], traefik.get("gid", traefik["uid"])
    a_uid, a_gid = authentik["uid"], authentik.get("gid", authentik["uid"])
    config, dynamic = _folder(traefik, "/etc/traefik"), _folder(traefik, "/dynamic")
    blueprints = _folder(authentik, "/blueprints/custom")

    files = {
        "rendered/files/traefik.yml": _fill("edge/traefik.yml.tmpl", {
            "DOMAIN": site["domain"], "ACME_EMAIL": site["acme_email"]}),
        "rendered/files/00-authentik.yml": _fill("edge/authentik-middleware.yml.tmpl", {
            "AUTHENTIK_HOST": site["edge"]["authentik"]["host"]}),
    }
    entries = [_file_entry(f"{config}/traefik.yml", "files/traefik.yml", t_uid, t_gid),
               _file_entry(f"{dynamic}/00-authentik.yml", "files/00-authentik.yml", t_uid, t_gid)]
    applies, providers, directories = [], [], []
    media = _folder(authentik, "/data") + "/media"
    for spec in routed:
        svc = spec["name"]
        route, blueprint = route_texts(spec, site)
        if spec.get("icon"):
            source = Path((icon_dirs or {}).get(svc, ".")) / spec["icon"]
            if not source.is_file():
                raise SpecError(f"service {svc!r}: icon file {source} is missing")
            ref = icon_ref(spec)
            data = source.read_bytes()
            if ref.endswith(".svg") and SVG_SCRIPT.search(data.decode("utf-8", "replace")):
                raise SpecError(f"service {svc!r}: icon {source.name} contains script; use a PNG or a clean SVG")
            files[f"rendered/files/icon-{svc}{Path(ref).suffix}"] = data
            entries.append(_file_entry(f"{media}/public/{ref}", f"files/icon-{svc}{Path(ref).suffix}", a_uid, a_gid))
            if not directories:
                # Authentik writes here too: declared with its owner, never created as root.
                directories = [_dir_entry(d, a_uid, a_gid) for d in (media, f"{media}/public", f"{media}/public/app-icons")]
        files[f"rendered/files/route-{svc}.yml"] = route
        files[f"rendered/files/app-{svc}.blueprint.yaml"] = blueprint
        entries.append(_file_entry(f"{dynamic}/{svc}.yml", f"files/route-{svc}.yml", t_uid, t_gid))
        entries.append(_file_entry(f"{blueprints}/app-{svc}.yaml", f"files/app-{svc}.blueprint.yaml", a_uid, a_gid))
        if spec["login"] != "authentik":  # own login: dashboard link only, never on the outpost
            continue
        # Names are quoted: a service called "null" or "on" must stay a string.
        applies.append(f"  - model: authentik_blueprints.metaapplyblueprint\n    attrs:\n"
                       f"      identifiers:\n        name: \"app-{svc}\"\n      required: true")
        providers.append(f"        - !Find [authentik_providers_proxy.proxyprovider, [name, \"{svc}\"]]")
    files["rendered/files/outpost-providers.blueprint.yaml"] = _fill("edge/outpost-providers.blueprint.yaml.tmpl", {
        "OUTPOST_APPLY_ENTRIES": "\n".join(applies),
        "OUTPOST_PROVIDER_LIST": "\n".join(providers) if providers else "        []"})
    entries.append(_file_entry(f"{blueprints}/outpost-providers.yaml", "files/outpost-providers.blueprint.yaml",
                               a_uid, a_gid))
    if people or signup or any(s.get("groups") for s in routed):
        files["rendered/files/access.blueprint.yaml"] = _access_blueprint(people, routed, signup, sources)
        entries.append(_file_entry(f"{blueprints}/access.yaml", "files/access.blueprint.yaml", a_uid, a_gid))
    if "user_pictures" in site:
        # Owner, 2026-11-03: not a built-in Authentik feature, and a picture stored as a user
        # attribute ends up in the outpost's sign-out link (the ID token in id_token_hint).
        raise SpecError("site.yaml: user_pictures was removed (uploaded pictures would end up in the "
                        "sign-out link); delete the line. Pictures follow Authentik's Avatars setting.")
    if signup:
        files["rendered/files/signup.blueprint.yaml"] = _signup_blueprint(signup, sources)
        entries.append(_file_entry(f"{blueprints}/signup.yaml", "files/signup.blueprint.yaml", a_uid, a_gid))
    files["rendered/login-frontend.bu"] = (
        "variant: fcos\nversion: 1.7.0\n\n"
        "# The login front end's settings, routes and blueprints, placed in the\n"
        "# folders Traefik and Authentik mount. Written by tools/login_frontend.py.\n"
        "storage:\n" + (("  directories:\n" + "\n".join(directories) + "\n") if directories else "")
        + "  files:\n" + "\n".join(entries) + "\n")
    files["secrets.md"] = "\n".join(secrets)
    return written + _write_all(out, "login-frontend", files)


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        import yaml
    except ImportError:
        print("install PyYAML (python-yaml / python3-yaml)", file=sys.stderr)
        return 2
    try:
        site = yaml.safe_load(Path(argv[1]).read_text(encoding="utf-8")) or {}
        services = [yaml.safe_load(Path(p).read_text(encoding="utf-8")) for p in argv[3:]]
        # Each service's icon file sits next to its spec.
        icon_dirs = {s.get("name"): Path(p).parent for s, p in zip(services, argv[3:]) if isinstance(s, dict)}
        for path in generate_login_frontend(site, services, argv[2], icon_dirs):
            print(path)
    except (OSError, yaml.YAMLError, SpecError) as error:
        print(f"login_frontend: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
