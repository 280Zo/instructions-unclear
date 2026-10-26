"""Keep executable install examples on the reviewed rulesync release."""

import re
import unittest

from test_security_re_context import ROOT


class RulesyncVersionTests(unittest.TestCase):
    def test_owned_install_commands_use_reviewed_version(self):
        paths = [ROOT / "AGENTS.md", ROOT / "README.md", ROOT / "groups/README.md"]
        for directory in ("skills", "agents", "mcp-servers"):
            paths.extend((ROOT / directory).glob("*/README.md"))
        stale = []
        for path in paths:
            for version in re.findall(r"npx rulesync@([0-9.]+)", path.read_text()):
                if version != "41.0.0":
                    stale.append(f"{path.relative_to(ROOT)}: {version}")
        self.assertEqual(stale, [], "Unreviewed install pins: " + ", ".join(stale))


if __name__ == "__main__":
    unittest.main()
