"""The pinned list of host-script checksums (host-scripts.sha256).

The owner runs the adapters' host scripts as root, after checking the checksum a step shows.
The step takes that checksum from the script itself, so a changed script would pass the owner's
check; the pinned list, which the agent's rules keep it from editing, is what makes the tool refuse
it. The list
is in `sha256sum -c` format, outside every skill folder, with paths relative to the skills folder.
"""
import hashlib
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from layout import CHECKSUMS, SKILLS, SKILLS_DIR  # noqa: E402
from test_agent import AGENT, effect  # noqa: E402
from test_drafter import DRAFTER  # noqa: E402

LINE = re.compile(r"^([0-9a-f]{64})  (adapter-[a-z0-9-]+/scripts/[A-Za-z0-9._-]+)$")


def shipped_scripts() -> dict[str, str]:
    return {p.relative_to(SKILLS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(SKILLS.glob("*/scripts/*")) if p.is_file()}


class PinnedListTests(unittest.TestCase):
    def test_the_list_sits_at_the_toolkit_root_outside_every_skill_folder(self):
        self.assertEqual(CHECKSUMS, ROOT / "host-scripts.sha256")
        self.assertTrue(CHECKSUMS.is_file())
        self.assertNotIn(SKILLS, CHECKSUMS.parents)

    def test_every_line_is_in_sha256sum_format_and_sorted(self):
        lines = CHECKSUMS.read_text().splitlines()
        self.assertTrue(lines)
        for line in lines:
            with self.subTest(line=line):
                self.assertRegex(line, LINE)
        self.assertEqual(lines, sorted(lines, key=lambda l: l.split("  ")[1]))

    def test_the_list_is_exactly_the_shipped_scripts(self):
        listed = dict(reversed(LINE.match(l).groups()) for l in CHECKSUMS.read_text().splitlines())
        shipped = shipped_scripts()
        self.assertGreaterEqual(len(shipped), 4)
        self.assertEqual(sorted(listed), sorted(shipped), "a script is unlisted or a listed script is gone")
        for path, digest in shipped.items():
            with self.subTest(script=path):
                self.assertEqual(listed[path], digest)

    def test_the_readme_says_how_to_change_a_host_script(self):
        readme = " ".join((ROOT / "README.md").read_text().split())
        self.assertIn("host-scripts.sha256", readme)
        self.assertIn("sha256sum -c", readme)
        self.assertIn(SKILLS_DIR, readme)


    def test_every_shipped_script_is_declared_by_its_adapter_so_it_is_pinned(self):
        # A script an adapter does not declare in `scripts:` gets no checksum and no pin check.
        import yaml
        for folder in sorted(SKILLS.glob("*/scripts")):
            adapter = yaml.safe_load((folder.parent / "adapter.yaml").read_text())
            with self.subTest(skill=folder.parent.name):
                present = {p.relative_to(folder.parent).as_posix() for p in folder.iterdir() if p.is_file()}
                self.assertEqual(present, set(adapter.get("scripts", [])))


class HonestWordingTests(unittest.TestCase):
    """The rules are a guard rail: the shell expands quoted and globbed names, and the agent runs as
    the owner's user. No file may say the agent *cannot* edit the list."""

    def test_nothing_claims_a_wall(self):
        for path in (ROOT / "README.md", ROOT / "tools" / "layout.py", ROOT / "tools" / "adapters.py"):
            with self.subTest(file=path.name):
                text = " ".join(path.read_text().split())
                self.assertNotRegex(text, r"(?i)\bagent (?:cannot|can't|can not) edit")

    def test_the_readme_says_it_is_a_guard_rail_and_what_makes_it_hard(self):
        section = " ".join((ROOT / "README.md").read_text().split("## Changing a host script", 1)[1]
                           .split("\n## ", 1)[0].split())
        self.assertIn("guard rail", section)
        self.assertIn("separate user", section)
        self.assertIn("read the change first", section)


class AgentGuardsTheListTests(unittest.TestCase):
    """A guard rail, not a wall: the agent's rules deny edits to the list and any shell command that
    names it, including the quoted, globbed and variable spellings of its name. The agent runs as
    the owner's user, so only a separate user (README) makes this a hard boundary. The agent reads
    the list with its read tool if it needs to."""

    def setUp(self):
        self.text = AGENT.read_text()

    def test_edits_are_denied_for_the_usual_spellings_of_the_path(self):
        for path in ("host-scripts.sha256", "./host-scripts.sha256", "/home/x/toolkit/host-scripts.sha256"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "deny")

    def test_shell_commands_naming_the_list_are_denied(self):
        for command in ("echo x > host-scripts.sha256",
                        f"sha256sum {SKILLS_DIR}/adapter-proxmox/scripts/lib.sh >host-scripts.sha256",
                        "python3 tools/render.py t v | tee host-scripts.sha256",
                        "cp /tmp/opencode/x host-scripts.sha256",
                        "git status && sed -i s/a/b/ host-scripts.sha256",
                        "python3 tools/adapters.py show --role file_server; mv x ./host-scripts.sha256"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_quoted_globbed_and_variable_spellings_of_the_name_are_denied_too(self):
        # Review of the checksum-list commit: the shell expands these to the real file.
        for command in ("sha256sum a > host-scripts.sha\"256\"",
                        "sha256sum a > host-scripts.sha25?",
                        "sha256sum a > host-scripts.sha2*",
                        "sha256sum a > 'host-scripts'.sha256",
                        "sha256sum a > ./*.sha256",
                        "python3 tools/adapters.py show; f=host-scripts; cp /tmp/opencode/x $f.sha256",
                        "python3 tools/adapters.py show; python3 -c \"open('host-scripts'+'.sha256','w')\""):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_the_scratch_and_checksum_commands_the_agent_needs_still_work(self):
        for command in ("sha256sum /tmp/opencode/v.json", "python3 tools/adapters.py show --role file_server",
                        "python3 tools/check_requirements.py"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")

    def test_the_drafter_cannot_edit_or_name_it_either(self):
        drafter = DRAFTER.read_text()
        self.assertEqual(effect(drafter, "edit", "host-scripts.sha256"), "deny")
        for command in ("python3 tools/adapters.py show --role x\ncp /tmp/opencode/x host-scripts.sha256",
                        "python3 tools/adapters.py show --role x\r\ncp /tmp/opencode/x host-scripts.sha256",
                        f"python3 tools/adapters.py show --role x\ncp /tmp/opencode/x {SKILLS_DIR}/adapter-proxmox/scripts/lib.sh",
                        "python3 tools/adapters.py show --role file_server --provider host-scripts.sha\"256\""):
            with self.subTest(command=command):
                self.assertEqual(effect(drafter, "shell", command), "deny")
        # What it is for still works.
        self.assertEqual(effect(drafter, "shell", "python3 tools/adapters.py show --role file_server"), "allow")


if __name__ == "__main__":
    unittest.main()
