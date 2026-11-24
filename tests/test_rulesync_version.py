"""Keep executable install examples on the reviewed rulesync release."""

import contextlib
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest

from test_security_re_context import ROOT


class RulesyncVersionTests(unittest.TestCase):
    def test_owned_install_commands_use_reviewed_version(self):
        paths = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "groups/README.md",
                 ROOT / "agents/fcos-app-installer/install.py"]
        for directory in ("skills", "agents", "mcp-servers"):
            paths.extend((ROOT / directory).glob("*/README.md"))
        stale = []
        for path in paths:
            for version in re.findall(r"npx rulesync@([0-9.]+)", path.read_text()):
                if version != "43.12.0":
                    stale.append(f"{path.relative_to(ROOT)}: {version}")
        self.assertEqual(stale, [], "Unreviewed install pins: " + ", ".join(stale))

    def test_version_comparison_reports_every_difference(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import compare_rulesync_versions as compare

        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "old", Path(tmp) / "new"
            for side, body in ((old, "aaaa"), (new, "bbbb")):  # same size, different bytes
                (side / "skills/x").mkdir(parents=True)
                (side / "skills/x/SKILL.md").write_text(body)
                (side / ".cache").mkdir()
                (side / ".cache/state").write_text(body)
            (new / "only-new.md").write_text("n")
            self.assertEqual(compare.differing(old, new), ["only-new.md", "skills/x/SKILL.md"])
            self.assertEqual(compare.differing(old, old), [])

    def test_version_comparison_refuses_a_local_selection(self):
        sys.path.insert(0, str(ROOT / "tests"))
        import compare_rulesync_versions as compare

        with tempfile.TemporaryDirectory() as tmp:
            repo, cli = Path(tmp), Path(tmp) / "cli.js"
            cli.write_text("")
            (repo / "rulesync.local.jsonc").write_text("{}")
            saved, argv = compare.REPO, sys.argv
            compare.REPO, sys.argv = repo, ["compare", str(cli), str(cli)]
            try:
                with self.assertRaises(SystemExit) as raised, \
                        contextlib.redirect_stderr(io.StringIO()) as err:
                    compare.main()
            finally:
                compare.REPO, sys.argv = saved, argv
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("rulesync.local.jsonc", err.getvalue())


if __name__ == "__main__":
    unittest.main()
