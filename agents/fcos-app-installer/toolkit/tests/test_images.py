"""The desktop-side container images: pinned by tag and digest in one file,
never pulled by a tool, and checked for updates by tools/check_updates.py."""
import io
import json
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

PINNED = re.compile(r"^quay\.io/[a-z0-9/_-]+:v[0-9][0-9A-Za-z.-]*@sha256:[0-9a-f]{64}$")


def pins() -> dict:
    out = {}
    for line in (ROOT / "tools" / "images.env").read_text().splitlines():
        if line and not line.startswith("#"):
            key, value = line.split("=", 1)
            out[key] = value
    return out


class PinTests(unittest.TestCase):
    def test_both_images_are_pinned_by_tag_and_digest(self):
        self.assertEqual(set(pins()), {"BUTANE_IMAGE", "PODMAN_IMAGE"})
        for key, ref in pins().items():
            with self.subTest(key=key):
                self.assertRegex(ref, PINNED)

    def test_tools_use_the_pins_and_never_pull(self):
        for script in ("build-vm.sh", "make_cidata_iso.sh"):
            text = (ROOT / "tools" / script).read_text()
            with self.subTest(script=script):
                self.assertIn("images.env", text)
                self.assertNotIn("quay.io/", text.split("images.env", 1)[1])  # no image named after the pins load
                runs = [l for l in text.splitlines() if re.search(r'"\$runtime" run\b|"\$runtime" run ', l)]
                self.assertTrue(runs)
                for line in runs:
                    self.assertIn("--pull=never", line)
                self.assertIn("pull", text.split("image inspect", 1)[1].split("\n", 3)[1])  # tells the user


class MissingPinTests(unittest.TestCase):
    """A missing pin made the scripts exit without a word."""

    def test_missing_pin_says_so(self):
        import shutil
        import subprocess
        import tempfile
        tmp = Path(tempfile.mkdtemp(prefix="pins-"))
        self.addCleanup(shutil.rmtree, tmp, True)
        tools = tmp / "tools"
        tools.mkdir()
        for name in ("build-vm.sh", "make_cidata_iso.sh"):
            shutil.copy(ROOT / "tools" / name, tools / name)
        (tools / "images.env").write_text("# no pins here\n")
        stub = tmp / "bin"
        stub.mkdir()
        (stub / "docker").write_text("#!/bin/sh\nexit 0\n")
        (stub / "docker").chmod(0o755)
        vm = tmp / "vm"
        vm.mkdir()
        env = {"PATH": f"{stub}:/usr/bin:/bin", "HOME": str(tmp)}
        build = subprocess.run(["bash", str(tools / "build-vm.sh"), str(vm)], capture_output=True, text=True,
                               env=env, timeout=60)
        self.assertNotEqual(build.returncode, 0)
        self.assertIn("missing in tools/images.env", build.stderr)
        ign = tmp / "x.ign"
        ign.write_text("{}")
        iso = subprocess.run(["bash", str(tools / "make_cidata_iso.sh"), str(ign), str(tmp / "x.iso")],
                             capture_output=True, text=True, env=env, timeout=60)
        self.assertNotEqual(iso.returncode, 0)
        self.assertIn("missing in tools/images.env", iso.stderr)


class CheckUpdatesTests(unittest.TestCase):
    def run_check(self, tags_by_repo):
        import check_updates
        saved = check_updates.fetch_tags
        check_updates.fetch_tags = lambda repo: tags_by_repo[repo]
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = check_updates.main([])
        finally:
            check_updates.fetch_tags = saved
        return code, out.getvalue()

    def current(self):
        tags = {}
        for ref in pins().values():
            name, digest = ref.split("@")
            repo, tag = name[len("quay.io/"):].rsplit(":", 1)
            tags[repo] = [{"name": tag, "manifest_digest": digest, "last_modified": "Mon, 12 Oct 2026 18:57:14 -0000"}]
        return tags

    def test_up_to_date(self):
        code, out = self.run_check(self.current())
        self.assertEqual(code, 0)
        self.assertIn("| Image | Pinned | Newest release | Status |", out)
        self.assertEqual(out.count("up to date"), 2)

    def test_newer_release_and_rebuilt_tag_are_reported(self):
        tags = self.current()
        butane = next(r for r in tags if "butane" in r)
        podman = next(r for r in tags if "podman" in r)
        tags[butane].append({"name": "v9.0.0", "manifest_digest": "sha256:" + "a" * 64,
                             "last_modified": "Tue, 03 Nov 2026 10:00:00 -0000"})
        tags[butane].append({"name": "v9.1.0-rc1", "manifest_digest": "sha256:" + "b" * 64, "last_modified": "x"})
        tags[podman][0]["manifest_digest"] = "sha256:" + "c" * 64
        tags[podman].append({"name": "v99.0.0-immutable", "manifest_digest": "sha256:" + "d" * 64, "last_modified": "x"})
        code, out = self.run_check(tags)
        self.assertEqual(code, 10)  # updates available
        self.assertIn("v9.0.0", out)
        self.assertNotIn("v9.1.0-rc1", out)  # pre-releases are not offered
        self.assertNotIn("v99.0.0", out)  # -immutable twins are not separate releases
        self.assertIn("newer release", out)
        self.assertIn("rebuilt", out)

    def test_network_failure_is_reported_not_hidden(self):
        import check_updates
        saved = check_updates.fetch_tags

        def boom(repo):
            raise OSError("offline")
        check_updates.fetch_tags = boom
        out = io.StringIO()
        try:
            with redirect_stdout(out):
                code = check_updates.main([])
        finally:
            check_updates.fetch_tags = saved
        self.assertEqual(code, 1)
        self.assertIn("couldn't check", out.getvalue())


class DocsTests(unittest.TestCase):
    def test_readme_says_how_to_update(self):
        readme = (ROOT / "README.md").read_text()
        section = readme.split("## Updating", 1)[1].split("\n## ", 1)[0]
        text = " ".join(section.split())
        for needle in ("python3 tools/check_updates.py", "tools/images.env", "official release notes",
                       "relies on it", "test-first", "10-trial-run.md",
                       "For the agent", "For a person"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)

    def test_prompt_checks_before_the_task(self):
        prompt = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        self.assertIn("python3 tools/check_updates.py", prompt)
        self.assertLess(prompt.index("python3 tools/check_updates.py"), prompt.index("2. **Earlier installs.**"))


if __name__ == "__main__":
    unittest.main()
