#!/usr/bin/env python3
"""Check that no two services in a workspace share what must be unique:

- the name (it is also the VM user, its group, and the route name),
- the UID, and the GID (each gives the app's pinned subordinate ID range),
- the port on one VM (strict: also when one service binds only to loopback),
- the web name (hostname), including the login page's own name.

Also taken: the login front end's own services (the modules site.yaml
chooses) and the ingress's web ports 80 and 443 on its VM; and what every VM
has: the admin account (name, and UID/GID 1000 and 1001, which useradd picks
from next to FCOS's core user; build-vm.sh makes base-config merge first),
core, root, nobody, wheel, sudo, and the shared groups (name and GID). The
rest of FCOS's system accounts are not listed yet (to be read from a real VM).
UIDs and GIDs are separate: a UID equal to another service's GID is fine.

Usage: check_workspace.py <workspace>   (reads site.yaml and services/*/service.yaml)
Exit 0 when all are unique, 1 with one line per problem, 2 on a read error.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
from gen_service import MAX_ID, MIN_ID, SpecError  # noqa: E402

KINDS = ("name", "uid", "gid", "port", "hostname")


def _scalar(value) -> bool:
    return isinstance(value, (str, int)) and not isinstance(value, bool)


def _frontend(site: dict, problems: list) -> list[dict]:
    """The login front end's specs; a broken edge section is one problem, not a stop."""
    if not isinstance(site.get("edge"), dict):
        return []
    import yaml
    from login_frontend import frontend_specs
    try:
        return list(frontend_specs(site))
    except (SpecError, OSError, yaml.YAMLError, KeyError, TypeError, AttributeError, ValueError) as error:
        problems.append(f"site.yaml: the login front end section can't be read ({error}); its accounts "
                        "and names are not checked until it is fixed")
        return []


def _free(kind: str, key, taken: dict):
    """The next free value at or after the clashing one, for uid, gid and port."""
    if kind in ("uid", "gid"):
        # Free as both: a spec's GID follows its UID unless set.
        start, limit, used = key, MAX_ID, set(taken["uid"]) | set(taken["gid"])
    elif kind == "port":
        vm, start = key
        limit, used = 65535, {p for v, p in taken["port"] if v == vm}
    else:
        return None
    return next((n for n in range(max(start, MIN_ID if kind != "port" else 1024), limit + 1) if n not in used), None)


def workspace_problems(site: dict, specs: list) -> list[str]:
    """Every clash between the services, the login front end and the accounts every VM has."""
    problems: list[str] = []
    taken: dict = {kind: {} for kind in KINDS}
    clashes = []  # (kind, key, owner, holder)

    def claim(kind, key, owner):
        if key in taken[kind]:
            clashes.append((kind, key, owner, taken[kind][key]))
        else:
            taken[kind][key] = owner

    # What every VM has.
    admin = site.get("admin_user")
    if isinstance(admin, str) and admin:
        claim("name", admin, "the VM's admin account")
    claim("name", "core", "FCOS's built-in core account")
    for name in ("root", "nobody"):
        claim("name", name, "a system account on every Linux")
    for name in ("wheel", "sudo"):
        claim("name", name, "the admin account's groups (base-config)")
    for number in (1000, 1001):
        claim("uid", number, "the VM's admin account or core (useradd picks 1000 or 1001)")
        claim("gid", number, "the VM's admin account or core (useradd picks 1000 or 1001)")
    for group in site.get("shared_groups") or []:
        if isinstance(group, dict):
            if _scalar(group.get("name")):
                claim("name", group["name"], f"shared group {group['name']!r}")
            if _scalar(group.get("gid")):
                claim("gid", group["gid"], f"shared group {group.get('name')!r}")

    # The login front end.
    edge = site.get("edge") if isinstance(site.get("edge"), dict) else {}
    chosen = modules.frontend_services(site)
    section = edge.get(chosen.get("auth_gateway"))
    host = section.get("host") if isinstance(section, dict) else None
    if isinstance(host, str) and host:
        claim("hostname", host.split(".")[0], f"{chosen['auth_gateway']} (the login page)")
    if _scalar(edge.get("vm")) and "ingress" in chosen:
        for port in (80, 443):
            claim("port", (edge["vm"], port), f"{chosen['ingress']} (the login front end's web ports)")

    for spec in _frontend(site, problems) + list(specs):
        if not isinstance(spec, dict):
            problems.append("a service spec is not a mapping")
            continue
        owner = f"service {spec.get('name')!r}"
        uid = spec.get("uid")
        values = {"name": spec.get("name"), "uid": uid, "gid": spec.get("gid", uid),
                  "hostname": spec.get("hostname"), "vm": spec.get("vm"), "port": spec.get("port")}
        bad = [k for k, v in values.items() if v is not None and not _scalar(v)]
        for key in bad:
            problems.append(f"{owner}: {key} must be a single {'number' if key in ('uid', 'gid', 'port') else 'name'}")
        for kind in ("name", "uid", "gid", "hostname"):
            if kind not in bad and values[kind] is not None:
                claim(kind, values[kind], owner)
        if values["port"] is not None and "port" not in bad and "vm" not in bad:
            claim("port", (values["vm"], values["port"]), owner)

    for kind, key, owner, holder in clashes:
        shown = key[1] if kind == "port" else key
        where = f" on vm {key[0]}" if kind == "port" else ""
        free = _free(kind, key, taken) if isinstance(shown, int) else None
        hint = f" (free: {free})" if free is not None else ""
        problems.append(f"{owner}: {kind} {shown!r} is already used by {holder}{where}{hint}")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not Path(argv[1]).is_dir():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        import yaml
    except ImportError:
        print("install PyYAML (python-yaml / python3-yaml)", file=sys.stderr)
        return 2
    ws = Path(argv[1])
    try:
        site = yaml.safe_load((ws / "site.yaml").read_text(encoding="utf-8")) or {}
        specs = [yaml.safe_load(p.read_text(encoding="utf-8"))
                 for p in sorted((ws / "services").glob("*/service.yaml"))]
    except (OSError, yaml.YAMLError) as error:
        print(f"check_workspace: {error}", file=sys.stderr)
        return 2
    found = workspace_problems(site if isinstance(site, dict) else {}, specs)
    for line in found:
        print(line)
    if not found:
        print(f"check_workspace: {len(specs)} service(s), no clashes")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
