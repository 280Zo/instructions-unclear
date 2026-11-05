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
# sha256sum -c list of every host script, paths relative to the skills folder. It stays outside
# every skill folder and the agent's rules deny edits to it; tools/adapters.py refuses a script
# whose hash differs from it.
CHECKSUMS = TOOLKIT_ROOT / "host-scripts.sha256"

# rulesync also installs companion agents (second-opinion, security, plan, explore) into this
# folder, with their own upstream commands, agents and skills. They are listed here by exact name,
# for the owner to pick as main agents (the installer agent starts none of them). The checks that
# are about the toolkit skip only these files: publish_check gives them the workspace-value scan
# alone (their examples hold example secrets), and the skill-format test leaves out their skills.
# Any other name, a new file included, is checked in full. A test in the repository this toolkit is
# kept in fails when these lists differ from what the folder group installs.
COMPANION_AGENTS = frozenset({
    "second-opinion", "evaluator", "metacognitive", "security", "security-auditor",
    "threat-modeling-expert", "plan", "explore",
})
COMPANION_COMMANDS = frozenset({"compliance-check", "security-dependencies", "security-hardening", "security-sast"})
COMPANION_SKILLS = frozenset({
    "attack-tree-construction", "sast-configuration", "security-best-practices",
    "security-requirement-extraction", "stride-analysis-patterns", "threat-mitigation-mapping",
})


def is_companion_skill(name: str) -> bool:
    return name in COMPANION_SKILLS


def is_companion(relative: Path) -> bool:
    """True for a file rulesync wrote for a companion agent: its agent or command file, or a file
    inside its skill folder, under exactly the listed name and in exactly the installed place."""
    parts = relative.parts
    skills = Path(SKILLS_DIR).parts
    if len(parts) == 3 and parts[:2] == (".opencode", "agents"):
        return parts[2].endswith(".md") and parts[2][:-3] in COMPANION_AGENTS
    if len(parts) == 3 and parts[:2] == (".opencode", "commands"):
        return parts[2].endswith(".md") and parts[2][:-3] in COMPANION_COMMANDS
    if len(parts) >= len(skills) + 2 and parts[:len(skills)] == skills:
        return parts[len(skills)] in COMPANION_SKILLS
    return False
