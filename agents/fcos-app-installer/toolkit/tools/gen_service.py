#!/usr/bin/env python3
"""Generate every file for one service from its service spec and the site config.

Usage: gen_service.py <service.yaml> <site.yaml> <out-dir>

Writes <out-dir>/rendered/ (Quadlets and the private network under files/,
Butane fragments next to them) and <out-dir>/secrets.md (secret names and how
to create them; never a value). A hidden .gen-service-<name>.json lists what
was written, so a re-run removes files the new spec no longer produces. Fragments are named <service>.bu,
<service>-port.bu, <service>-backup-<container>.bu and <service>-backup-files.bu.
A service behind the login page also gets files/route-<service>.yml and
files/app-<service>.blueprint.yaml, which tools/login_frontend.py places on the
login front end VM. Everything is filled into templates/ with render.py.

Spec values are untrusted: nothing is written unless the whole spec passes
validate_spec. Host network values (IPs, bridges, VLANs) and storage are never
chosen here; they come from the site config, and a missing one is an error.
Field reference: schemas/service.schema.md.
"""

import ipaddress
import json
import posixpath
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
from errors import SpecError  # noqa: E402,F401  (re-exported: other tools import it from here)
from render import render  # noqa: E402
from secret_scan import scan_text  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
APPDATA = "/var/lib/appdata"
# Service UIDs/GIDs and their pinned subordinate ID ranges (see subid_range).
# A lasting promise: files on data disks are owned by IDs from these ranges, so
# never change SUBID_BASE, SUBID_COUNT or MIN_ID (tests pin them).
SUBID_COUNT = 65536
SUBID_BASE = 9157 * SUBID_COUNT  # 600113152, first multiple above SUB_UID_MAX 600100000
MIN_ID = 1000
MAX_ID = 24608  # last range ends at 2147352575, just below the foreign UID range
ALLOWED_CAPS = ("CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID", "NET_BIND_SERVICE")
ENGINES = ("sqlite", "postgres", "mariadb", "mysql", "custom")
CLASSES = ("nfs", "local", "local-db")
TOP_KEYS = {"name", "vm", "uid", "gid", "extra_groups", "title", "description", "login", "login_reason",
            "hostname", "api_paths", "port", "bind", "containers", "secrets", "backups", "accepted_risks",
            "groups", "redirects", "icon", "section"}
CTR_KEYS = {"name", "image", "user_mode", "add_capabilities", "publish", "command", "depends_on", "env",
            "secrets", "volumes", "network", "shm_size_mib"}
VOL_KEYS = {"path", "class", "host", "name", "expected_gib", "engine", "file", "command", "read_only"}

NAME = re.compile(r"[a-z][a-z0-9-]{0,30}")
ENV_KEY = re.compile(r"[A-Z_][A-Z0-9_]*")
PODMAN_NAME = re.compile(r"[a-z][a-z0-9_]{0,62}")
VOL_NAME = re.compile(r"[a-z0-9][a-z0-9-]{0,40}")
FILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}")
IDENT = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,62}")
HOST_LABEL = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")
DOMAIN = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+")
TITLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,60}")
PATH = re.compile(r"/[A-Za-z0-9._+@/-]+")
SCHEDULE = re.compile(r"[A-Za-z0-9 :*,/.-]{1,60}")
IMAGE = re.compile(r"[a-z0-9][a-z0-9._-]*(?::[0-9]+)?(?:/[a-z0-9][a-z0-9._-]*)+"
                   r":([A-Za-z0-9_][A-Za-z0-9_.-]{0,127})(?:@sha256:[0-9a-f]{64})?")


def _plain(value, limit=200, allow_empty=False, human=False) -> bool:
    """A string that can't inject a line, a template placeholder or a control character.

    Every character must be printable (str.isprintable): that refuses ASCII and
    C1 controls (U+0085 NEL among them), U+2028/U+2029 and other separators that
    YAML, systemd or Python treat as line breaks, and format characters. Only
    free text read by people (human=True) may hold non-ASCII letters; every
    value that reaches a config file, command line or regex must be ASCII.
    """
    return (isinstance(value, str) and (allow_empty or value != "") and len(value) <= limit
            and "{{" not in value and all(c.isprintable() for c in value)
            and (human or value.isascii()))


def _text(value, pattern, limit=200) -> bool:
    return _plain(value, limit) and pattern.fullmatch(value) is not None


def _int(value, low, high) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _unknown(node: dict, allowed: set, where: str, errors: list) -> None:
    for key in node:
        if key not in allowed:
            errors.append(f"{where}: unknown field {key!r}")


def _is_path(value) -> bool:
    return (_text(value, PATH, 200) and posixpath.normpath(value) == value
            and ".." not in value.split("/") and value != "/")


def _image_error(value) -> str | None:
    if not _plain(value, 300):
        return "must be a plain image reference"
    match = IMAGE.fullmatch(value)
    if not match:
        return "must be registry/name:tag (a tag is required, optionally followed by @sha256:digest)"
    if match.group(1) == "latest":
        return "must be pinned to a version tag, not latest"
    return None


def _secret_pairs(raw):
    """Normalize a container's secrets to [(env, name)], or None when malformed."""
    if raw is None:
        return []
    if isinstance(raw, dict):
        pairs = list(raw.items())
    elif isinstance(raw, list) and all(isinstance(i, dict) and set(i) == {"env", "name"} for i in raw):
        pairs = [(i["env"], i["name"]) for i in raw]
    else:
        return None
    if not all(isinstance(e, str) and isinstance(n, str) for e, n in pairs):
        return None
    return pairs


def _volume_host(svc: str, ctr: str, vol: dict) -> str:
    if vol["class"] == "local-db":
        return f"{APPDATA}/{svc}/db/{ctr}"
    if vol["class"] == "local":
        return f"{APPDATA}/{svc}/{vol.get('name') or vol['path'].strip('/').replace('/', '-')}"
    return vol["host"]


def _vm_entry(site: dict, name):
    for vm in site.get("vms") or []:
        if isinstance(vm, dict) and vm.get("name") == name:
            return vm
    return None


