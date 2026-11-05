import base64
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "make_cidata_iso.sh"
IMAGE = next(line.split("=", 1)[1] for line in (ROOT / "tools" / "images.env").read_text().splitlines()
             if line.startswith("PODMAN_IMAGE="))
RUNTIME = shutil.which("podman") or shutil.which("docker")


def image_present() -> bool:
    if not RUNTIME:
        return False
    result = subprocess.run([RUNTIME, "image", "inspect", IMAGE], capture_output=True, timeout=60)
    return result.returncode == 0


NO_CONTAINER = (None if image_present() else
                f"needs podman or docker with the image {IMAGE} already pulled (nothing is downloaded for you)")

# No trailing newline and a non-ASCII character, so byte-identity means something.
IGNITION = '{"ignition":{"version":"3.6.0"},"passwd":{"users":[{"name":"x\u00e9"}]}}'.encode()


class ScriptArgumentTests(unittest.TestCase):
    """No container needed: these fail before one is started."""

    def run_script(self, *args):
        return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, timeout=60)

    def test_usage_error(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage", result.stderr)

    def test_missing_input_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script(str(Path(tmp) / "nope.ign"), str(Path(tmp) / "out.iso"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a readable file", result.stderr)

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            ign = Path(tmp) / "vm.ign"
            ign.write_bytes(IGNITION)
            out = Path(tmp) / "out.iso"
            out.write_bytes(b"keep me")
            result = self.run_script(str(ign), str(out))
            self.assertEqual(result.returncode, 2)
            self.assertIn("already exists", result.stderr)
            self.assertEqual(out.read_bytes(), b"keep me")


@unittest.skipIf(NO_CONTAINER, NO_CONTAINER or "")
class IsoLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls._tmp.cleanup)
        cls.dir = Path(cls._tmp.name)
        cls.ign = cls.dir / "vm.ign"
        cls.ign.write_bytes(IGNITION)
        cls.iso = cls.dir / "out.iso"
        cls.build = subprocess.run(["bash", str(SCRIPT), str(cls.ign), str(cls.iso)],
                                   capture_output=True, text=True, timeout=600)

    def read_back(self):
        """Volume label, user-data bytes and meta-data size, read in the same container image."""
        inner = (
            "dnf -y install xorriso >/dev/null 2>&1; "
            "xorriso -osirrox on -indev /iso/out.iso -pvd_info -extract /user-data /tmp/ud "
            "-extract /meta-data /tmp/md 2>/dev/null | grep '^Volume Id'; "
            "echo UD=$(base64 -w0 /tmp/ud); echo MD=$(wc -c < /tmp/md)")
        result = subprocess.run(
            [RUNTIME, "run", "--rm", "--pull=never", "--user", "root", "-v", f"{self.dir}:/iso:ro,z", IMAGE,
             "sh", "-c", inner], capture_output=True, text=True, timeout=600)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_iso_layout(self):
        self.assertEqual(self.build.returncode, 0, self.build.stderr)
        self.assertTrue(self.iso.is_file())
        shown = self.read_back()
        self.assertRegex(shown, r"(?m)^Volume Id\s*: cidata$")
        lines = dict(line.split("=", 1) for line in shown.splitlines() if line.startswith(("UD=", "MD=")))
        self.assertEqual(base64.b64decode(lines["UD"]), IGNITION)
        self.assertEqual(lines["MD"].strip(), "0")

    def test_input_is_unchanged_and_only_the_output_is_created(self):
        self.assertEqual(self.ign.read_bytes(), IGNITION)
        self.assertEqual(sorted(p.name for p in self.dir.iterdir()), ["out.iso", "vm.ign"])


if __name__ == "__main__":
    sys.exit(unittest.main())
