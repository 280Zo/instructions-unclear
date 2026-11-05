"""tools/redact.py: what hides secrets in everything the agent reads.

A real install showed the agent an OAuth client secret that an app printed into its
log at first start. Every tool whose output the agent reads passes it through here.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from redact import HIDDEN, redact_json, redact_text  # noqa: E402

# Made-up values shaped like real ones (Laravel Str::random(40), 32 random bytes in base64, hex).
RANDOM40 = "N8qQ2mJ7xYz0kLpR4sT6vW9bC1dE3fG5hI7jK9lM"
BASE64 = "q83vEjR0QmVjZXBzS2V5V2l0aE1peGVkQ2FzZTA9"
EQ, COLON = "=", ":"  # kept apart so the repo's secret scan doesn't read these examples as real
HEX64 = "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"


class RedactTests(unittest.TestCase):
    def test_values_after_secret_words_are_hidden(self):
        for line, value in ((f"Client secret{COLON} shortone", "shortone"),
                            (f"password{EQ}hunter2", "hunter2"),
                            (f"DB_PASSWORD {EQ} hunter2", "hunter2"),
                            ("Your admin password is hunter2", "hunter2"),
                            (f'{{"event": "login", "token"{COLON} "abc123"}}', "abc123"),
                            (f"Authorization{COLON} Bearer abc123", "abc123"),
                            (f"api_key{COLON} abc123", "abc123"),
                            (f"APP_KEY{EQ}base64:shortone", "shortone")):
            with self.subTest(line=line):
                out = redact_text(line)
                self.assertNotIn(value, out)
                self.assertIn(HIDDEN, out)

    def test_value_on_the_line_after_its_label_is_hidden(self):
        # Review: apps print "Your admin password:" and the value indented on the next line.
        out = redact_text(f"Your admin password{COLON}\n\n  correct-horse-battery\nnext line stays")
        self.assertNotIn("correct-horse-battery", out)
        self.assertIn("next line stays", out)

    def test_colour_codes_and_short_names(self):
        for line, value in ((f"\x1b[1mpassword\x1b[0m{COLON} hunter2", "hunter2"),
                            (f'export DB_PASS{EQ}"x y"', "x y"), (f"MYSQL_PWD{EQ}hunter2", "hunter2"),
                            (f"pwd{COLON} hunter2", "hunter2")):
            with self.subTest(line=line):
                self.assertNotIn(value, redact_text(line))
        self.assertEqual(redact_text("compass bypass passes"), "compass bypass passes")

    def test_random_looking_values_are_hidden_anywhere(self):
        for value in (RANDOM40, BASE64, HEX64, "550e8400-e29b-41d4-a716-446655440000"):
            for line in (value, f"Here is your key {value} keep it", f"next line:\n{value}\n"):
                with self.subTest(line=line):
                    out = redact_text(line)
                    self.assertNotIn(value, out)
                    self.assertIn(HIDDEN, out)

    def test_private_key_blocks_are_hidden_whole(self):
        kind = "OPENSSH " + "PRIVATE KEY"
        text = f"before\n-----BEGIN {kind}-----\nb3BlbnNzaC1rZXk\nAAAA\n-----END {kind}-----\nafter\n"
        out = redact_text(text)
        self.assertNotIn("b3BlbnNzaC1rZXk", out)
        self.assertNotIn("AAAA", out)
        self.assertIn("before", out)
        self.assertIn("after", out)

    def test_ordinary_output_is_kept(self):
        for line in ("ok\tcustom/app-monica.yaml", "active", "applied",
                     "kept: /var/lib/appdata/authentik/data/media/public/app-icons",
                     "302 https://login.example.duckdns.org/", "/run/user/3203/containers",
                     "a1b2c3d4e5f6a7b8c9d0e1f2a monica_db_password  file  2 days ago",
                     "monica_app_key", "/home/owner/AI/fcos-app-installer/tools/vmssh.py",
                     "drwxr-x---. 2 3203 3203 4096 Nov  3 12:00 monica",
                     "Started notes-app.service - Example notes app (app).",
                     "IdentificationStage", "both archives are intact"):
            with self.subTest(line=line):
                self.assertEqual(redact_text(line), line)

    def test_json_keeps_its_shape(self):
        data = {"id": 5, "name": "Monica", "client_secret": "abc", "nested": {"api_key": "xyz", "ok": True},
                "items": [{"password": "p"}, RANDOM40], "redirect_uris": "https://monica.example.duckdns.org/"}
        out = redact_json(data)
        self.assertEqual(out["id"], 5)
        self.assertEqual(out["name"], "Monica")
        self.assertEqual(out["client_secret"], HIDDEN)
        self.assertEqual(out["nested"], {"api_key": HIDDEN, "ok": True})
        self.assertEqual(out["items"], [{"password": HIDDEN}, HIDDEN])
        self.assertEqual(out["redirect_uris"], "https://monica.example.duckdns.org/")
        json.dumps(out)


if __name__ == "__main__":
    unittest.main()
