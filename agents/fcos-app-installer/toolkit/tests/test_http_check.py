"""tools/http_check.py: status code and redirect only; never writes, never sends data."""
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = [sys.executable, str(ROOT / "tools" / "http_check.py")]


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            self.send_response(200)
            self.send_header("Content-Length", "1000")
            self.end_headers()
            self.wfile.flush()
            time.sleep(3)  # body stalls after the status line
            return
        if self.path == "/code":
            self.send_response(302)
            self.send_header("Location", "https://app.example.duckdns.org/cb?code" + "=N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM")
            self.end_headers()
            return
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "https://auth.example.duckdns.org/flow")
            self.end_headers()
            return
        self.send_response(200 if self.path == "/" else 401)
        self.end_headers()
        self.wfile.write(b"x" * 100000)

    def log_message(self, *args):
        pass


class HttpCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def run_tool(self, *args):
        return subprocess.run(TOOL + list(args), capture_output=True, text=True, timeout=30)

    def test_status_and_redirect_not_followed(self):
        result = self.run_tool(f"http://127.0.0.1:{self.port}/")
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "200"))
        result = self.run_tool(f"http://127.0.0.1:{self.port}/redirect")
        self.assertEqual(result.stdout.strip(), "302 https://auth.example.duckdns.org/flow")
        result = self.run_tool(f"http://127.0.0.1:{self.port}/api")
        self.assertEqual(result.stdout.strip(), "401")

    def test_redirect_location_is_redacted(self):
        result = self.run_tool(f"http://127.0.0.1:{self.port}/code")
        self.assertNotIn("N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM", result.stdout)
        self.assertIn("302 https://app.example.duckdns.org/cb", result.stdout)

    def test_refused_is_reported(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        result = self.run_tool("--timeout", "3", f"http://127.0.0.1:{port}/")
        self.assertEqual((result.returncode, result.stdout.strip()), (2, "refused"))

    def test_timeout_is_reported_apart_from_refused(self):
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(1)  # accepts the connection, never answers
        self.addCleanup(sock.close)
        result = self.run_tool("--timeout", "1", f"http://127.0.0.1:{sock.getsockname()[1]}/")
        self.assertEqual((result.returncode, result.stdout.strip()), (2, "timeout"))

    def test_status_counts_even_if_the_body_stalls(self):
        # An open port that answers slowly must never read as "not reachable".
        result = self.run_tool("--timeout", "1", f"http://127.0.0.1:{self.port}/slow")
        self.assertEqual((result.returncode, result.stdout.strip()), (0, "200"))

    def test_malformed_url_is_a_clean_error(self):
        result = self.run_tool("http://[::1/")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stderr)

    def test_only_http_and_https_and_no_extra_arguments(self):
        for args in (("file:///etc/passwd",), ("ftp://x/",), ("http://x/", "extra"), ("-d", "a", "http://x/"),
                     ("--output", "x", "http://x/"), ()):
            with self.subTest(args=args):
                result = self.run_tool(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("200", result.stdout)


if __name__ == "__main__":
    unittest.main()
