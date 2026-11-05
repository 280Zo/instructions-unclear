#!/usr/bin/env python3
"""Check what the toolkit needs on this desktop. Changes nothing.

Usage: check_requirements.py

- OpenCode 2.1.3 or newer. Earlier V2 releases (2.0.0-2.0.29) parse the config's
  `instructions` list but never load it, so rules/*.md would silently be missing
  (anomalyco/opencode issue #51341; the loader is in 2.0.30 and later), and the
  agents' skill and subagent filters were tested on 2.1.3.
- git: the host-script check compares each shipped script with the committed one.
- Python 3 with PyYAML: every tool reads YAML.
- podman or docker: the build checks run Butane and Podman in containers.

Exits 0 when everything is there, 1 otherwise, with one line per item.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys

MINIMUM_OPENCODE = (2, 1, 3)


def opencode_version() -> str:
    exe = shutil.which("opencode")
    if not exe:
        return ""
    done = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
    return done.stdout.strip() or done.stderr.strip()


def has_pyyaml() -> bool:
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def _parse(version: str):
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
    return tuple(int(p) for p in match.groups()) if match else None


def main(argv: list[str]) -> int:
    if argv:
        print(__doc__.strip().splitlines()[2], file=sys.stderr)
        return 2
    minimum = ".".join(map(str, MINIMUM_OPENCODE))
    found = opencode_version()
    version = _parse(found)
    runtime = shutil.which("podman") or shutil.which("docker")
    rows = [  # (name, ok, shown when ok, shown when missing)
        ("OpenCode", version is not None and version >= MINIMUM_OPENCODE,
         f"{found} (needs {minimum} or newer)", f"needs {minimum} or newer; found {found or 'none'}"),
        ("git", shutil.which("git") is not None, "found", "not found; needed for the host-script check"),
        ("Python 3 with PyYAML", has_pyyaml(), "found", "PyYAML missing; install python3-yaml"),
        ("podman or docker", runtime is not None, f"found {runtime}",
         "neither found; needed for the build checks"),
    ]
    for name, ok, good, bad in rows:
        print(f"{'ok  ' if ok else 'FAIL'}  {name}: {good if ok else bad}")
    return 0 if all(row[1] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