def _accepted(spec: dict, opening: str) -> bool:
    """True when a risk sentence opens with `<opening>: <reason>` (case-insensitive).

    A substring match would let "15 GB" waive the 5 GB rule, so the sentence
    must start with the exact phrase the error message asks for.
    """
    risks = spec.get("accepted_risks")
    prefix = opening.lower() + ":"
    return isinstance(risks, list) and any(
        isinstance(r, str) and r.strip().lower().startswith(prefix) and r.strip()[len(prefix):].strip()
        for r in risks)


def _backup_settings(spec: dict, site: dict):
    """Return (OnCalendar, keep, errors); spec wins, the site config fills gaps."""
    errors = []
    backups = spec.get("backups") or {}
    if not isinstance(backups, dict):
        return None, None, ["backups must be a mapping"]
    _unknown(backups, {"schedule", "keep"}, "backups", errors)
    site_b = site.get("backups") if isinstance(site.get("backups"), dict) else {}
    keep = backups.get("keep", site_b.get("keep"))
    if keep is None:
        errors.append("backups: no retention; set backups.keep in the service spec or backups.keep in site.yaml")
    elif not _int(keep, 1, 365):
        errors.append("backups.keep must be a whole number from 1 to 365")
    schedule, base = backups.get("schedule"), site_b.get("oncalendar")
    calendar = None
    if schedule in (None, "daily", "weekly"):
        if not _text(base, SCHEDULE):
            errors.append("backups: no time of day; set backups.oncalendar in site.yaml or a literal schedule in the spec")
        elif schedule == "weekly":
            if base.startswith("*-*-* "):
                calendar = "Sun " + base
            else:
                errors.append("backups: weekly needs backups.oncalendar in site.yaml to look like '*-*-* 02:15:00'")
        else:
            calendar = base
    elif _text(schedule, SCHEDULE):
        calendar = schedule
    else:
        errors.append("backups.schedule must be daily, weekly or an OnCalendar time such as 'Mon *-*-* 03:00:00'")
    return calendar, keep, errors


def _check_env(env, where: str, errors: list) -> dict:
    if env is None:
        return {}
    if not isinstance(env, dict):
        errors.append(f"{where}: env must be a mapping")
        return {}
    clean = {}
    for key, value in env.items():
        if not (isinstance(key, str) and ENV_KEY.fullmatch(key)):
            errors.append(f"{where}: environment variable name {key!r} must be capital letters, digits and underscores")
        elif isinstance(value, bool) or not isinstance(value, (str, int)) or not _plain(str(value), 500, True):
            errors.append(f"{where}: value of {key} must be plain text or a number on one line")
        elif scan_text(f"{key}={value}"):
            errors.append(f"{where}: {key} looks like a secret value; use secrets instead of env")
        else:
            clean[key] = str(value)
    return clean


def _check_volumes(site, vm, ctr, where, mode, env, secret_envs, errors):
    volumes = ctr.get("volumes") or []
    if not isinstance(volumes, list) or not all(isinstance(v, dict) for v in volumes):
        errors.append(f"{where}: volumes must be a list of mappings")
        return []
    shares = {s.get("name") for s in (vm or {}).get("nfs_shares") or [] if isinstance(s, dict)}
    seen_paths, hosts, dbs = [], set(), 0
    for number, vol in enumerate(volumes, start=1):
        label = f"{where} volume {number}"
        _unknown(vol, VOL_KEYS, label, errors)
        cls, path = vol.get("class"), vol.get("path")
        if cls not in CLASSES:
            errors.append(f"{label}: class must be one of {', '.join(CLASSES)}")
            continue
        if not _is_path(path):
            errors.append(f"{label}: path must be an absolute, normalized path (no .., no spaces or colons)")
            continue
        for a in seen_paths:
            if path == a or path.startswith(a + "/") or a.startswith(path + "/"):
                errors.append(f"{label}: {path} is inside or the same as {a}; a mount can't hold another mount")
        seen_paths.append(path)
        for field, only in (("host", "nfs"), ("name", "local"), ("engine", "local-db"),
                            ("file", "local-db"), ("command", "local-db")):
            if field in vol and cls != only:
                errors.append(f"{label}: {field} is only for class {only}")
        if "read_only" in vol:
            if not isinstance(vol["read_only"], bool):
                errors.append(f"{label}: read_only must be true or false")
            elif vol["read_only"] and cls == "local-db":
                errors.append(f"{label}: read_only can't be used on a local-db volume (the database must write)")
        if cls == "nfs":
            host = vol.get("host")
            if not _is_path(host) or not host.startswith("/var/mnt/") or host.count("/") < 3:
                errors.append(f"{label}: an NFS folder must be an absolute path under /var/mnt/<share>")
            elif host.split("/")[3] not in shares:
                errors.append(f"{label}: the NFS share {host.split('/')[3]!r} is not listed for this VM in site.yaml")
            if mode == "root-start":
                errors.append(f"{where}: root-start can't use an NFS volume (ownership would not match the file "
                              f"server user); use user_mode map-user")
            continue
        gib = vol.get("expected_gib")
        if isinstance(gib, bool) or not isinstance(gib, (int, float)) or not 0 < gib <= 10000:
            errors.append(f"{label}: expected_gib is required (a number above 0) for {cls} volumes")
        host_name = vol.get("name") or path.strip("/").replace("/", "-")
        if cls == "local" and not (_text(host_name, VOL_NAME, 41) and host_name != "db"):
            errors.append(f"{label}: give this volume a name (lowercase letters, digits, hyphens; not 'db')")
        if cls == "local":
            if host_name in hosts:
                errors.append(f"{label}: two volumes of {where} use the folder {host_name!r}")
            hosts.add(host_name)
        if cls == "local-db":
            dbs += 1
            _check_engine(vol, label, env, secret_envs, site, errors)
    if dbs > 1:
        errors.append(f"{where}: at most one local-db volume per container")
    return volumes


