"""tools/validate.sh writes only into a folder of its own, never a fixed path in a shared /tmp."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ValidateScriptTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / "tools" / "validate.sh").read_text()

    def test_it_builds_in_a_private_temporary_folder(self):
        # A fixed /tmp/opencode/render could be pre-created by another user (a link), and the script
        # runs rm -rf on it.
        self.assertNotIn("/tmp/opencode", self.text)
        self.assertIn("mktemp -d", self.text)

    def test_it_never_removes_a_path_it_did_not_create(self):
        for line in self.text.splitlines():
            if "rm -rf" in line:
                self.assertIn("$work", line, line)


if __name__ == "__main__":
    unittest.main()
