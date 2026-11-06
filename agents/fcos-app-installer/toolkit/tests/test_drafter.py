"""The adapter-drafter subagent: researches a product that has no adapter
skill and drafts one from what the user did, into the workspace only."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

from test_agent import SKILLS_DIR, body, effect, frontmatter  # noqa: E402

DRAFTER = ROOT / ".opencode" / "agents" / "adapter-drafter.md"
WS = "/home/owner/fcos-workspace"


class DrafterTests(unittest.TestCase):
    def setUp(self):
        self.text = DRAFTER.read_text()

    def test_the_commands_it_is_told_to_run_are_on_one_line(self):
        # The drafter's rules deny a newline in a command (it separates commands), so a command the
        # prompt wraps over two lines would be refused if a model copied the wrap.
        import re
        for command in re.findall(r"`(python3 tools/[^`]*)`", self.text.split("\n---\n", 1)[1]):
            with self.subTest(command=command[:60]):
                self.assertNotIn("\n", command)

    def test_is_a_subagent(self):
        fm = frontmatter(self.text)
        self.assertIn("mode: subagent", fm)
        self.assertIn("description:", fm)

    def test_shell_only_the_adapter_tool(self):
        for command in ("python3 tools/adapters.py show --role file_server --provider synology",
                        f"python3 tools/adapters.py draft --role file_server --provider synology --from /tmp/opencode/r.json --workspace {WS}"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")
        for command in ("python3 tools/vmssh.py run edge -- true", "python3 tools/hypervisor.py list", "ssh x", "rm -rf /",
                        "python3 tools/adapters.py render --role x --step y --values v",
                        "python3 tools/adapters.py draft --from ../x", "python3 tools/adapters.py show; ssh x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_writes_only_drafts_and_scratch(self):
        for path in (f"{WS}/adapters-draft/fileserver-synology/SKILL.md", "/tmp/opencode/recorded.json"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "allow")
        for path in (f"{SKILLS_DIR}/hypervisor-proxmox/adapter.yaml", "tools/adapters.py", f"{WS}/site.yaml",
                     ".opencode/agents/fcos-app-installer.md", f"{WS}/secrets/x.token"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "deny")

    def test_never_reads_secrets_or_starts_others(self):
        for path in (f"{WS}/secrets/proxmox-a.token", "/x/y.token"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "read", path), "deny")
        self.assertEqual(effect(self.text, "subagent", "general"), "deny")
        self.assertEqual(effect(self.text, "skill", "adapter-generic"), "allow")
        self.assertEqual(effect(self.text, "skill", "brainstorming"), "deny")

    def test_same_secret_and_folder_guards_as_the_main_agent(self):
        for action, path in (("read", "secrets/x"), ("read", "secrets"), ("read", f"{WS}/secrets"),
                             ("read", "notes/x.md"), ("edit", "secrets/x")):
            with self.subTest(action=action, path=path):
                self.assertEqual(effect(self.text, action, path), "deny")
        for path in ("/tmp/anything/fcos-x", "/home/owner/.cfg/fcos-x"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "external_directory", path), "ask")
        self.assertEqual(effect(self.text, "external_directory", "/tmp/opencode/x"), "allow")
        self.assertEqual(effect(self.text, "external_directory", f"{WS}/adapters-draft/x"), "allow")
        for pattern in ("**/secrets/*", "**/*.token"):
            self.assertEqual(effect(self.text, "glob", pattern), "deny")

    def test_unneeded_mcp_servers_are_denied(self):
        for action in ("pmb_record_batch", "docling_convert_x", "podman_run", "codebase_memory_mcp_search"):
            with self.subTest(action=action):
                self.assertEqual(effect(self.text, action, "*"), "deny")

    def test_prompt_says_how(self):
        text = " ".join(body(self.text).split())
        for needle in ("official documentation", "recorded steps", "python3 tools/adapters.py draft",
                       "adapters-draft", "never touch", "label", "SKILL.md", "report back"):
            with self.subTest(needle=needle):
                self.assertIn(needle, text)


if __name__ == "__main__":
    unittest.main()