def _check_engine(vol, label, env, secret_envs, site, errors):
    engine = vol.get("engine")
    if engine not in ENGINES:
        errors.append(f"{label}: engine must be one of {', '.join(ENGINES)}")
        return
    if engine == "sqlite":
        if not _text(vol.get("file"), FILE_NAME):
            errors.append(f"{label}: sqlite needs file, the database file name inside the volume")
        image = (site.get("backups") or {}).get("sqlite_image") if isinstance(site.get("backups"), dict) else None
        problem = "is missing" if image is None else _image_error(image)
        if problem:
            errors.append(f"site.yaml backups.sqlite_image {problem}")
    elif "file" in vol:
        errors.append(f"{label}: file is only for sqlite")
    if engine == "custom":
        command = vol.get("command")
        if not _plain(command, 500) or command.strip() == "DUMP_COMMAND_END":
            errors.append(f"{label}: custom needs command, one line that prints the dump on standard output")
    elif "command" in vol:
        errors.append(f"{label}: command is only for custom")
    if engine == "postgres":
        for key in ("POSTGRES_USER", "POSTGRES_DB"):
            if key in env and not IDENT.fullmatch(env[key]):
                errors.append(f"{label}: {key} must be plain letters, digits, _ . -")
    if engine in ("mariadb", "mysql"):
        for key in ("MARIADB_USER", "MARIADB_DATABASE", "MARIADB_PASSWORD"):
            if key not in env and key not in secret_envs:
                errors.append(f"{label}: the {engine} backup reads {key} inside the container; set it in env or secrets")


def _check_container(spec, site, vm, ctr, index, errors):
    where = f"container {index}"
    if not isinstance(ctr, dict):
        errors.append(f"{where} must be a mapping")
        return None
    _unknown(ctr, CTR_KEYS, where, errors)
    name = ctr.get("name")
    if not _text(name, NAME, 31):
        errors.append(f"{where}: name must be lowercase letters, digits and hyphens, starting with a letter")
    elif name in ("files", "network") or name.startswith("backup"):
        errors.append(f"{where}: the name {name!r} is reserved (files, network, backup...)")
    else:
        where = f"container {name}"
    problem = _image_error(ctr.get("image"))
    if problem:
        errors.append(f"{where}: image {problem}")
    mode, caps = ctr.get("user_mode"), ctr.get("add_capabilities") or []
    if mode not in ("map-user", "root-start"):
        errors.append(f"{where}: user_mode must be map-user or root-start")
    if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
        errors.append(f"{where}: add_capabilities must be a list of names")
        caps = []
    if mode == "map-user" and caps:
        errors.append(f"{where}: map-user can't add capabilities; use root-start or remove add_capabilities")
    for cap in caps:
        if mode == "root-start" and cap not in ALLOWED_CAPS:
            errors.append(f"{where}: capability {cap!r} is not allowed (allowed: {', '.join(ALLOWED_CAPS)})")
    if len(set(caps)) != len(caps):
        errors.append(f"{where}: add_capabilities lists a capability twice")
    network = ctr.get("network", "private")
    if network not in ("private", "host"):
        errors.append(f"{where}: network must be private or host")
    publish = ctr.get("publish")
    if publish is not None and not _int(publish, 1, 65535):
        errors.append(f"{where}: publish must be a container port number")
    if publish is not None and network == "host":
        errors.append(f"{where}: a host-network container can't publish a port")
    if "shm_size_mib" in ctr and not _int(ctr["shm_size_mib"], 1, 65536):
        errors.append(f"{where}: shm_size_mib must be a whole number of MiB from 1 to 65536")
    command = ctr.get("command")
    if command is not None and not (isinstance(command, list) and command and all(_plain(c, 500) for c in command)):
        errors.append(f"{where}: command must be a list of plain strings")
    env = _check_env(ctr.get("env"), where, errors)
    pairs = _secret_pairs(ctr.get("secrets"))
    if pairs is None:
        errors.append(f"{where}: secrets must be a mapping ENV: name, or a list of {{env, name}}")
        pairs = []
    for env_name, secret in pairs:
        if not ENV_KEY.fullmatch(env_name) or not PODMAN_NAME.fullmatch(secret):
            errors.append(f"{where}: secret {env_name!r}: {secret!r} has an invalid name")
        if env_name in env:
            errors.append(f"{where}: {env_name} is set in both env and secrets")
    deps = ctr.get("depends_on") or []
    if not isinstance(deps, list) or not all(isinstance(d, str) for d in deps):
        errors.append(f"{where}: depends_on must be a list of container names")
        deps = []
    volumes = _check_volumes(site, vm, ctr, where, mode, env, {e for e, _ in pairs}, errors)
    return {"name": name, "publish": publish, "deps": deps, "pairs": pairs, "volumes": volumes,
            "network": network, "mode": mode}


def _has_cycle(graph: dict) -> bool:
    state = {}

    def visit(node) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        found = any(visit(dep) for dep in graph.get(node, ()) if dep in graph)
        state[node] = 2
        return found

    return any(visit(node) for node in graph)


def _frontend_code(spec, site, errors):
    """(ingress code, gateway code) when the site chose its login front end modules. A spec that
    uses the login page or a key only they give meaning to needs them; there is no default."""
    needs = spec.get("login") == "gateway" or any(k in spec for k in ("groups", "icon", "section", "redirects"))
    if not needs:
        return None, None
    try:
        names = modules.chosen(site)
    except SpecError as error:
        errors.append(str(error))
        return None, None
    return modules.code(names["ingress"]), modules.code(names["auth_gateway"])


