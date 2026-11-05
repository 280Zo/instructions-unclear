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
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None
sys.path.insert(0, str(ROOT / "tools"))

SKILL_PATH = re.compile(r"\.(?:agents|claude|opencode)/skills")
SKILL_PIECES = re.compile(r"""["']\.(?:agents|claude|opencode)["']\s*(?:/|,)\s*["']skills["']""")
SKIP_DIRS = {"__pycache__", ".git"}
# The folders OpenCode V2 reads project skills from (its Skills docs).
PROJECT_SKILL_SOURCES = {".opencode/skills", ".claude/skills", ".agents/skills"}
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
        self.assertIn(layout.SKILLS_DIR, PROJECT_SKILL_SOURCES)  # a folder OpenCode really reads
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
        found = sorted(layout.SKILLS.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(found), 6)
        for path in found:
            with self.subTest(skill=str(path.relative_to(ROOT))):
                self.assertEqual(path.parent.parent, layout.SKILLS)

    def test_no_skill_exists_anywhere_else_in_the_toolkit(self):
        # A SKILL.md nested in another skill, or in any other folder OpenCode reads skills from
        # (.claude/skills, .agents/skills), would register a second skill or shadow an adapter.
        import layout
        expected = {layout.SKILLS / p.parent.name / "SKILL.md" for p in layout.SKILLS.glob("*/SKILL.md")}
        stray = []
        for base, dirs, names in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            stray += [Path(base) / n for n in names if n.lower() == "skill.md" and Path(base) / n not in expected]
        self.assertEqual([str(p.relative_to(ROOT)) for p in stray], [])

    def test_the_skills_folder_holds_only_skill_folders(self):
        # OpenCode reads a loose *.md at the root of a skills folder as a skill of its own.
        import layout
        loose = [p.name for p in layout.SKILLS.iterdir() if not (p.is_dir() and (p / "SKILL.md").is_file())]
        self.assertEqual(loose, [])

    def test_no_other_project_skill_source_exists(self):
        for source in PROJECT_SKILL_SOURCES - {Path(sys.modules["layout"].SKILLS_DIR).as_posix()}:
            with self.subTest(source=source):
                self.assertFalse((ROOT / source).exists())

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

    def run_drafted(self, test, **env):
        clean = {k: v for k, v in os.environ.items() if k != "FCOS_AGENT_ROOT"}
        return subprocess.run([sys.executable, str(test)], capture_output=True, text=True, env=dict(clean, **env))

    def test_a_wrong_toolkit_folder_is_named_not_a_traceback(self):
        folder = self.draft()
        empty = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, empty, True)
        result = self.run_drafted(folder / "test_synology.py", FCOS_AGENT_ROOT=str(empty))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not the toolkit's folder", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_a_skills_folder_of_another_project_is_not_taken_for_the_toolkit(self):
        import layout
        folder = self.draft()
        project = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, project, True)
        moved = project / layout.SKILLS_DIR / "adapter-synology"
        shutil.copytree(folder, moved)
        result = self.run_drafted(moved / "test_synology.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not the toolkit's folder", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_the_path_arithmetic_holds_for_any_depth_of_the_setting(self):
        import adapters
        folder = self.draft()
        for skills_dir in ("skills", ".opencode/skills", "a/b/skills"):
            with self.subTest(skills_dir=skills_dir):
                toolkit = Path(tempfile.mkdtemp(dir=SCRATCH))
                self.addCleanup(shutil.rmtree, toolkit, True)
                (toolkit / "tools").symlink_to(ROOT / "tools")
                moved = toolkit / skills_dir / "adapter-synology"
                shutil.copytree(folder, moved)
                (moved / "test_synology.py").write_text(adapters.TEST_TEMPLATE.format(
                    skills_dir=skills_dir, role="file_server", provider="synology"))
                result = self.run_drafted(moved / "test_synology.py")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
