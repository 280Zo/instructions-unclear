#!/usr/bin/env python3
"""Fail if any file git would publish holds private data.

Usage: publish_check.py [<folder>]

Checks, in the toolkit's own folder (the one holding tools/), wherever it is run
from, or in <folder>: every tracked file plus every untracked file that isn't
git-ignored, when the folder is inside a git checkout (inside a larger
repository, with the toolkit as one folder of it, only that folder is scanned);
every file in it, git's own folder, Python caches and links excepted, when it
isn't a checkout (an installed copy). A scan that reads no file is an error.
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

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from secret_scan import scan_text as secret_lines  # noqa: E402
from workspace import WorkspaceError, WorkspaceNotSet, git_env, private_values, resolve_workspace  # noqa: E402

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


SKIP_DIRS = {".git", "__pycache__"}


def _in_checkout(root: Path) -> bool:
    # git runs in a scrubbed environment (workspace.git_env): a caller's GIT_DIR must not decide this.
    try:
        done = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True,
                              text=True, env=git_env(), timeout=30)
    except (OSError, subprocess.SubprocessError):  # git isn't installed, or hung
        return False
    return done.returncode == 0 and done.stdout.strip() == "true"


def _walk(root: Path, unreadable: list[Path] | None = None) -> list[Path]:
    """Every file under root, for a folder that isn't a git checkout (an installed copy of the
    toolkit). Git's own folder and Python caches are skipped, and links are never followed, so
    nothing outside root is read. A folder that cannot be opened is added to `unreadable`."""
    found = []

    def failed(error: OSError) -> None:
        if unreadable is not None and error.filename:
            unreadable.append(Path(os.fsdecode(error.filename)))

    for base, dirs, names in os.walk(root, followlinks=False, onerror=failed):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (Path(base) / d).is_symlink())
        found += [Path(base) / n for n in sorted(names) if not (Path(base) / n).is_symlink()]
    return found


def published_files(root: Path) -> tuple[list[Path], str, list[Path]]:
    """What would be published from root, how it was found, and the folders that could not be
    opened. Inside a git checkout (possibly a larger one that holds the toolkit as one folder) the
    files are git's own list for root alone, files outside root being that checkout's business
    ("git list"); in a plain folder they are every file in it ("walked"). If git fails the walk is
    used too: scanning more, git-ignored files included, is the safe direction. File names are
    bytes on this system, so they are decoded without loss. Git skips a folder it cannot open
    without saying so on stdout, so the folders are always found by a walk of their own: one that
    cannot be opened could hold anything, and counts as a hit."""
    unreadable: list[Path] = []
    walked = _walk(root, unreadable)
    if not _in_checkout(root):
        return walked, "walked", unreadable
    try:
        out, tracked_but_ignored = (subprocess.run(
            ["git", "ls-files", *flags, "--exclude-standard", "-z"], cwd=root, capture_output=True,
            check=True, env=git_env(), timeout=120).stdout for flags in (("--cached", "--others"),
                                                                      ("--cached", "--ignored")))
    except (OSError, subprocess.SubprocessError):
        return walked, "walked", unreadable
    names = {os.fsdecode(p) for p in (out + b"\0" + tracked_but_ignored).split(b"\0") if p}
    return [root / name for name in sorted(names)], "git list", unreadable


def _shown(path: Path) -> str:
    """A path for the output: names that are not valid UTF-8 are shown escaped, and so are newlines
    and other control characters, so a file name can neither crash printing nor forge a line."""
    text = str(path).encode("utf-8", "backslashreplace").decode("utf-8")
    return "".join(c if c.isprintable() else c.encode("unicode_escape").decode("ascii") for c in text)


TOOLKIT = Path(__file__).resolve().parent.parent


def main(argv: list[str]) -> int:
    args = argv[1:]
    if len(args) > 1 or (args and args[0].startswith("-")):
        print("usage: publish_check.py [<folder>]   (default: the toolkit's own folder; the workspace "
              "comes from FCOS_WORKSPACE or the remembered path; there is no --config)", file=sys.stderr)
        return 2
    root = Path(args[0]).resolve() if args else TOOLKIT
    if not root.is_dir():
        print(f"publish_check: {root} is not a folder", file=sys.stderr)
        return 2
    listed, how, unreadable = published_files(root)
    # A link is never read, in either mode: its target may be outside the folder, and git publishes
    # only the link itself.
    files = [p for p in listed if p.is_file() and not p.is_symlink()]
    if not files and not unreadable:
        print(f"publish_check: nothing to scan in {root} (every file is git-ignored, or the folder is empty); "
              "a scan that reads no file proves nothing", file=sys.stderr)
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
    hits = [f"{_shown(folder.relative_to(root))}: unreadable folder (not checked)" for folder in unreadable
            if folder != root and root in folder.parents]
    if root in unreadable:
        hits.append(".: unreadable folder (not checked)")
    for path in files:
        shown = _shown(path.relative_to(root))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            hits.append(f"{shown}: binary file (publish only text)")
            continue
        except OSError:  # a file that can't be read can't be cleared
            hits.append(f"{shown}: unreadable (not checked)")
            continue
        hits += [f"{shown}:{hit}" for hit in check_text(text, private)]
    for hit in hits:
        print(hit)
    count = f"{len(files)} file" + ("" if len(files) == 1 else "s")
    print(f"publish_check: {len(hits)} hit(s); values from {source}; scanned {_shown(root)} ({count}, {how})",
          file=sys.stderr)
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
