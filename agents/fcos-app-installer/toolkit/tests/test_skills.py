"""The toolkit's skills (<skills folder>/<id>/SKILL.md, owner 2026-11-04).

Format: the Agent Skills specification (agentskills.io/specification) and OpenCode V2
(opencode.ai/v2/docs/skills): name 1-64 lowercase letters, digits and single hyphens,
equal to its folder; description 1-1024 characters, saying what and when.
"""
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from layout import SKILLS, is_companion_skill  # noqa: E402
from adapters import ROLE_STEPS, AdapterError, load_adapter  # noqa: E402

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ADAPTERS = {"proxmox": "virtualization", "opnsense": "router_firewall", "truenas": "file_server",
            "duckdns": "dns_certificates"}


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    head, body = text[4:].split("\n---\n", 1)
    return yaml.safe_load(head), body


class SkillFormatTests(unittest.TestCase):
    def test_every_skill_follows_the_spec(self):
        # Every skill but the companion agents' upstream ones, which sit beside ours (tools/layout.py).
        skills = sorted(p for p in SKILLS.glob("*/SKILL.md") if not is_companion_skill(p.parent.name))
        self.assertGreaterEqual(len(skills), 5)
        for path in skills:
            with self.subTest(skill=path.parent.name):
                meta, body = frontmatter(path)
                self.assertEqual(meta["name"], path.parent.name)
                self.assertRegex(meta["name"], NAME)
                self.assertLessEqual(len(meta["name"]), 64)
                self.assertTrue(0 < len(meta["description"]) <= 1024)
                self.assertIn("Use when", meta["description"])
                self.assertLessEqual(set(meta), {"name", "description", "license", "compatibility", "metadata"})
                self.assertLess(len(body.splitlines()), 500)

    def test_old_folders_are_gone(self):
        self.assertFalse((ROOT / "adapters").exists())
        self.assertFalse((ROOT / "host-scripts").exists())


class AdapterSkillTests(unittest.TestCase):
    def test_each_adapter_is_a_skill_with_its_data(self):
        for provider, role in ADAPTERS.items():
            with self.subTest(provider=provider):
                folder = SKILLS / f"adapter-{provider}"
                self.assertTrue((folder / "SKILL.md").is_file())
                self.assertTrue((folder / "adapter.yaml").is_file())
                adapter = load_adapter(role, provider)
                self.assertFalse(adapter["generic"])
                meta, body = frontmatter(folder / "SKILL.md")
                self.assertIn("tools/adapters.py", body)  # the shared renderer, never hand-written commands
                for link in adapter["docs"]:
                    self.assertIn(link, body)
        self.assertTrue((SKILLS / "adapter-generic" / "adapter.yaml").is_file())

    def test_proxmox_host_scripts_live_in_its_skill(self):
        scripts = SKILLS / "adapter-proxmox" / "scripts"
        for name in ("lib.sh", "setup-agent-access.sh", "teardown-agent-access.sh", "discover-host.sh"):
            self.assertTrue((scripts / name).is_file(), name)
        self.assertEqual(sorted(load_adapter("virtualization", "proxmox")["scripts"]),
                         sorted(f"scripts/{n}" for n in ("lib.sh", "setup-agent-access.sh",
                                                         "teardown-agent-access.sh", "discover-host.sh")))

    def test_an_adapter_for_another_role_is_refused(self):
        root = Path(tempfile.mkdtemp(prefix="skills-"))
        self.addCleanup(shutil.rmtree, root, True)
        (root / "adapter-pfsense").mkdir()
        data = yaml.safe_load((SKILLS / "adapter-opnsense" / "adapter.yaml").read_text())
        data["provider"] = "pfsense"
        (root / "adapter-pfsense" / "adapter.yaml").write_text(yaml.safe_dump(data))
        self.assertFalse(load_adapter("router_firewall", "pfsense", root=root)["generic"])
        with self.assertRaises(AdapterError):
            load_adapter("file_server", "pfsense", root=root)

    def test_role_steps_still_complete(self):
        for provider, role in ADAPTERS.items():
            with self.subTest(provider=provider):
                adapter = load_adapter(role, provider)
                for step in ROLE_STEPS[role]:
                    self.assertIn(step, adapter["owner_steps"])


class AppResearchSkillTests(unittest.TestCase):
    """Owner, 2026-11-04: researching an app is a portable skill; guide 3.2 maps its facts to the spec."""

    SKILL = SKILLS / "researching-apps-for-self-hosting" / "SKILL.md"

    def test_the_skill_holds_the_research_procedure(self):
        meta, body = frontmatter(self.SKILL)
        self.assertNotIn("compatibility", meta)  # works without the toolkit
        for needle in ("official", "major-version tag", "never `latest`", "starts as root", "5 GB",
                       "without a browser", "single sign-on", "OpenID Connect", "prints at start",
                       "sender address", "logo", "research.md", "label"):
            self.assertIn(needle.lower(), body.lower())
        for toolkit_word in ("service.yaml", "gen_service", "vmssh", "Authentik", "Butane"):
            self.assertNotIn(toolkit_word, body)

    def test_guide_and_prompt_use_it(self):
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        section = guide.split("## 3.2", 1)[1].split("## 3.3", 1)[0]
        self.assertIn("researching-apps-for-self-hosting", section)
        self.assertIn("| Fact | Goes to (service spec) |", section)  # the toolkit mapping stays here
        self.assertNotIn("**Credentials in its logs.**", section)  # moved to the skill
        prompt = (ROOT / ".opencode" / "agents" / "fcos-app-installer.md").read_text()
        self.assertIn("researching-apps-for-self-hosting", prompt)


if __name__ == "__main__":
    unittest.main()
