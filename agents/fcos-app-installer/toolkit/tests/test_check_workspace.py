"""tools/check_workspace.py: no two services share a name, UID, GID, port on a VM, or web name."""
import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_workspace import workspace_problems  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SITE = yaml.safe_load((FIXTURES / "site.yaml").read_text())


def spec(name):
    return yaml.safe_load((FIXTURES / "services" / f"{name}.yaml").read_text())


class CheckWorkspaceTests(unittest.TestCase):
    def test_distinct_services_pass(self):
        self.assertEqual(workspace_problems(SITE, [spec("single"), spec("crm")]), [])

    def test_duplicates_refused(self):
        cases = {
            "name": lambda a, b: b.update(name=a["name"], hostname="other"),
            "uid": lambda a, b: b.update(uid=a["uid"]),
            "gid": lambda a, b: b.update(gid=a.get("gid", a["uid"])),
            "hostname": lambda a, b: b.update(hostname=a["hostname"]),
            "port": lambda a, b: b.update(vm=a["vm"], port=a["port"]),
        }
        for what, mutate in cases.items():
            with self.subTest(what=what):
                a, b = spec("single"), spec("crm")
                mutate(a, b)
                problems = workspace_problems(SITE, [a, b])
                self.assertTrue(any(f": {what} " in p for p in problems), problems)

    def test_same_port_on_different_vms_is_fine(self):
        a, b = spec("single"), spec("crm")
        b["port"] = a["port"]  # crm is on vm apps, single on ai
        self.assertEqual(workspace_problems(SITE, [a, b]), [])

    def test_login_front_end_accounts_and_names_are_taken(self):
        b = spec("crm")
        b["uid"] = SITE["edge"]["authentik"]["uid"]
        self.assertTrue(any("uid" in p and "authentik" in p for p in workspace_problems(SITE, [b])))
        b = spec("crm")
        b["hostname"] = SITE["edge"]["authentik"]["host"].split(".")[0]
        self.assertTrue(any(": hostname " in p and "login page" in p for p in workspace_problems(SITE, [b])))
        b = spec("crm")
        b["name"] = "traefik"
        self.assertTrue(any(": name " in p for p in workspace_problems(SITE, [b])))

    def test_accounts_every_vm_has_are_taken(self):
        # The admin account (UID picked by useradd: 1000 or 1001 next to FCOS's
        # core) and the shared groups exist on every VM; a clash fails Ignition.
        site = copy.deepcopy(SITE)
        site["shared_groups"] = [{"name": "ai-projects", "gid": 3100}]
        for what, mutate in (("name", lambda s: s.update(name=site["admin_user"])),
                             ("name", lambda s: s.update(name="core")),
                             ("name", lambda s: s.update(name="ai-projects")),
                             ("uid", lambda s: s.update(uid=1000)),
                             ("uid", lambda s: s.update(uid=1001)),
                             ("gid", lambda s: s.update(gid=1001)),
                             ("gid", lambda s: s.update(gid=3100))):
            with self.subTest(what=what):
                b = spec("crm")
                mutate(b)
                self.assertTrue(any(f": {what} " in p for p in workspace_problems(site, [b])))

    def test_login_front_end_web_ports_are_taken(self):
        b = spec("crm")
        b.update(vm=SITE["edge"]["vm"], port=443)
        problems = workspace_problems(SITE, [b])
        self.assertTrue(any(": port 443 " in p and "traefik" in p for p in problems), problems)

    def test_uid_equal_to_another_gid_is_fine(self):
        # /etc/subuid and /etc/subgid are separate, and so are UIDs and GIDs.
        a, b = spec("single"), spec("crm")
        a["gid"] = 3150
        b["uid"] = 3150
        b["gid"] = 3151
        self.assertEqual(workspace_problems(SITE, [a, b]), [])

    def test_clash_suggests_a_free_value(self):
        a, b = spec("single"), spec("crm")
        b["uid"] = a["uid"]
        problem = next(p for p in workspace_problems(SITE, [a, b]) if ": uid " in p)
        self.assertRegex(problem, r"free: \d+")

    def test_free_hint_skips_numbers_taken_as_the_other_kind(self):
        # crm takes opencode's UID; the next number up is a shared group's GID,
        # and crm's GID follows its UID, so that number is not free.
        site = copy.deepcopy(SITE)
        a, b = spec("single"), spec("crm")
        b.pop("gid", None)
        b["uid"] = a["uid"]
        site["shared_groups"] = [{"name": "ai-projects", "gid": a["uid"] + 1}]
        problem = next(p for p in workspace_problems(site, [a, b]) if ": uid " in p)
        self.assertNotIn(f"free: {a['uid'] + 1})", problem)
        self.assertIn(f"free: {a['uid'] + 2})", problem)

    def test_system_names_taken(self):
        # root and nobody exist on every Linux; wheel and sudo are the admin's
        # groups in templates/base/base-config.bu.tmpl.
        for name in ("root", "nobody", "wheel", "sudo"):
            with self.subTest(name=name):
                b = spec("crm")
                b["name"] = name
                self.assertTrue(any(": name " in p for p in workspace_problems(SITE, [b])))

    def test_broken_front_end_section_still_reports_other_clashes(self):
        site = copy.deepcopy(SITE)
        del site["edge"]["authentik"]["uid"]
        a, b = spec("single"), spec("crm")
        b["uid"] = a["uid"]
        problems = workspace_problems(site, [a, b])
        self.assertTrue(any("login front end" in p for p in problems), problems)
        self.assertTrue(any(": uid " in p for p in problems), problems)

    def test_odd_specs_reported_not_crashing(self):
        b = spec("crm")
        b["uid"] = [1, 2]
        problems = workspace_problems(SITE, [b, ["not", "a", "mapping"]])
        self.assertTrue(any("uid" in p and "number" in p for p in problems), problems)
        self.assertTrue(any("not a mapping" in p for p in problems), problems)

    def test_command_line_read_errors_exit_2(self):
        tool = [sys.executable, str(ROOT / "tools" / "check_workspace.py")]
        self.assertEqual(subprocess.run(tool + ["/nonexistent"], capture_output=True).returncode, 2)
        ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "site.yaml").write_text("a: [unclosed\n")
        self.assertEqual(subprocess.run(tool + [str(ws)], capture_output=True).returncode, 2)

    def test_command_line_reads_the_workspace(self):
        ws = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "site.yaml").write_text(yaml.safe_dump(SITE))
        for name, data in (("opencode", spec("single")), ("crm", spec("crm"))):
            (ws / "services" / name).mkdir(parents=True)
            (ws / "services" / name / "service.yaml").write_text(yaml.safe_dump(data))
        tool = [sys.executable, str(ROOT / "tools" / "check_workspace.py"), str(ws)]
        ok = subprocess.run(tool, capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        clash = copy.deepcopy(spec("crm"))
        clash["uid"] = spec("single")["uid"]
        (ws / "services" / "crm" / "service.yaml").write_text(yaml.safe_dump(clash))
        bad = subprocess.run(tool, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1)
        self.assertIn("uid", bad.stdout)


if __name__ == "__main__":
    unittest.main()