def _check_login(spec, site, publisher, errors):
    ingress, gateway = _frontend_code(spec, site, errors)
    if gateway is not None:
        gateway.check_spec(spec, errors)
        ingress.check_spec(spec, gateway.reserved_paths(), errors)
    login = spec.get("login")
    if login not in ("gateway", "app-only"):
        errors.append("login is required: gateway (behind the login page) or app-only (with login_reason)")
    elif login == "app-only":
        if not _plain(spec.get("login_reason"), human=True):
            errors.append("login app-only needs login_reason, a sentence on why there is no login in front")
        # With a hostname it gets an HTTPS route without the login page.
        if "hostname" in spec:
            if not _text(spec.get("hostname"), HOST_LABEL, 63):
                errors.append("hostname must be one name under the site domain (no dots)")
            if not publisher:
                errors.append("hostname needs one container that publishes a port (the route's target)")
            if not _text(site.get("domain"), DOMAIN, 253):
                errors.append("site.yaml: domain is missing or invalid")
    else:
        if not publisher:
            errors.append("login gateway needs one container that publishes a port")
        if not _text(spec.get("hostname"), HOST_LABEL, 63):
            errors.append("login gateway needs hostname, one name under the site domain (no dots)")
        if not _text(site.get("domain"), DOMAIN, 253):
            errors.append("site.yaml: domain is missing or invalid")
        edge = site.get("edge") if isinstance(site.get("edge"), dict) else {}
        if ingress is not None:
            for who in (modules.service_name(modules.chosen(site)[k]) for k in ("ingress", "auth_gateway")):
                entry = edge.get(who) if isinstance(edge.get(who), dict) else {}
                for key in ("uid", "gid"):
                    if not _int(entry.get(key), MIN_ID, MAX_ID):
                        errors.append(f"site.yaml: edge.{who}.{key} is missing or invalid")
    paths = spec.get("api_paths", [])
    if not isinstance(paths, list):
        errors.append("api_paths must be a list of regular expressions")
        return
    for path in paths:
        try:
            ok = _plain(path, 200) and path == path.strip() and re.compile(path)
        except re.error:
            ok = False
        if not ok:
            errors.append(f"api_paths: {path!r} must be a valid one-line regular expression")


def validate_spec(spec, site) -> list[str]:
    """Return every problem with the spec (empty list = valid)."""
    if not isinstance(spec, dict):
        return ["the service spec must be a mapping"]
    if not isinstance(site, dict):
        return ["the site config must be a mapping"]
    errors: list[str] = []
    _unknown(spec, TOP_KEYS, "service spec", errors)
    if not _text(spec.get("name"), NAME, 31):
        errors.append("name must be lowercase letters, digits and hyphens, starting with a letter, at most 31 characters")
    if not _int(spec.get("uid"), MIN_ID, MAX_ID):
        errors.append(f"uid is required (a number from {MIN_ID} to {MAX_ID}, the IDs whose pinned container "
                      "ranges fit; match the file server user if it uses NFS)")
    if "gid" in spec and not _int(spec["gid"], MIN_ID, MAX_ID):
        errors.append(f"gid must be a number from {MIN_ID} to {MAX_ID}")
    groups = spec.get("extra_groups") or []
    if not isinstance(groups, list) or not all(_text(g, NAME, 31) for g in groups):
        errors.append("extra_groups must be a list of group names")
    if "title" in spec and not _text(spec["title"], TITLE, 61):
        errors.append("title must be plain words (letters, digits, spaces, . _ -)")
    if "description" in spec and not (_plain(spec["description"], 120, human=True)
                                      and not set(spec["description"]) & set("{}%$")):
        errors.append("description must be one plain line")
    risks = spec.get("accepted_risks", [])
    if not isinstance(risks, list) or not all(_plain(r, 300, human=True) for r in risks):
        errors.append("accepted_risks must be a list of plain sentences")
    vm = _vm_entry(site, spec.get("vm"))
    if vm is None:
        errors.append(f"vm {spec.get('vm')!r} is not listed in site.yaml (vms)")
    elif not _text(vm["name"], HOST_LABEL, 63):
        errors.append("the vm name in site.yaml must be lowercase letters, digits and hyphens")

    containers = spec.get("containers")
    if not isinstance(containers, list) or not containers:
        errors.append("containers must be a non-empty list")
        containers = []
    info = [i for i in (_check_container(spec, site, vm, c, n, errors) for n, c in enumerate(containers, 1)) if i]
    names = [i["name"] for i in info if isinstance(i["name"], str)]
    if len(set(names)) != len(names):
        errors.append("two containers have the same name")
    graph = {}
    for i in info:
        for dep in i["deps"]:
            if dep not in names:
                errors.append(f"container {i['name']}: depends_on {dep!r} is not a container of this service")
            elif dep == i["name"]:
                errors.append(f"container {i['name']}: depends on itself")
        graph[i["name"]] = i["deps"]
    if _has_cycle(graph):
        errors.append("depends_on has a cycle")
    publishers = [i for i in info if i["publish"] is not None]
    if len(publishers) > 1:
        errors.append("only one container may publish a port; found " + ", ".join(str(i["name"]) for i in publishers))
    _check_publish(spec, vm, publishers, errors)
    _check_login(spec, site, bool(publishers), errors)

    declared = spec.get("secrets") or []
    if not isinstance(declared, list) or not all(isinstance(s, dict) for s in declared):
        errors.append("secrets must be a list of mappings with name, durable, source")
        declared = []
    declared_names = set()
    for secret in declared:
        _unknown(secret, {"name", "durable", "source", "value"}, "secrets", errors)
        if "value" in secret and not (_plain(secret["value"], 200, human=True) and "|" not in secret["value"]):
            errors.append(f"secret {secret.get('name')}: value must say on one line (no |, at most 200 "
                          "characters) what to enter, as the app's docs describe it")
        if not _text(secret.get("name"), PODMAN_NAME, 63):
            errors.append(f"secret name {secret.get('name')!r} must be lowercase letters, digits and underscores")
            continue
        declared_names.add(secret["name"])
        if not isinstance(secret.get("durable", False), bool):
            errors.append(f"secret {secret['name']}: durable must be true or false")
        if secret.get("source", "prompt" if secret.get("durable") else "generate") not in ("generate", "prompt", "file"):
            errors.append(f"secret {secret['name']}: source must be generate, prompt or file")
        elif secret.get("durable") is True and secret.get("source") == "generate":
            errors.append(f"secret {secret['name']}: a durable value must be kept by the user, so source can't be generate")
    used = {n for i in info for _, n in i["pairs"]}
    for name in sorted(used - declared_names):
        errors.append(f"secret {name} is used by a container but not listed in secrets")
    for name in sorted(declared_names - used):
        errors.append(f"secret {name} is listed in secrets but no container uses it")

    sizes: dict[str, float] = {}
    targets = []
    modes: dict[str, dict] = {}  # host folder -> {user_mode: [container names]}
    for i in info:
        for vol in i["volumes"]:
            if vol.get("class") in ("local", "local-db") and _is_path(vol.get("path")) \
                    and isinstance(vol.get("expected_gib"), (int, float)) and not isinstance(vol["expected_gib"], bool):
                host = _volume_host(str(spec.get("name")), str(i["name"]), vol)
                sizes[host] = max(sizes.get(host, 0), vol["expected_gib"])
                targets.append(host)
                if i.get("mode") in ("map-user", "root-start"):
                    modes.setdefault(host, {}).setdefault(i["mode"], []).append(str(i["name"]))
    # map-user writes files as the service user; root-start writes them as a
    # sub-UID. Sharing one folder would leave each unable to use the other's files.
    for host, by_mode in sorted(modes.items()):
        if len(by_mode) > 1:
            who = "; ".join(f"{m}: {', '.join(n)}" for m, n in sorted(by_mode.items()))
            errors.append(f"folder {host} is shared by containers with different user_mode ({who}); "
                          "use the same user_mode or give each its own folder")
    if sum(sizes.values()) > 5 and not _accepted(spec, "over the 5 GB rule"):
        errors.append(f"local storage adds up to {sum(sizes.values()):g} GiB, over the 5 GB rule; use NFS, shrink it, "
                      "or record 'over the 5 GB rule: ...' in accepted_risks")
    if targets or "backups" in spec:
        errors += _backup_settings(spec, site)[2]
    if targets and vm is not None and "backups" not in {s.get("name") for s in vm.get("nfs_shares") or [] if isinstance(s, dict)} \
            and not _accepted(spec, "no backups"):
        errors.append("this VM has no 'backups' NFS share in site.yaml, so backups could never run; add it or record "
                      "'no backups: ...' in accepted_risks")
    return errors


