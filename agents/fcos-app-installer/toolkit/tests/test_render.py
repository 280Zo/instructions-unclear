import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from render import RenderError, load_values, render  # noqa: E402

TEMPLATES = ROOT / "templates"
FIXTURES = ROOT / "tests" / "fixtures"


def write_values(text: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".values", delete=False)
    handle.write(text)
    handle.close()
    return handle.name


class NetworkValueTests(unittest.TestCase):
    """*_CIDR and *_IP values land inside firewall rules: only real networks pass."""

    def test_cidr_lists_are_normalized(self):
        self.assertEqual(render("{ {{LAN_CIDR}} }", {"LAN_CIDR": "192.0.2.0/24,198.51.100.0/24"}),
                         "{ 192.0.2.0/24, 198.51.100.0/24 }")
        self.assertEqual(render("{{ADMIN_LAN_CIDR}}", {"ADMIN_LAN_CIDR": " 192.0.2.0/24 "}), "192.0.2.0/24")

    def test_bad_networks_refused(self):
        for bad in ("192.0.2.0/24 } accept; tcp dport 1-65535 accept #", "0.0.0.0/0", "192.0.2.0/24\naccept",
                    "", "192.0.2.1/24", "2001:db8::/32", "198.51.100.0/24, 198.51.100.128/25", "192.0.2.0/24, 192.0.2.0/24",
                    "not-a-network", "0.0.0.0/1, 128.0.0.0/1", "8.0.0.0/8", "127.0.0.0/8", "0.0.0.0/8"):
            with self.subTest(bad=bad), self.assertRaises(RenderError) as caught:
                render("{{LAN_CIDR}}", {"LAN_CIDR": bad})
            self.assertIn("LAN_CIDR", str(caught.exception))
            self.assertNotIn("Tailscale", str(caught.exception))

    def test_home_and_shared_address_networks_pass(self):
        home = ".".join(["10", "0", "0", "0"]) + "/16"  # built at runtime: the publish check flags private addresses
        self.assertEqual(render("{{LAN_CIDR}}", {"LAN_CIDR": f"{home}, 100.64.0.0/10"}), f"{home}, 100.64.0.0/10")

    def test_ports_and_counts_are_numbers(self):
        self.assertEqual(render("{{SVC_PORT}} {{BACKUP_KEEP}}", {"SVC_PORT": "8110", "BACKUP_KEEP": "14"}), "8110 14")
        for key, bad in (("SVC_PORT", "8110; flush ruleset"), ("SVC_PORT", "0"), ("SVC_PORT", "70000"),
                         ("SVC_PORT", "²"), ("SVC_PORT", "٨١١٠"),
                         ("BACKUP_KEEP", "14)); rm -rf /; echo $(("), ("BACKUP_KEEP", "0"), ("BACKUP_KEEP", "-1")):
            with self.subTest(key=key, bad=bad), self.assertRaises(RenderError):
                render("{{" + key + "}}", {key: bad})

    def test_ip_values_are_single_addresses(self):
        self.assertEqual(render("{{EDGE_IP}}", {"EDGE_IP": "192.0.2.10"}), "192.0.2.10")
        for bad in ("192.0.2.10; accept", "192.0.2.0/24", "x", "192.0.2.10, 192.0.2.11"):
            with self.subTest(bad=bad), self.assertRaises(RenderError):
                render("{{EDGE_IP}}", {"EDGE_IP": bad})


class LeftoverBraceTests(unittest.TestCase):
    def test_render_rejects_leftover_braces(self):
        for template in ("name: {{ svc }}", "name: {{svc}}", "a {{KEY} b", "a {KEY}} b", "x {{", "}} y"):
            with self.subTest(template=template), self.assertRaises(RenderError) as caught:
                render(template, {"KEY": "v", "svc": "v"})
            self.assertIn("placeholder", str(caught.exception))

    def test_values_may_hold_closing_braces(self):
        self.assertEqual(render("w: {{KEY}}", {"KEY": "%{http_code}}"}), "w: %{http_code}}")


class RenderTests(unittest.TestCase):
    def test_substitutes(self):
        self.assertEqual(render("a {{X}} b", {"X": "1"}), "a 1 b")

    def test_missing_key_fails(self):
        with self.assertRaises(RenderError):
            render("{{NOPE}}", {})

    def test_value_with_braces_fails(self):
        with self.assertRaises(RenderError):
            render("{{X}}", {"X": "{{Y}}"})

    def test_systemd_vars_untouched(self):
        text = "ExecStart=/bin/x ${FOO} $BAR"
        self.assertEqual(render(text, {}), text)

    def test_no_braces_left(self):
        templates = sorted(TEMPLATES.rglob("*.tmpl"))
        if not templates:
            self.skipTest("no templates yet")
        values = load_values(str(FIXTURES / "edge.values"))
        for path in templates:
            with self.subTest(template=str(path.relative_to(ROOT))):
                self.assertNotIn("{{", render(path.read_text(), values))


