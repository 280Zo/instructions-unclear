#!/usr/bin/env python3
"""Write <workspace>/AGENTS.md: what exists in this install and how a new service hooks in.

Usage: install_notes.py <workspace> [--note "<one line>"]

Every service deployment leaves notes for the next one. The
file is rebuilt from site.yaml and services/*/service.yaml after every service,
so it never drifts from them. Only the part between the notes markers is kept
as it is: things a spec can't hold, added with --note (one line each). The
file holds names, numbers and addresses from the workspace, never a secret
value and never a client ID.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules  # noqa: E402
from workspace import load_site  # noqa: E402

NOTES_START = "<!-- notes for future services: kept when this file is rebuilt -->"
NOTES_END = "<!-- end of notes -->"


def _specs(ws: Path) -> list[dict]:
    out = []
    for path in sorted((ws / "services").glob("*/service.yaml")):
        spec = yaml.safe_load(path.read_text()) or {}
        if isinstance(spec, dict) and spec.get("name"):
            out.append(spec)
    return out


def _old_notes(path: Path) -> list[str]:
    if not path.is_file():
        return []
    text = path.read_text()
    if NOTES_START not in text or NOTES_END not in text:
        return []
    body = text.split(NOTES_START, 1)[1].split(NOTES_END, 1)[0]
    return [line for line in body.strip().splitlines() if line.startswith("- ")]


def _volumes(spec: dict) -> list[dict]:
    return [v for c in spec.get("containers") or [] for v in c.get("volumes") or [] if isinstance(v, dict)]


def _web_name(spec: dict, domain: str) -> str:
    host = spec.get("hostname")
    if not host:
        return "none"
    return host if "." in str(host) else f"{host}.{domain}"


def render(ws: Path, notes: list[str]) -> str:
    site = load_site(ws)
    specs = _specs(ws)
    domain = site.get("domain", "<domain>")
    edge = site.get("edge") or {}
    edge_vm = edge.get("vm", "none yet")
    chosen = modules.frontend_services(site)
    login_host = (edge.get(chosen.get("auth_gateway")) or {}).get("host", f"login.{domain}")
    by_vm: dict[str, list[str]] = {}
    for spec in specs:
        by_vm.setdefault(spec.get("vm"), []).append(spec["name"])

    out = ["# Install notes", "",
           "Read this before adding a service to this install. `tools/install_notes.py` rebuilds it from "
           "`site.yaml` and `services/*/service.yaml` after every service; only the notes at the end are kept "
           "by hand. Secrets are listed by name only.", "",
           "## Machines", "", "| VM | Server | Address | VLAN | Shares | Services |", "|---|---|---|---|---|---|"]
    for vm in site.get("vms") or []:
        if not isinstance(vm, dict):
            continue
        shares = ", ".join(s.get("name", "?") for s in vm.get("nfs_shares") or [] if isinstance(s, dict)) or "none"
        names = list(by_vm.get(vm.get("name"), []))
        if vm.get("name") == edge_vm:
            products = ", ".join(modules.frontend_products(site))
            names = [f"login front end ({products})" if products else "login front end"] + names
        out.append(f"| {vm.get('name')} | {vm.get('host', '?')} | {vm.get('ip', '?')} | {vm.get('vlan_tag', 'none')} "
                   f"| {shares} | {', '.join(names) or 'none'} |")

    groups = sorted({g for s in specs for g in s.get("groups") or []} | (
        {site["signup"]["group"]} if isinstance(site.get("signup"), dict) and site["signup"].get("group") else set()))
    sections = sorted({s["section"] for s in specs if s.get("section")})
    sources = sorted((site.get("signin_sources") or {}).keys())
    shared = ", ".join(f"{g.get('name')} (GID {g.get('gid')})" for g in site.get("shared_groups") or []
                       if isinstance(g, dict))
    out += ["", "## Login front end", "",
            f"- VM: {edge_vm}; login page `https://{login_host}/`; every web name `*.{domain}` points at it.",
            f"- Sign-up: {'on, new accounts go to ' + site['signup']['group'] if isinstance(site.get('signup'), dict) else 'off'}.",
            f"- Sign-in with: {', '.join(sources) or 'local accounts only'}.",
            f"- Groups in use: {', '.join(groups) or 'none'}.",
            f"- Dashboard sections in use: {', '.join(sections) or 'none'}.",
            f"- Shared groups (file server): {shared or 'none'}."]

    out += ["", "## Services", "",
            "| Service | VM | Web name | Login | Groups | Section | Port | UID/GID | Data | Backups |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for spec in specs:
        classes = sorted({v.get("class") for v in _volumes(spec)})
        backups = (spec.get("backups") or {}).get("schedule", "daily") if any(c != "nfs" for c in classes) else "none"
        uid = spec.get("uid")
        out.append(f"| {spec['name']} | {spec.get('vm')} | {_web_name(spec, domain)} | {spec.get('login', 'gateway')} "
                   f"| {', '.join(spec.get('groups') or []) or 'every user'} | {spec.get('section', 'none')} "
                   f"| {spec.get('port', 'none')} | {uid}/{spec.get('gid', uid)} | {', '.join(classes) or 'none'} "
                   f"| {backups} |")

    uids = sorted(({s.get("uid") for s in specs} | {(edge.get(k) or {}).get("uid") for k in chosen.values()}) - {None})
    ports: dict[str, list] = {}
    for spec in specs:
        if spec.get("port"):
            ports.setdefault(spec.get("vm"), []).append(spec["port"])
    out += ["", "## Numbers in use", "",
            f"- UIDs: {', '.join(map(str, uids)) or 'none'}.",
            *[f"- Ports on {vm}: {', '.join(map(str, sorted(p)))}." for vm, p in sorted(ports.items())],
            f"- Web names: {', '.join(sorted(_web_name(s, domain) for s in specs if s.get('hostname'))) or 'none'}."]

    out += ["", "## Secrets (names only)", "", "| Secret | Service | Durable |", "|---|---|---|"]
    for spec in specs:
        for secret in spec.get("secrets") or []:
            if isinstance(secret, dict):
                out.append(f"| {secret.get('name')} | {spec['name']} | {'yes' if secret.get('durable') else 'no'} |")

    out += ["", "## How a new service hooks in", "",
            "- **Where:** ask which server and VM; the table above shows what each VM already runs.",
            "- **Login:** ask whether the app goes behind the login page (`login: gateway`, with a route and the "
            "gateway's rules) or keeps its own login (`login: app-only`). An app on another VM binds to its VM "
            "address, and that VM's firewall accepts its port only from the login front end.",
            "- **Who sees it:** reuse an existing group when it fits, or ask to create one; no groups means every user.",
            "- **Dashboard:** reuse an existing section when the app fits one, or propose a new one and ask.",
            "- **Numbers:** pick a free UID and port (not in the lists above); `tools/check_workspace.py` checks.",
            "- **File server:** backups go to the backups share under the VM's folder; show the service's "
            "`file-server.md` table to the owner.",
            "- **Secrets:** new names only; never reuse another service's secret.",
            "", "## Notes for future services", "", NOTES_START, *notes, NOTES_END, ""]
    return "\n".join(out)


def write_notes(ws: Path) -> Path:
    ws = Path(ws)
    path = ws / "AGENTS.md"
    path.write_text(render(ws, _old_notes(path)))
    return path


def add_note(ws: Path, note: str) -> Path:
    if not isinstance(note, str) or not note.strip() or len(note) > 1000 or "\n" in note \
            or "<!--" in note or "-->" in note:
        raise ValueError("a note is one line of plain text (at most 1000 characters, no comment markers)")
    path = Path(ws) / "AGENTS.md"
    notes = _old_notes(path)
    line = f"- {note.strip()}"
    if line not in notes:
        notes.append(line)
    path.write_text(render(Path(ws), notes))
    return path


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 3) or (len(argv) == 3 and argv[1] != "--note"):
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    try:
        path = add_note(Path(argv[0]), argv[2]) if len(argv) == 3 else write_notes(Path(argv[0]))
    except (ValueError, OSError, yaml.YAMLError) as error:
        print(f"install_notes: {error}", file=sys.stderr)
        return 1
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
