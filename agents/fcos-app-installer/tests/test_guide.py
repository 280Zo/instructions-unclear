import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "guide"


def page(name: str) -> str:
    return (GUIDE / name).read_text()


def code_lines() -> list[tuple[str, str]]:
    out = []
    for path in sorted(GUIDE.glob("*.md")):
        in_code = False
        for line in path.read_text().splitlines():
            if line.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                out.append((path.name, line))
    return out


class GuideTests(unittest.TestCase):
    def test_rebuild_unlinks_only_old_os_disk(self):
        # The commands moved to the virtualization adapter (provider-neutral guide).
        self.assertIn("rebuild_os_disk", page("05-rebuild-a-vm.md"))
        adapter = (ROOT / ".agents" / "skills" / "adapter-proxmox" / "adapter.yaml").read_text()
        self.assertNotIn("--idlist unused0", adapter)
        self.assertIn('--idlist "$SLOT"', adapter)

    def test_stateful_secrets_not_generated_blind(self):
        text = page("06-edge-vm.md")
        self.assertIsNone(re.search(r"openssl rand[^\n]*\|[^\n]*podman secret create", text))
        self.assertIn("your password manager", page("03-add-a-service.md"))
        self.assertIn("same value", page("05-rebuild-a-vm.md"))

    def test_live_push_stops_on_failure(self):
        text = page("03-add-a-service.md")
        self.assertNotIn("or break", text)
        self.assertNotIn("apply-$svc*.sh", text)
        self.assertRegex(text, r"ign_to_script\.py \$ws/vms/\$vm/igns/\{[^}]+\}\.ign > \S+; and")

    def test_privileged_commands_use_sudo(self):
        for name, line in code_lines():
            for match in re.finditer(r"(?:^|[;'\"]\s*)(systemctl --user -M|ls -l\S* /var/mnt/backups)", line):
                with self.subTest(page=name, line=line.strip()):
                    before = line[: match.start(1)]
                    self.assertTrue(before.rstrip().endswith("sudo"), line)


if __name__ == "__main__":
    unittest.main()
