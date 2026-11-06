"""Traefik as the ingress of the login front end (module ingress-traefik).

Everything specific to Traefik lives here and in the module's folder: the static settings, the route
files (one per service, read from a folder, no container socket), the redirect rules and the glue for
each auth gateway it has been tested with. tools/login_frontend.py calls this module through
tools/modules.py and knows nothing of Traefik. Values come from the site file.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import modules  # noqa: E402
from gen_service import SpecError, _plain  # noqa: E402
from placement import file_entry, folder, site_value  # noqa: E402
from render import render  # noqa: E402

MODULE = "ingress-traefik"
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
REDIRECT_PATH = re.compile(r"/[A-Za-z0-9._~/-]{0,200}")
MAX_REDIRECTS = 10


def _fill(relative: str, values: dict) -> str:
    text = modules.template_path(MODULE, relative).read_text(encoding="utf-8")
    return render(text, {k: str(v) for k, v in values.items()})


def _matches(regex, path) -> bool:
    try:
        return re.search(regex, path) is not None
    except (re.error, TypeError):
        return False


def check_site(site: dict) -> None:
    """The site keys this module needs: the address the certificate authority writes to."""
    email = site_value(site, "acme_email")
    if not (_plain(email) and EMAIL.fullmatch(email)):
        raise SpecError("site.yaml: acme_email must be an email address")


def route_name_problem(name: str) -> str | None:
    """A service name that would collide with a router this module makes for a redirect."""
    if re.search(r"-redirect-[0-9]+$", name):
        return "<name>-redirect-<n>"
    return None


def check_spec(spec: dict, reserved_paths: list[str], errors: list) -> None:
    """Paths answered with an https redirect (an app whose own redirect builds http:// behind the
    proxy, e.g. an app's .htaccess for /.well-known/carddav)."""
    if "redirects" not in spec:
        return
    items = spec["redirects"]
    ok = isinstance(items, list) and 0 < len(items) <= MAX_REDIRECTS and all(
        isinstance(i, dict) and set(i) == {"path", "to"}
        and all(isinstance(i[k], str) and REDIRECT_PATH.fullmatch(i[k]) for k in ("path", "to")) for i in items)
    if not ok:
        errors.append(f"redirects must be a list of 1 to {MAX_REDIRECTS} {{path, to}} entries, each a path "
                      "starting with / (letters, digits, . _ ~ / -)")
    elif not spec.get("hostname"):
        errors.append("redirects need a hostname (they are answered on the app's web name)")
    else:
        paths = [i["path"] for i in items]
        if len(set(paths)) != len(paths):
            errors.append("redirects: each path at most once")
        for item in items:
            if item["to"] == item["path"]:
                errors.append(f"redirects: {item['path']} would redirect to itself")
            for reserved in reserved_paths:
                if item["path"].startswith(reserved):
                    errors.append(f"redirects: paths under {reserved} belong to the login page")
            # Behind the login page, a client that follows the redirect must not land on the login.
            if spec.get("login") == "gateway" and not any(
                    _matches(rx, item["to"]) for rx in spec.get("api_paths") or []):
                errors.append(f"redirects: {item['to']} is behind the login page; add it to api_paths "
                              "or redirect to a path that is")


def redirect_blocks(svc: str, host: str, redirects: list) -> dict:
    """Routers and redirectRegex middlewares (doc.traefik.io, middlewares/redirectregex) for each
    redirect; above the app's routers (10) and its gateway path (15)."""
    routers, middlewares = [], []
    for n, item in enumerate(redirects):
        name = f"{svc}-redirect-{n}"
        routers.append(f'    "{name}":\n      rule: "Host(`{host}`) && Path(`{item["path"]}`)"\n'
                       f'      entryPoints: [websecure]\n      middlewares: ["{name}"]\n'
                       f'      service: "{svc}"\n      priority: 20')
        middlewares.append(f'    "{name}":\n      redirectRegex:\n        regex: "^.*$"\n'
                           f'        replacement: "https://{host}{item["to"]}"\n        permanent: true')
    return {"REDIRECT_ROUTERS": "\n".join(routers) if routers else "    # redirects: none",
            "REDIRECT_MIDDLEWARES": ("  middlewares:\n" + "\n".join(middlewares)) if middlewares
            else "  # middlewares: none"}


def _glue(gateway: str, name: str) -> str:
    path = f"gateways/{gateway}/{name}"
    if not modules.template_path(MODULE, path).is_file():
        raise SpecError(f"{MODULE} has no tested pairing with {gateway}: no templates/gateways/{gateway}/. "
                        "Add one with docs/guide/12-add-a-module.md, or choose a tested pairing "
                        "(python3 tools/modules.py list)")
    return path


def route_text(kind: str, gateway: str, values: dict) -> str:
    """The route file for a service: kind "gateway" goes through the auth gateway, "open" does not."""
    if kind == "gateway":
        return _fill(_glue(gateway, "route.yml.tmpl"), values)
    if kind == "open":
        return _fill("route-open.yml.tmpl", values)
    raise SpecError(f"login {kind!r} has no route kind")  # fail closed on a new value


def place(site: dict, spec: dict, gateway: str, gateway_values: dict, routes: dict,
          acme: dict) -> tuple[dict, list]:
    """(files, Butane entries) for the ingress on the login VM: static settings (with the DNS
    provider's certificate data), the shared glue file for the auth gateway, and one route file per
    routed service."""
    uid, gid = spec["uid"], spec.get("gid", spec["uid"])
    config, dynamic = folder(spec, "/etc/traefik"), folder(spec, "/dynamic")
    glue_name = f"00-{gateway}.yml"
    files = {
        "rendered/files/traefik.yml": _fill("traefik.yml.tmpl", {
            "DOMAIN": site["domain"], "ACME_EMAIL": site["acme_email"], "ACME_PROVIDER": acme["provider"],
            "ACME_NOTE": f"# {acme['notes']}" if acme.get("notes") else "#"}),
        f"rendered/files/{glue_name}": _fill(_glue(gateway, "middleware.yml.tmpl"), gateway_values),
    }
    entries = [file_entry(f"{config}/traefik.yml", "files/traefik.yml", uid, gid),
               file_entry(f"{dynamic}/{glue_name}", f"files/{glue_name}", uid, gid)]
    for svc, text in routes.items():
        files[f"rendered/files/route-{svc}.yml"] = text
        entries.append(file_entry(f"{dynamic}/{svc}.yml", f"files/route-{svc}.yml", uid, gid))
    return files, entries
