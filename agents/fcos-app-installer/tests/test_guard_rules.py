"""The agent's guard rules for .opencode/ (its own agents, commands and skills).

The skills hold host scripts the owner runs as root. Review of the skills-setting commit: a shell
command that starts with an allowed word (git status, dig, sha256sum) and then chains a write
into .opencode/ was allowed. The rules deny any shell command that names .opencode/ at all, and
every edit path that reaches .opencode/ in its usual spellings. Guard rails, not a wall: the shell
expands wildcards, quotes and variables after the rules have matched, and the agent runs as the
owner's user (README).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from layout import SKILLS_DIR  # noqa: E402
from test_agent import AGENT, effect  # noqa: E402


class ShellGuardTests(unittest.TestCase):
    def setUp(self):
        self.text = AGENT.read_text()

    def test_no_shell_command_may_name_the_agent_folder(self):
        for command in (
                f"sha256sum x && cp evil {SKILLS_DIR}/adapter-proxmox/scripts/lib.sh",
                f"git status && sed -i s/a/b/ {SKILLS_DIR}/adapter-proxmox/scripts/lib.sh",
                f"dig x ; ln -sf /tmp/x {SKILLS_DIR}/y",
                "git diff && mv x ./.opencode/agents/fcos-app-installer.md",
                "python3 tools/x.py && cd .opencode && cp y skills/z",
                "git log | tee .opencode/commands/add-service.md",
                "git status && cp x .opencode",
                f"git status && dd if=/dev/zero of={SKILLS_DIR}/x",
                f"python3 tools/render.py t v > {SKILLS_DIR}/adapter-proxmox/scripts/lib.sh",
                f"python3 tools/gen_service.py s site {SKILLS_DIR}/x",
                f"bash tools/build-vm.sh {SKILLS_DIR}/x",
                # Separators written right after the folder name (review of the first fixes commit).
                "git status --short;cd .opencode;cp x skills/y",
                "git status --short&&cd .opencode&&cp x skills/y",
                "git status --short\ncd .opencode\ncp x skills/y",
                "git status --short; cd '.opencode'; cp x skills/y",
                "git status --short; (cd .opencode)",
                "git status --short; cd .opencode>/dev/null; cp x skills/y"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_the_scratch_folder_is_not_mistaken_for_it(self):
        # /tmp/opencode/ is the agent's scratch folder: no dot, a different folder.
        for command in ("python3 tools/adapters.py render --role file_server --step s --values /tmp/opencode/v.json",
                        "sha256sum /tmp/opencode/v.json",
                        "python3 tools/adapters.py draft --role file_server --provider x --from /tmp/opencode/r.json"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")


class PromptSaysSoTests(unittest.TestCase):
    def test_the_commits_section_explains_that_git_may_not_name_the_agent_folder(self):
        prompt = " ".join(AGENT.read_text().split("## Commits", 1)[1].split("\n## ", 1)[0].split())
        self.assertIn("may not name `.opencode/`", prompt)
        self.assertIn("git add -A", prompt)


class EditGuardTests(unittest.TestCase):
    def setUp(self):
        self.text = AGENT.read_text()

    def test_agents_commands_and_config_are_denied_however_the_path_is_written(self):
        for path in (".opencode/agents/fcos-app-installer.md", "./.opencode/agents/fcos-app-installer.md",
                     "/home/x/AI/toolkit/.opencode/commands/add-service.md", "./.opencode/opencode.json",
                     ".opencode/agents/adapter-drafter.md"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "deny")

    def test_a_path_that_climbs_out_of_a_folder_is_denied(self):
        # A path through the skills folder and back up must not borrow the skills' ask rule.
        for path in (f"{SKILLS_DIR}/../agents/fcos-app-installer.md", f"{SKILLS_DIR}/../opencode.json",
                     f"./{SKILLS_DIR}/../commands/add-service.md", "/tmp/opencode/../x",
                     "docs/../.opencode/agents/adapter-drafter.md"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "deny")

    def test_the_skills_still_ask_however_the_path_is_written(self):
        for path in (f"{SKILLS_DIR}/adapter-x/SKILL.md", f"./{SKILLS_DIR}/adapter-x/SKILL.md",
                     f"/home/x/AI/toolkit/{SKILLS_DIR}/adapter-x/scripts/lib.sh"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "ask")


if __name__ == "__main__":
    unittest.main()
