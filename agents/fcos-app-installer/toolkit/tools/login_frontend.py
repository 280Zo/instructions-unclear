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
get no route. The site's dashboard_links (devices the toolkit doesn't run) become dashboard links that
open the device itself, with an optional sign-on provider; their logos are in <workspace>/links/.
secrets.md lists the secrets of both parts.
"""

import copy
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
from gen_service import (DOMAIN, SpecError, _plain, _vm_entry, _write_all, forget_other_services,  # noqa: E402
                         generate, has_route, route_texts, validate_spec)
from adapters import AdapterError, acme_data  # noqa: E402
from placement import filled, site_value  # noqa: E402


def _modules(site: dict):
    """(chosen module names, ingress code, gateway code)."""
    names = modules.chosen(site)
    return names, modules.code(names["ingress"]), modules.code(names["auth_gateway"])


def _acme(site: dict) -> dict:
    """The certificate data of the DNS provider the site names (its adapter's acme block)."""
    try:
        return acme_data(site)
    except AdapterError as error:
        raise SpecError(str(error)) from None


def frontend_specs(site: dict) -> tuple[dict, dict]:
    """The ingress and gateway specs with every <site: ...> and <acme: ...> value filled in."""
    import yaml
    names = modules.chosen(site)
    acme = _acme(site)
    specs = [filled(yaml.safe_load(modules.spec_path(names[key]).read_text(encoding="utf-8")), site, acme)
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


def _check_links(site: dict, services: list, names: dict, gateway, config: dict) -> None:
    """Dashboard links (devices the toolkit doesn't run) take names in the gateway's application
    list: none may be a service's or the login front end's own name."""
    if not hasattr(gateway, "link_names"):
        if site.get("dashboard_links") is not None:
            raise SpecError(f"site.yaml: dashboard_links: the auth gateway {names['auth_gateway']} can't make "
                            "dashboard links; remove the list or add it to that module")
        return
    taken = {s.get("name") for s in services if isinstance(s, dict)}
    taken |= {modules.service_name(names[key]) for key in ("ingress", "auth_gateway")}
    clash = [n for n in gateway.link_names(config) if n in taken]
    if clash:
        raise SpecError("\n".join(f"site.yaml dashboard_links: name {n!r} is already used by a service or the "
                                  "login front end; pick another" for n in clash))


BACKEND = re.compile(r"(https?)://[A-Za-z0-9.-]+(:[0-9]{1,5})?")
ROUTE_KEYS = {"hostname", "backend", "allow_from", "ca_file", "server_name"}
SERVER_NAME = re.compile(r"(?=.{1,253}$)[A-Za-z0-9]([A-Za-z0-9-]{0,62})(\.[A-Za-z0-9]([A-Za-z0-9-]{0,62}))*")
MAX_ALLOW = 20


def _ca_pem(path) -> str | None:
    """The device's CA certificate(s), read from an absolute path: PEM certificates only, never a key."""
    if not (isinstance(path, str) and Path(path).is_absolute() and Path(path).is_file()):
        return None
    text = Path(path).read_text(encoding="ascii", errors="replace")
    blocks = re.findall(r"-----BEGIN ([A-Z ]+)-----", text)
    if not blocks or set(blocks) != {"CERTIFICATE"} or len(text) > 65536 or "PRIVATE" in text:
        return None
    return text


def _device_routes(site: dict, routed: list, login_label: str, ingress) -> dict:
    """{route file name: text} for dashboard links with a route: a web name on the ingress for a device
    the toolkit doesn't run, limited to private networks, checking an https device's own certificate."""
    import ipaddress
    links = [link for link in site.get("dashboard_links") or [] if isinstance(link, dict) and "route" in link]
    if not links:
        return {}
    if not hasattr(ingress, "device_route_text"):
        raise SpecError("site.yaml dashboard_links: the chosen ingress can't serve a device's web name (route:)")
    taken = {s["hostname"]: s["name"] for s in routed}
    service_names = {s["name"] for s in routed}
    domain = site_value(site, "domain")
    errors, texts = [], {}
    for link in links:
        name, route = link.get("name"), link["route"]
        where = f"site.yaml dashboard_links {name!r} route"
        if not isinstance(route, dict) or not {"hostname", "backend", "allow_from"} <= set(route) <= ROUTE_KEYS:
            errors.append(f"{where}: needs hostname, backend and allow_from; may have ca_file")
            continue
        host, backend, allow = route["hostname"], route["backend"], route["allow_from"]
        if host == login_label:
            errors.append(f"{where}: hostname {host!r} is the login page's own name")
        elif host in taken:
            errors.append(f"{where}: hostname {host!r} is already used by {taken[host]!r}")
        taken[host] = f"dashboard link {name}"
        if f"link-{name}" in service_names or ingress.route_name_problem(f"link-{name}"):
            errors.append(f"{where}: the route name link-{name} clashes with a service's; pick another link name")
        match = BACKEND.fullmatch(backend) if isinstance(backend, str) else None
        if not match:
            errors.append(f"{where}: backend must be http:// or https://, a host or address and an optional port, "
                          "nothing after it")
        nets = []
        if not isinstance(allow, list) or not 0 < len(allow) <= MAX_ALLOW:
            errors.append(f"{where}: allow_from must list 1 to {MAX_ALLOW} private networks (who may use the name)")
            allow = []
        for net in allow:
            try:
                parsed = ipaddress.IPv4Network(net, strict=True) if isinstance(net, str) else None
            except ValueError:
                parsed = None
            if parsed is None or not parsed.is_private or parsed.prefixlen < 8:
                errors.append(f"{where}: allow_from {net!r} must be a private IPv4 network address "
                              "(192.0.2.0/24, /8 or smaller)")
            else:
                nets.append(str(parsed))
        pem = None
        if match and match.group(1) == "https":
            pem = _ca_pem(route.get("ca_file"))
            if pem is None:
                errors.append(f"{where}: an https device needs ca_file: the absolute path of its CA certificate "
                              "(PEM certificates only, no key); its certificate is always checked")
        elif "ca_file" in route:
            errors.append(f"{where}: ca_file is only for an https backend")
        server_name = route.get("server_name")
        if "server_name" in route:
            if not (match and match.group(1) == "https"):
                errors.append(f"{where}: server_name is only for an https backend")
            elif not (isinstance(server_name, str) and SERVER_NAME.fullmatch(server_name)):
                errors.append(f"{where}: server_name must be the host name the device's certificate names")
        if not errors:
            texts[f"link-{name}"] = ingress.device_route_text(name, f"{host}.{domain}", backend, nets, pem,
                                                             server_name)
    if errors:
        raise SpecError("\n".join(errors))
    return texts


def generate_login_frontend(site: dict, services: list, out, icon_dirs: dict | None = None,
                            links_dir=None) -> list[Path]:
    """links_dir: the folder holding the dashboard links' logos (<workspace>/links)."""
    names, ingress, gateway = _modules(site)
    ingress.check_site(site)  # the site keys the chosen ingress needs are its own business
    edge_vm, login_label = _check_site(site, gateway)
    ingress_spec, gateway_spec = frontend_specs(site)
    config = gateway.settings(site)
    config["links_dir"] = links_dir
    _check_links(site, services, names, gateway, config)
    gateway.prepare_spec(gateway_spec, config)
    # Check both parts before writing anything, so a bad site value can't leave
    # a half-updated folder (new ingress files next to old gateway ones).
    problems = [f"login front end {s['name']}: {p}" for s in (ingress_spec, gateway_spec)
                for p in validate_spec(s, site)]
    if problems:
        raise SpecError("\n".join(problems))
    routed = _routed(site, services, edge_vm, login_label)
    out = Path(out)
    forget_other_services(out, {ingress_spec["name"], gateway_spec["name"], "login-frontend"})
    # Build both parts like any service; keep both secret lists.
    written, secrets = [], []
    for spec in (ingress_spec, gateway_spec):
        written += generate(copy.deepcopy(spec), site, out)
        secrets.append((out / "secrets.md").read_text(encoding="utf-8"))

    routes, bindings = {}, {}
    for spec in routed:
        routes[spec["name"]], bindings[spec["name"]] = route_texts(spec, site)
    routes.update(_device_routes(site, routed, login_label, ingress))
    files, entries = ingress.place(site, ingress_spec, names["auth_gateway"],
                                   gateway.forward_auth_values(site), routes, _acme(site))
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
        note = modules.pairing_note(modules.chosen(site))
        if note:
            print(f"login_frontend: note: {note}", file=sys.stderr)
        # Dashboard links' logos sit in the links folder next to the site file.
        links_dir = Path(argv[1]).resolve().parent / "links"
        for path in generate_login_frontend(site, services, argv[2], icon_dirs, links_dir):
            print(path)
    except (OSError, yaml.YAMLError, SpecError, AdapterError) as error:
        print(f"login_frontend: {error}", file=sys.stderr)
        return 1
    except (TypeError, AttributeError, KeyError, ValueError, IndexError) as error:
        print(f"login_frontend: the site file or a spec has a value of the wrong type or shape "
              f"({type(error).__name__}); nothing was written before the checks passed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
