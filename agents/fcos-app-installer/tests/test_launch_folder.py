"""OpenCode is started in the toolkit's own folder, and everything resolves from there.

The agent's allow rules (python3 tools/*, bash tools/*), its guard rules, the commands in the
prompts and the guide, and opencode.json's `instructions` are all relative paths. They hold
only when the launch folder is the folder that holds tools/, rules/, docs/ and .opencode/.
These tests read that installed layout and check every such path against it.
"""
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))

from layout import SKILLS  # noqa: E402
from test_agent import effect, rules  # noqa: E402

TOOL_COMMAND = re.compile(r"\b(?:python3|bash) (tools/[A-Za-z0-9_.-]+\.(?:py|sh))")
FOLDER_PATH = re.compile(r"(?<![\w/<>.~-])((?:docs/guide|rules|templates|schemas|specs|tools)/"
                         r"[A-Za-z0-9_./-]*\.(?:md|yaml|tmpl|py|sh|values|env))")
# Named in prose as optional: read when present.
OPTIONAL = {"docs/superpowers/followups/"}


def instruction_files():
    folders = [ROOT / ".opencode" / "agents", ROOT / ".opencode" / "commands", SKILLS,
               ROOT / "rules", ROOT / "docs" / "guide"]
    files = [ROOT / "README.md"]
    for folder in folders:
        files += sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml"})
    return files


class LaunchFolderTests(unittest.TestCase):
    def test_every_tool_command_resolves_from_the_launch_folder(self):
        seen = 0
        for path in instruction_files():
            for command in TOOL_COMMAND.findall(path.read_text(encoding="utf-8")):
                seen += 1
                with self.subTest(file=str(path.relative_to(ROOT)), command=command):
                    self.assertTrue((ROOT / command).is_file())
        self.assertGreater(seen, 30)

    def test_every_folder_path_named_in_the_instructions_resolves(self):
        seen = 0
        for path in instruction_files():
            for named in FOLDER_PATH.findall(path.read_text(encoding="utf-8")):
                seen += 1
                with self.subTest(file=str(path.relative_to(ROOT)), named=named):
                    self.assertTrue((ROOT / named).is_file())
        self.assertGreater(seen, 30)

    def test_the_instruction_globs_match_rule_files_from_the_launch_folder(self):
        config = json.loads((ROOT / ".opencode" / "opencode.json").read_text())
        self.assertTrue(config["instructions"])
        for pattern in config["instructions"]:
            with self.subTest(pattern=pattern):
                self.assertFalse(pattern.startswith("/") or pattern.startswith(".."), pattern)
                matched = [p for p in ROOT.rglob("*.md") if fnmatch.fnmatch(str(p.relative_to(ROOT)), pattern)]
                self.assertTrue(matched)

    def test_the_allow_rules_are_relative_to_the_launch_folder(self):
        text = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        allowed = [r for a, r, e in rules(text) if a == "shell" and e == "allow" and "tools/" in r]
        self.assertIn("python3 tools/*", allowed)
        self.assertIn("bash tools/*", allowed)
        for pattern in allowed:
            with self.subTest(pattern=pattern):
                self.assertRegex(pattern, r"^(?:python3|bash) tools/")
        # Started anywhere else, the same command line is not an allowed tool run.
        self.assertEqual(effect(text, "shell", "python3 /elsewhere/tools/pve.py list"), "ask")

    def test_the_run_starts_by_checking_the_launch_folder(self):
        prompt = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        step = prompt.split("1. **Where to keep the files.**", 1)[1].split("2. **Earlier installs.**", 1)[0]
        self.assertIn("python3 tools/check_requirements.py", step)
        self.assertIn("launch folder", step)

    def test_the_readme_says_where_to_start_opencode(self):
        readme = " ".join((ROOT / "README.md").read_text().split()).lower()
        self.assertIn("start opencode in the toolkit's folder", readme)


class CheckRequirementsLaunchFolderTests(unittest.TestCase):
    def run_tool(self, cwd):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "check_requirements.py")], cwd=cwd,
                              capture_output=True, text=True)

    def test_started_in_the_toolkit_folder_is_ok(self):
        line = next(l for l in self.run_tool(ROOT).stdout.splitlines() if "launch folder" in l)
        self.assertTrue(line.startswith("ok"), line)

    def test_started_anywhere_else_fails_and_names_the_folder(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as other:
            result = self.run_tool(other)
        line = next(l for l in result.stdout.splitlines() if "launch folder" in l)
        self.assertTrue(line.startswith("FAIL"), line)
        self.assertIn(str(ROOT), line)
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
