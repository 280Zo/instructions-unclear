"""Helpers the login front end and its modules share: site-file placeholders, the VM folder behind a
volume, and Butane file entries. No product is named here."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_service import SpecError, _volume_host  # noqa: E402

PLACEHOLDER = re.compile(r"<site: ([a-z_]+(?:\.[a-z_]+)*)>")


def site_value(site: dict, dotted: str):
    node = site
    for key in dotted.split("."):
        if not isinstance(node, dict) or node.get(key) is None:
            raise SpecError(f"site.yaml: {dotted} is missing (the login front end needs it)")
        node = node[key]
    return node


def filled(node, site: dict):
    """A spec with every "<site: a.b.c>" value filled in from the site file."""
    if isinstance(node, dict):
        return {k: filled(v, site) for k, v in node.items()}
    if isinstance(node, list):
        return [filled(v, site) for v in node]
    if isinstance(node, str):
        match = PLACEHOLDER.fullmatch(node)
        if match:
            return site_value(site, match.group(1))
        if "<site:" in node:
            raise SpecError(f"login front end spec: malformed placeholder {node!r}")
    return node


def folder(spec: dict, container_path: str) -> str:
    """The VM folder behind the volume mounted at container_path."""
    for ctr in spec["containers"]:
        for vol in ctr.get("volumes") or []:
            if vol["path"] == container_path:
                return _volume_host(spec["name"], ctr["name"], vol)
    raise SpecError(f"login front end spec {spec['name']}: no volume at {container_path}")


def dir_entry(path: str, uid: int, gid: int) -> str:
    return (f"    - path: {path}\n      mode: 0750\n"
            f"      user:\n        id: {uid}\n      group:\n        id: {gid}")


def file_entry(path: str, local: str, uid: int, gid: int) -> str:
    return (f"    - path: {path}\n      mode: 0640\n      overwrite: true\n"
            f"      user:\n        id: {uid}\n      group:\n        id: {gid}\n"
            f"      contents:\n        local: {local}")
