#!/usr/bin/env python3
"""Check what the toolkit needs on this desktop. Changes nothing.

Usage: check_requirements.py

- OpenCode 2.1.3 or newer: the agents' skill and subagent filters were tested on 2.1.3.
- Python 3 with PyYAML: every tool reads YAML.
- podman or docker: the build checks run Butane and Podman in containers.
- launch folder: OpenCode must be started in the toolkit's folder. The agent's allow rules
  (python3 tools/*), its guard rules and the AGENTS.md it loads are relative to that folder.

Exits 0 when everything is there, 1 otherwise, with one line per item.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layout import TOOLKIT_ROOT  # noqa: E402

MINIMUM_OPENCODE = (2, 1, 3)


def launch_folder() -> Path:
    return Path.cwd().resolve()


def opencode_version() -> str:
    exe = shutil.which("opencode")
    if not exe:
        return ""
    try:
        done = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):  # a hung or unrunnable opencode counts as not found
        return ""
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
        ("Python 3 with PyYAML", has_pyyaml(), "found", "PyYAML missing; install python3-yaml"),
        ("podman or docker", runtime is not None, f"found {runtime}",
         "neither found; needed for the build checks"),
        ("launch folder", launch_folder() == TOOLKIT_ROOT, f"{TOOLKIT_ROOT}",
         f"OpenCode was started in {launch_folder()}; stop and start it in {TOOLKIT_ROOT}"),
    ]
    for name, ok, good, bad in rows:
        print(f"{'ok  ' if ok else 'FAIL'}  {name}: {good if ok else bad}")
    return 0 if all(row[1] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
