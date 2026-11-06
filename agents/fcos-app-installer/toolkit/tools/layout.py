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
# An adapter skill is named <prefix>-<product> after the role it fills (hypervisor-proxmox);
# adapter-generic is the provider-neutral fallback for every role.
ADAPTER_PREFIX = {"virtualization": "hypervisor", "router_firewall": "router", "file_server": "fileserver",
                  "dns_certificates": "dns"}


def adapter_skill(role: str, provider: str) -> str:
    """The skill folder name of the adapter for a role and provider."""
    return f"{ADAPTER_PREFIX[role]}-{provider}"
