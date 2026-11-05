#!/usr/bin/env python3
"""Report whether the toolkit's pinned desktop-side images have updates. Changes nothing.

Usage: check_updates.py

Reads tools/images.env and asks quay.io's public tag API
(https://docs.quay.io/api/swagger/, GET /api/v1/repository/<repo>/tag/) for each image:

- a newer release: the highest vX.Y.Z tag above the pinned one (pre-releases such
  as -rc1, and the -immutable twins Podman publishes, are not offered);
- a rebuilt tag: the pinned tag now points to another digest than the pin.

Prints one Markdown table. Exits 0 when everything is up to date, 10 when an
update is available, 1 when a check couldn't run (the reason is in the table).
Updating is the procedure in README.md "Updating"; this tool never edits a pin.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PINS = Path(__file__).resolve().parent / "images.env"
REF = re.compile(r"^quay\.io/(?P<repo>[a-z0-9/_-]+):(?P<tag>[^@]+)@(?P<digest>sha256:[0-9a-f]{64})$")
RELEASE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def fetch_tags(repo: str) -> list[dict]:
    """Every active tag of a public quay.io repository (paged)."""
    tags, page = [], 1
    while True:
        url = (f"https://quay.io/api/v1/repository/{urllib.parse.quote(repo)}/tag/"
               f"?onlyActiveTags=true&limit=100&page={page}")
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.load(response)
        tags += data.get("tags", [])
        if not data.get("has_additional") or page >= 20:
            return tags
        page += 1


def load_pins() -> dict[str, str]:
    pins = {}
    for line in PINS.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, value = line.partition("=")
            pins[key.strip()] = value.strip()
    return pins


def _version(tag: str):
    match = RELEASE.match(tag)
    return tuple(int(p) for p in match.groups()) if match else None


def check(ref: str) -> tuple[str, str, str]:
    """(pinned, newest release, status) for one pinned image."""
    match = REF.match(ref)
    if not match:
        return ref, "-", "couldn't check: not a quay.io tag@digest pin"
    repo, tag, digest = match["repo"], match["tag"], match["digest"]
    try:
        tags = fetch_tags(repo)
    except (OSError, ValueError) as error:
        return f"{repo}:{tag}", "-", f"couldn't check: {error}"
    releases = sorted(((v, t["name"]) for t in tags if (v := _version(t["name"]))), reverse=True)
    newest = releases[0][1] if releases else "-"
    status = []
    current = _version(tag)
    if releases and current and releases[0][0] > current:
        status.append(f"newer release {newest}")
    now = next((t.get("manifest_digest") for t in tags if t.get("name") == tag), None)
    if now and now != digest:
        status.append(f"rebuilt: {tag} now points to {now[:19]}")
    return f"{repo}:{tag}", newest, "; ".join(status) or "up to date"


def main(argv: list[str]) -> int:
    if argv:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    rows = [(key, *check(ref)) for key, ref in sorted(load_pins().items())]
    print("| Image | Pinned | Newest release | Status |")
    print("|---|---|---|---|")
    for key, pinned, newest, status in rows:
        print(f"| {key} | {pinned} | {newest} | {status} |")
    if any(status.startswith("couldn't check") for *_, status in rows):
        return 1
    return 10 if any(status != "up to date" for *_, status in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
