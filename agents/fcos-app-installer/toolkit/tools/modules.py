#!/usr/bin/env python3
"""Service modules: which are installed, which the site chose, and their code.

A module is a skill folder in the skills folder (tools/layout.py), one per product, named
<capability prefix>-<product>: ingress-<product> (a reverse proxy) or authgw-<product> (an auth
gateway). Its module.yaml says what it provides, what it needs and what it pairs with (and whether
that pairing was tested). The site file chooses one module per capability under login_frontend;
nothing is chosen for you. The generic tools (login_frontend.py, gen_service.py) read a module's data
and call its code (tools/<family>/<product>.py) and never name a product themselves.

Usage:
  modules.py list [--capability ingress|auth_gateway]   what is installed, for choosing or recommending
  modules.py services <site.yaml>                       the service names of the modules the site chose

To add a module for another product, see docs/guide/12-add-a-module.md.
"""
import importlib
import inspect
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import SKILLS  # noqa: E402

# capability -> (skill folder prefix, key under login_frontend in site.yaml)
CAPABILITIES = {"ingress": ("ingress-", "ingress"), "auth_gateway": ("authgw-", "auth_gateway")}
SITE_BLOCK = "login_frontend"
REQUIRED = ("capability", "product", "summary", "provides", "needs", "pairs_with", "spec", "code")
# The Python package each capability's code lives in: tools/<package>/<product>.py
PACKAGES = {"ingress": "ingress", "auth_gateway": "authgw"}
CODE_NAME = re.compile(r"(ingress|authgw)\.[a-z][a-z0-9_]*")
# What the generic tools call, with the parameter names (docs/guide/12-add-a-module.md lists the same).
CONTRACT = {
    "ingress": {
        "route_name_problem": ("name",),
        "check_spec": ("spec", "reserved_paths", "errors"),
        "redirect_blocks": ("svc", "host", "redirects"),
        "route_text": ("kind", "gateway", "values"),
        "place": ("site", "spec", "gateway", "gateway_values", "routes", "acme"),
    },
    "auth_gateway": {
        "reserved_route_names": (),
        "reserved_route_suffix": (),
        "reserved_paths": (),
        "forward_auth_values": ("site",),
        "host_label": ("site", "domain"),
        "check_spec": ("spec", "errors"),
        "binding_text": ("spec", "values", "kind"),
        "settings": ("site",),
        "prepare_spec": ("spec", "config"),
        "place": ("site", "spec", "config", "routed", "bindings", "icon_dirs"),
    },
}


def _error(message: str):
    from gen_service import SpecError  # imported late: gen_service imports this module
    return SpecError(message)


def _yaml():
    import yaml
    return yaml


def _strings(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v for v in value)


def read(name: str) -> dict:
    """A module's module.yaml, checked: required keys, their types, a code name inside the toolkit's
    own packages and a spec file inside the module's folder. The message names the module."""
    if not (isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9-]{0,60}", name)):
        raise _error(f"module name {name!r} is not a valid skill folder name")
    folder = SKILLS / name
    path = folder / "module.yaml"
    if not path.is_file():
        raise _error(f"module {name!r} is not installed (no {path})")
    try:
        data = _yaml().safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:  # a YAML syntax error
        raise _error(f"module {name!r}: module.yaml can't be read ({error})") from None
    if not isinstance(data, dict):
        raise _error(f"module {name!r}: module.yaml must be a mapping")
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        raise _error(f"module {name!r}: module.yaml lacks {', '.join(missing)}")
    capability = data["capability"]
    if capability not in CAPABILITIES:
        raise _error(f"module {name!r}: unknown capability {capability!r}; known: {', '.join(CAPABILITIES)}")
    if not (isinstance(data["product"], str) and isinstance(data["summary"], str)):
        raise _error(f"module {name!r}: product and summary must be text")
    for key in ("provides", "needs"):
        if not _strings(data[key]):
            raise _error(f"module {name!r}: {key} must be a list of words")
    pairs = data["pairs_with"]
    if not (isinstance(pairs, list) and all(
            isinstance(p, dict) and isinstance(p.get("module"), str) and isinstance(p.get("tested"), bool)
            and isinstance(p.get("how"), str) and p["how"].strip() for p in pairs)):
        raise _error(f"module {name!r}: pairs_with must be a list of {{module, tested (true or false), how}}")
    code_name = data["code"]
    if not (isinstance(code_name, str) and CODE_NAME.fullmatch(code_name)
            and code_name.split(".")[0] == PACKAGES[capability]):
        raise _error(f"module {name!r}: code must be {PACKAGES[capability]}.<product> "
                     f"(a file in tools/{PACKAGES[capability]}/), not {code_name!r}")
    spec = data["spec"]
    if not isinstance(spec, str) or not (folder / spec).resolve().is_relative_to(folder.resolve()) or spec.startswith("/"):
        raise _error(f"module {name!r}: spec must be a file inside the module's folder, not {spec!r}")
    return data


def _scan(capability: str) -> tuple[list[str], list[tuple[str, str]]]:
    """(installed module names, (name, reason) for each module folder that can't be read)."""
    if capability not in CAPABILITIES:
        raise _error(f"unknown capability {capability!r}; known: {', '.join(CAPABILITIES)}")
    prefix = CAPABILITIES[capability][0]
    good, bad = [], []
    if SKILLS.is_dir():
        for path in sorted(SKILLS.glob(f"{prefix}*/module.yaml")):
            try:
                declared = read(path.parent.name)["capability"]
                if declared == capability:
                    good.append(path.parent.name)
                else:
                    bad.append((path.parent.name, f"its folder name says {capability} but module.yaml declares {declared}"))
            except Exception as error:
                bad.append((path.parent.name, str(error)))
    return good, bad


