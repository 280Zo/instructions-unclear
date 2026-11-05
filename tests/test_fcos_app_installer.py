"""agents/fcos-app-installer/install.py: places the toolkit files rulesync cannot place.

rulesync writes the agent, its helper, the command, the skills and the rules into the folder you
start OpenCode in (groups/fcos_app_installer.jsonc). The toolkit's own files (tools/, templates/,
docs/, tests/ and so on) are not rulesync components, so install.py copies them from the
folder's toolkit/ directory, from this repository, so that installing never depends on where
the toolkit was developed.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import stat
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # the repo's tests are stdlib-only; the frontmatter checks need a YAML parser
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "agents" / "fcos-app-installer"
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None


def load_installer():
    spec = importlib.util.spec_from_file_location("fcos_install", FOLDER / "install.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(module, *args, source=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(list(args), source=source)
    return code, out.getvalue(), err.getvalue()


def tree(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
            for p in sorted(folder.rglob("*")) if p.is_file()}


class InstallerBase(unittest.TestCase):
    """A throwaway toolkit source and target; no test of its own."""

    def setUp(self):
        self.module = load_installer()
        self._tmp = tempfile.TemporaryDirectory(dir=SCRATCH)
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.source = self.tmp / "agent" / "toolkit"
        for rel, text in {"tools/a.py": "print('a')\n", "tools/run.sh": "#!/bin/sh\n", "docs/guide/README.md": "# g\n",
                          "site.example.yaml": "x: 1\n", "host-scripts.sha256": "\n"}.items():
            path = self.source / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        (self.source / "tools" / "run.sh").chmod(0o755)
        self.target = self.tmp / "installed"


class InstallerTests(InstallerBase):
    def test_a_dry_run_writes_nothing_and_says_what_it_would_do(self):
        code, out, _ = run(self.module, str(self.target), source=self.source)
        self.assertEqual(code, 0)
        self.assertFalse(self.target.exists())
        self.assertIn("5 new", out)
        self.assertIn("dry run", out.lower())
        self.assertIn("--apply", out)

    def test_apply_copies_the_toolkit_with_modes_and_nothing_else(self):
        code, out, _ = run(self.module, str(self.target), "--apply", source=self.source)
        self.assertEqual(code, 0, out)
        self.assertEqual(tree(self.target), tree(self.source))
        self.assertTrue(os.access(self.target / "tools" / "run.sh", os.X_OK))
        self.assertFalse(os.access(self.target / "tools" / "a.py", os.X_OK))

    def test_a_second_run_changes_nothing_and_check_agrees(self):
        run(self.module, str(self.target), "--apply", source=self.source)
        before = tree(self.target)
        code, out, _ = run(self.module, str(self.target), "--apply", source=self.source)
        self.assertEqual((code, tree(self.target)), (0, before))
        self.assertIn("0 new, 0 changed, 5 unchanged", out)
        self.assertEqual(run(self.module, str(self.target), "--check", source=self.source)[0], 0)

    def test_an_edited_file_is_reported_then_restored_and_other_files_are_left_alone(self):
        run(self.module, str(self.target), "--apply", source=self.source)
        (self.target / "tools" / "a.py").write_text("print('edited')\n")
        (self.target / "my-notes.txt").write_text("mine\n")
        (self.target / ".opencode").mkdir()
        (self.target / ".opencode" / "kept.md").write_text("rulesync's\n")
        code, out, _ = run(self.module, str(self.target), "--check", source=self.source)
        self.assertEqual(code, 1)
        self.assertIn("tools/a.py", out)
        run(self.module, str(self.target), "--apply", source=self.source)
        self.assertEqual((self.target / "tools" / "a.py").read_text(), "print('a')\n")
        self.assertEqual((self.target / "my-notes.txt").read_text(), "mine\n")
        self.assertEqual((self.target / ".opencode" / "kept.md").read_text(), "rulesync's\n")

    def test_it_never_deletes_what_the_toolkit_no_longer_ships(self):
        run(self.module, str(self.target), "--apply", source=self.source)
        (self.source / "docs" / "guide" / "README.md").unlink()
        run(self.module, str(self.target), "--apply", source=self.source)
        self.assertTrue((self.target / "docs" / "guide" / "README.md").exists())

    def test_the_real_toolkit_installs_with_its_readme_and_owns_no_rulesync_output(self):
        code, out, _ = run(self.module, str(self.target), "--apply")
        self.assertEqual(code, 0, out)
        installed = tree(self.target)
        for needed in ("tools/adapters.py", "tools/layout.py", "tests/test_agent.py", "docs/guide/README.md",
                       "host-scripts.sha256", "site.example.yaml", "templates/base/config.bu.tmpl", "README.md"):
            self.assertIn(needed, installed)
        # What rulesync writes is never the installer's to write.
        for path in installed:
            self.assertFalse(path.startswith(".opencode/") or path == "AGENTS.md", path)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()),
                         sorted([p.name for p in (FOLDER / "toolkit").iterdir() if p.name != "__pycache__"]
                                + ["README.md"]))
        # Every file arrives with its source's content and mode; the README is this folder's own.
        expected = {k: v for k, v in tree(FOLDER / "toolkit").items() if "__pycache__" not in k}
        expected["README.md"] = ((FOLDER / "README.md").read_bytes(), 0o644)
        self.assertEqual(installed, expected)

    def test_a_readme_beside_the_toolkit_is_installed_as_readme_md(self):
        (self.source.parent / "README.md").write_text("# readme\n")
        run(self.module, str(self.target), "--apply", source=self.source)
        self.assertEqual((self.target / "README.md").read_text(), "# readme\n")
        self.assertIn("6 new", run(self.module, str(self.tmp / "other"), source=self.source)[1])

    def test_a_python_cache_is_never_copied(self):
        (self.source / "tools" / "__pycache__").mkdir()
        (self.source / "tools" / "__pycache__" / "a.cpython-314.pyc").write_bytes(b"\0")
        run(self.module, str(self.target), "--apply", source=self.source)
        self.assertFalse((self.target / "tools" / "__pycache__").exists())


class InstallerRefusalTests(InstallerBase):
    """Refusals: nothing is written, exit code 2, and the message says why."""

    def refused(self, *args, source=None, why=""):
        code, out, err = run(self.module, *args, source=source or self.source)
        self.assertEqual(code, 2, out + err)
        self.assertIn(why, err)

    def test_the_source_checkout_itself_is_refused(self):
        inside = ROOT / "agents" / "never-created"
        self.refused(str(inside), "--apply", source=FOLDER / "toolkit", why="the repository the installer belongs to")
        self.assertFalse(inside.exists())

    def test_the_toolkit_folder_is_refused(self):
        self.refused(str(self.source), "--apply", why="source")

    def test_a_target_that_is_a_file_is_refused(self):
        self.target.write_text("x")
        self.refused(str(self.target), "--apply", why="not a folder")

    def test_a_link_in_the_way_is_refused_not_followed(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        self.target.mkdir()
        (self.target / "tools").symlink_to(outside, target_is_directory=True)
        self.refused(str(self.target), "--apply", why="link")
        self.assertEqual(list(outside.iterdir()), [])

    def test_a_link_in_the_toolkit_is_refused(self):
        (self.source / "tools" / "link.py").symlink_to(self.source / "tools" / "a.py")
        self.refused(str(self.target), "--apply", why="link")
        self.assertFalse(self.target.exists())

    def test_a_top_level_entry_that_is_not_on_the_install_list_is_refused(self):
        (self.source / "notes.txt").write_text("private\n")
        self.refused(str(self.target), "--apply", why="not on the install list")
        self.assertFalse(self.target.exists())

    def test_files_that_look_like_secrets_are_refused(self):
        for name in ("tools/api.token", "tools/id_rsa.pem", "docs/secrets/x.md"):
            with self.subTest(name=name):
                path = self.source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n")
                self.refused(str(self.target), "--apply", why="looks like a secret")
                path.unlink()

    def test_usage_errors_exit_2(self):
        self.refused(source=self.source, why="usage")
        self.refused(str(self.target), "--frobnicate", why="usage")

    def test_a_target_inside_another_checkout_is_allowed_with_a_warning(self):
        other = self.tmp / "other"
        (other / ".git").mkdir(parents=True)
        code, out, err = run(self.module, str(other / "toolkit"), "--apply", source=self.source)
        self.assertEqual(code, 0, err)
        self.assertIn("git checkout", err)
        self.assertIn("folder of its own", err)

    def test_more_secret_looking_names_are_refused_whatever_their_case(self):
        for name in ("tools/.env", "tools/.env.local", "docs/id_ed25519", "docs/id_rsa.pub.bak", "docs/credentials.json",
                     "tools/Foo.KEY", "tools/x.PEM", "docs/.npmrc", "docs/.netrc", "docs/auth.json", "docs/vault.kdbx",
                     "docs/terraform.tfstate", "docs/.ssh/config", "docs/Secrets/x.md"):
            with self.subTest(name=name):
                path = self.source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n")
                self.refused(str(self.target), "--apply", why="looks like a secret")
                path.unlink()

    def test_the_secret_name_list_covers_the_common_credential_files(self):
        for name in ("tools/secrets.yaml", "tools/secret.txt", "tools/token", "tools/token.txt", "tools/api_key.txt",
                     "tools/password.txt", "docs/.aws/credentials", "docs/.git-credentials", "docs/.pgpass",
                     "docs/.htpasswd", "docs/.dockercfg", "docs/.boto", "docs/kubeconfig", "docs/service-account.json",
                     "docs/oauth.json", "docs/terraform.tfvars", "docs/x.tfstate.backup", "docs/x.p8", "docs/x.jks",
                     "docs/x.keystore", "docs/x.asc", "docs/x.gpg", "docs/known_hosts", "docs/.gnupg/pubring.kbx", "tools/.pypirc", "tools/x.keytab", "tools/x.secret",
                     "tools/vault-password.txt", "tools/kubeconfig.yaml", "tools/service_account.json"):
            with self.subTest(name=name):
                path = self.source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n")
                self.refused(str(self.target), "--apply", why="looks like a secret")
                path.unlink()

    def test_names_that_only_mention_a_secret_are_not_refused(self):
        for name in ("tools/secret_scan.py", "tests/test_secret_scan.py", "tools/images.env", "docs/secret-handling.md",
                     "tools/token_check.py", "docs/passwords-in-the-workspace.md"):
            with self.subTest(name=name):
                path = self.source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("x\n")
                code, out, err = run(self.module, str(self.target), source=self.source)
                self.assertEqual(code, 0, err)
                path.unlink()

    def test_a_named_pipe_at_a_destination_is_refused_not_waited_on(self):
        import signal
        self.target.mkdir()
        os.mkfifo(self.target / "site.example.yaml")
        signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("install.py hung on a pipe")))
        signal.alarm(5)
        self.addCleanup(signal.alarm, 0)
        self.refused(str(self.target), "--check", why="not a regular file")

    def test_an_unwritable_folder_with_nothing_to_change_is_not_a_reason_to_refuse(self):
        run(self.module, str(self.target), "--apply", source=self.source)
        guide = self.target / "docs" / "guide"
        guide.chmod(0o555)
        self.addCleanup(guide.chmod, 0o755)
        code, out, err = run(self.module, str(self.target), "--check", source=self.source)
        self.assertEqual((code, err), (0, ""), out)

    def test_a_padded_folder_argument_is_a_usage_error(self):
        self.refused("  " + str(self.target) + "  ", "--apply", why="usage")

    def test_an_empty_folder_argument_is_a_usage_error_not_the_current_folder(self):
        self.refused("", "--apply", why="usage")

    def test_a_target_that_is_a_link_is_refused(self):
        real = self.tmp / "real"
        real.mkdir()
        self.target.symlink_to(real, target_is_directory=True)
        self.refused(str(self.target), "--apply", why="link")
        self.assertEqual(list(real.iterdir()), [])

    def test_a_folder_where_a_file_belongs_is_refused_in_the_dry_run_too(self):
        (self.target / "tools" / "a.py").mkdir(parents=True)
        self.refused(str(self.target), why="is a folder")
        self.assertEqual(list((self.target / "tools" / "a.py").iterdir()), [])

    def test_a_target_under_a_file_is_refused_in_the_dry_run(self):
        self.target.write_text("x")
        self.refused(str(self.target / "sub"), why="not a folder")

    @unittest.skipIf(os.geteuid() == 0, "root can write anywhere")
    def test_an_unwritable_folder_is_refused_before_anything_is_written(self):
        # The earlier claim "nothing is written when a file cannot be placed" has to hold for this too.
        (self.target / "docs" / "guide").mkdir(parents=True)
        (self.target / "docs" / "guide").chmod(0o555)
        self.addCleanup((self.target / "docs" / "guide").chmod, 0o755)
        self.refused(str(self.target), "--apply", why="not writable")
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["docs"])
        self.assertEqual(list((self.target / "docs").iterdir()), [self.target / "docs" / "guide"])

    def test_a_pinned_images_file_named_env_is_not_taken_for_a_secret(self):
        (self.source / "tools" / "images.env").write_text("BUTANE_IMAGE=quay.io/x\n")
        code, out, err = run(self.module, str(self.target), source=self.source)
        self.assertEqual(code, 0, err)

    @unittest.skipIf(os.geteuid() == 0, "root can write anywhere")
    def test_an_unwritable_existing_target_is_refused(self):
        self.target.mkdir()
        self.target.chmod(0o555)
        self.addCleanup(self.target.chmod, 0o755)
        self.refused(str(self.target), "--apply", why="not writable")

    def test_a_failure_while_writing_exits_2_and_says_a_rerun_is_safe(self):
        original = self.module.write

        def broken(*args, **kwargs):
            raise OSError(28, "No space left on device")
        self.module.write = broken
        self.addCleanup(setattr, self.module, "write", original)
        code, out, err = run(self.module, str(self.target), "--apply", source=self.source)
        self.assertEqual(code, 2, out + err)
        self.assertIn("run it again", err)
        self.assertIn("partly", err)

    def test_a_file_name_that_is_not_utf8_does_not_crash_the_listing(self):
        odd = os.fsdecode(b"tools/caf\xe9.py")
        (self.source / odd).write_text("x\n")
        code, out, err = run(self.module, str(self.target), source=self.source)
        self.assertEqual(code, 0, err)
        self.assertIn("caf", out)

    def test_the_next_steps_quote_a_target_with_a_space(self):
        spaced = self.tmp / "my folder"
        code, out, _ = run(self.module, str(spaced), "--apply", source=self.source)
        self.assertEqual(code, 0)
        self.assertIn(f"'{spaced}'", out)

    def test_nothing_is_written_when_one_file_cannot_be_placed(self):
        # Placement is planned first: a refusal anywhere means no file is written anywhere.
        self.target.mkdir()
        (self.target / "docs").write_text("a file where the docs folder goes")
        self.refused(str(self.target), "--apply", why="not a folder")
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["docs"])


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), path
    return yaml.safe_load(text[4:].split("\n---\n", 1)[0])


def jsonc(path: Path) -> dict:
    text = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*', lambda m: "" if m[0].startswith("//") else m[0],
                  path.read_text(encoding="utf-8"))
    return json.loads(text)


@unittest.skipIf(yaml is None, "PyYAML is not installed; the frontmatter checks need it")
class SourceTests(unittest.TestCase):
    """The rulesync sources in agents/fcos-app-installer/ follow this repo's rules (AGENTS.md)."""

    def test_agents_have_the_source_format(self):
        files = sorted((FOLDER / "subagents").glob("*.md"))
        self.assertEqual([p.stem for p in files], ["adapter-drafter", "fcos-app-installer"])
        for path in files:
            with self.subTest(agent=path.stem):
                meta = frontmatter(path)
                self.assertEqual(meta["name"], path.stem)
                self.assertEqual(meta["targets"], ["*"])
                self.assertIsInstance(meta["description"], str)
                self.assertLessEqual(set(meta), {"name", "targets", "description", "opencode", "claudecode"})
                self.assertIn(meta["opencode"]["mode"], {"primary", "subagent", "all"})
                permissions = meta["opencode"]["permissions"]
                self.assertTrue(permissions)
                for rule in permissions:
                    self.assertEqual(set(rule), {"action", "resource", "effect"}, rule)
                    self.assertIn(rule["effect"], {"allow", "ask", "deny"})
                body = path.read_text().split("\n---\n", 1)[1].strip()
                self.assertTrue(body)

    def test_the_command_runs_in_the_main_agent(self):
        meta = frontmatter(FOLDER / "commands" / "add-service.md")
        self.assertEqual(meta["targets"], ["*"])
        self.assertEqual(meta["opencode"]["agent"], "fcos-app-installer")
        self.assertTrue((FOLDER / "subagents" / f"{meta['opencode']['agent']}.md").is_file())

    def test_the_rules_are_root_rules(self):
        rules = sorted((FOLDER / "rules").glob("*.md"))
        self.assertEqual([p.name for p in rules], ["owner-steps.md", "secret-handling.md"])
        for path in rules:
            with self.subTest(rule=path.name):
                meta = frontmatter(path)
                self.assertIs(meta["root"], True)
                self.assertEqual(meta["targets"], ["*"])
                self.assertTrue(meta["description"])

    def test_skills_use_only_the_shared_fields_and_names_stay_unique_in_the_repo(self):
        skills = sorted((FOLDER / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skills), 6)
        for path in skills:
            with self.subTest(skill=path.parent.name):
                meta = frontmatter(path)
                self.assertEqual(meta["name"], path.parent.name)
                self.assertLessEqual(set(meta), {"name", "description", "license", "compatibility", "metadata"})
        ours = {p.parent.name for p in skills}
        elsewhere = {p.parent.name for p in ROOT.glob("**/SKILL.md")
                     if FOLDER not in p.parents and ".git" not in p.parts}
        self.assertEqual(ours & elsewhere, set())

    def test_agent_names_are_unique_across_the_repo(self):
        # rulesync merges source trees by file path: a later file with the same name replaces an earlier one.
        seen = {}
        for path in ROOT.glob("agents/*/subagents/*.md"):
            seen.setdefault(path.name, []).append(str(path.relative_to(ROOT)))
        self.assertEqual({k: v for k, v in seen.items() if len(v) > 1}, {})

    def test_the_toolkit_folder_holds_nothing_rulesync_writes(self):
        for name in (".opencode", "rules", "skills", "subagents", "commands", "AGENTS.md", "opencode.json"):
            with self.subTest(name=name):
                self.assertFalse((FOLDER / "toolkit" / name).exists())

    def test_the_rule_comment_names_the_gaps_in_the_source(self):
        # Comments do not survive in the file rulesync writes, so the source is where they are checked.
        text = (FOLDER / "subagents" / "fcos-app-installer.md").read_text()
        comment = " ".join(text.split("The pinned list of host-script checksums", 1)[1].split("action: shell", 1)[0].split())
        self.assertIn("avoid all three", comment)
        self.assertIn("guard rail", comment)


