#!/usr/bin/env python3
"""Place the FCOS app installer toolkit's own files into the folder you start OpenCode in.

rulesync writes the agent, its helper, the command, the skills and the rules there (see
groups/fcos_app_installer.jsonc and this folder's README). It cannot place the rest: tools/,
templates/, docs/, schemas/, specs/, tests/, site.example.yaml and host-scripts.sha256. This
script copies those from this folder's toolkit/ directory, from the repository, so that
installing never depends on where the toolkit was developed.

Usage:
  install.py <folder>            dry run: lists what would be created and replaced, writes nothing
  install.py <folder> --apply    do it
  install.py <folder> --check    dry run that exits 1 when anything would change

It copies a fixed list of top-level entries and nothing else, refuses links and common secret
file names (it never reads a file's contents for secrets), never deletes, and never touches
files that are not on that list (.opencode/, AGENTS.md, your workspace, your own files). A file that is on the list and differs from the
toolkit's copy IS replaced, including a README.md or .gitignore of yours at the folder's top and
edits you made to a toolkit file; the dry run lists every such file as "changed" first, so read it
before adding --apply. Everything is checked before anything is written; a failure while writing
(a full disk) can still leave the folder partly installed, and running it again is safe.
Standard library only. Exit 0 on success, 1 on --check differences, 2 on a refusal, a failure or
bad usage.
"""
import os
import shlex
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The only top-level entries of toolkit/ that get installed. Anything else in toolkit/ is an error,
# so a stray file can never be copied by accident.
INSTALL_LIST = ("tools", "templates", "docs", "schemas", "specs", "tests", "site.example.yaml",
                "host-scripts.sha256", ".gitignore")
SKIP_DIRS = {"__pycache__"}
SECRET_SUFFIXES = (".token", ".key", ".pem", ".p12", ".pfx", ".p8", ".jks", ".keystore", ".kdbx", ".cred",
                   ".tfstate", ".tfstate.backup", ".gpg", ".asc", ".keytab", ".secret", ".secrets")
