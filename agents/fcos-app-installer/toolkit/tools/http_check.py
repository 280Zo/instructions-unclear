#!/usr/bin/env python3
"""Print the HTTP status of one URL, for the guide's checks.

Usage: http_check.py [--timeout <seconds>] <http(s) url>

Prints "<status>" or "<status> <redirect location>" (redirects are not
followed), and exits 0. Prints "refused" (connection refused) or "timeout"
(no answer in time) and exits 2: either way not reachable from here. Exits 1
on a TLS error, a malformed URL or any other error, with the reason on stderr. It only sends a GET without a body, reads at most 64 KiB of
the answer and throws it away, writes no file, and refuses every scheme except
http and https. TLS certificates are verified, so a bad certificate is an error.
"""

import http.client
import socket
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from redact import redact_text  # noqa: E402

MAX_BODY = 64 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def check(url: str, timeout: float) -> tuple[int, str]:
    opener = urllib.request.build_opener(_NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    try:
        request = urllib.request.Request(url, method="GET", headers={"User-Agent": "fcos-agent-http-check"})
        with opener.open(request, timeout=timeout) as response:
            try:
                response.read(MAX_BODY)
            except (OSError, http.client.HTTPException):
                pass  # the status line arrived: the port answered, whatever the body does
            return 0, str(response.status)
    except urllib.error.HTTPError as error:  # 3xx (not followed), 4xx, 5xx
        location = error.headers.get("Location", "") if error.headers else ""
        return 0, f"{error.code} {location}".strip()
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, ConnectionRefusedError):
            return 2, "refused"
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return 2, "timeout"
        if isinstance(reason, ssl.SSLError):
            print(f"http_check: TLS error: {reason}", file=sys.stderr)
            return 1, ""
        print(f"http_check: {reason}", file=sys.stderr)
        return 1, ""
    except ConnectionRefusedError:
        return 2, "refused"
    except (socket.timeout, TimeoutError):
        return 2, "timeout"
    except (http.client.HTTPException, ValueError, OSError) as error:
        print(f"http_check: {type(error).__name__}: {error}", file=sys.stderr)
        return 1, ""


def main(argv: list[str]) -> int:
    args = argv[1:]
    timeout = 10.0
    if len(args) == 3 and args[0] == "--timeout":
        try:
            timeout = float(args[1])
        except ValueError:
            args = []
        else:
            args = args[2:]
    if len(args) != 1 or not args[0].startswith(("http://", "https://")) or not 0 < timeout <= 120:
        print(__doc__.strip(), file=sys.stderr)
        return 2 if not args else 1
    code, text = check(args[0], timeout)
    if text:
        print(redact_text(text))  # a redirect can carry a code or token in its query
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
