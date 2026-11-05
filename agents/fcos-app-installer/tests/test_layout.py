"""Where the skills sit is one setting, tools/layout.py SKILLS_DIR; nothing else spells the path.

OpenCode treats a folder holding SKILL.md as one skill and does not look inside it for
more (OpenCode V2 Skills docs), so every skill must be a direct child of the skills
folder, never nested in another skill and never in the toolkit's own folder.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRATCH = Path(os.environ.get("TMPDIR", "/tmp/opencode"))
sys.path.insert(0, str(ROOT / "tools"))

SKILL_PATH = re.compile(r"\.(?:agents|claude|opencode)/skills")
SKILL_PIECES = re.compile(r"""["']\.(?:agents|claude|opencode)["']\s*/\s*["']skills["']""")
SKIP_DIRS = {"__pycache__", ".git"}
SETTING_FILES = {ROOT / "tools" / "layout.py", ROOT / "tests" / "test_layout.py"}


def text_files():
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in names:
            path = Path(base) / name
            try:
                yield path, path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue


class SettingTests(unittest.TestCase):
    def test_one_module_holds_the_setting(self):
        import layout
        self.assertEqual(layout.SKILLS_DIR, ".opencode/skills")
        self.assertEqual(layout.SKILLS, ROOT / layout.SKILLS_DIR)

    def test_adapters_read_the_setting(self):
        import adapters
        import layout
        self.assertEqual(adapters.ADAPTERS, layout.SKILLS)

    def test_no_file_spells_the_skills_path_but_the_setting(self):
        import layout
        spelled = []
        for path, text in text_files():
            if path in SETTING_FILES:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                for found in SKILL_PATH.findall(line):
                    # Code imports the setting; prose (docs, prompts, shell comments) may quote it, exactly.
                    if path.suffix == ".py" or found != layout.SKILLS_DIR:
                        spelled.append(f"{path.relative_to(ROOT)}:{number}: {found}")
                if path.suffix == ".py":
                    spelled += [f"{path.relative_to(ROOT)}:{number}: {found}" for found in SKILL_PIECES.findall(line)]
        self.assertEqual(spelled, [])


class SiblingSkillTests(unittest.TestCase):
    def test_every_skill_is_a_direct_child_of_the_skills_folder(self):
        import layout
        found = sorted(layout.SKILLS.rglob("SKILL.md"))
        self.assertGreaterEqual(len(found), 6)
        for path in found:
            with self.subTest(skill=str(path.relative_to(ROOT))):
                self.assertEqual(path.parent.parent, layout.SKILLS)

    def test_the_toolkit_folder_is_not_itself_a_skill(self):
        import layout
        folder = ROOT
        for part in Path(layout.SKILLS_DIR).parts:
            self.assertFalse((folder / "SKILL.md").exists(), folder)
            folder = folder / part
        self.assertFalse((folder / "SKILL.md").exists(), folder)


class DraftFollowsTheSettingTests(unittest.TestCase):
    def draft(self):
        ws = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, ws, True)
        (ws / "site.yaml").write_text("{}\n")
        recorded = ws / "recorded.json"
        recorded.write_text('[{"id": "nfs_export", "title": "Share", "steps": ["Allow {{VM_IP}}."], '
                            '"uses": ["VM_IP"], "report_back": ["done"]}]')
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "adapters.py"), "draft", "--role",
                                 "file_server", "--provider", "synology", "--from", str(recorded),
                                 "--workspace", str(ws)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return ws / "adapters-draft" / "adapter-synology"

    def test_the_drafted_skill_says_where_it_goes(self):
        import layout
        text = (self.draft() / "SKILL.md").read_text()
        self.assertIn(layout.SKILLS_DIR, text)

    def test_the_drafted_test_holds_no_absolute_toolkit_path(self):
        import layout
        text = (self.draft() / "test_synology.py").read_text()
        self.assertNotIn(str(ROOT), text)
        self.assertNotIn("/home/", text)
        self.assertIn(layout.SKILLS_DIR, text)

    def test_the_drafted_test_needs_the_toolkit_named_when_it_is_still_a_draft(self):
        folder = self.draft()
        env = {k: v for k, v in os.environ.items() if k != "FCOS_AGENT_ROOT"}
        result = subprocess.run([sys.executable, str(folder / "test_synology.py")], capture_output=True,
                                text=True, env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FCOS_AGENT_ROOT", result.stdout + result.stderr)

    def test_the_drafted_test_finds_the_toolkit_once_moved_into_the_skills_folder(self):
        import layout
        folder = self.draft()
        toolkit = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, toolkit, True)
        (toolkit / "tools").symlink_to(ROOT / "tools")
        skills = toolkit / layout.SKILLS_DIR
        skills.mkdir(parents=True)
        moved = skills / "adapter-synology"
        shutil.copytree(folder, moved)
        env = {k: v for k, v in os.environ.items() if k != "FCOS_AGENT_ROOT"}
        result = subprocess.run([sys.executable, str(moved / "test_synology.py")], capture_output=True,
                                text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
