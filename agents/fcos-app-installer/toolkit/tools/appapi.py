#!/usr/bin/env python3
"""The agent's temporary API access to an app.

The owner creates a time-limited admin token in the app itself (its official
docs say how), stores it from a hidden prompt, and deletes it in the app when
the setup is done. The agent never sees the token: this tool reads it from
<workspace>/secrets/app-<svc>.token and never prints it.

  store-step <svc>                 print the owner's hidden-prompt store command
  call <svc> <METHOD> <PATH> [--data <json file>] [--scheme Bearer|Token]
                                   one request to https://<hostname>.<domain><PATH>;
                                   behind the login page only the app's api_paths
  forget <svc>                     delete the local token (the owner deletes it in the app)

Exit status: 0 for a 2xx answer, 1 otherwise. TLS certificates are verified;
the address is always https://<hostname>.<domain> (no override), and redirects
are never followed (they would carry the token to another address).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import workspace  # noqa: E402
from gen_service import DOMAIN, HOST_LABEL  # noqa: E402
from redact import redact_json, redact_text  # noqa: E402
from workspace import WorkspaceError  # noqa: E402

SVC = re.compile(r"^[a-z][a-z0-9-]{0,30}$")
PATH = re.compile(r"^/[A-Za-z0-9._~/%?&=+,:@-]{0,500}$")
# Encoded dots, slashes or backslashes could reach a path the api_paths check didn't see.
SNEAKY = re.compile(r"%2e|%2f|%5c|(^|/)\.\.?(/|$|\?)", re.I)
MATERIAL_CHARS = re.compile(r"^[A-Za-z0-9._~+/=-]{8,1024}$")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


# The address the owner confirmed when storing the token: https, a plain host name, no path.
URL_LINE = re.compile(r"^url=(https://[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?)+)$")


def _base(ws: Path, svc: str) -> str:
    """The app's address, from the token file (written by the owner's store step; the
    agent can't edit it), never from the spec or site file the agent edits."""
    return _read_file(ws, svc)[0]


METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
MAX_BODY = 64 * 1024


class ApiError(Exception):
    pass


def _spec(ws: Path, svc: str) -> dict:
    if not SVC.match(svc):
        raise ApiError(f"invalid service name {svc!r}")
    try:
        return workspace.load_service(ws, svc)
    except WorkspaceError as exc:
        raise ApiError(str(exc)) from None


def _token_path(ws: Path, svc: str) -> Path:
    return ws / "secrets" / f"app-{svc}.token"


def _read_file(ws: Path, svc: str) -> tuple[str, str]:
    path = _token_path(ws, svc)
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        raise ApiError(f"no token for {svc}; the owner stores one first (appapi.py store-step {svc})") from None
    except OSError:
        raise ApiError(f"{path} cannot be opened (is it a symlink?)") from None
    with os.fdopen(fd, "r", encoding="utf-8", errors="replace") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ApiError(f"{path} must be a regular file you own")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise ApiError(f"{path} has mode {stat.S_IMODE(info.st_mode):04o}; run: chmod 600 {path}")
        lines = handle.read(4096).strip().splitlines()
    url = URL_LINE.match(lines[0].strip()) if len(lines) == 2 else None
    material = lines[1].strip() if len(lines) == 2 else ""
    if not url:
        raise ApiError(f"{path} must start with the line url=https://<app address>; store it again "
                       f"with the step from appapi.py store-step {svc}")
    if not MATERIAL_CHARS.match(material):
        raise ApiError(f"{path}: the token must be one line (letters, digits, . _ ~ + / = -)")
    return url.group(1), material


