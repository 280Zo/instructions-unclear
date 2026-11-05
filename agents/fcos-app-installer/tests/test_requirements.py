"""tools/check_requirements.py: what the toolkit needs on the desktop (owner, 2026-11-04)."""
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


class RequirementsTests(unittest.TestCase):
    def run_check(self, opencode="opencode v2.2.4", which=lambda name: "/usr/bin/" + name, yaml_ok=True,
                  launch=None):
        import check_requirements as mod
        saved = mod.opencode_version, mod.shutil.which, mod.has_pyyaml, mod.launch_folder
        mod.opencode_version = lambda: opencode
        mod.shutil.which = which
        mod.has_pyyaml = lambda: yaml_ok
        mod.launch_folder = lambda: launch if launch is not None else mod.TOOLKIT_ROOT
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = mod.main([])
        finally:
            mod.opencode_version, mod.shutil.which, mod.has_pyyaml, mod.launch_folder = saved
        return code, out.getvalue()

    def test_all_present(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        for needle in ("OpenCode", "2.1.3", "git", "PyYAML", "podman or docker", "launch folder"):
            self.assertIn(needle, out)

    def test_started_elsewhere_refused(self):
        code, out = self.run_check(launch=Path("/somewhere/else"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL  launch folder", out)

    def test_old_opencode_refused(self):
        for version in ("opencode v2.0.29", "opencode v2.1.2", "1.17.10", "not a version"):
            with self.subTest(version=version):
                code, out = self.run_check(opencode=version)
                self.assertEqual(code, 1)
                self.assertIn("2.1.3", out)
        self.assertEqual(self.run_check(opencode="2.1.3")[0], 0)
        self.assertEqual(self.run_check(opencode="opencode v3.0.0")[0], 0)

    def test_missing_tools_refused(self):
        self.assertEqual(self.run_check(which=lambda n: None if n == "git" else "/x/" + n)[0], 1)
        self.assertEqual(self.run_check(which=lambda n: None if n in ("podman", "docker") else "/x/" + n)[0], 1)
        self.assertEqual(self.run_check(which=lambda n: None if n == "podman" else "/x/" + n)[0], 0)  # docker will do
        self.assertEqual(self.run_check(yaml_ok=False)[0], 1)

    def test_readme_and_guide_state_it(self):
        readme = (ROOT / "README.md").read_text()
        needs = readme.split("## What it needs", 1)[1].split("\n## ", 1)[0]
        for needle in ("OpenCode 2.1.3", "git", "PyYAML", "Podman or Docker"):
            self.assertIn(needle, needs)
        guide = (ROOT / "docs" / "guide" / "10-trial-run.md").read_text()
        self.assertIn("python3 tools/check_requirements.py", guide)
        notes = (ROOT / "docs" / "guide" / "research-notes.md").read_text()
        self.assertIn("2.0.30", notes)
        self.assertIn("51341", notes)


if __name__ == "__main__":
    unittest.main()