class GroupTests(unittest.TestCase):
    def test_profile_and_group_select_the_same_things(self):
        profile = jsonc(FOLDER / "profile.jsonc")
        group = jsonc(ROOT / "groups" / "fcos_app_installer.jsonc")
        for config in (profile, group):
            self.assertEqual(config["targets"], ["opencode"])
            self.assertEqual(config["features"], ["rules", "subagents", "commands", "skills"])
            self.assertIs(config["delete"], False)
            self.assertNotIn("global", config)
            for root in config["inputRoots"]:
                self.assertTrue((ROOT / root).is_dir(), root)
        self.assertEqual(profile["inputRoots"][0], "agents/fcos-app-installer")
        self.assertEqual(group["inputRoots"][0], "agents/fcos-app-installer")

    def test_the_group_installs_the_installer_alone_and_matches_the_profile(self):
        # No companion agents in this folder. A subagent runs with its own
        # permissions, not the starter's, and the installer starts only adapter-drafter.
        group = jsonc(ROOT / "groups" / "fcos_app_installer.jsonc")
        profile = jsonc(FOLDER / "profile.jsonc")
        self.assertEqual(group["inputRoots"], ["agents/fcos-app-installer"])
        self.assertEqual(group["inputRoots"], profile["inputRoots"])  # the two selections never drift
        self.assertEqual(group["targets"], ["opencode"])

    def test_every_subagent_it_may_start_is_installed_by_the_group(self):
        # A permission to start an agent the folder lacks would be a promise the install cannot keep.
        allowed = [r["resource"] for r in frontmatter(FOLDER / "subagents" / "fcos-app-installer.md")
                   ["opencode"]["permissions"] if r["action"] == "subagent" and r["effect"] == "allow"]
        group = jsonc(ROOT / "groups" / "fcos_app_installer.jsonc")
        installed = {p.stem for root in group["inputRoots"] for p in (ROOT / root / "subagents").glob("*.md")}
        self.assertEqual(installed, {"fcos-app-installer", "adapter-drafter"})
        self.assertEqual(allowed, ["adapter-drafter"])

    def test_it_is_a_folder_group_not_part_of_default(self):
        default = jsonc(ROOT / "groups" / "default.jsonc")["inputRoots"]
        self.assertNotIn("agents/fcos-app-installer", default)
        self.assertNotIn("agents/fcos-app-installer", jsonc(ROOT / "rulesync.jsonc")["inputRoots"])

    def test_it_is_listed_everywhere_a_new_folder_must_be(self):
        # AGENTS.md: "Whenever you add a folder ... check groups/*.jsonc and groups/README.md" and keep
        # the catalog READMEs, the file list with tool sections and the tests README in step.
        for path, needle in (("groups/README.md", "fcos_app_installer"),
                             ("groups/README.md", "agents/fcos-app-installer"),
                             ("agents/README.md", "fcos-app-installer"),
                             ("README.md", "agents/fcos-app-installer"),
                             ("README.md", "`fcos_app_installer`"),
                             ("AGENTS.md", "fcos_app_installer"),
                             ("AGENTS.md", "agents/fcos-app-installer/subagents"),
                             ("tests/README.md", "test_fcos_app_installer")):
            with self.subTest(file=path, needle=needle):
                self.assertIn(needle, (ROOT / path).read_text(encoding="utf-8"))

    def test_the_root_readme_says_default_leaves_out_the_installer(self):
        text = " ".join((ROOT / "README.md").read_text().split())
        self.assertIn("except REA and the FCOS app installer", text)

    def test_the_groups_readme_shows_the_install_commands(self):
        section = (ROOT / "groups" / "README.md").read_text().split("## fcos_app_installer", 1)[1]
        section = section.split("\n## ", 1)[0]
        for needle in ("install.py", "--apply", "npx rulesync@41.0.0 generate --config groups/fcos_app_installer.jsonc",
                       "--output-roots"):
            with self.subTest(needle=needle):
                self.assertIn(needle, section)

    def test_the_readme_install_names_the_files_that_exist(self):
        readme = (FOLDER / "README.md").read_text()
        install = readme.split("## Install", 1)[1].split("\n## ", 1)[0]
        for needle in ("agents/fcos-app-installer/install.py", "groups/fcos_app_installer.jsonc",
                       "rulesync@41.0.0", "--apply", "--output-roots"):
            with self.subTest(needle=needle):
                self.assertIn(needle, install)
        self.assertTrue((FOLDER / "install.py").is_file())
        self.assertTrue((ROOT / "groups" / "fcos_app_installer.jsonc").is_file())


if __name__ == "__main__":
    unittest.main()
