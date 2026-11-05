"""tools/authgw/authentik_rules_status.py runs inside the Authentik worker (ak shell). Here
Authentik's modules are stand-ins; field names from authentik 2026.8.5
(blueprints/models.py, blueprints/v1/tasks.py)."""
import sys
import tempfile
import types
import unittest
from hashlib import sha512
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "authgw" / "authentik_rules_status.py"


class Instance:
    def __init__(self, status, last_applied_hash):
        self.status, self.last_applied_hash = status, last_applied_hash


def fake_authentik(blueprints_dir, instances, ready=1):
    class Query:
        def __init__(self, found):
            self.found = found

        def first(self):
            return self.found

    class Objects:
        @staticmethod
        def filter(path=None, ready=None):
            if ready is not None:
                return [Tenant() for _ in range(1)]
            value = instances.get(path)
            return Query(value() if callable(value) else value)

    class Tenant:
        objects = Objects()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    class BlueprintInstance:
        objects = Objects()

    mods = {
        "authentik": types.ModuleType("authentik"),
        "authentik.blueprints": types.ModuleType("authentik.blueprints"),
        "authentik.blueprints.models": types.ModuleType("authentik.blueprints.models"),
        "authentik.lib": types.ModuleType("authentik.lib"),
        "authentik.lib.config": types.ModuleType("authentik.lib.config"),
        "authentik.tenants": types.ModuleType("authentik.tenants"),
        "authentik.tenants.models": types.ModuleType("authentik.tenants.models"),
    }
    mods["authentik.blueprints.models"].BlueprintInstance = BlueprintInstance
    mods["authentik.lib.config"].CONFIG = {"blueprints_dir": str(blueprints_dir)}
    mods["authentik.tenants.models"].Tenant = Tenant
    return mods


class RulesStatusTests(unittest.TestCase):
    def run_script(self, files, instances, deadline=0, expected=None):
        with tempfile.TemporaryDirectory() as root:
            custom = Path(root, "custom")
            custom.mkdir()
            hashes = {}
            for name, text in files.items():
                Path(custom, name).write_text(text)
                hashes[f"custom/{name}"] = sha512(text.encode()).hexdigest()
            inst = {path: (make(hashes.get(path, "")) if callable(make) else make) for path, make in instances.items()}
            saved = dict(sys.modules)
            sys.modules.update(fake_authentik(root, inst))
            out = []
            namespace = {"__name__": "django.core.management.commands.shell", "print": lambda *a: out.append(" ".join(map(str, a))),
                         "SLEEP": lambda s: None, "DEADLINE_S": deadline}
            if expected is not None:
                namespace["EXPECTED"] = expected(hashes)
            try:
                with self.assertRaises(SystemExit) as stop:
                    exec(compile(SCRIPT.read_text(), str(SCRIPT), "exec"), namespace)
            finally:
                sys.modules.clear()
                sys.modules.update(saved)
            return stop.exception.code, "\n".join(out)

    def test_all_applied_passes(self):
        code, out = self.run_script({"app-a.yaml": "a", "outpost-providers.yaml": "o"},
                                    {"custom/app-a.yaml": lambda h: Instance("successful", h),
                                     "custom/outpost-providers.yaml": lambda h: Instance("successful", h)})
        self.assertEqual(code, 0, out)
        self.assertIn("ok      custom/app-a.yaml", out)

    def test_an_old_hash_is_still_pending(self):
        code, out = self.run_script({"app-a.yaml": "new"}, {"custom/app-a.yaml": Instance("successful", "old")})
        self.assertEqual(code, 1)
        self.assertIn("pending custom/app-a.yaml", out)

    def test_an_error_fails(self):
        code, out = self.run_script({"app-a.yaml": "a"}, {"custom/app-a.yaml": lambda h: Instance("error", "x")})
        self.assertEqual(code, 1)
        self.assertIn("error   custom/app-a.yaml", out)

    def test_a_stale_error_waits_for_the_new_apply(self):
        # Review: an error from the previous push must not end the wait; the restarted
        # worker re-applies the fixed file a moment later.
        class Flips(Instance):
            def __init__(self, digest):
                super().__init__("error", "old")
                self.reads, self.digest = 0, digest

            def __getattribute__(self, name):
                if name == "status":
                    object.__setattr__(self, "reads", object.__getattribute__(self, "reads") + 1)
                    if object.__getattribute__(self, "reads") > 2:
                        object.__setattr__(self, "last_applied_hash", object.__getattribute__(self, "digest"))
                        return "successful"
                    return "error"
                return object.__getattribute__(self, name)

        code, out = self.run_script({"app-a.yaml": "a"}, {"custom/app-a.yaml": Flips}, deadline=60)
        self.assertEqual(code, 0, out)
        self.assertIn("ok      custom/app-a.yaml", out)

    def test_a_file_not_yet_registered_is_pending(self):
        code, out = self.run_script({"app-new.yaml": "n"}, {})
        self.assertEqual(code, 1)
        self.assertIn("pending custom/app-new.yaml (not registered: Authentik ignored this file", out)

    def test_expected_hashes_from_the_vm_are_used_when_the_folder_is_unreadable(self):
        # podman exec lacks the worker's extra group, so it can't list the
        # folder; the VM hashes the files (sudo sha512sum) and passes them in as EXPECTED.
        code, out = self.run_script({}, {"custom/app-a.yaml": lambda h: Instance("successful", "abc")},
                                    expected=lambda hashes: {"custom/app-a.yaml": "abc"})
        self.assertEqual(code, 0, out)
        self.assertIn("ok      custom/app-a.yaml", out)
        code, out = self.run_script({}, {"custom/app-a.yaml": lambda h: Instance("successful", "old")},
                                    expected=lambda hashes: {"custom/app-a.yaml": "abc"})
        self.assertEqual(code, 1)

    def test_nothing_to_check_is_a_failure_with_a_reason(self):
        code, out = self.run_script({}, {})
        self.assertEqual(code, 1)
        self.assertIn("no rules files found", out)

    def test_guide_runs_it_after_the_worker_restart(self):
        guide = " ".join((ROOT / "docs" / "guide" / "03-add-a-service.md").read_text().split())
        # As an argument, never through the interactive shell (Django falls back to it).
        self.assertIn('ak shell -c \\"\\$(cat)\\"', guide)
        self.assertIn("< tools/authgw/authentik_rules_status.py", guide)
        self.assertIn("sudo sha512sum", guide)
        self.assertIn("sudo find /var/lib/appdata/authentik/blueprints", guide)  # admin can't list it
        self.assertIn("EXPECTED = {", guide)
        self.assertNotIn("grep -E \"Applying blueprint", guide)


if __name__ == "__main__":
    unittest.main()
