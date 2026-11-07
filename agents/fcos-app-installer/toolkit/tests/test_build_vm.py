"""tools/build-vm.sh checks that need no container runtime."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = """variant: fcos
version: 1.7.0
ignition:
  config:
    merge:
{entries}
"""


class MergeOrderTests(unittest.TestCase):
    def run_build(self, fragments):
        vm = Path(tempfile.mkdtemp()) / "apps"
        vm.mkdir()
        self.addCleanup(shutil.rmtree, vm.parent, True)
        entries = "\n".join(f"      - local: igns/{f}.ign" for f in fragments)
        (vm / "config.bu").write_text(CONFIG.format(entries=entries))
        # A PATH with only the tools the early checks use: the script stops at
        # "need podman or docker", never pulling images inside a unit test.
        bin_dir = vm.parent / "bin"
        bin_dir.mkdir()
        for tool in ("bash", "grep", "sed", "realpath", "basename", "find"):
            (bin_dir / tool).symlink_to(shutil.which(tool))
        return subprocess.run([str(bin_dir / "bash"), str(ROOT / "tools" / "build-vm.sh"), str(vm)],
                              capture_output=True, text=True, timeout=60, env={"PATH": str(bin_dir)})

    def test_a_folder_with_no_butane_fragments_is_refused_and_nothing_is_deleted(self):
        vm = Path(tempfile.mkdtemp()) / "apps"
        (vm / "igns").mkdir(parents=True)
        (vm / "igns" / "keep.ign").write_text("{}")
        self.addCleanup(shutil.rmtree, vm.parent, True)
        bin_dir = vm.parent / "bin"
        bin_dir.mkdir()
        for tool in ("bash", "grep", "sed", "realpath", "basename", "find"):
            (bin_dir / tool).symlink_to(shutil.which(tool))
        result = subprocess.run([str(bin_dir / "bash"), str(ROOT / "tools" / "build-vm.sh"), str(vm)],
                                capture_output=True, text=True, timeout=60, env={"PATH": str(bin_dir)})
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("no Butane fragments", result.stdout)
        self.assertTrue((vm / "igns" / "keep.ign").exists())

    def test_config_without_entries_says_why(self):
        result = self.run_build([])
        self.assertEqual(result.returncode, 1)
        self.assertIn("found: nothing", result.stdout)

    def test_base_config_must_merge_first(self):
        # Ignition creates users in merge order and useradd gives the admin the
        # next UID above every existing user: base-config first keeps it at 1000/1001.
        result = self.run_build(["authentik", "base-config", "firewall"])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("base-config", result.stdout)
        self.assertIn("first", result.stdout)

    def test_base_config_first_passes_the_order_check(self):
        result = self.run_build(["base-config", "authentik", "firewall"])
        self.assertNotIn("merge order", result.stdout + result.stderr)
        self.assertIn("need podman or docker", result.stderr)


if __name__ == "__main__":
    unittest.main()