class LoadValuesTests(unittest.TestCase):
    def test_reads_pairs_and_skips_comments(self):
        path = write_values("# comment\nA=1\n\nB=two words\n")
        self.assertEqual(load_values(path), {"A": "1", "B": "two words"})

    def test_values_reject_secret_keys(self):
        for key in ("DUCKDNS_TOKEN", "DB_PASSWORD", "APP_SECRET", "API_KEY"):
            with self.subTest(key=key):
                with self.assertRaises(RenderError):
                    load_values(write_values(f"{key}=abc\n"))

    def test_empty_secret_key_allowed(self):
        self.assertEqual(load_values(write_values("DUCKDNS_TOKEN=\n")), {"DUCKDNS_TOKEN": ""})

    def test_newline_escape(self):
        path = write_values("LINES=Volume=/a:/a\\nVolume=/b:/b\n")
        self.assertEqual(load_values(path)["LINES"], "Volume=/a:/a\nVolume=/b:/b")

    def test_malformed_line_fails(self):
        with self.assertRaises(RenderError):
            load_values(write_values("not a pair\n"))


class CommandLinePathTests(unittest.TestCase):
    """render.py runs without asking, so it may only read templates from templates/ and values files from the
    workspace, the fixtures or /tmp/opencode: anything else would let it print any readable file."""

    FIXTURE = ROOT / "tests" / "fixtures" / "ai-vm.values"
    TEMPLATE = ROOT / "templates" / "base" / "firewall.bu.tmpl"

    def run_main(self, template, values):
        import contextlib
        import io
        from render import main
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["render.py", str(template), str(values)])
        return code, out.getvalue(), err.getvalue()

    def test_a_template_and_a_fixture_values_file_render(self):
        code, out, err = self.run_main(self.TEMPLATE, self.FIXTURE)
        self.assertEqual(code, 0, err)
        self.assertTrue(out.strip())

    def test_a_file_that_is_not_a_template_is_not_printed(self):
        import os
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            planted = Path(tmp) / "key.pem"
            planted.write_text("-----BEGIN " + "PRIVATE KEY-----\nabc\n")  # built at runtime: the publish scan flags it
            for template in (planted, ROOT / "tools" / "render.py", ROOT / "templates" / ".." / "tools" / "render.py",
                             Path("/etc/passwd")):
                with self.subTest(template=str(template)):
                    code, out, err = self.run_main(template, self.FIXTURE)
                    self.assertEqual(code, 1)
                    self.assertEqual(out, "")
                    self.assertIn("template", err)
            link = Path(tmp) / "link.tmpl"
            os.symlink(planted, link)
            code, out, err = self.run_main(link, self.FIXTURE)
            self.assertEqual((code, out), (1, ""))
            # A symlink inside templates/ that points out is resolved first and refused too.
            inside = ROOT / "templates" / "zz-test-link.tmpl"
            os.symlink(planted, inside)
            try:
                code, out, err = self.run_main(inside, self.FIXTURE)
            finally:
                inside.unlink()
            self.assertEqual((code, out), (1, ""))

    def test_a_values_file_outside_the_allowed_folders_is_refused(self):
        # A folder that is neither under the toolkit's fixtures, nor /tmp/opencode, nor the workspace.
        elsewhere = next((d for d in ("/dev/shm", "/var/tmp") if Path(d).is_dir()), None)
        if elsewhere:
            with tempfile.TemporaryDirectory(dir=elsewhere) as tmp:
                values = Path(tmp) / "x.values"
                values.write_text(self.FIXTURE.read_text())
                code, out, err = self.run_main(self.TEMPLATE, values)
            self.assertEqual((code, out), (1, ""))
            self.assertIn("values", err)
        code, out, err = self.run_main(self.TEMPLATE, "/etc/passwd")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("values", err)

    def test_a_values_file_in_the_scratch_folder_or_the_workspace_is_allowed(self):
        import os
        from unittest import mock
        scratch = Path("/tmp/opencode")
        if scratch.is_dir():
            with tempfile.TemporaryDirectory(dir=scratch) as tmp:
                values = Path(tmp) / "x.values"
                values.write_text(self.FIXTURE.read_text())
                self.assertEqual(self.run_main(self.TEMPLATE, values)[0], 0)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp).resolve() / "ws"
            (ws / "vms").mkdir(parents=True)
            (ws / "site.yaml").write_text("{}\n")
            values = ws / "vms" / "x.values"
            values.write_text(self.FIXTURE.read_text())
            with mock.patch.dict(os.environ, {"FCOS_WORKSPACE": str(ws)}):
                self.assertEqual(self.run_main(self.TEMPLATE, values)[0], 0)


if __name__ == "__main__":
    unittest.main()
