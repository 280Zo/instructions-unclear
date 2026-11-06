import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render import load_values, render  # noqa: E402
from secret_scan import scan_text  # noqa: E402


class SecretScanTests(unittest.TestCase):
    def test_flags_secret_values(self):
        # Values are joined at runtime so tools/publish_check.py doesn't flag
        # this file's own test vectors.
        for name, value in (
            ("Environment=OPENAI_API_KEY=", "sk-abc123456789"),
            ("Environment=DB_PASSWORD=", "hunter2hunter2"),
            ("api_key: ", "abcdefghijklmnop"),
            ("token = ", "abcdefghijkl"),
            ("client_secret: ", "abcdefghijkl"),
            ("AWS_ACCESS_KEY=", "AKIAABCDEFGH"),
        ):
            line = name + value
            with self.subTest(line=line):
                self.assertTrue(scan_text(line + "\n"), line)

    def test_allows_secret_references(self):
        for line in (
            "Secret=opencode_model_api,type=env,target=MODEL_API_KEY",
            "Secret=authentik_pg_password,type=env,target=AUTHENTIK_POSTGRESQL__PASSWORD",
            'password_hash: "$y$j9T$EXAMPLEONLY$NOTAREAL"',
            "Environment=POSTGRES_USER=authentik",
            "Environment=AUTHENTIK_POSTGRESQL__HOST=authentik-postgres",
            "# Secrets needed on the VM (the user creates them): duckdns_token",
        ):
            with self.subTest(line=line):
                self.assertEqual(scan_text(line + "\n"), [], line)

    def test_rendered_fixtures_clean(self):
        for fixture in ("ai-vm", "edge"):
            v = load_values(str(ROOT / "tests" / "fixtures" / f"{fixture}.values"))
            for path in sorted((ROOT / "templates").rglob("*.tmpl")):
                with self.subTest(fixture=fixture, template=path.name):
                    self.assertEqual(scan_text(render(path.read_text(), v)), [])


if __name__ == "__main__":
    unittest.main()
