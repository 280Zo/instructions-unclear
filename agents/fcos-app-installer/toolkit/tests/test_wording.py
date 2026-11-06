"""Wording rules for the guide and the question bank (design section 10).

- Questions are plain language: no config keys, field paths or internal names.
- The procedure pages are provider-neutral: provider commands and names live in
  the adapter skills (adapter-* in the skills folder). A paragraph that starts with **Providers.** may name providers and
  link their adapters.
- Real values live in the private workspace, never in a repo config.yaml or vms/.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "guide"
QUESTIONS = GUIDE / "questions.md"
PROVIDER_EXEMPT = set()
PROVIDER_WORDS = [r"\bqm ", r"\bpvesm\b", r"\bpveum\b", r"\bpvesh\b", r"OPNsense", r"TrueNAS", r"Proxmox",
                  r"DuckDNS"]


def guide_pages(provider_check=False):
    pages = sorted(GUIDE.glob("*.md"))
    return [p for p in pages if not (provider_check and p.name in PROVIDER_EXEMPT)]


def paragraphs(text: str):
    return re.split(r"\n\s*\n", text)


class QuestionTests(unittest.TestCase):
    def setUp(self):
        self.text = QUESTIONS.read_text()

    def test_questions_have_no_config_keys(self):
        self.assertNotRegex(self.text, r"`[a-z0-9]+_[a-z0-9_]+`", "backticked snake_case key")
        self.assertNotRegex(self.text, r"[a-z_]+\[\]\.", "field path like vms[].ip")
        self.assertNotRegex(self.text, r"\b[a-z_]+\.[a-z_]+\.[a-z_]+\b", "dotted key path")
        for word in ("vms", "services", "site.yaml", "hosts:", "accepted_risks", "login_reason"):
            self.assertNotIn(word, self.text, word)

    def test_questions_avoid_jargon(self):
        for phrase in ("edge VM", "edge", "always-on", "always_on", "Quadlet", "Butane", "Ignition"):
            self.assertNotIn(phrase, self.text, phrase)

    def test_every_question_says_what_it_fills_and_when_it_is_skipped(self):
        sections = [s for s in re.split(r"\n(?=## )", self.text) if s.startswith("## ")]
        self.assertGreaterEqual(len(sections), 10)
        for section in sections:
            title = section.splitlines()[0]
            with self.subTest(section=title):
                self.assertIn("**Asked:**", section)
                self.assertIn("**Fills:**", section)
                self.assertIn("**Skipped when:**", section)


class GuideTests(unittest.TestCase):
    def test_guide_provider_neutral(self):
        for page in guide_pages(provider_check=True):
            for para in paragraphs(page.read_text()):
                if para.lstrip().startswith("**Providers.**"):
                    continue
                for pattern in PROVIDER_WORDS:
                    with self.subTest(page=page.name, pattern=pattern):
                        self.assertIsNone(re.search(pattern, para), para[:120])

    def test_providers_paragraphs_link_adapters(self):
        found = 0
        for page in guide_pages():
            for para in paragraphs(page.read_text()):
                if para.lstrip().startswith("**Providers.**"):
                    found += 1
                    self.assertIn("adapter-", para, page.name)
        self.assertGreaterEqual(found, 1)

    def test_guide_refers_to_workspace(self):
        for page in guide_pages():
            text = page.read_text()
            with self.subTest(page=page.name):
                self.assertNotIn("config.yaml", text)
                self.assertIsNone(re.search(r"(?<!<workspace>/)(?<![\w/])vms/", text),
                                  "vms/ must be <workspace>/vms/")

    def test_guide_links_resolve(self):
        for page in guide_pages() + [ROOT / "README.md"]:
            for target in re.findall(r"\]\(([^)#:]+)(?:#[^)]*)?\)", page.read_text()):
                with self.subTest(page=page.name, target=target):
                    self.assertTrue((page.parent / target).exists(), target)

    def test_one_login_front_end_explained(self):
        text = (GUIDE / "06-edge-vm.md").read_text()
        self.assertIn("## Why one login front end", text)
        for needle in ("create_recovery_key", "break-glass", "always on"):
            self.assertIn(needle, text)

    def test_verification_checklist_stays_at_3_10(self):
        self.assertIn("## 3.10 ", (GUIDE / "03-add-a-service.md").read_text())

    def test_commands_on_service_folders_use_sudo(self):
        # /var/lib/appdata/<svc> folders are 0750 and owned by the service user;
        # backup folders on NFS are too, and root is squashed there, so those
        # need `sudo -u <svc>`. Each command segment touching them starts with sudo.
        commands = ("ls", "rm", "cat", "cp", "find", "du", "mv", "tar")
        for page in guide_pages():
            in_code = False
            for line in page.read_text().splitlines():
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if not in_code:
                    continue
                for segment in re.split(r"[;&|'\"]", line):
                    words = segment.split()
                    if not words or words[0] not in commands:
                        continue
                    with self.subTest(page=page.name, segment=segment.strip()[:80]):
                        self.assertNotIn("/var/lib/appdata/", segment, "needs sudo")
                        self.assertNotIn("/var/mnt/backups/", segment, "needs sudo -u <svc>")

    def test_backup_listing_runs_as_the_service_user(self):
        for page in guide_pages():
            for line in page.read_text().splitlines():
                if re.search(r"\bls\b[^;'\"]*/var/mnt/backups/", line):
                    with self.subTest(page=page.name, line=line.strip()[:80]):
                        self.assertRegex(line, r"sudo -u \S+ ls\b[^;'\"]*/var/mnt/backups/")

    def test_remove_stops_all_backup_timers(self):
        # Deferred fix 5: every timer stops, not only <svc>-backup.timer. Stopping the
        # user's whole systemd manager stops all its units; the file list then
        # removes every timer and timer link its fragments wrote.
        text = (GUIDE / "07-remove-and-rollback.md").read_text()
        self.assertIn("sudo loginctl disable-linger $svc; sudo systemctl stop user@$uid.service", text)
        self.assertIn('for k in ("files","links")', text)
        self.assertNotIn("$svc-backup.timer", text)

    def test_removal_uses_exact_paths(self):
        text = (GUIDE / "07-remove-and-rollback.md").read_text()
        self.assertNotIn("/usr/local/bin/$svc-*", text)
        self.assertNotIn("$svc-backup*", text)

    def test_remove_also_removes_the_system_units_ignition_made(self):
        # On a real removal the file list covers files and links only, so
        # subids-<svc>.service (a unit) stayed behind and would fail at the next boot once
        # the account is gone. The units and the empty Quadlet folder go too.
        text = (GUIDE / "07-remove-and-rollback.md").read_text()
        self.assertIn('get("systemd"', text)
        self.assertIn("disable --now", text)
        self.assertIn("/etc/systemd/system/", text)
        self.assertIn("daemon-reload", text)
        self.assertIn("rmdir /etc/containers/systemd/users/", text)
        # The data folders still stay until the owner says so.
        self.assertIn("stay until", text)

    def test_app_log_checks_keep_generated_credentials_out_of_view(self):
        # Monica prints an OAuth client secret into its log at first start; the
        # agent read it. Logs are read only through vmssh.py logs (redacted), and the page says why.
        text = (GUIDE / "03-add-a-service.md").read_text()
        self.assertIn("python3 tools/vmssh.py logs $vm $svc-app.service", text)
        commands = [l for l in text.splitlines() if l.startswith("python3 tools/vmssh.py run")]
        self.assertTrue(commands)
        self.assertFalse([l for l in commands if "journalctl" in l or "podman logs" in l])
        self.assertIn("generated credentials", text)
        self.assertIn("rotate", text.lower())

    def test_database_page_has_a_mariadb_restore_and_a_restore_test(self):
        # The page covered SQLite and Postgres restores only, and no way to prove a backup
        # restores. The restore test ran on a real install: a throwaway
        # MariaDB with no network and its data in memory, counts compared with the live one.
        text = (GUIDE / "04-databases-and-backups.md").read_text()
        self.assertIn("## Test a restore", text)
        self.assertIn("--network none", text)
        self.assertIn("--tmpfs /var/lib/mysql", text)
        self.assertIn("MARIADB_ALLOW_EMPTY_ROOT_PASSWORD", text)
        self.assertIn("init process done", text)  # wait for it, or the load hits the temporary server
        self.assertIn("count", text.lower())
        self.assertNotRegex(text, r"select \*", "counts only: never print rows into the agent's view")
        restore = text.split("## Restore", 1)[1]
        self.assertIn("MariaDB", restore)
        self.assertIn("gunzip -c", restore)
        self.assertIn("not tested", restore.split("MariaDB", 1)[1].split("Then run", 1)[0])

    def test_break_glass_says_the_tunnel_fails_for_apps_that_force_their_own_https(self):
        # Tested on a real install: Monica's login page loaded through the SSH
        # tunnel, but signing in redirected to https://localhost:<port> and failed. The
        # working way in is the app's route without the login, edited by hand and put back.
        text = (GUIDE / "08-break-glass.md").read_text()
        self.assertIn("builds every link from its own `https://` address", text)
        self.assertIn("SSL_ERROR_RX_RECORD_TOO_LONG", text)
        self.assertIn("middlewares: [authentik]", text)
        self.assertIn('[ "$(hostnamectl hostname)" = "<login-vm>" ]', text)
        self.assertIn("monica.yml.login", text)
        self.assertIn("put it back", text.lower())

    def test_apps_that_mail_need_a_sender_address_for_the_log_mailer(self):
        # Monica's invitations failed with 'An email must have a From or a Sender header'
        # until MAIL_FROM_ADDRESS was set, although the mail only goes to the log.
        text = (GUIDE / "03-add-a-service.md").read_text()
        self.assertIn("sender address", text)
        self.assertIn("MAIL_FROM_ADDRESS", text)
        self.assertIn("Nothing here uses an email server", text)

    def test_login_front_end_vm_gets_its_backup_folders(self):
        text = (GUIDE / "06-edge-vm.md").read_text()
        self.assertIn("backup_folder", text)
        self.assertIn("service_user", text)

    def test_dns_provider_gap_is_stated_where_the_choice_is_offered(self):
        self.assertIn("only one", (GUIDE / "questions.md").read_text().split("## 4.")[0])
        self.assertIn("DuckDNS only today", (ROOT / "README.md").read_text())

    def test_login_front_end_output_outside_vm_folders(self):
        for page in guide_pages():
            with self.subTest(page=page.name):
                self.assertNotRegex(page.read_text(), r"login_frontend\.py \S+ \S*vms/")

    def test_app_only_reachability_stated(self):
        text = (GUIDE / "07-remove-and-rollback.md").read_text()
        self.assertIn("without the login page", text)
        self.assertNotIn("is not built yet", text)
        self.assertIn("without the login page", (GUIDE / "questions.md").read_text())

    def test_no_deleted_templates_named(self):
        for page in guide_pages():
            text = page.read_text()
            for name in ("traefik.bu.tmpl", "authentik.bu.tmpl", "edge-route.bu.tmpl", "app.container.tmpl",
                         "OUTPOST_PROVIDER_LIST"):
                with self.subTest(page=page.name, name=name):
                    self.assertNotIn(name, text)


class ReadmeTests(unittest.TestCase):
    def test_root_readme(self):
        text = (ROOT / "README.md").read_text()
        for needle in ("OpenCode", "workspace", "setup-agent-access.sh", "docs/guide/README.md", "publish_check.py"):
            self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
