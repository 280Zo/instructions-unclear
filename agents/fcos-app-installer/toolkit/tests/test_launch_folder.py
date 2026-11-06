"""OpenCode is started in the toolkit's own folder, and everything resolves from there.

The agent's allow rules (python3 tools/*, bash tools/*), its guard rules, the commands in the
prompts and the guide, and the AGENTS.md OpenCode loads are all relative to the folder it is
started in. They hold only when the launch folder is the folder that holds tools/, AGENTS.md,
docs/ and .opencode/. These tests read that installed layout and check every such path against
it. They assert the allow rules; the deny and ask rules are in test_agent.py and
test_guard_rules.py.
"""
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

from layout import SKILLS_DIR  # noqa: E402

# "python3 tools/x.py", "python3 ./tools/x.py" and "python3 $dir/tools/x.py" all name a tool.
TOOL_COMMAND = re.compile(r"\b(?:python3|bash) (?:\./|\$\w+/)?(tools/[A-Za-z0-9_.-]+\.(?:py|sh))")
FOLDER_PATH = re.compile(r"(?<![\w/<>.~$-])((?:docs/guide|rules|templates|schemas|specs|tools|tests|"
                         + re.escape(SKILLS_DIR) + r")/[A-Za-z0-9_./-]*\.(?:md|yaml|tmpl|py|sh|values|env))")


# Targets a trial-run row tries to write and expects to be refused: they must not exist.
REFUSED_EXAMPLES = {f"{SKILLS_DIR}/x.md"}


def instruction_files():
    folders = [ROOT / ".opencode" / "agents", ROOT / ".opencode" / "commands", SKILLS,
               ROOT / "docs" / "guide"]
    files = [ROOT / "README.md", ROOT / "AGENTS.md"]
    for folder in folders:
        files += sorted(p for p in folder.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml"})
    # The tools quote paths and commands in their messages and usage text too.
    files += sorted(p for p in (ROOT / "tools").iterdir() if p.suffix in {".py", ".sh"})
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
                if named in REFUSED_EXAMPLES:
                    continue
                seen += 1
                with self.subTest(file=str(path.relative_to(ROOT)), named=named):
                    self.assertTrue((ROOT / named).is_file())
        self.assertGreater(seen, 30)

    def test_the_rules_file_is_in_the_launch_folder(self):
        # OpenCode loads AGENTS.md from the folder it is started in (and above); rulesync writes the
        # toolkit's rules there. A path to a rules/ file would not resolve: that folder stays in the repo.
        self.assertTrue((ROOT / "AGENTS.md").is_file())
        self.assertFalse((ROOT / "rules").exists())

    def test_the_allow_rules_are_relative_to_the_launch_folder(self):
        text = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        allowed = [r for a, r, e in rules(text) if a == "shell" and e == "allow" and "tools/" in r]
        self.assertIn("python3 tools/*", allowed)
        self.assertIn("bash tools/*", allowed)
        for pattern in allowed:
            with self.subTest(pattern=pattern):
                self.assertRegex(pattern, r"^(?:python3|bash) tools/")
        # Started anywhere else, the same command line is not an allowed tool run.
        self.assertEqual(effect(text, "shell", "python3 /elsewhere/tools/hypervisor.py list"), "ask")

    def test_the_run_starts_by_checking_the_launch_folder(self):
        prompt = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        step = " ".join(prompt.split("1. **Where to keep the files.**", 1)[1]
                        .split("2. **Earlier installs.**", 1)[0].split())
        self.assertIn("python3 tools/check_requirements.py", step)
        self.assertIn("launch folder", step)
        # Started in a subfolder, OpenCode still loads the agent but the relative command finds no
        # tool, so Python prints an error and no launch folder line: that case must stop the run too.
        self.assertIn("can't find `tools/check_requirements.py`", step)
        self.assertIn("stop", step)
        self.assertIn("do nothing else", step)
        # The check comes before the first question.
        self.assertLess(step.index("python3 tools/check_requirements.py"), step.index("Where should I keep"))

    def test_started_in_a_subfolder_the_command_the_agent_runs_cannot_find_the_tool(self):
        # What the prompt's step answers: the allowed relative command fails loudly, not silently.
        result = subprocess.run([sys.executable, "tools/check_requirements.py"], cwd=ROOT / "docs",
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("can't open file", result.stderr)

    def test_the_add_service_command_starts_with_the_same_check(self):
        text = " ".join((ROOT / ".opencode" / "commands" / "add-service.md").read_text().split())
        self.assertIn("requirement check", text)
        self.assertLess(text.index("requirement check"), text.index("asking where the workspace is"))

    def test_the_readme_says_where_to_start_opencode(self):
        readme = " ".join((ROOT / "README.md").read_text().split())
        self.assertIn("Start OpenCode in the toolkit's folder, the one that holds `tools/`", readme)
        install = " ".join(readme.split("## Install", 1)[1].split("\n## ", 1)[0].split())
        self.assertNotIn("project folder", install)
        self.assertIn("toolkit's folder", install)
        # The install must not send you to run the toolkit inside a clone of another repository: that
        # clone's own AGENTS.md and skills would load into every session (README, OpenCode versions and where it looks).
        self.assertNotIn("Clone this repository", install)
        self.assertIn("folder of its own", install)
        # OpenCode searches AGENTS.md and project skills from the launch folder upward: to the git
        # root, or to the home folder when the launch folder is under it.
        segment = " ".join(readme.split("(searched upward", 1)[1].split("The agents' skill and subagent", 1)[0].split())
        for needle in ("git root", "home folder", "skills"):
            with self.subTest(needle=needle):
                self.assertIn(needle, segment)
        # The rules are no longer loaded through the config's instructions list.
        self.assertNotIn("opencode.json", readme)
        self.assertNotIn("`instructions`", readme)

    def test_the_guide_tells_a_person_where_to_run_its_commands(self):
        guide = " ".join((ROOT / "docs" / "guide" / "README.md").read_text().split())
        self.assertIn("from the toolkit's folder", guide)
        self.assertNotIn("from this repository", guide)

    def test_the_rules_lookup_is_recorded_with_its_source(self):
        readme = " ".join((ROOT / "README.md").read_text().split())
        section = readme.split("### OpenCode versions and where it looks", 1)[1].split("\n## ", 1)[0]
        self.assertIn("v2.1.3/packages/core/src/config/plugin/instruction.ts", section)
        self.assertIn("home folder", section)  # AGENTS.md stops at home, not the git root, under home
        self.assertIn("opencode.ai/v2/docs/skills", section)  # project skills are searched upward as well


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
