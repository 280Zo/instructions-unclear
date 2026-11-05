#!/usr/bin/env python3
"""Check that every Quadlet's Volume= host paths sit under the roots its
require-mounts line checks, so a container never starts on an empty folder
when the data disk or a share isn't mounted.

Usage: check_mount_roots.py <dir>   (checks every *.container in it)
Exit 0 when all pass, 1 with one line per problem.

Roots come from ExecStartPre= or ExecCondition= lines that run
/usr/local/bin/require-mounts. Named volumes (no leading /) are skipped.
"""

import shlex
import sys
from pathlib import Path

CHECK = "/usr/local/bin/require-mounts"


def problems(path: Path) -> list[str]:
    roots, volumes = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(("ExecStartPre=", "ExecCondition=")):
            words = shlex.split(line.split("=", 1)[1])
            if words and words[0].lstrip("-+!@:") == CHECK:
                roots += words[1:]
        elif line.startswith("Volume="):
            source = line.split("=", 1)[1].split(":", 1)[0]
            if source.startswith("/"):
                volumes.append(source)
    if volumes and not roots:
        return [f"{path.name}: has volumes but no require-mounts check"]
    out = []
    for source in volumes:
        if not any(source == root or source.startswith(root.rstrip("/") + "/") for root in roots):
            out.append(f"{path.name}: {source} is not under {' '.join(roots)}")
    return out


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not Path(argv[1]).is_dir():
        print(__doc__.strip(), file=sys.stderr)
        return 2
    found = [p for path in sorted(Path(argv[1]).rglob("*.container")) for p in problems(path)]
    for line in found:
        print(line)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
