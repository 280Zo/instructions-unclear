"""Authentik as the auth gateway of the login front end (module authgw-authentik).

Everything here is specific to Authentik: its rules files ("blueprints"), its users and groups, the
sign-up page, sign-in with an existing account, the dashboard entries and the embedded outpost that a
reverse proxy asks (forward auth). tools/login_frontend.py calls this module through tools/modules.py
and knows nothing of Authentik. Values come from the site file; no real value is written here.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import modules  # noqa: E402
from gen_service import HOST_LABEL, SpecError, _plain  # noqa: E402
from placement import dir_entry, file_entry, folder, site_value  # noqa: E402
from render import render  # noqa: E402

MODULE = "authgw-authentik"
GROUP = re.compile(r"[a-z][a-z0-9-]{0,62}")
MAX_GROUPS = 10
ICON = re.compile(r"[a-z0-9][a-z0-9-]{0,62}\.(svg|png|webp|jpg)")
SECTION = re.compile(r"[A-Za-z0-9][A-Za-z0-9 &'.,-]{0,49}")
# An SVG served from the login page's own address must not carry script.
SVG_SCRIPT = re.compile(r"<script|\bon[a-z]+\s*=|javascript:|<foreignObject", re.I)

PERSON = re.compile(r"[a-z][a-z0-9._-]{0,62}")
GROUP_NAME = re.compile(r"[a-z][a-z0-9-]{0,62}")
RESERVED_USERS = {"akadmin"}


def _people(site: dict) -> list[dict]:
    """site.yaml people: local Authentik users (no email, no self sign-up).
    Each {username, name, groups}; passwords are set by the user in Authentik."""
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
                          "the user sets the password in Authentik)")
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
    """site.yaml signup: {group, approve?}: a sign-up page for anyone who can reach the login page,
    no email; new accounts land in `group`, inactive until approved if approve."""
    signup = site.get("signup")
    if signup is None:
        return None
    if (not isinstance(signup, dict) or not set(signup) <= {"group", "approve"}
            or not (isinstance(signup.get("group"), str) and GROUP_NAME.fullmatch(signup["group"]))
            or not isinstance(signup.get("approve", False), bool)):
        raise SpecError("site.yaml: signup must be {group: <lowercase group>, approve: true|false (optional)}")
    return signup


# Sign in with an existing account. The client id is not secret; the
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
    not created yet) must never roll back the app bindings."""
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
    bound = [s for s in routed if s.get("groups") and s["login"] == "gateway"]
    groups = sorted({g for p in people for g in p["groups"]} | {g for s in bound for g in s["groups"]}
                    | ({signup["group"]} if signup else set()))
    out = ["# Groups, local people and app access in Authentik (site.yaml people, each app's groups).",
           "# Written by tools/login_frontend.py. Users are created once (state: created): later group",
           "# changes made in the admin interface stay. No passwords: the user sets each one in Authentik.",
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
        # Found by app + group, so the user's own bindings and the other groups are left alone.
        for order, group in enumerate(spec["groups"]):
            out += ["  - model: authentik_policies.policybinding", "    identifiers:",
                    f'      target: !Find [authentik_core.application, [slug, "{spec["name"]}"]]',
                    f"      group: !KeyOf group-{group}", "    attrs:", f"      order: {order}"]
    return "\n".join(out) + "\n"


def _fill(relative: str, values: dict) -> str:
    text = modules.template_path(MODULE, relative).read_text(encoding="utf-8")
    return render(text, {k: str(v) for k, v in values.items()})


# ---- what the generic tools ask of an auth gateway -------------------------------------------

def reserved_route_names() -> set[str]:
    """Router and service names the ingress glue defines for this gateway."""
    return {"authentik-server", "authentik-outpost"}


def reserved_route_suffix() -> str:
    """Each service behind the login page gets a <name>-outpost router in the ingress glue."""
    return "-outpost"


def reserved_paths() -> list[str]:
    """Paths the gateway answers itself on every app's web name."""
    return ["/outpost.goauthentik.io"]


def forward_auth_values(site: dict) -> dict:
    """The values the ingress glue for this gateway is filled with."""
    return {"GATEWAY_HOST": site["edge"]["authentik"]["host"]}


def host_label(site: dict, domain: str) -> str:
    """The login page's own name: one label directly under the domain (the certificate covers only
    *.<domain>)."""
    host = site_value(site, "edge.authentik.host")
    label, _, rest = host.partition(".") if isinstance(host, str) else ("", "", "")
    if not (_plain(host) and HOST_LABEL.fullmatch(label) and rest == domain):
        raise SpecError("site.yaml: edge.authentik.host must be one name directly under the domain "
                        "(the certificate covers only *.<domain>)")
    return label


def icon_ref(spec: dict) -> str:
    """The icon's media path as the gateway references it (/data/media/public/<this>)."""
    return f"app-icons/{spec['name']}{Path(spec['icon']).suffix}"


def check_spec(spec: dict, errors: list) -> None:
    """The service spec keys this gateway gives meaning to: groups, icon and section."""
    if "groups" in spec:
        groups = spec["groups"]
        if (not isinstance(groups, list) or not groups or len(groups) > MAX_GROUPS
                or not all(isinstance(g, str) and GROUP.fullmatch(g) for g in groups)
                or len(set(groups)) != len(groups)):
            errors.append(f"groups must be a list of 1 to {MAX_GROUPS} different lowercase names (letters, digits, -)")
        if spec.get("login") != "gateway":
            # Its route skips the login page: a binding would only hide the dashboard link.
            errors.append("groups only work for apps behind the login page (login: gateway)")
    if "icon" in spec and not (isinstance(spec["icon"], str) and ICON.fullmatch(spec["icon"])):
        errors.append("icon must be a file name in the service's folder (letters, digits, -; .svg .png .webp .jpg)")
    if "icon" in spec and not spec.get("hostname"):
        errors.append("icon needs a hostname (it is shown on the app's dashboard entry)")
    if "section" in spec and not (isinstance(spec["section"], str) and SECTION.fullmatch(spec["section"])):
        errors.append("section must be a short heading (letters, digits, spaces, & ' . , -; at most 50)")


def _access_entries(svc: str, groups: list) -> str:
    """Groups and their bindings are written by the login front end's access.yaml only
    (one creator per group: two rules files creating the same unique name race)."""
    if groups:
        # Until access.yaml has bound the groups, nobody gets in (policy engine "any": a member's
        # group binding still passes); never an app open to every account in between.
        return (f"  # groups {', '.join(groups)}: bound in access.yaml (tools/login_frontend.py)\n"
                f"  - model: authentik_policies_expression.expressionpolicy\n    id: deny-{svc}\n"
                f"    identifiers:\n      name: \"deny-until-bound-{svc}\"\n    attrs:\n      expression: return False\n"
                f"  - model: authentik_policies.policybinding\n    identifiers:\n      target: !KeyOf app-{svc}\n"
                f"      policy: !KeyOf deny-{svc}\n    attrs:\n      order: 99")
    return "  # groups: none listed, so every Authentik user may open it"


def binding_text(spec: dict, values: dict, kind: str) -> str:
    """The rules file for one service: kind "gateway" is a forward-auth provider and its application;
    "open" is a dashboard link only (an application with no provider). Each api_paths regex goes on
    its own line of the skip_path_regex block, indented to the block's level (an unindented line
    would end the block)."""
    values = dict(values)
    values["ACCESS_ENTRIES"] = _access_entries(spec["name"], spec.get("groups") or [])
    values["SECTION_LINE"] = (f'      group: "{spec["section"]}"' if spec.get("section")
                              else "      # section: none (listed under Ungrouped)")
    values["ICON_LINE"] = (f'      icon: "{icon_ref(spec)}"' if spec.get("icon")
                           else "      # icon: none (Authentik shows the app's initials)")
    if kind == "gateway":
        return _fill("app.blueprint.yaml.tmpl", values)
    if kind == "open":
        return _fill("bookmark.blueprint.yaml.tmpl", values)
    raise SpecError(f"login {kind!r} has no binding kind")  # fail closed on a new value


def settings(site: dict) -> dict:
    """The gateway's own site settings, checked: people, sign-up page and sign-in sources."""
    people = _people(site)
    signup = _signup(site)
    return {"people": people, "signup": signup, "sources": _sources(site, signup)}


def prepare_spec(spec: dict, config: dict) -> None:
    """Add the secrets that sign-in sources need to the worker container and the secret list."""
    for kind in config["sources"]:
        info = SOURCE_TYPES[kind]
        worker = next(c for c in spec["containers"] if c["name"] == "worker")
        worker.setdefault("secrets", []).append({"env": info["env"], "name": info["secret"]})
        spec.setdefault("secrets", []).append({"name": info["secret"], "durable": True, "source": info["how"]})


def place(site: dict, spec: dict, config: dict, routed: list, bindings: dict, icon_dirs: dict | None
          ) -> tuple[dict, list, list]:
    """(files, Butane entries, directories) for the gateway's own files on the login VM: one rules
    file per routed service, the binding of them all to the embedded outpost, groups and people, the
    sign-up page, and the apps' icons."""
    uid, gid = spec["uid"], spec.get("gid", spec["uid"])
    blueprints = folder(spec, "/blueprints/custom")
    media = folder(spec, "/data") + "/media"
    people, signup, sources = config["people"], config["signup"], config["sources"]
    files, entries, directories = {}, [], []
    applies, providers = [], []
    for item in routed:
        svc = item["name"]
        if item.get("icon"):
            source = Path((icon_dirs or {}).get(svc, ".")) / item["icon"]
            if not source.is_file():
                raise SpecError(f"service {svc!r}: icon file {source} is missing")
            ref = icon_ref(item)
            data = source.read_bytes()
            if ref.endswith(".svg") and SVG_SCRIPT.search(data.decode("utf-8", "replace")):
                raise SpecError(f"service {svc!r}: icon {source.name} contains script; use a PNG or a clean SVG")
            files[f"rendered/files/icon-{svc}{Path(ref).suffix}"] = data
            entries.append(file_entry(f"{media}/public/{ref}", f"files/icon-{svc}{Path(ref).suffix}", uid, gid))
            if not directories:
                # Authentik writes here too: declared with its owner, never created as root.
                directories = [dir_entry(d, uid, gid) for d in (media, f"{media}/public", f"{media}/public/app-icons")]
        files[f"rendered/files/app-{svc}.blueprint.yaml"] = bindings[svc]
        entries.append(file_entry(f"{blueprints}/app-{svc}.yaml", f"files/app-{svc}.blueprint.yaml", uid, gid))
        if item["login"] != "gateway":  # own login: dashboard link only, never on the outpost
            continue
        # Names are quoted: a service called "null" or "on" must stay a string.
        applies.append(f"  - model: authentik_blueprints.metaapplyblueprint\n    attrs:\n"
                       f"      identifiers:\n        name: \"app-{svc}\"\n      required: true")
        providers.append(f"        - !Find [authentik_providers_proxy.proxyprovider, [name, \"{svc}\"]]")
    files["rendered/files/outpost-providers.blueprint.yaml"] = _fill("outpost-providers.blueprint.yaml.tmpl", {
        "OUTPOST_APPLY_ENTRIES": "\n".join(applies),
        "OUTPOST_PROVIDER_LIST": "\n".join(providers) if providers else "        []"})
    entries.append(file_entry(f"{blueprints}/outpost-providers.yaml", "files/outpost-providers.blueprint.yaml",
                              uid, gid))
    if people or signup or any(s.get("groups") for s in routed):
        files["rendered/files/access.blueprint.yaml"] = _access_blueprint(people, routed, signup, sources)
        entries.append(file_entry(f"{blueprints}/access.yaml", "files/access.blueprint.yaml", uid, gid))
    if "user_pictures" in site:
        # Not a built-in Authentik feature, and a picture stored as a user
        # attribute ends up in the outpost's sign-out link (the ID token in id_token_hint).
        raise SpecError("site.yaml: user_pictures is not supported (uploaded pictures would end up in the "
                        "sign-out link); delete the line. Pictures follow Authentik's Avatars setting.")
    if signup:
        files["rendered/files/signup.blueprint.yaml"] = _signup_blueprint(signup, sources)
        entries.append(file_entry(f"{blueprints}/signup.yaml", "files/signup.blueprint.yaml", uid, gid))
    return files, entries, directories