def cmd_store_step(ws: Path, site: dict, args) -> int:
    spec = _spec(ws, args.svc)
    host, domain = spec.get("hostname"), site.get("domain")
    if not (isinstance(host, str) and HOST_LABEL.fullmatch(host) and isinstance(domain, str)
            and DOMAIN.fullmatch(domain)):
        raise ApiError("the app needs a valid hostname and the site a valid domain")
    url = f"https://{host}.{domain}"
    path = _token_path(ws, args.svc)
    print(f"The token will only ever be sent to {url} (check this is your app's address).\n")
    print(f"Store the {args.svc} token on your desktop, pasting it when prompted (input is hidden):\n")
    print("```fish\n# desktop (fish)")
    # Always single-quoted; in fish \' is a literal quote inside single quotes.
    q = "'" + str(path).replace("\\", "\\\\").replace("'", "\\'") + "'"
    print(f'read -s -P "token for {args.svc}: " t; and printf \'url={url}\\n%s\\n\' $t > {q}; '
          f'and chmod 600 {q}; set -e t')
    print("```")
    return 0


def cmd_call(ws: Path, site: dict, args) -> int:
    spec = _spec(ws, args.svc)
    method = args.method.upper()
    if method not in METHODS:
        raise ApiError(f"method must be one of {', '.join(METHODS)}")
    if not PATH.match(args.path) or SNEAKY.search(args.path):
        raise ApiError("path must start with / and use plain URL characters (no encoded or .. segments)")
    if spec.get("login") == "authentik":
        allowed = spec.get("api_paths") or []
        if not any(re.search(rx, args.path.split("?", 1)[0]) for rx in allowed):
            raise ApiError(f"{args.path} is behind the login page; only the app's api_paths are reachable "
                           "with a token")
    base = _base(ws, args.svc)
    body = None
    if args.data:
        data = Path(args.data).resolve()
        for private in ((ws / "secrets").resolve(), Path.home().resolve() / ".ssh"):
            if data == private or private in data.parents:
                raise ApiError(f"--data may not come from {private} (secrets stay where they are)")
        body = data.read_bytes()
        if len(body) > MAX_BODY:
            raise ApiError(f"--data is larger than {MAX_BODY} bytes")
        json.loads(body)  # must be JSON
    material = _read_file(ws, args.svc)[1]
    request = urllib.request.Request(base + args.path, data=body, method=method, headers={
        "Authorization": f"{args.scheme} {material}", "Accept": "application/json",
        "User-Agent": "fcos-agent-appapi", **({"Content-Type": "application/json"} if body else {})})
    location = ""
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        with opener.open(request, timeout=30) as response:
            status, text = response.status, response.read(MAX_BODY).decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        status, text = error.code, error.read(MAX_BODY).decode("utf-8", "replace")
        location = (error.headers.get("Location", "") if error.headers else "")
    except (urllib.error.URLError, OSError) as error:
        raise ApiError(f"{method} {args.path}: {getattr(error, 'reason', error)}") from None
    print(status)
    if 300 <= status < 400:
        print(f"redirect to {location!r} not followed (it would carry the token)")
    for form in (material, urllib.parse.quote(material, safe="")):
        text = text.replace(form, "<token>")
    # An answer can carry a secret (a new OAuth client's, say); hide it.
    try:
        print(json.dumps(redact_json(json.loads(text)), indent=2))
    except ValueError:
        print(redact_text(text))
    return 0 if 200 <= status < 300 else 1


def cmd_forget(ws: Path, site: dict, args) -> int:
    _spec(ws, args.svc)
    path = _token_path(ws, args.svc)
    path.unlink(missing_ok=True)
    print(f"deleted the local token for {args.svc}; the owner must also delete the token in the app itself")
    return 0


COMMANDS = {"store-step": cmd_store_step, "call": cmd_call, "forget": cmd_forget}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="name", required=True)
    for name in COMMANDS:
        p = sub.add_parser(name)
        p.add_argument("svc")
        p.add_argument("--workspace")
        if name == "call":
            p.add_argument("method")
            p.add_argument("path")
            p.add_argument("--data")
            p.add_argument("--scheme", choices=("Bearer", "Token"), default="Bearer")
    args = parser.parse_args(argv)
    try:
        ws = workspace.resolve_workspace(args.workspace)
        site = workspace.load_site(ws)
        return COMMANDS[args.name](ws, site, args)
    except (ApiError, WorkspaceError, ValueError, OSError) as exc:
        print(f"appapi: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
