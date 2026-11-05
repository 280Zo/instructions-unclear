#!/usr/bin/env python3
"""Generate the login front end (an ingress and an auth gateway) for its VM.

Usage: login_frontend.py <site.yaml> <out-dir> [<service.yaml> ...]

The site file chooses the two modules under login_frontend (ingress: and auth_gateway:, see
tools/modules.py list); nothing is chosen for you. Each module is a normal service spec
(spec.yaml in its skill folder) plus code that writes its own files. Values written in the spec as
"<site: a.b.c>" come from the site file; a missing one is an error that names it. Both are built
with gen_service.generate into <out-dir>/rendered/, like any service. On top, this writes the login
front end's own files and one Butane fragment, rendered/login-frontend.bu, that places them in the
folders the containers mount (overwrite: true, so a rebuild rewrites them):

  ingress   its static settings, the glue for the chosen gateway, and one route per routed service
            (through the login page, or open for own-login services)
  gateway   one rules file per routed service (an access provider and application, or a dashboard
            link only), the binding of them all to the gateway's proxy endpoint, and its
            groups, people and sign-up settings

Every service spec given is validated in full. Services behind the login page (login gateway) get a
route through the gateway, its rules and a binding; services on their own login with a hostname get
an HTTPS route without the login page and a dashboard link (never bound to the gateway); the rest
get no route. secrets.md lists the secrets of both parts.
"""

import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
from gen_service import (DOMAIN, SpecError, _plain, _vm_entry, _write_all, generate, has_route,  # noqa: E402
                         route_texts, validate_spec)
from placement import filled, site_value  # noqa: E402

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")


def _modules(site: dict):
    """(chosen module names, ingress code, gateway code)."""
    names = modules.chosen(site)
    return names, modules.code(names["ingress"]), modules.code(names["auth_gateway"])


def frontend_specs(site: dict) -> tuple[dict, dict]:
    """The ingress and gateway specs with every <site: ...> value filled in."""
    import yaml
    names = modules.chosen(site)
    specs = [filled(yaml.safe_load(modules.spec_path(names[key]).read_text(encoding="utf-8")), site)
             for key in ("ingress", "auth_gateway")]
    return specs[0], specs[1]


def _check_site(site: dict, gateway) -> tuple[str, str]:
    """(edge vm name, the login page's own name); errors name the site field."""
    edge_vm = site_value(site, "edge.vm")
    if _vm_entry(site, edge_vm) is None:
        raise SpecError(f"site.yaml: edge.vm {edge_vm!r} is not listed in vms")
    domain = site_value(site, "domain")
    if not (_plain(domain) and DOMAIN.fullmatch(domain)):
        raise SpecError("site.yaml: domain is invalid")
    email = site_value(site, "acme_email")
    if not (_plain(email) and EMAIL.fullmatch(email)):
        raise SpecError("site.yaml: acme_email must be an email address")
    return edge_vm, gateway.host_label(site, domain)


def _routed(site: dict, services: list, edge_vm: str, login_label: str) -> list[dict]:
    chosen, ingress, gateway = _modules(site)
    own_names = {modules.service_name(chosen[key]) for key in ("ingress", "auth_gateway")}
    errors, routed, hostnames, names = [], [], {}, set()
    reserved = gateway.reserved_route_names()
    for spec in services:
        name = spec.get("name") if isinstance(spec, dict) else None
        problems = validate_spec(spec, site)
        if problems:
            errors += [f"service {name!r}: {p}" for p in problems]
            continue
        if name in names or name in own_names:
            errors.append(f"service {name!r}: the name is used twice or by the login front end")
        names.add(name)
        if not has_route(spec):
            continue
        # Router and service names in the ingress files: the gateway's glue defines some, and each
        # login-page route adds <svc>-outpost-style names (open routes don't, but a later switch to
        # the login page would). A name defined twice would break the shared login routes for every app.
        clash = ingress.route_name_problem(name)
        if name in reserved or name.endswith(gateway.reserved_route_suffix()) or clash:
            listed = ", ".join(sorted(reserved) + [f"<name>{gateway.reserved_route_suffix()}"]
                               + ([clash] if clash else []))
            errors.append(f"service {name!r}: this name clashes with the login front end's route names "
                          f"({listed}); pick another")
        if spec.get("bind", "vm_ip") == "loopback" and spec["vm"] != edge_vm:
            errors.append(f"service {name!r}: bind loopback is only reachable on the login front end VM "
                          f"({edge_vm}); use vm_ip")
        hostname = spec["hostname"]
        if hostname == login_label:
            errors.append(f"service {name!r}: hostname {hostname!r} is the login page's own name")
        elif hostname in hostnames:
            errors.append(f"service {name!r}: hostname {hostname!r} is already used by {hostnames[hostname]!r}")
        hostnames[hostname] = name
        routed.append(spec)
    if errors:
        raise SpecError("\n".join(errors))
    return sorted(routed, key=lambda s: s["name"])


def generate_login_frontend(site: dict, services: list, out, icon_dirs: dict | None = None) -> list[Path]:
    names, ingress, gateway = _modules(site)
    edge_vm, login_label = _check_site(site, gateway)
    ingress_spec, gateway_spec = frontend_specs(site)
    config = gateway.settings(site)
    gateway.prepare_spec(gateway_spec, config)
    # Check both parts before writing anything, so a bad site value can't leave
    # a half-updated folder (new ingress files next to old gateway ones).
    problems = [f"login front end {s['name']}: {p}" for s in (ingress_spec, gateway_spec)
                for p in validate_spec(s, site)]
    if problems:
        raise SpecError("\n".join(problems))
    routed = _routed(site, services, edge_vm, login_label)
    out = Path(out)
    # Build both parts like any service; keep both secret lists.
    written, secrets = [], []
    for spec in (ingress_spec, gateway_spec):
        written += generate(copy.deepcopy(spec), site, out)
        secrets.append((out / "secrets.md").read_text(encoding="utf-8"))

    routes, bindings = {}, {}
    for spec in routed:
        routes[spec["name"]], bindings[spec["name"]] = route_texts(spec, site)
    files, entries = ingress.place(site, ingress_spec, names["auth_gateway"],
                                   gateway.forward_auth_values(site), routes)
    more_files, more_entries, directories = gateway.place(site, gateway_spec, config, routed, bindings, icon_dirs)
    files.update(more_files)
    entries += more_entries
    files["rendered/login-frontend.bu"] = (
        "variant: fcos\nversion: 1.7.0\n\n"
        "# The login front end's settings, routes and rules files, placed in the\n"
        "# folders its containers mount. Written by tools/login_frontend.py.\n"
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
