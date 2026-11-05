#!/usr/bin/env python3
"""Flag lines that look like they hold a secret value.

Usage: secret_scan.py <file-or-dir>...   (exit 1 and print hits if any)

A line is flagged when a secret-like name (token, password, secret, key,
api_key, credential, passwd, bearer...) is assigned a value of 8+ characters,
in KEY=value, KEY: value or KEY = value form. Allowed: Quadlet Secret= lines
(they hold only a secret's name), password_hash (a hash, by design), and
comments.
"""

import os
import re
import sys

NAME = r"[A-Za-z0-9_.-]*(?:token|passw(?:or)?d|secret|api_?key|access_?key|private_?key|credential|bearer)[A-Za-z0-9_.-]*"
ASSIGN = re.compile(rf"(?i)(?:^|[\s,;=\"'])({NAME})\s*[=:]\s*[\"']?([^\s\"',;]{{8,}})")
ALLOWED_LINE = re.compile(r"^\s*(?:#|Secret=)")
ALLOWED_NAMES = re.compile(r"(?i)^(?:password_hash|ADMIN_PASSWORD_HASH|authorization_flow|authResponseHeaders)$")


def scan_text(text: str) -> list[str]:
    hits = []
    for number, line in enumerate(text.splitlines(), start=1):
        if ALLOWED_LINE.match(line):
            continue
        # A Quadlet Secret= reference names a secret; it never holds one.
        line = re.sub(r"Secret=[^\s\"']*", "", line)
        for match in ASSIGN.finditer(line):
            if ALLOWED_NAMES.match(match.group(1)):
                continue
            hits.append(f"{number}: {line.strip()}")
            break
    return hits


def scan_paths(paths: list[str]) -> list[str]:
    hits = []
    for top in paths:
        files = [top]
        if os.path.isdir(top):
            files = []
            for dirpath, dirnames, filenames in os.walk(top):
                dirnames[:] = [d for d in dirnames if d not in ("igns", "values")]
                files += [os.path.join(dirpath, f) for f in filenames
                          if not f.endswith((".ign", ".txt"))]
        for path in sorted(files):
            try:
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
            except (UnicodeDecodeError, OSError):
                continue
            hits += [f"{path}:{hit}" for hit in scan_text(text)]
    return hits


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    hits = scan_paths(argv[1:])
    for hit in hits:
        print(hit)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