def _check_publish(spec, vm, publishers, errors):
    bind = spec.get("bind", "vm_ip")
    if bind not in ("vm_ip", "loopback"):
        errors.append("bind must be vm_ip or loopback")
    if not publishers:
        if "port" in spec:
            errors.append("port is set but no container publishes; add publish to one container or remove port")
        return
    if not _int(spec.get("port"), 1024, 65535):
        errors.append("port is required when a container publishes (the host port, 1024-65535)")
    if bind == "vm_ip" and vm is not None:
        try:
            if not isinstance(vm.get("ip"), str):
                raise ValueError
            ipaddress.IPv4Address(vm["ip"])
        except ValueError:
            errors.append(f"vm {vm.get('name')!r} has no valid ip in site.yaml (vms[].ip)")


def _escape(text: str) -> str:
    """Escape for a systemd unit line: quotes, backslashes, and % and $ (which systemd expands)."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%").replace("$", "$$")


def _quote(text: str) -> str:
    text = _escape(text)
    return text if re.fullmatch(r"[A-Za-z0-9_@+=:,./%-]+", text) else f'"{text}"'


def _dir_entry(path: str, mode: str, uid: int, gid: int) -> str:
    return (f"    - path: {path}\n      mode: {mode}\n      user:\n        id: {uid}\n"
            f"      group:\n        id: {gid}")


def _tidy(text: str) -> str:
    """Drop the blank lines left by empty placeholders; keep one before each section."""
    lines = text.split("\n")
    kept: list[str] = []
    for number, line in enumerate(lines):
        if line == "":
            following = next((x for x in lines[number + 1:] if x), None)
            if following is None or not following.startswith("[") or (kept and kept[-1] == ""):
                continue
        kept.append(line)
    return "\n".join(kept) + "\n"


def _fill(template: str, values: dict) -> str:
    return render((TEMPLATES / template).read_text(encoding="utf-8"), {k: str(v) for k, v in values.items()})


def _secret_value_text(secret: dict) -> tuple[str, str]:
    """(what to enter, keep it) for the user's secrets table."""
    durable = secret.get("durable", False)
    source = secret.get("source", "prompt" if durable else "generate")
    if source == "generate":
        return "nothing: generated on the VM, never shown", "no; a rebuild makes a new one"
    what = secret.get("value") or ("a key file" if source == "file" else "a long random value, no spaces")
    keep = "yes, in your password manager: a rebuild needs the same value" if durable else "no"
    return what, keep


def _secrets_report(spec, svc, vm, uid, containers) -> str:
    run = f"sudo -u {svc} XDG_RUNTIME_DIR=/run/user/{uid} podman secret create"
    users = {}
    for ctr in containers:
        for env, name in _secret_pairs(ctr.get("secrets")):
            users.setdefault(name, []).append(f"{ctr['name']} ({env})")
    out = [f"# Secrets for {svc}", "",
           f"Podman secrets belong to the user that runs the containers, so every command below runs as user `{svc}` "
           "on the VM, before the first start. This file lists names only; no value is stored in it.", "",
           "| Secret | Used by | What to enter | Keep it |", "|---|---|---|---|"]
    for secret in spec.get("secrets") or []:
        what, keep = _secret_value_text(secret)
        out.append(f"| `{secret['name']}` | {', '.join(users[secret['name']])} | {what} | {keep} |")
    out.append("")
    for secret in spec.get("secrets") or []:
        name, durable = secret["name"], secret.get("durable", False)
        source = secret.get("source", "prompt" if durable else "generate")
        out += [f"## {name}", "", f"- Owner: user `{svc}` on vm {vm}", f"- Used by: {', '.join(users[name])}"]
        if source == "file":
            out += ["- Durable: keep the file in your password manager; a rebuild must load the same file again.",
                    "- Value: a file (several lines, e.g. a key file). Copy it to /dev/shm on the VM (memory, "
                    "not the VM's disk), then run the command: it loads the file into the secret and removes the copy."]
        elif durable:
            out += ["- Durable: save this value in your password manager; a rebuild must re-enter the same value.",
                    "- Value: create it in your password manager first, then paste it at the hidden prompt."]
        elif source == "prompt":
            out += ["- Value: you enter it at the hidden prompt (for example a key from the provider)."]
        else:
            out += ["- Value: generated on the VM, never shown; nothing to keep (a rebuild creates a new one)."]
        out += ["", "```bash", f"# vm {vm} (bash, admin)", "cd /"]
        if source == "prompt":
            out += [f'read -rs -p "value for {name}: " v; echo', f'printf %s "$v" | {run} {name} -', "unset v"]
        elif source == "file":
            out += [f'read -r -p "path of the {name} file on this VM (e.g. /dev/shm/key.p8): " f',
                    f'{run} {name} - < "$f" && shred -u -- "$f" && echo "{name} created; the copy is removed"']
        else:
            out += [f"head -c 32 /dev/urandom | base64 | {run} {name} -"]
        out += ["```", ""]
    return "\n".join(out)


