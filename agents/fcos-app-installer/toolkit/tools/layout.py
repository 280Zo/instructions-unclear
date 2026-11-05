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
# folder, with their own commands, agents and skills. What is the toolkit's own is fixed here, so
# the checks that are about the toolkit (publish_check's generic rules, the skill-format test)
# skip upstream files they have no say over.
OWN_AGENTS = {"fcos-app-installer.md", "adapter-drafter.md"}
OWN_COMMANDS = {"add-service.md"}


def is_own_skill(name: str) -> bool:
    return name.startswith("adapter-") or name == "researching-apps-for-self-hosting"


def is_companion(relative: Path) -> bool:
    """True for a file rulesync wrote for a companion agent: an agent or command file, or a file
    inside a skill folder, in the installed places and not one of the toolkit's own."""
    parts = relative.parts
    skills = Path(SKILLS_DIR).parts
    if len(parts) == 3 and parts[:2] == (".opencode", "agents"):
        return parts[2] not in OWN_AGENTS
    if len(parts) == 3 and parts[:2] == (".opencode", "commands"):
        return parts[2] not in OWN_COMMANDS
    if len(parts) >= len(skills) + 2 and parts[:len(skills)] == skills:
        return not is_own_skill(parts[len(skills)])
    return False
