"""tools/check_mount_roots.py: every Volume= host path sits under a require-mounts root."""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = [sys.executable, str(ROOT / "tools" / "check_mount_roots.py")]

GOOD = """[Container]
Volume=/var/lib/appdata/svc/data:/data:z
Volume=/var/mnt/projects/ai:/projects
Volume=named.volume:/cache
[Service]
ExecStartPre=/usr/local/bin/require-mounts /var/lib/appdata /var/mnt/projects
"""


class MountRootTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)

    def check(self, **files):
        for name, text in files.items():
            (self.dir / name).write_text(text)
        return subprocess.run(TOOL + [str(self.dir)], capture_output=True, text=True)

    def test_mount_roots_cover_volumes(self):
        result = self.check(**{"a.container": GOOD, "x.network": "[Network]\n"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_volume_outside_the_roots_fails(self):
        bad = GOOD.replace("/var/lib/appdata /var/mnt/projects", "/var/lib/appdata")
        result = self.check(**{"a.container": bad})
        self.assertEqual(result.returncode, 1)
        self.assertIn("a.container", result.stdout)
        self.assertIn("/var/mnt/projects/ai", result.stdout)

    def test_prefix_is_not_enough(self):
        bad = "[Container]\nVolume=/var/lib/appdata2/x:/x\n[Service]\nExecStartPre=/usr/local/bin/require-mounts /var/lib/appdata\n"
        self.assertEqual(self.check(**{"a.container": bad}).returncode, 1)

    def test_volume_without_any_mount_check_fails(self):
        result = self.check(**{"a.container": "[Container]\nVolume=/var/lib/appdata/x:/x:z\n"})
        self.assertEqual(result.returncode, 1)
        self.assertIn("no require-mounts", result.stdout)

    def test_exec_condition_counts(self):
        text = "[Container]\nVolume=/var/mnt/backups/vm/x:/dest\n[Service]\nExecCondition=/usr/local/bin/require-mounts /var/mnt/backups\n"
        self.assertEqual(self.check(**{"b.container": text}).returncode, 0)

    def test_generated_services_pass(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import yaml
        from gen_service import generate
        site = yaml.safe_load((ROOT / "tests" / "fixtures" / "site.yaml").read_text())
        for fixture in ("single", "crm", "authentik"):
            with self.subTest(fixture=fixture):
                out = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, out, True)
                spec = yaml.safe_load((ROOT / "tests" / "fixtures" / "services" / f"{fixture}.yaml").read_text())
                generate(spec, site, out)
                # Quadlets from the generator, plus the ones embedded in backup fragments.
                quadlets = out / "q"
                quadlets.mkdir()
                for path in (out / "rendered" / "files").glob("*.container"):
                    shutil.copy(path, quadlets)
                for fragment in (out / "rendered").glob("*-backup-*.bu"):
                    data = yaml.safe_load(fragment.read_text())
                    for entry in data.get("storage", {}).get("files", []):
                        if entry["path"].endswith(".container"):
                            (quadlets / Path(entry["path"]).name).write_text(entry["contents"]["inline"])
                result = subprocess.run(TOOL + [str(quadlets)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
