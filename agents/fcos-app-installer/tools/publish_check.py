#!/usr/bin/env python3
"""Fail if any file git would publish holds private data.

Usage: publish_check.py [<folder>]

Checks every tracked file plus every untracked file that isn't git-ignored, in
the toolkit's own folder (the one holding tools/), wherever it is run from; or
in <folder>, which must be inside a git checkout. Inside a larger repository
(the toolkit as one folder of it) only that folder is scanned.
Private data belongs only in the workspace, a folder outside the repo (see
tools/workspace.py), or in git-ignored files (notes/).

Two kinds of rules:
  - workspace values: any value from the workspace's site.yaml and service
    specs (that isn't also in the public site.example.yaml) appearing anywhere
    in a published file. Skipped, with generic rules only, if no workspace is
    set (FCOS_WORKSPACE or the remembered path). A workspace that is set but
    has no site.yaml is an error (exit 2), not a pass;
  - generic rules: private IPv4 addresses, DuckDNS names other than
    example.duckdns.org, email addresses outside example.com/.org/.net, SSH
    keys, password hashes, private keys, and secret-looking assignments.
    Placeholders are allowed: 192.0.2.x, 198.51.100.x, 203.0.113.x, and
    keys or hashes containing EXAMPLE.

Hits print as file:line: rule, never the matched value. Exit 1 on any hit.
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secret_scan import scan_text as secret_lines  # noqa: E402
from workspace import WorkspaceError, WorkspaceNotSet, private_values, resolve_workspace  # noqa: E402

RULES = [
    ("private IPv4 address",
     re.compile(r"\b(?:10\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])|192\.168)\.\d{1,3}\.\d{1,3}\b")),
    ("DuckDNS name other than example.duckdns.org",
     re.compile(r"(?i)\b(?!(?:[a-z0-9-]+\.)*example\.duckdns\.org\b)[a-z0-9-]+(?:\.[a-z0-9-]+)*\.duckdns\.org\b")),
    ("email address outside example.com/.org/.net",
     re.compile(r"(?i)\b[a-z0-9._%+-]+@(?!(?:[a-z0-9-]+\.)*example\.(?:com|org|net)\b)(?=[a-z0-9.-]*[a-z])[a-z0-9-]+(?:\.[a-z0-9-]+)+\b")),
    ("SSH public key", re.compile(r"ssh-(?:ed25519|rsa|ecdsa-[a-z0-9-]+) AAAA(?![A-Za-z0-9+/=]*EXAMPLE)[A-Za-z0-9+/=]{20,}")),
    ("password hash", re.compile(r"\$(?:y|2[aby]|5|6)\$(?![^\s\"']*EXAMPLE)[^\s\"']{10,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]

def check_text(text: str, private: set[str]) -> list[str]:
    hits = []
    lowered = text.lower()
    for value in private:
        if value.lower() in lowered:
            for number, line in enumerate(text.splitlines(), start=1):
                if value.lower() in line.lower():
                    hits.append(f"{number}: value from workspace")
    for number, line in enumerate(text.splitlines(), start=1):
        for name, pattern in RULES:
            if pattern.search(line):
                hits.append(f"{number}: {name}")
    for hit in secret_lines(text):
        hits.append(f"{hit.split(':', 1)[0]}: secret-looking assignment")
    return sorted(set(hits), key=lambda h: int(h.split(":", 1)[0]))


def published_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, text=True, check=True).stdout
    tracked_but_ignored = subprocess.run(
        ["git", "ls-files", "--cached", "--ignored", "--exclude-standard", "-z"],
        cwd=root, capture_output=True, text=True, check=True).stdout
    files = [p for p in out.split("\0") if p]
    still_tracked = [p for p in tracked_but_ignored.split("\0") if p]
    return [root / p for p in sorted(set(files) | set(still_tracked))]


TOOLKIT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    args = argv[1:]
    if len(args) > 1 or (args and args[0].startswith("-")):
        print("usage: publish_check.py [<folder>]   (default: the toolkit's own folder; the workspace "
              "comes from FCOS_WORKSPACE or the remembered path; there is no --config)", file=sys.stderr)
        return 2
    root = Path(args[0]).resolve() if args else TOOLKIT
    inside = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True,
                            text=True) if root.is_dir() else None
    if inside is None or inside.stdout.strip() != "true":
        print(f"publish_check: {root} is not a folder inside a git checkout", file=sys.stderr)
        return 2
    try:
        ws = resolve_workspace()
        if not (ws / "site.yaml").is_file():
            print(f"publish_check: workspace {ws} has no site.yaml "
                  "(wrong FCOS_WORKSPACE or moved folder?); fix it or unset the workspace",
                  file=sys.stderr)
            return 2
        private = private_values(ws)
        source = "the workspace"
    except WorkspaceNotSet:
        private = set()
        source = "no workspace set (generic rules only)"
    except WorkspaceError as exc:
        print(f"publish_check: {exc}", file=sys.stderr)
        return 2
    hits = []
    for path in published_files(root):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append(f"{path.relative_to(root)}: binary file (publish only text)")
            continue
        hits += [f"{path.relative_to(root)}:{hit}" for hit in check_text(text, private)]
    for hit in hits:
        print(hit)
    print(f"publish_check: {len(hits)} hit(s); values from {source}; scanned {root}", file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
