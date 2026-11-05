#!/usr/bin/env python3
"""The private workspace: where one install's real files live, outside the repo.

Usage:
  workspace.py init <path>         create the workspace layout and remember it
  workspace.py where               print the workspace path in use
  workspace.py previous <dir>...   summarize earlier installs as JSON

The workspace is found, in order, from an explicit path, the FCOS_WORKSPACE
environment variable, then the path remembered in
~/.config/fcos-agent/workspace. It must never be inside the toolkit's folder or
anywhere in the nearest git checkout that folder belongs to (git rev-parse
--show-toplevel, or, when git can't answer, the nearest .git above the folder;
a toolkit in no checkout is guarded at its own folder), so private files
can't become publishable. Secret files are only ever listed by path
(existence flags), never read.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import SKILLS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = REPO_ROOT / "site.example.yaml"
SKIP_VALUE = re.compile(r"(?i)^(?:\d+(?:\.\d+)?|true|false|null|none|ask|yes|no)$")
SERVICE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SUBDIRS = ("secrets", "vms", "services", "adapters-draft")


class WorkspaceError(Exception):
    pass


class WorkspaceNotSet(WorkspaceError):
    pass


def _remembered_file() -> Path:
    return Path.home() / ".config" / "fcos-agent" / "workspace"


def git_env() -> dict:
    """The only environment git is run in: the caller's GIT_DIR, GIT_WORK_TREE and similar (a git
    hook sets them) would point it at another repository, and the user's and system's git config
    can change its answers."""
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null", "HOME": "/nonexistent"}


def _git_toplevel(folder: Path) -> Path | None:
    git = shutil.which("git")
    if not git:
        return None
    try:
        done = subprocess.run([git, "-C", str(folder), "rev-parse", "--show-toplevel"], env=git_env(),
                              capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    top = done.stdout.decode("utf-8", "replace").rstrip("\n") if done.returncode == 0 else ""
    return Path(top).resolve() if top else None


def _nearest_git_folder(folder: Path) -> Path | None:
    """The nearest folder at or above this one that has a .git (a folder, or a file for a worktree
    or submodule), found without git."""
    return next((p for p in [folder, *folder.parents] if (p / ".git").exists()), None)


def _enclosing_checkout(folder: Path) -> Path:
    """The top level of the git checkout that holds folder, or folder itself when it isn't in one.
    The guard fails closed: when git can't answer (not installed, refusing a checkout owned by
    another user, hung), the checkout is found by looking for .git above the folder."""
    top = _git_toplevel(folder)
    if top is not None and (top == folder or top in folder.parents):
        return top
    return _nearest_git_folder(folder) or folder


def _outside_repo(path: Path) -> Path:
    """A workspace holds private values, so it may sit neither in the toolkit's folder nor anywhere
    else in the checkout that folder belongs to: that checkout is what gets published."""
    resolved = path.expanduser().resolve()
    base = _enclosing_checkout(REPO_ROOT)
    if resolved == base or base in resolved.parents:
        raise WorkspaceError(
            f"workspace {resolved} is inside {base}, the git checkout the toolkit sits in, and whatever "
            f"that checkout publishes must never include private values; choose a folder outside it "
            f"(better, install the toolkit in a folder of its own, outside any other checkout)")
    return resolved


def resolve_workspace(explicit: str | None = None) -> Path:
    if explicit:
        return _outside_repo(Path(explicit))
    from_env = os.environ.get("FCOS_WORKSPACE", "").strip()
    if from_env:
        return _outside_repo(Path(from_env))
    remembered = _remembered_file()
    if remembered.is_file():
        text = remembered.read_text(encoding="utf-8").strip()
        if text:
            return _outside_repo(Path(text))
    raise WorkspaceNotSet(
        "no workspace set: pass a path, set FCOS_WORKSPACE, or run `workspace.py init <path>`")


def init_workspace(path: Path) -> None:
    ws = _outside_repo(Path(path))
    ws.mkdir(parents=True, exist_ok=True)
    site = ws / "site.yaml"
    if not site.exists():
        site.write_text(EXAMPLE.read_text(encoding="utf-8"), encoding="utf-8")
    for name in SUBDIRS:
        (ws / name).mkdir(exist_ok=True)
    secrets = ws / "secrets"
    if secrets.stat().st_mode & 0o777 != 0o700:
        secrets.chmod(0o700)
    # rg, and search tools built on it, skip paths listed in .ignore, so a
    # search of the whole workspace doesn't read the secrets folder.
    ignore = ws / ".ignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.is_file() else []
    if "secrets/" not in lines:
        ignore.write_text("\n".join(lines + ["secrets/"]) + "\n", encoding="utf-8")
    remembered = _remembered_file()
    wanted = f"{ws}\n"
    if not remembered.is_file() or remembered.read_text(encoding="utf-8") != wanted:
        remembered.parent.mkdir(parents=True, exist_ok=True)
        remembered.write_text(wanted, encoding="utf-8")


def _yaml():
    try:
        import yaml
    except ImportError:
        print("install PyYAML (python-yaml / python3-yaml)", file=sys.stderr)
        raise SystemExit(2)
    return yaml


def _safe_load(path: Path):
    return _yaml().safe_load(path.read_text(encoding="utf-8"))


def _mapping(path: Path) -> dict:
    data = _safe_load(path)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise WorkspaceError(f"{path.name} must be a mapping at the top level")
    return data


def load_site(ws: Path) -> dict:
    return _mapping(Path(ws) / "site.yaml")


def load_service(ws: Path, name: str) -> dict:
    if not SERVICE_NAME.match(name) or ".." in name:
        raise WorkspaceError(f"invalid service name {name!r}")
    path = Path(ws) / "services" / name / "service.yaml"
    if not path.is_file():
        raise WorkspaceError(f"no service spec at {path}")
    return _mapping(path)


def _strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)


SPEC_IDENTIFYING = ("hostname", "title", "description", "login_reason", "accepted_risks")


def _identifying(spec) -> list:
    """The parts of an app spec that can identify the owner (owner decision 2026-10-31)."""
    if not isinstance(spec, dict):
        return []
    own = str(spec.get("name", "")).lower()
    # A web name or title that is just the app's own (public) name doesn't identify anyone.
    out = [spec.get(key) for key in SPEC_IDENTIFYING
           if not (key in ("hostname", "title") and str(spec.get(key, "")).lower() == own)]
    for ctr in spec.get("containers") or []:
        if not isinstance(ctr, dict):
            continue
        for vol in ctr.get("volumes") or []:
            if isinstance(vol, dict) and vol.get("class") == "nfs":
                out.append(vol.get("host"))
        # Env values that carry an address, a domain or free text (an admin email,
        # a person's name, an outside mail host) can identify the owner.
        env = ctr.get("env") if isinstance(ctr.get("env"), dict) else {}
        out += [v for v in env.values() if isinstance(v, str) and IDENTIFYING_ENV.search(v)]
    return [item for item in out if item is not None]


# "@", whitespace, a name with a dot and a 2+ letter last label (example.net),
# or an IPv4 address.
IDENTIFYING_ENV = re.compile(r"@|\s|[A-Za-z0-9-]+\.[A-Za-z]{2,}|\b\d{1,3}(?:\.\d{1,3}){3}\b")


def private_values(ws: Path) -> set[str]:
    """Every scalar in site.yaml and the service specs worth protecting."""
    ws = Path(ws)
    public = EXAMPLE.read_text(encoding="utf-8") if EXAMPLE.exists() else ""
    # Exact names of the adapters the agent ships (adapter-<name>/ in the skills folder) are public.
    shipped = {p.parent.name.removeprefix("adapter-") for p in SKILLS.glob("adapter-*/adapter.yaml")}
    files = [ws / "site.yaml", *sorted((ws / "services").glob("*/service.yaml")),
             *sorted((ws / "vms").glob("*/vm.yaml"))]
    values = set()
    for path in files:
        if not path.is_file():
            continue
        try:
            data = _mapping(path)
        except _yaml().YAMLError:
            raise WorkspaceError(f"{path} is not valid YAML") from None
        # Site file: every value. App specs: only the fields that can identify
        # the owner (a public app's image, folders and settings are public; the
        # domain and addresses inside them are caught through the site file).
        if path.name == "site.yaml":
            source = data
        elif path.name == "vm.yaml":  # its free-text description (the rest is public settings)
            settings = data.get("settings") if isinstance(data, dict) else None
            desc = settings.get("description") if isinstance(settings, dict) else None
            source = [desc["use"]] if isinstance(desc, dict) and isinstance(desc.get("use"), str) else []
        else:
            source = _identifying(data)
        for text in _strings(source):
            for part in text.splitlines():
                part = part.strip()
                if len(part) < 4 or SKIP_VALUE.match(part) or part in public or part in shipped:
                    continue
                values.add(part)
    return values


def _installs(directory: Path) -> list[Path]:
    def is_install(path: Path) -> bool:
        return (path / "site.yaml").is_file() or (path / "services").is_dir()

    if not directory.is_dir():
        return []
    if is_install(directory):
        return [directory]
    return [child for child in sorted(directory.iterdir()) if child.is_dir() and is_install(child)]


def _merge(into: dict, new: dict) -> None:
    for key, value in new.items():
        if key not in into or into[key] in (None, "ASK"):
            into[key] = value
        elif isinstance(into[key], dict) and isinstance(value, dict):
            _merge(into[key], value)
        elif isinstance(into[key], list) and isinstance(value, list):
            into[key].extend(item for item in value if item not in into[key])


def _collect_used(node, vm: str, used: dict) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "uid" and isinstance(value, int) and not isinstance(value, bool):
                used["uids"].add(value)
            elif key == "port" and isinstance(value, int) and not isinstance(value, bool):
                used["ports"].setdefault(vm, set()).add(value)
            elif key == "hostname" and isinstance(value, str) and value:
                used["hostnames"].add(value)
            else:
                _collect_used(value, vm, used)
    elif isinstance(node, list):
        for item in node:
            _collect_used(item, vm, used)


def _secret_files(install: Path) -> list[Path]:
    found = []
    for root, _dirs, files in os.walk(install / "secrets"):
        for name in files:
            path = Path(root) / name
            if not path.is_symlink():
                found.append(path)
    return sorted(found)


def scan_previous(dirs: list[Path]) -> dict:
    site: dict = {}
    used = {"uids": set(), "ports": {}, "hostnames": set()}
    present: list[Path] = []
    for directory in dirs:
        for install in _installs(Path(directory)):
            if (install / "site.yaml").is_file():
                _merge(site, load_site(install))
            for spec_path in sorted((install / "services").glob("*/service.yaml")):
                spec = _mapping(spec_path)
                vm = spec.get("vm") if isinstance(spec.get("vm"), str) else ""
                _collect_used(spec, vm, used)
            present += _secret_files(install)
    return {"site": site, "used": used, "secret_files": present}


def _printable(result: dict) -> dict:
    used = result["used"]
    return {
        "site": result["site"],
        "used": {
            "uids": sorted(used["uids"]),
            "ports": {vm: sorted(ports) for vm, ports in sorted(used["ports"].items())},
            "hostnames": sorted(used["hostnames"]),
        },
        "secret_files": {str(path): True for path in result["secret_files"]},
    }


def main(argv: list[str]) -> int:
    usage = "usage: workspace.py init <path> | where | previous <dir>..."
    if not argv:
        print(usage, file=sys.stderr)
        return 2
    command, args = argv[0], argv[1:]
    try:
        if command == "init" and len(args) == 1:
            init_workspace(Path(args[0]))
            print(resolve_workspace(args[0]))
        elif command == "where" and not args:
            print(resolve_workspace())
        elif command == "previous" and args:
            print(json.dumps(_printable(scan_previous([Path(a) for a in args])),
                             indent=2, default=str))
        else:
            print(usage, file=sys.stderr)
            return 2
    except WorkspaceError as exc:
        print(f"workspace: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
