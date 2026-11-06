"""Facts about software the agent doesn't write come from its
official docs or source, never from memory, and are recorded with the source."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from layout import SKILLS as SKILLS_FOLDER  # noqa: E402
GUIDE = ROOT / "docs" / "guide"
FACT_PAGES = {"02-build-a-vm.md": "## 2.8 Facts the base configuration relies on",
              "04-databases-and-backups.md": "## Facts the restore test relies on",
              "03-add-a-service.md": "## 3.13 Facts the service files rely on"}
ISO_DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
AGENT = ROOT / ".opencode" / "agents" / "fcos-app-installer.md"


def sections(text: str, marker: str):
    """(heading, body) for each section that starts with marker's level, split on that level."""
    level = marker.split(" ", 1)[0]
    parts = re.split(rf"^({re.escape(level)} .*)$", text, flags=re.M)
    return [(parts[i], parts[i + 1]) for i in range(1, len(parts), 2)]


def reference_files():
    return sorted(SKILLS_FOLDER.glob("*/reference.md"))


class SourceTests(unittest.TestCase):
    def cites(self, body: str) -> bool:
        source = [line for line in body.splitlines() if line.startswith("Source:")]
        return bool(source) and ("https://" in source[0] or "Tested on" in source[0] or "package lock" in source[0])

    def test_every_fact_in_a_reference_file_cites_a_source_or_says_it_is_a_design_note(self):
        total = 0
        for path in reference_files():
            for heading, body in sections(path.read_text(), "## "):
                with self.subTest(file=f"{path.parent.name}/reference.md", heading=heading):
                    self.assertTrue(self.cites(body) or "design note" in heading, heading)
                    total += 1
        self.assertGreater(total, 15)

    def test_every_fact_on_a_guide_page_cites_a_source(self):
        for name, marker in FACT_PAGES.items():
            text = (GUIDE / name).read_text()
            self.assertIn(marker, text, name)
            block = text.split(marker, 1)[1].split("\n## ", 1)[0]
            facts = sections(block, "### ")
            for heading, body in facts:
                if "How the templates" in heading:
                    continue
                with self.subTest(page=name, heading=heading):
                    self.assertTrue(self.cites(body), heading)

    def test_facts_carry_no_date(self):
        # A fact is true or it is out of date; the source link is what lets anyone re-check it.
        for path in reference_files():
            self.assertNotRegex(path.read_text(), ISO_DATE, str(path))
        for name, marker in FACT_PAGES.items():
            block = (GUIDE / name).read_text().split(marker, 1)[1].split("\n## ", 1)[0]
            self.assertNotRegex(block, ISO_DATE, name)

    def test_nothing_points_at_the_deleted_notes_by_row_number(self):
        pages = list(GUIDE.glob("*.md")) + list(SKILLS_FOLDER.rglob("*.md")) + list(SKILLS_FOLDER.rglob("*.yaml"))
        for path in pages:
            text = " ".join(path.read_text().split())
            with self.subTest(file=str(path.relative_to(ROOT))):
                self.assertNotRegex(text, r"(?i)research[- ]notes")
                self.assertNotRegex(text, r"(?i)\brows? \d+")

    def test_no_ledger_file_exists(self):
        self.assertFalse((GUIDE / "research-notes.md").exists())

    def test_pushed_blueprints_are_applied_explicitly(self):
        # Authentik's watcher only reacts to created/modified files
        # (authentik/blueprints/v1/tasks.py); the push renames a temp file into place.
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        # Review: ak apply_blueprint never registers a new file, so the outpost file's
        # required metaapplyblueprint fails for a new app; a worker restart rescans (apps.py
        # send_on_startup).
        self.assertIn("systemctl --user restart authentik-worker.service", guide)
        self.assertIn("tools/authgw/authentik_rules_status.py", guide)
        self.assertNotIn("ak apply_blueprint custom/", guide)
        self.assertIn("races the push", guide)
        self.assertNotIn("Authentik applies changed blueprint files on its own", guide)
        notes = (SKILLS_FOLDER / "authgw-authentik" / "reference.md").read_text()
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
                # The owner's machine is a desktop.
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
        for needle in ("never from memory", "reference.md", "where something is in an app's menus",
                       "test it on an FCOS-shaped"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