def subid_range(number: int) -> tuple[int, int]:
    """(first, last) subordinate ID for a UID or GID: 65536 IDs per number.

    Distinct numbers never overlap. The first range starts at SUBID_BASE, the
    first multiple of 65536 above useradd's whole area (Fedora login.defs:
    SUB_UID_MIN 524288 .. SUB_UID_MAX 600100000), so no automatic range can
    ever collide. MAX_ID keeps the last range below systemd's foreign UID
    range (2147352576, open to every user) and the IDs above 2**31 that some
    kernel code mishandles (systemd.io/UIDS-GIDS).
    """
    first = SUBID_BASE + (number - MIN_ID) * SUBID_COUNT
    return first, first + SUBID_COUNT - 1


def _span(number: int) -> str:
    first, last = subid_range(number)
    return f"{first}-{last}"


def _file_server_report(spec, site, svc, vm, uid, gid) -> str:
    """One table of every folder the user makes on the file server for this service."""
    shares = {s.get("name"): s.get("export") for s in (_vm_entry(site, vm) or {}).get("nfs_shares") or []
              if isinstance(s, dict)}
    gids = {g.get("name"): g.get("gid") for g in site.get("shared_groups") or [] if isinstance(g, dict)}
    user = f"`{svc}` (UID {uid})"
    rows = []
    backed_up = any(v["class"] != "nfs" for c in spec["containers"] for v in c.get("volumes") or [])
    if backed_up and shares.get("backups"):
        base = shares["backups"].rstrip("/")
        rows.append(f"| `{base}/{vm}/` | the share's admin account | its own group | 0755 | one folder per "
                    f"service on VM {vm}; not group-writable |")
        rows.append(f"| `{base}/{vm}/{svc}/` | {user} | `{svc}` (GID {gid}) | 0750 | backups of {svc} |")
    shared = (spec.get("extra_groups") or [None])[0]
    group, mode = (f"`{shared}` (GID {gids.get(shared, 'from shared_groups')})", "2775") if shared \
        else (f"`{svc}` (GID {gid})", "0750")
    for ctr in spec["containers"]:
        for vol in ctr.get("volumes") or []:
            if vol["class"] == "nfs":
                share, rest = vol["host"].split("/")[3], "/".join(vol["host"].split("/")[4:])
                path = f"{shares.get(share, '<' + share + ' export>').rstrip('/')}/{rest}".rstrip("/")
                rows.append(f"| `{path}` | {user} | {group} | {mode} | {vol['path']} in container {ctr['name']} |")
    if not rows:
        return f"# File server folders for {svc}\n\nNone: {svc} keeps nothing on the file server.\n"
    return "\n".join([
        f"# File server folders for {svc}", "",
        "Create these on the file server (you do this; the agent never touches it). The VM sends "
        "numbers, so the UID and GID must match; the names on the file server don't matter. Create a user "
        "or group only when none has that number yet, otherwise use the existing one. A mode with 2 in front "
        "(setgid) keeps new files in the shared group.", "",
        "| Folder on the file server | User | Group | Mode | What it holds |", "|---|---|---|---|---|",
        *rows, ""])


BACKUP_FILE = {"mariadb": "sql.gz", "mysql": "sql.gz", "postgres": "dump", "sqlite": "sqlite", "custom": "dump.gz"}


def _backups_report(spec, site, svc, vm, calendar, keep) -> str:
    """For the final report: what is backed up, when, where, and how to restore it."""
    rows = []
    for ctr in spec["containers"]:
        for vol in ctr.get("volumes") or []:
            if vol["class"] == "local-db":
                time = "<time>" if vol["engine"] == "sqlite" else "<UTC time>"
                rows.append(f"| database of {ctr['name']} ({vol['engine']}) | `{svc}-backup-{ctr['name']}.timer` | "
                            f"`{ctr['name']}-{time}.{BACKUP_FILE[vol['engine']]}` | {calendar} |")
    if any(v["class"] == "local" for c in spec["containers"] for v in c.get("volumes") or []):
        rows.append(f"| files of {svc} (data disk, without the database) | `{svc}-backup-files.timer` | "
                    f"`files-<UTC time>.tar.gz` | {calendar} |")
    if not rows:
        return f"# Backups of {svc}\n\nNothing to back up: {svc} keeps no data on the VM's data disk.\n"
    export = next((s.get("export") for s in (_vm_entry(site, vm) or {}).get("nfs_shares") or []
                   if isinstance(s, dict) and s.get("name") == "backups"), None)
    if not export:
        return "\n".join([f"# Backups of {svc}", "", "| What | Unit | File | When |", "|---|---|---|---|", *rows, "",
                          f"VM {vm} has no backups share, so these backups can't run (recorded in the "
                          "service's accepted risks). Add the share to the VM in the site file to start them.", ""])
    where = f"`{export.rstrip('/')}/{vm}/{svc}/`"
    return "\n".join([
        f"# Backups of {svc}", "",
        "| What | Unit | File | When |", "|---|---|---|---|", *rows, "",
        f"- **Where:** {where} on the file server (`/var/mnt/backups/{vm}/{svc}/` on VM {vm}).",
        f"- **Kept:** the newest {keep} of each kind; older ones are deleted after each run.",
        "- **When:** each timer runs at the time above (systemd OnCalendar, the VM's clock). The timers are "
        "Persistent, so a run missed while the VM was off happens right after it starts again.",
        "- **File server off:** the run skips quietly and tries again next time; nothing on the VM changes.",
        "- **Check one now:** guide 4, Check a backup (`docs/guide/04-databases-and-backups.md` in the agent's folder).",
        "- **Restore** (only if the data disk is lost): guide 4, Restore. It needs the same durable secrets as "
        "before, from your password manager.",
        "- **Prove it restores** without touching anything live: guide 4, Test a restore.", ""])


