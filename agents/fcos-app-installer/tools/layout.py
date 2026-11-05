"""Where the toolkit's pieces sit in the folder OpenCode is started in.

SKILLS_DIR is the one setting for the skills folder, relative to the toolkit's folder. Tools
and tests import it from here; prompts and docs quote it exactly, and tests/test_layout.py
fails on any other spelling. Every skill is a direct child of this folder: OpenCode treats a
folder holding SKILL.md as one skill and does not look inside it for more.
"""
from pathlib import Path

TOOLKIT_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ".opencode/skills"
SKILLS = TOOLKIT_ROOT / SKILLS_DIR
