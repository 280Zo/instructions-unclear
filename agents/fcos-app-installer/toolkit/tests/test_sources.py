"""Owner, 2026-11-02: facts about software the agent doesn't write come from its
official docs or source, never from memory, and are recorded with the source."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "docs" / "guide" / "research-notes.md"
AGENT = ROOT / ".opencode" / "agents" / "fcos-app-installer.md"


def rows():
    for line in NOTES.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("| ") and len(cells) >= 4 and cells[0].isdigit():
            yield cells


class SourceTests(unittest.TestCase):
    def test_every_research_note_cites_a_source(self):
        found = list(rows())
        self.assertGreater(len(found), 10)
        for cells in found:
            with self.subTest(row=cells[0]):
                source = cells[-1]
                self.assertTrue(re.search(r"https://", source) or source.startswith("Tested on"), source)

    def test_pushed_blueprints_are_applied_explicitly(self):
        # Trial 2026-11-02: Authentik's watcher only reacts to created/modified files
        # (authentik/blueprints/v1/tasks.py); the push renames a temp file into place.
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        # Review: ak apply_blueprint never registers a new file, so the outpost file's
        # required metaapplyblueprint fails for a new app; a worker restart rescans (apps.py
        # send_on_startup), as proven on the trial VM 2026-11-02.
        self.assertIn("systemctl --user restart authentik-worker.service", guide)
        self.assertIn("tools/authentik_rules_status.py", guide)
        self.assertNotIn("ak apply_blueprint custom/", guide)
        self.assertIn("races the push", guide)
        self.assertNotIn("Authentik applies changed blueprint files on its own", guide)
        notes = NOTES.read_text()
        self.assertNotIn("discovered and applied automatically when they change", notes)
        self.assertIn("authentik/blueprints/v1/tasks.py", notes)

    def test_trial_wording_fixes(self):
        guide = ROOT / "docs" / "guide"
        pages = {p.name: " ".join(p.read_text().split()) for p in guide.glob("*.md")}
        for name, text in pages.items():
            with self.subTest(page=name):
                # The login page's name comes from the site file (edge.authentik.host), e.g. login.<domain>.
                self.assertNotIn("auth.<domain>", text)
                self.assertNotIn("auth.example.duckdns.org", text)
                # The owner's machine is a desktop (owner, 2026-11-01).
                self.assertNotIn("laptop", text)
        edge = pages["06-edge-vm.md"]
        # docs.goauthentik.io/users-sources/user/user-interface/: gear icon > Credentials > MFA Devices.
        self.assertIn("gear icon", edge)
        self.assertIn("**Credentials** tab", edge)
        self.assertIn("Static tokens", edge)
        self.assertIn("users-sources/user/user-interface", edge)
        # Services start at boot and retry (RestartSec=30) until their secrets exist.
        self.assertIn("retry every 30 seconds until", edge)

    def test_people_icons_and_access_are_in_the_procedure(self):
        guide = ROOT / "docs" / "guide"
        three = " ".join((guide / "03-add-a-service.md").read_text().split())
        for needle in ("anyone new", "`people:`", "official repository or website", "`icon:`"):
            self.assertIn(needle, three)
        edge = " ".join((guide / "06-edge-vm.md").read_text().split())
        for needle in ("## 6.10", "Reset password", "users-sources/user/user_basic_operations", "no email",
                       "`guests`", "`family`"):
            self.assertIn(needle, edge)
        prompt = " ".join(AGENT.read_text().split())
        for needle in ("anyone new needs an account", "logo", "never set a password"):
            self.assertIn(needle, prompt)

    def test_prompt_forbids_facts_from_memory(self):
        text = " ".join(AGENT.read_text().split())
        for needle in ("never from memory", "research-notes.md", "where something is in an app's menus",
                       "test it on an FCOS-shaped"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