def _ids_report(spec, svc, vm, uid, gid) -> str:
    first_u, last_u = subid_range(uid)
    first_g, last_g = subid_range(gid)
    out = [f"# IDs for {svc}", "",
           "Keep this with your notes: it says which numbers own this app's files on disk. "
           "It holds no secret.", "",
           f"- VM: {vm}",
           f"- User: `{svc}`, UID {uid}",
           f"- Group: `{svc}`, GID {gid}",
           f"- Subordinate UIDs: {first_u}-{last_u} (first ID {first_u})",
           f"- Subordinate GIDs: {first_g}-{last_g} (first ID {first_g})",
           f"- Pinned at boot by `subids-{svc}.service`, from the UID and GID, so a rebuild or another app's "
           "removal never changes them.",
           "- Lasting: changing this app's UID or GID later changes its ranges, and its files on the data disk "
           "then need new owners (shift each by the difference between the old and new first ID).", "",
           "## Container user to disk owner", "",
           f"Rootless Podman maps container root to the app's own user ({uid}:{gid}) and container user n "
           f"(n of 1 or more) to first ID + n - 1: container user 999 owns its files on disk as "
           f"{first_u + 998}. The same for groups: container group n is {first_g} + n - 1 on disk.", "",
           f"Containers with `UserNS=keep-id` (user_mode map-user) run as {uid} inside, which owns its "
           f"files as {uid}; their other container users map differently, so read the real map below "
           "before changing owners by hand.", "",
           "| Container | user_mode |", "|---|---|"]
    out += [f"| {svc}-{c['name']} | {c['user_mode']} |" for c in spec["containers"]]
    out += ["", "To see the real mapping of a running container (the source of truth):", "",
            "```bash", f"# vm {vm} (bash, admin)", "cd /",
            f"sudo -u {svc} XDG_RUNTIME_DIR=/run/user/{uid} podman exec {svc}-{spec['containers'][0]['name']} "
            "cat /proc/self/uid_map /proc/self/gid_map", "```", ""]
    return "\n".join(out)


def _check_output_folder(out: Path) -> Path:
    """The resolved output folder. These generators run without asking and delete files an earlier run
    listed in a manifest, so the folder may not be the toolkit, inside it, or a folder that holds it."""
    toolkit = Path(__file__).resolve().parent.parent
    root = Path(out).resolve()
    if root == toolkit or toolkit in root.parents or root in toolkit.parents:
        raise SpecError(f"output folder {out} is the toolkit, inside it or around it; use a folder in the "
                        "workspace (for example <workspace>/services/<svc> or <workspace>/login-frontend)")
    return root


def _write_all(out: Path, svc: str, files: dict[str, str]) -> list[Path]:
    """Write files, remove ones an earlier run wrote that this run does not, return every path."""
    root = _check_output_folder(out)
    manifest = out / f".gen-service-{svc}.json"
    try:
        old = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else []
    except ValueError:
        old = []
    for rel in old if isinstance(old, list) else []:
        stale = (out / rel).resolve() if isinstance(rel, str) else None
        if stale and rel not in files and root in stale.parents and stale.is_file():
            stale.unlink()
    written = []
    for rel, text in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            path.unlink()
        if isinstance(text, bytes):  # an app icon
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")
        written.append(path)
    manifest.write_text(json.dumps(sorted(files)), encoding="utf-8")
    return written + [manifest]


def generate(spec: dict, site: dict, out) -> list[Path]:
    errors = validate_spec(spec, site)
    if errors:
        raise SpecError("\n".join(errors))
    out = Path(out)
    svc, vm_name, uid = spec["name"], spec["vm"], spec["uid"]
    gid = spec.get("gid", uid)
    vm = _vm_entry(site, vm_name)
    loopback = spec.get("bind", "vm_ip") == "loopback"
    bind_ip = "127.0.0.1" if loopback else vm["ip"]
    title = spec.get("title", svc)
    base = {"SVC_NAME": svc, "SVC_UID": uid, "SVC_GID": gid, "VM_NAME": vm_name,
            "SVC_EXTRA_GROUPS": ", ".join(spec.get("extra_groups") or [])}
    calendar, keep, _ = _backup_settings(spec, site)
    files: dict[str, str] = {}
    dirs: dict[str, str] = {}
    quadlets = []
    local_volumes = False
    publisher = None

    files[f"rendered/files/{svc}.network"] = _fill("service/network.tmpl", base)
    quadlets.append((f"{svc}.network", f"files/{svc}.network"))
    for ctr in spec["containers"]:
        name = ctr["name"]
        roots, volume_lines = {APPDATA}, []
        for vol in ctr.get("volumes") or []:
            host = _volume_host(svc, name, vol)
            ro = vol.get("read_only") is True
            if vol["class"] == "nfs":
                roots.add("/".join(host.split("/")[:4]))
                volume_lines.append(f"Volume={host}:{vol['path']}" + (":ro" if ro else ""))
                continue
            volume_lines.append(f"Volume={host}:{vol['path']}:" + ("ro,z" if ro else "z"))
            if vol["class"] == "local-db":
                dirs[f"{APPDATA}/{svc}/db"] = "0750"
                dirs[host] = "0700"
            else:
                dirs[host] = "0750"
                local_volumes = True
        mode, caps = ctr["user_mode"], ctr.get("add_capabilities") or []
        security = ["UserNS=keep-id"] if mode == "map-user" else [f"AddCapability={c}" for c in caps]
        deps = [line for d in ctr.get("depends_on") or [] for line in (f"Requires={svc}-{d}.service", f"After={svc}-{d}.service")]
        publish = ""
        if ctr.get("publish") is not None:
            publish = f"PublishPort={bind_ip}:{spec['port']}:{ctr['publish']}"
            publisher = ctr
        command = ctr.get("command")
        values = dict(base, CTR_NAME=name, SVC_IMAGE=ctr["image"], SVC_DESCRIPTION=f"{spec.get('description', title)} ({name})",
                      CTR_DEPENDS="\n".join(deps), CTR_SECURITY="\n".join(security),
                      CTR_NETWORK="Network=host" if ctr.get("network") == "host" else f"Network={svc}.network",
                      CTR_PUBLISH=publish, SVC_VOLUMES="\n".join(volume_lines),
                      CTR_SHM=f"ShmSize={ctr['shm_size_mib']}m" if "shm_size_mib" in ctr else "",
                      SVC_SECRETS="\n".join(f"Secret={n},type=env,target={e}" for e, n in _secret_pairs(ctr.get("secrets"))),
                      SVC_ENVIRONMENT="\n".join(f'Environment="{_escape(f"{k}={v}")}"'
                                                for k, v in (ctr.get("env") or {}).items()),
                      CTR_EXEC="Exec=" + " ".join(_quote(str(a)) for a in command) if command else "",
                      SVC_MOUNT_ROOTS=" ".join([APPDATA] + sorted(roots - {APPDATA})))
        files[f"rendered/files/{svc}-{name}.container"] = _tidy(_fill("service/container.tmpl", values))
        quadlets.append((f"{svc}-{name}.container", f"files/{svc}-{name}.container"))
        engine_db = next((v for v in ctr.get("volumes") or [] if v["class"] == "local-db"), None)
        if engine_db:
            files.update(_backup_fragment(spec, site, ctr, engine_db, base, calendar, keep))

    quad_text = "\n".join(f"    - path: /etc/containers/systemd/users/{uid}/{dest}\n      mode: 0644\n"
                          f"      overwrite: true\n      contents:\n        local: {src}" for dest, src in quadlets)
    files[f"rendered/{svc}.bu"] = _fill("service/service.bu.tmpl", dict(
        base, SVC_APPDATA_DIRS="\n".join(_dir_entry(p, m, uid, gid) for p, m in sorted(dirs.items())),
        SVC_QUADLET_FILES=quad_text, SVC_SUBUIDS=_span(uid), SVC_SUBGIDS=_span(gid)))
    if publisher and not loopback:
        files[f"rendered/{svc}-port.bu"] = _fill("service/service-port.bu.tmpl", dict(base, SVC_PORT=spec["port"]))
    if local_volumes:
        files[f"rendered/{svc}-backup-files.bu"] = _fill("service/backup-files.bu.tmpl",
                                                          dict(base, BACKUP_KEEP=keep, BACKUP_ONCALENDAR=calendar))
    if has_route(spec):
        files.update(_route_files(spec, site))
    files["secrets.md"] = _secrets_report(spec, svc, vm_name, uid, spec["containers"])
    files["ids.md"] = _ids_report(spec, svc, vm_name, uid, gid)
    files["file-server.md"] = _file_server_report(spec, site, svc, vm_name, uid, gid)
    files["backups.md"] = _backups_report(spec, site, svc, vm_name, calendar, keep)
    return _write_all(out, svc, files)


