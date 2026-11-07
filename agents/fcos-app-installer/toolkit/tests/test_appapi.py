"""tools/appapi.py: the agent's temporary API access to an app.
The user creates a time-limited token in the app, stores it from a hidden prompt
into secrets/, and deletes it in the app at the end. The agent never sees it."""
import http.server
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "appapi.py"
FAKE = "fake-abcdefghijklmnopqrstuvwxyz-0123456789"

SITE = "domain: example.duckdns.org\n"
SPEC = """name: crm
login: gateway
hostname: crm
api_paths:
  - "^/api/.*$"
  - "^/dav(/.*)?$"
"""


class Handler(http.server.BaseHTTPRequestHandler):
    seen = []

    def log_message(self, *args):
        pass

    def _answer(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode() if length else ""
        Handler.seen.append({"method": self.command, "path": self.path,
                             "auth": self.headers.get("Authorization"), "body": body})
        if self.path == "/api/moved":
            self.send_response(302)
            self.send_header("Location", "http://127.0.0.1:9/api/stolen")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        payload = json.dumps({"ok": True, "echo": self.headers.get("Authorization")}).encode()
        if self.path == "/api/oauth":
            payload = json.dumps({"name": "x", "client_secret": "abc", "nested": {"api_key": "xyz"},
                                  "plain": "N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM"}).encode()
        self.send_response(200 if self.path != "/api/fail" else 403)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = do_POST = do_PUT = do_DELETE = _answer


class AppApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        Handler.seen.clear()
        self.ws = Path(tempfile.mkdtemp(prefix="fcos-appapi-"))
        self.addCleanup(subprocess.run, ["rm", "-rf", str(self.ws)])
        (self.ws / "secrets").mkdir(mode=0o700)
        (self.ws / "services" / "crm").mkdir(parents=True)
        (self.ws / "site.yaml").write_text(SITE)
        (self.ws / "services" / "crm" / "service.yaml").write_text(SPEC)
        self.token = self.ws / "secrets" / "app-crm.token"

    def run_tool(self, *args, test_http=True):
        # In-process with the base address patched: the tool itself has no test switch.
        import contextlib
        import io
        sys.path.insert(0, str(ROOT / "tools"))
        import appapi
        out, err = io.StringIO(), io.StringIO()
        saved = appapi._base
        if test_http:
            appapi._base = lambda ws, svc: self.base
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = appapi.main([*args, "--workspace", str(self.ws)])
                except SystemExit as stop:
                    code = stop.code
        finally:
            appapi._base = saved
        return code, out.getvalue(), err.getvalue()

    def store(self, url="https://crm.example.duckdns.org"):
        # The user's store step writes the app's address beside the token (agent can't edit it).
        self.token.write_text(f"url={url}\n{FAKE}\n")
        self.token.chmod(0o600)

    def test_store_step_is_a_hidden_prompt_with_the_workspace_filled_in(self):
        code, out, err = self.run_tool("store-step", "crm")
        self.assertEqual(code, 0, err)
        self.assertIn("# desktop (fish)", out)
        self.assertIn('read -s -P "token for crm: " t', out)
        self.assertIn(f"'{self.ws}/secrets/app-crm.token'", out)  # quoted
        self.assertIn("chmod 600", out)
        self.assertIn("set -e t", out)
        # The address is in plain sight in the user's command, and stored with the token.
        self.assertIn("https://crm.example.duckdns.org", out)
        self.assertIn("url=https://crm.example.duckdns.org", out)

    def test_call_sends_the_token_and_never_prints_it(self):
        self.store()
        code, out, err = self.run_tool("call", "crm", "GET", "/api/me")
        self.assertEqual(code, 0, err)
        self.assertEqual(Handler.seen[-1]["auth"], f"Bearer {FAKE}")
        self.assertEqual(Handler.seen[-1]["path"], "/api/me")
        self.assertNotIn(FAKE, out + err)  # the echo in the body is scrubbed
        self.assertIn("200", out)

    def test_secrets_in_the_answer_are_hidden(self):
        # An API answer (e.g. a new OAuth client) can carry a secret.
        self.store()
        code, out, err = self.run_tool("call", "crm", "GET", "/api/oauth")
        self.assertEqual(code, 0, err)
        for value in ("abc", "xyz", "N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM"):
            self.assertNotIn(value, out)
        body = json.loads(out.split("\n", 1)[1])
        self.assertEqual(body["name"], "x")
        self.assertEqual(body["client_secret"], "[hidden]")

    def test_post_sends_a_json_body_from_a_file(self):
        self.store()
        data = self.ws / "body.json"
        data.write_text('{"name": "x"}')
        code, out, err = self.run_tool("call", "crm", "POST", "/api/contacts", "--data", str(data))
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(Handler.seen[-1]["body"]), {"name": "x"})

    def test_only_the_apps_api_paths(self):
        # Behind the login page only the paths that skip it are reachable with a token.
        self.store()
        code, out, err = self.run_tool("call", "crm", "GET", "/settings")
        self.assertEqual(code, 1)
        self.assertIn("api_paths", err)
        self.assertEqual(Handler.seen, [])

    def test_errors_exit_1_and_bad_inputs_are_refused(self):
        self.store()
        self.assertEqual(self.run_tool("call", "crm", "GET", "/api/fail")[0], 1)
        for args in (("call", "crm", "TRACE", "/api/x"), ("call", "crm", "GET", "api/x"),
                     ("call", "../x", "GET", "/api/x")):
            with self.subTest(args=args):
                self.assertNotEqual(self.run_tool(*args)[0], 0)

    def test_token_file_must_be_private(self):
        self.store()
        self.token.chmod(0o644)
        code, out, err = self.run_tool("call", "crm", "GET", "/api/me")
        self.assertEqual(code, 1)
        self.assertIn("chmod 600", err)
        self.assertEqual(Handler.seen, [])

    def test_https_only_outside_tests(self):
        # Without the test-only address, the tool speaks https to the stored address and nothing else. The
        # request is recorded and stopped before it leaves the machine: no DNS lookup, no connection.
        from unittest import mock
        import urllib.error
        import urllib.request
        self.store()
        seen = []

        def stop(opener, request, *args, **kwargs):
            seen.append(request.full_url)
            raise urllib.error.URLError("stopped in the test")

        with mock.patch.object(urllib.request.OpenerDirector, "open", stop):
            code, out, err = self.run_tool("call", "crm", "GET", "/api/me", test_http=False)
        self.assertNotEqual(code, 0)
        self.assertEqual(seen, ["https://crm.example.duckdns.org/api/me"])
        self.assertEqual(Handler.seen, [])

    def test_redirects_are_not_followed(self):
        # Review: urllib would resend the Authorization header to the redirect's host.
        self.store()
        code, out, err = self.run_tool("call", "crm", "GET", "/api/moved")
        self.assertEqual(code, 1)
        self.assertIn("302", out)
        self.assertIn("not followed", out + err)
        self.assertEqual([s["path"] for s in Handler.seen], ["/api/moved"])

    def test_no_environment_switch(self):
        self.assertNotIn("environ", (ROOT / "tools" / "appapi.py").read_text())

    def test_data_from_secrets_refused(self):
        self.store()
        evil = self.ws / "secrets" / "x.json"
        evil.write_text("{}")
        link = self.ws / "link.json"
        link.symlink_to(evil)
        for data in (str(evil), str(link)):
            with self.subTest(data=data):
                code, out, err = self.run_tool("call", "crm", "POST", "/api/x", "--data", data)
                self.assertEqual(code, 1)
                self.assertIn("secrets", err)
        self.assertEqual(Handler.seen, [])

    def test_encoded_paths_refused(self):
        self.store()
        for path in ("/api/%2e%2e/admin", "/api/%2F/x", "/api/../settings", "/api/%5c"):
            with self.subTest(path=path):
                self.assertEqual(self.run_tool("call", "crm", "GET", path)[0], 1)
        self.assertEqual(Handler.seen, [])

    def test_odd_token_characters_refused(self):
        self.token.write_text("url=https://crm.example.duckdns.org\nabc<def>\n")
        self.token.chmod(0o600)
        code, out, err = self.run_tool("call", "crm", "GET", "/api/me")
        self.assertEqual(code, 1)
        self.assertNotIn("abc<def>", out + err)

    def test_the_address_comes_from_the_token_file_not_the_spec(self):
        # Review: hostname/domain are files the agent edits; a crafted one sent the token elsewhere.
        sys.path.insert(0, str(ROOT / "tools"))
        import appapi
        self.store("https://crm.example.duckdns.org")
        (self.ws / "services" / "crm" / "service.yaml").write_text(
            SPEC.replace("hostname: crm", "hostname: x@example.com/a#"))
        self.assertEqual(appapi._base(self.ws, "crm"), "https://crm.example.duckdns.org")
        for bad in ("http://crm.example.duckdns.org", "https://x@example.com", "https://a.b/c", "https://a b"):
            self.store(bad)
            with self.subTest(bad=bad), self.assertRaises(appapi.ApiError):
                appapi._base(self.ws, "crm")

    def test_store_step_refuses_a_crafted_hostname(self):
        (self.ws / "services" / "crm" / "service.yaml").write_text(
            SPEC.replace("hostname: crm", "hostname: x@example.com/a#"))
        code, out, err = self.run_tool("store-step", "crm")
        self.assertEqual(code, 1)
        self.assertNotIn("x@example.com", out)

    def test_forget_deletes_the_local_token(self):
        self.store()
        code, out, err = self.run_tool("forget", "crm")
        self.assertEqual(code, 0, err)
        self.assertFalse(self.token.exists())
        self.assertIn("delete the token in the app", out)


class RulesTests(unittest.TestCase):
    def test_agent_may_run_it_and_never_read_the_token(self):
        sys.path.insert(0, str(ROOT / "tests"))
        from test_agent import AGENT, effect
        text = AGENT.read_text()
        self.assertEqual(effect(text, "shell", "python3 tools/appapi.py call crm GET /api/me"), "allow")
        self.assertEqual(effect(text, "read", "/home/owner/fcos-ws/secrets/app-crm.token"), "deny")
        prompt = " ".join(text.split())
        self.assertIn("tools/appapi.py", prompt)
        self.assertIn("forget", prompt)


if __name__ == "__main__":
    unittest.main()