SECRET_PREFIXES = (".env", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")
SECRET_NAMES = {"credentials.json", ".credentials.json", "auth.json", ".claude.json", ".npmrc", ".netrc",
                ".git-credentials", ".pgpass", ".htpasswd", ".dockercfg", ".boto", "kubeconfig", "known_hosts",
                "service-account.json", "oauth.json", "terraform.tfvars", ".pypirc"}
# A file whose whole name (before the extension) is one of these; "secret_scan.py" is not.
SECRET_STEMS = {"secret", "secrets", "token", "tokens", "password", "passwords", "passwd", "api_key", "apikey",
                "api-key", "credentials", "credential", "vault-password", "vault_password",
                "service_account", "service-account", "kubeconfig"}
SECRET_FOLDERS = {"secrets", ".ssh", ".aws", ".gnupg"}


class Refusal(Exception):
    pass


def looks_secret(relative: Path) -> bool:
    """Names that hold or suggest a secret, whatever their case; nothing like them is installed."""
    name = relative.name.lower()
    return (name.endswith(SECRET_SUFFIXES) or name.startswith(SECRET_PREFIXES) or name in SECRET_NAMES
            or name.split(".", 1)[0] in SECRET_STEMS
            or bool(SECRET_FOLDERS & {part.lower() for part in relative.parts}))


def shown(text: str) -> str:
    """A path for the output: bytes that are not valid text, and control characters, are escaped."""
    return "".join(c if c.isprintable() else c.encode("unicode_escape").decode("ascii")
                   for c in text.encode("utf-8", "backslashreplace").decode("utf-8"))


def nearest_checkout(folder: Path) -> Path | None:
    return next((p for p in [folder, *folder.parents] if (p / ".git").exists()), None)


def plan_files(source: Path) -> dict[str, Path]:
    """Every file to install, by path relative to the toolkit; refuses anything unexpected."""
    if not source.is_dir():
        raise Refusal(f"the toolkit source folder {source} is missing")
    for entry in sorted(source.iterdir()):
        if entry.name not in INSTALL_LIST and entry.name not in SKIP_DIRS:
            raise Refusal(f"{entry.name} is in {source.name}/ but not on the install list; "
                          "add it to INSTALL_LIST in install.py on purpose, or move it out")
    files = {}
    for name in INSTALL_LIST:
        top = source / name
        if top.is_symlink():
            raise Refusal(f"{name} is a link; the installer never copies links")
        if not top.exists():
            continue
        candidates = [top] if top.is_file() else sorted(top.rglob("*"))
        for path in candidates:
            relative = path.relative_to(source)
            if SKIP_DIRS & set(relative.parts) or path.suffix == ".pyc":
                continue
            if path.is_symlink():
                raise Refusal(f"{relative} is a link; the installer never copies links")
            if path.is_dir():
                continue
            if looks_secret(relative):
                raise Refusal(f"{shown(str(relative))} looks like a secret; nothing like that belongs in the toolkit")
            files[relative.as_posix()] = path
    # This folder's README goes with the toolkit, as README.md: it is what you read in the folder you
    # run the toolkit in, and the toolkit's tests read it.
    readme = source.parent / "README.md"
    if readme.is_symlink():
        raise Refusal("README.md is a link; the installer never copies links")
    if readme.is_file():
        files["README.md"] = readme
    return files


def check_target(target: Path, folder: Path, source: Path, checkout: Path | None) -> None:
    if target == folder or folder in target.parents or target in (source, *source.parents):
        raise Refusal(f"{target} is the toolkit's source folder (or a parent of it); "
                      "choose a folder of its own to run the toolkit in")
    if checkout is not None and (target == checkout or checkout in target.parents):
        raise Refusal(f"{target} is inside {checkout}, the repository the installer belongs to; OpenCode "
                      "started there would load that repository's own AGENTS.md and rules. "
                      "Choose a folder of its own, outside it")
    if target.exists() and not target.is_dir():
        raise Refusal(f"{target} exists and is not a folder")


def check_room(target: Path) -> None:
    """The nearest folder that exists above (or at) the target must be one we can create in."""
    base = target
    while not base.exists():
        if base.is_symlink():
            raise Refusal(f"{base} is a broken link; the installer never writes through links")
        base = base.parent
    if not base.is_dir():
        raise Refusal(f"{base} is not a folder")
    if not os.access(base, os.W_OK | os.X_OK):
        raise Refusal(f"{base} is not writable")


def classify(files: dict[str, Path], target: Path) -> dict[str, list[str]]:
    """new / changed / same, refusing a destination that would be written through a link, over a
    folder or a pipe, into a file, or into a folder we cannot write to; the whole plan is checked
    before anything is written. A folder we cannot write to matters only where a file is to be
    created or replaced in it."""
    result = {"new": [], "changed": [], "same": []}
    for relative, path in files.items():
        destination = target / relative
        if destination.is_dir() and not destination.is_symlink():
            raise Refusal(f"{shown(relative)} in {target} is a folder where a file belongs")
        for parent in [*reversed(destination.relative_to(target).parents)][1:] + [Path(relative)]:
            step = target / parent
            if step.is_symlink():
                raise Refusal(f"{parent.as_posix()} in {target} is a link; the installer never writes through links")
        for parent in Path(relative).parents:
            if parent != Path(".") and (target / parent).exists() and not (target / parent).is_dir():
                raise Refusal(f"{parent.as_posix()} in {target} is not a folder")
        if destination.exists() and not destination.is_file():
            raise Refusal(f"{shown(relative)} in {target} is not a regular file (a pipe, a device or a socket)")
        if not destination.exists():
            kind = "new"
        elif (destination.read_bytes() != path.read_bytes()
              or (destination.stat().st_mode & 0o111) != (path.stat().st_mode & 0o111)):
            kind = "changed"
        else:
            kind = "same"
        if kind != "same":
            container = destination.parent
            while not container.exists():
                container = container.parent
            if container.is_dir() and not os.access(container, os.W_OK | os.X_OK):
                raise Refusal(f"{shown(container.relative_to(target).as_posix() or '.')} in {target} is not writable")
        result[kind].append(relative)
    return result


def write(files: dict[str, Path], target: Path, names: list[str]) -> None:
    for relative in names:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        data = files[relative].read_bytes()
        mode = 0o755 if files[relative].stat().st_mode & 0o111 else 0o644
        handle, temporary = tempfile.mkstemp(dir=destination.parent, prefix=".install-")
        try:
            with os.fdopen(handle, "wb") as out:
                out.write(data)
            os.chmod(temporary, mode)
            os.replace(temporary, destination)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise


def main(argv: list[str], source: Path | None = None) -> int:
    flags = {a for a in argv if a.startswith("--")}
    folders = [a for a in argv if not a.startswith("--")]
    if (len(folders) != 1 or not folders[0].strip() or folders[0] != folders[0].strip()
            or not flags <= {"--apply", "--check"}
            or {"--apply", "--check"} <= flags):
        print("usage: install.py <folder> [--apply | --check]   (the folder must be named, without surrounding spaces)", file=sys.stderr)
        return 2
    source = Path(source) if source is not None else HERE / "toolkit"
    folder = source.resolve().parent  # the installer's own folder, whatever source is
    try:
        given = Path(folders[0]).expanduser()
        if given.is_symlink():
            raise Refusal(f"{given} is a link; name the folder it points to, so the installer never writes through a link")
        target = given.resolve()
        checkout = nearest_checkout(HERE)
        check_target(target, folder, source.resolve(), checkout)
        check_room(target)
        files = plan_files(source.resolve())
        plan = classify(files, target) if target.exists() else {"new": sorted(files), "changed": [], "same": []}
    except Refusal as refusal:
        print(f"install: {refusal}", file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as error:  # a loop of links, a name too long, an unreadable file
        print(f"install: cannot plan the install ({error.__class__.__name__}: {error}); nothing was written",
              file=sys.stderr)
        return 2
    other = nearest_checkout(target if target.exists() else target.parent)
    if other is not None:
        print(f"install: warning: {target} is inside the git checkout {other}. OpenCode started there loads "
              "that checkout's own AGENTS.md, rules and skills, and the workspace guard will refuse a "
              "workspace inside it; a folder of its own, outside any other checkout, is better.", file=sys.stderr)
    for kind in ("new", "changed"):
        for relative in plan[kind]:
            print(f"{kind:8} {shown(relative)}")
    print(f"{len(plan['new'])} new, {len(plan['changed'])} changed, {len(plan['same'])} unchanged")
    if "--apply" in flags:
        try:
            write(files, target, plan["new"] + plan["changed"])
        except OSError as error:
            print(f"install: stopped while writing ({error.__class__.__name__}: {error}). The folder may be "
                  "partly installed; nothing else is touched, so run it again once the cause is fixed",
                  file=sys.stderr)
            return 2
        print(f"installed into {target}")
        repo = HERE.parents[1]
        print("next, with rulesync (from the repository):\n"
              f"  cd {shlex.quote(str(repo))}\n"
              f"  npx rulesync@41.0.0 generate --config groups/fcos_app_installer.jsonc "
              f"--output-roots {shlex.quote(str(target))}\n"
              f"then start OpenCode in {shlex.quote(str(target))} and run: python3 tools/check_requirements.py")
        return 0
    differs = bool(plan["new"] or plan["changed"])
    if "--check" in flags:
        return 1 if differs else 0
    print("dry run: nothing was written; add --apply to install")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
