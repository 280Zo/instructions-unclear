"""Helpers for tests that need git out of the picture.

A test of "a folder that is not a git checkout" needs a folder with no checkout around it, and
TMPDIR may sit inside one (a developer's repo, a CI workspace). These helpers look for a place
that does not, so the test runs instead of being skipped.
"""
import os
import shutil
import tempfile
from pathlib import Path

CANDIDATE_BASES = (None, "/tmp/opencode", "/dev/shm", "/var/tmp")


def in_a_checkout(path: Path) -> bool:
    path = Path(path).resolve()
    return any((p / ".git").exists() for p in [path, *path.parents])


def folder_outside_any_checkout(prefix: str = "plain-") -> Path | None:
    """A new empty folder with no git checkout around it, or None if no candidate place qualifies.
    The caller removes it (shutil.rmtree)."""
    for base in CANDIDATE_BASES:
        if base is not None and not os.path.isdir(base):
            continue
        try:
            path = Path(tempfile.mkdtemp(prefix=prefix, dir=base)).resolve()
        except OSError:
            continue
        if not in_a_checkout(path):
            return path
        shutil.rmtree(path, ignore_errors=True)
    return None


def without_git_variables(env: dict) -> dict:
    """The environment minus every GIT_* variable (a git hook sets GIT_DIR and friends)."""
    return {k: v for k, v in env.items() if not k.startswith("GIT_")}
