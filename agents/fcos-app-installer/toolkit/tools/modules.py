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

To add a module for another product, see docs/guide/12-add-a-module.md.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import SKILLS  # noqa: E402

# capability -> (skill folder prefix, key under login_frontend in site.yaml)
CAPABILITIES = {"ingress": ("ingress-", "ingress"), "auth_gateway": ("authgw-", "auth_gateway")}
SITE_BLOCK = "login_frontend"
REQUIRED = ("capability", "product", "summary", "provides", "needs", "pairs_with", "spec", "code")


def _error(message: str):
    from gen_service import SpecError  # imported late: gen_service imports this module
    return SpecError(message)


def _yaml():
    import yaml
    return yaml


def read(name: str) -> dict:
    """A module's module.yaml, checked for its required keys."""
    path = SKILLS / name / "module.yaml"
    if not path.is_file():
        raise _error(f"module {name!r} is not installed (no {path})")
    data = _yaml().safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [key for key in REQUIRED if key not in data]
    if missing:
        raise _error(f"module {name!r}: module.yaml lacks {', '.join(missing)}")
    return data


def installed(capability: str) -> list[str]:
    """The installed modules that fill a capability, by folder name."""
    if capability not in CAPABILITIES:
        raise _error(f"unknown capability {capability!r}; known: {', '.join(CAPABILITIES)}")
    prefix = CAPABILITIES[capability][0]
    if not SKILLS.is_dir():
        return []
    return sorted(p.parent.name for p in SKILLS.glob(f"{prefix}*/module.yaml")
                  if read(p.parent.name)["capability"] == capability)


def chosen(site: dict) -> dict[str, str]:
    """{capability: module name} from site.yaml login_frontend. Missing or unknown is an error that
    lists the installed choices; there is no default."""
    block = site.get(SITE_BLOCK) if isinstance(site, dict) else None
    result = {}
    for capability, (_prefix, key) in CAPABILITIES.items():
        have = installed(capability)
        choices = f"choose one of: {', '.join(have) or '(none installed)'} (python3 tools/modules.py list)"
        value = block.get(key) if isinstance(block, dict) else None
        if value is None:
            raise _error(f"site.yaml: {SITE_BLOCK}.{key} is missing; {choices}")
        if value not in have:
            raise _error(f"site.yaml: {SITE_BLOCK}.{key} {value!r} is not an installed {capability} module; {choices}")
        result[capability] = value
    return result


def code(name: str):
    """The Python module that holds a module's code (tools/<family>/<product>.py)."""
    return importlib.import_module(read(name)["code"])


def spec_path(name: str) -> Path:
    return SKILLS / name / read(name)["spec"]


def service_name(name: str) -> str:
    """The name of the service a module's spec describes (the site file's edge.<name> section)."""
    return _yaml().safe_load(spec_path(name).read_text(encoding="utf-8"))["name"]


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
    except Exception as error:  # SpecError, YAML errors, a missing file: say it, exit 1
        print(f"modules: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
