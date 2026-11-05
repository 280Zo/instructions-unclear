"""tools/install_notes.py: <workspace>/AGENTS.md, what exists in an install and how a new
service hooks into it."""
import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from install_notes import NOTES_END, NOTES_START, add_note, write_notes  # noqa: E402
from test_gen_service import SITE, spec_fixture  # noqa: E402


class InstallNotesTests(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp(prefix="fcos-notes-"))
        self.addCleanup(shutil.rmtree, self.ws, True)
        site = copy.deepcopy(SITE)
        site["edge"]["vm"] = "edge"
        site["edge"]["authentik"]["host"] = "login.example.duckdns.org"
        site["signup"] = {"group": "guests"}
        site["signin_sources"] = {"google": {"client_id": "x.apps.googleusercontent.com"}}
        site["shared_groups"] = [{"name": "ai-projects", "gid": 3100}]
        (self.ws / "site.yaml").write_text(yaml.safe_dump(site))
        monica = spec_fixture("monica")
        monica.update(login="authentik", hostname="monica", groups=["family"], section="Relationships")
        for spec in (monica, spec_fixture("single")):
            folder = self.ws / "services" / spec["name"]
            folder.mkdir(parents=True)
            (folder / "service.yaml").write_text(yaml.safe_dump(spec))

    def text(self):
        write_notes(self.ws)
        return (self.ws / "AGENTS.md").read_text()

    def test_lists_what_exists(self):
        text = self.text()
        for needle in ("## Machines", "| ai |", "| apps |", "## Login front end", "login.example.duckdns.org",
                       "guests", "google", "## Services", "| monica | apps |", "family", "Relationships",
                       "| opencode | ai |", "## Numbers in use", "3110", "3101", "## Secrets (names only)",
                       "monica_db_password", "ai-projects (GID 3100)"):
            self.assertIn(needle, text)

    def test_says_how_a_new_service_hooks_in(self):
        text = self.text()
        self.assertIn("## How a new service hooks in", text)
        for needle in ("existing group", "existing section", "login front end", "free UID", "file-server.md"):
            self.assertIn(needle, text)

    def test_no_secret_values(self):
        text = self.text()
        self.assertIn("names only", text)
        self.assertNotIn("x.apps.googleusercontent.com", text)  # IDs stay in the site file

    def test_hand_written_notes_survive_regeneration(self):
        self.text()
        add_note(self.ws, "Monica has no single sign-on (monicahq/monica#1154); share it by invitation.")
        text = self.text()
        notes = text.split(NOTES_START, 1)[1].split(NOTES_END, 1)[0]
        self.assertIn("Monica has no single sign-on", notes)
        add_note(self.ws, "Second note.")
        self.assertEqual(self.text().count("Monica has no single sign-on"), 1)
        self.assertIn("Second note.", self.text())

    def test_bad_notes_refused(self):
        for bad in ("", "x" * 1001, NOTES_END, "line\nbreak"):
            with self.subTest(bad=bad[:20]), self.assertRaises(ValueError):
                add_note(self.ws, bad)

    def test_cli(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "install_notes.py"), str(self.ws)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.ws / "AGENTS.md").is_file())


class AgentUsesItTests(unittest.TestCase):
    def test_prompt_and_guide(self):
        prompt = " ".join((ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text().split())
        self.assertIn("<workspace>/AGENTS.md", prompt)
        self.assertIn("tools/install_notes.py", prompt)
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        self.assertIn("tools/install_notes.py", guide)


if __name__ == "__main__":
    unittest.main()