def _backup_fragment(spec, site, ctr, vol, base, calendar, keep) -> dict:
    svc, name, engine = spec["name"], ctr["name"], vol["engine"]
    env = ctr.get("env") or {}
    unit = f"{svc}-backup-{name}"
    values = dict(base, CTR_NAME=name, BACKUP_UNIT=unit, BACKUP_KEEP=keep, BACKUP_ONCALENDAR=calendar,
                  BACKUP_SECURITY="UserNS=keep-id" if ctr["user_mode"] == "map-user" else "AddCapability=DAC_OVERRIDE",
                  SVC_DB_DIR=_volume_host(svc, name, vol), SVC_DB_FILE=vol.get("file", ""),
                  BACKUP_SQLITE_IMAGE=(site.get("backups") or {}).get("sqlite_image", ""),
                  DUMP_COMMAND=vol.get("command", ""), PG_CONTAINER=f"{svc}-{name}",
                  PG_USER=env.get("POSTGRES_USER", "postgres"))
    values["PG_DB"] = env.get("POSTGRES_DB", values["PG_USER"])
    template = "mariadb" if engine == "mysql" else engine
    return {f"rendered/{unit}.bu": _fill(f"service/backup-{template}.bu.tmpl", values)}


def route_backend(spec: dict, site: dict) -> str:
    """The address the ingress forwards to: the VM's IP, or 127.0.0.1 for a loopback service."""
    if spec.get("bind", "vm_ip") == "loopback":
        return f"http://127.0.0.1:{spec['port']}"
    return f"http://{_vm_entry(site, spec['vm'])['ip']}:{spec['port']}"


def has_route(spec: dict) -> bool:
    """Behind the login page, or on its own login with a hostname (HTTPS, no login page)."""
    return spec.get("login") == "gateway" or (spec.get("login") == "app-only" and "hostname" in spec)


def route_texts(spec: dict, site: dict) -> tuple[str, str]:
    """(route file, gateway rules file) for a validated, routed spec, written by the chosen modules.

    login gateway: a route through the auth gateway, and rules that give the app a provider and an
    application. login app-only with a hostname: a route without the login, and a dashboard link only.
    """
    names = modules.chosen(site)
    ingress, gateway = modules.code(names["ingress"]), modules.code(names["auth_gateway"])
    svc = spec["name"]
    values = {"ROUTE_NAME": svc, "ROUTE_TITLE": spec.get("title", svc), "ROUTE_BACKEND": route_backend(spec, site),
              "ROUTE_HOST": f"{spec['hostname']}.{site['domain']}",
              "API_SKIP_REGEX": "\n        ".join(spec.get("api_paths") or [])}
    values.update(ingress.redirect_blocks(svc, values["ROUTE_HOST"], spec.get("redirects") or []))
    kind = {"gateway": "gateway", "app-only": "open"}.get(spec["login"])
    if kind is None:
        raise SpecError(f"login {spec['login']!r} has no route kind")  # fail closed on a new value
    return (ingress.route_text(kind, names["auth_gateway"], values), gateway.binding_text(spec, values, kind))


def _route_files(spec, site) -> dict:
    """The route (and gateway rules), written next to the service for review; the
    login front end (tools/login_frontend.py) places them on its VM."""
    svc = spec["name"]
    route, blueprint = route_texts(spec, site)
    return {f"rendered/files/route-{svc}.yml": route, f"rendered/files/app-{svc}.blueprint.yaml": blueprint}


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        import yaml
    except ImportError:
        print("install PyYAML (python-yaml / python3-yaml)", file=sys.stderr)
        return 2
    try:
        spec, site = (yaml.safe_load(Path(p).read_text(encoding="utf-8")) for p in argv[1:3])
        for path in generate(spec, site or {}, argv[3]):
            print(path)
    except (OSError, yaml.YAMLError, SpecError) as error:
        print(f"gen_service: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