def installed(capability: str) -> list[str]:
    """The installed, readable modules that fill a capability, by folder name."""
    return _scan(capability)[0]


def broken() -> list[tuple[str, str]]:
    """Module folders whose module.yaml can't be used, with the reason."""
    return [item for capability in CAPABILITIES for item in _scan(capability)[1]]


def chosen(site: dict) -> dict[str, str]:
    """{capability: module name} from site.yaml login_frontend. Missing or unknown is an error that
    lists the installed choices; there is no default."""
    block = site.get(SITE_BLOCK) if isinstance(site, dict) else None
    result = {}
    for capability, (_prefix, key) in CAPABILITIES.items():
        have, bad = _scan(capability)
        unreadable = "".join(f"; unusable: {n}: {why}" for n, why in bad)
        choices = f"choose one of: {', '.join(have) or '(none installed)'} (python3 tools/modules.py list){unreadable}"
        value = block.get(key) if isinstance(block, dict) else None
        if value is None:
            raise _error(f"site.yaml: {SITE_BLOCK}.{key} is missing; {choices}")
        if value not in have:
            raise _error(f"site.yaml: {SITE_BLOCK}.{key} {value!r} is not an installed {capability} module; {choices}")
        result[capability] = value
    return result


def code(name: str):
    """The Python module that holds a module's code (tools/<package>/<product>.py), checked to have
    every function of the contract with the parameters the generic tools pass."""
    data = read(name)
    try:
        loaded = importlib.import_module(data["code"])
    except Exception as error:  # ImportError, or whatever the module's code raises while loading
        raise _error(f"module {name!r}: its code {data['code']!r} can't be loaded ({type(error).__name__}: {error})") from None
    for function, params in CONTRACT[data["capability"]].items():
        target = getattr(loaded, function, None)
        if not callable(target) or tuple(inspect.signature(target).parameters) != params:
            raise _error(f"module {name!r}: its code lacks {function}({', '.join(params)})")
    return loaded


def pairing_note(names: dict[str, str]) -> str | None:
    """A sentence when the chosen ingress and auth gateway are not marked as a tested pairing in both
    modules' data. The pairing still works if its glue exists; the user should know it is untested."""
    ingress, gateway = names["ingress"], names["auth_gateway"]
    untested = []
    for mine, other in ((ingress, gateway), (gateway, ingress)):
        marks = {p["module"]: p["tested"] for p in read(mine)["pairs_with"]}
        if marks.get(other) is not True:
            untested.append(mine)
    if not untested:
        return None
    return (f"{ingress} with {gateway} is not marked tested in the data of {' and '.join(untested)}; "
            "it may work, but nobody has confirmed it on a real install")


def spec_path(name: str) -> Path:
    return SKILLS / name / read(name)["spec"]  # read() has checked that it stays inside the folder


def service_name(name: str) -> str:
    """The name of the service a module's spec describes (the site file's edge.<name> section)."""
    path = spec_path(name)  # a module error from read() passes through
    try:
        service = _yaml().safe_load(path.read_text(encoding="utf-8"))["name"]
    except Exception as error:
        raise _error(f"module {name!r}: its spec can't be read or has no name ({type(error).__name__}: {error})") from None
    if not (isinstance(service, str) and service):
        raise _error(f"module {name!r}: its spec has no name")
    return service


def frontend_services(site: dict) -> dict[str, str]:
    """{capability: the site file's edge.<name> key} for the chosen modules; {} when the site doesn't
    name usable modules (the workspace tools then skip the login front end's own claims)."""
    try:
        return {capability: service_name(name) for capability, name in chosen(site).items()}
    except Exception:
        return {}


def frontend_products(site: dict) -> list[str]:
    """The product names of the chosen modules, for text meant to be read; [] when none are chosen."""
    try:
        return [read(name)["product"] for name in chosen(site).values()]
    except Exception:
        return []


def template_path(name: str, relative: str) -> Path:
    return SKILLS / name / "templates" / relative


def _describe(name: str) -> str:
    data = read(name)
    pairs = [f"{p['module']}, {'tested' if p['tested'] else 'untested'}: {p['how']}" for p in data["pairs_with"]]
    lines = [f"{name}  ({data['capability']}: {data['product']})", f"  {data['summary']}",
             f"  provides: {', '.join(data['provides'])}", f"  needs: {', '.join(data['needs'])}",
             "  pairs with: " + ("\n              ".join(pairs) if pairs else "nothing listed")]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = argv[:]
    if len(args) == 2 and args[0] == "services":
        try:
            import yaml
            site = yaml.safe_load(Path(args[1]).read_text(encoding="utf-8"))
            for name in chosen(site if isinstance(site, dict) else {}).values():
                print(service_name(name))
        except Exception as error:
            print(f"modules: {error}", file=sys.stderr)
            return 1
        return 0
    if not args or args[0] != "list":
        print(__doc__.strip(), file=sys.stderr)
        return 2
    wanted = None
    if args[1:2] == ["--capability"] and len(args) == 3:
        wanted = args[2]
    elif len(args) != 1:
        print("usage: modules.py list [--capability ingress|auth_gateway]", file=sys.stderr)
        return 2
    try:
        capabilities = [wanted] if wanted else list(CAPABILITIES)
        for capability in capabilities:
            for name in installed(capability):
                print(_describe(name) + "\n")
            for name, why in _scan(capability)[1]:
                print(f"broken: {name}: {why}\n")
    except Exception as error:  # SpecError, YAML errors, a missing file: say it, exit 1
        print(f"modules: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
