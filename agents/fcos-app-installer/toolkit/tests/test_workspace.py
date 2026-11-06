import contextlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))

from gitfree import folder_outside_any_checkout  # noqa: E402

import workspace  # noqa: E402
from workspace import (WorkspaceError, init_workspace, load_service, load_site,  # noqa: E402
                       private_values, resolve_workspace, scan_previous)


def j(*parts: str) -> str:
    """Join pieces at runtime, so this file never holds a real-looking value
    that publish_check would (rightly) flag."""
    return "".join(parts)


class TempHome(unittest.TestCase):
    """Every test gets a throwaway HOME and no FCOS_WORKSPACE."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        # No GIT_* variable from the caller: a git hook sets GIT_DIR, which would point every
        # git call in these tests at the wrong repository.
        env = {k: v for k, v in os.environ.items() if k != "FCOS_WORKSPACE" and not k.startswith("GIT_")}
        env["HOME"] = str(self.home)
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    @property
    def remembered(self) -> Path:
        return self.home / ".config" / "fcos-agent" / "workspace"


class InitTests(TempHome):
    def test_init_layout(self):
        ws = self.tmp / "ws"
        init_workspace(ws)
        for name in ("secrets", "vms", "services", "adapters-draft"):
            self.assertTrue((ws / name).is_dir(), name)
        self.assertEqual(stat.S_IMODE((ws / "secrets").stat().st_mode), 0o700)
        site = ws / "site.yaml"
        self.assertEqual(site.read_text(), (ROOT / "site.example.yaml").read_text())
        self.assertEqual(self.remembered.read_text().strip(), str(ws))

        site.write_text("domain: kept.example.org\n")
        before = {p: p.stat().st_mtime_ns for p in (site, self.remembered)}
        init_workspace(ws)
        self.assertEqual(site.read_text(), "domain: kept.example.org\n")
        self.assertEqual({p: p.stat().st_mtime_ns for p in before}, before)
        self.assertEqual(stat.S_IMODE((ws / "secrets").stat().st_mode), 0o700)

    def test_init_hides_secrets_from_searches(self):
        # rg (and OpenCode's grep, built on it) skip paths listed in .ignore.
        ws = self.tmp / "ws-ignore"
        init_workspace(ws)
        self.assertIn("secrets/", (ws / ".ignore").read_text().splitlines())
        (ws / ".ignore").write_text("own-rule/\n")
        init_workspace(ws)  # re-run keeps the user's lines and adds the rule once
        lines = (ws / ".ignore").read_text().splitlines()
        self.assertEqual(lines.count("secrets/"), 1)
        self.assertIn("own-rule/", lines)

    def test_init_tightens_existing_secrets_dir(self):
        ws = self.tmp / "ws"
        (ws / "secrets").mkdir(parents=True)
        (ws / "secrets").chmod(0o755)
        init_workspace(ws)
        self.assertEqual(stat.S_IMODE((ws / "secrets").stat().st_mode), 0o700)

    def test_workspace_inside_repo_refused(self):
        for bad in (ROOT, ROOT / "ws-inside", ROOT / "tools" / "x"):
            with self.subTest(path=str(bad)):
                with self.assertRaises(WorkspaceError):
                    resolve_workspace(str(bad))
                with self.assertRaises(WorkspaceError):
                    init_workspace(bad)
        self.assertFalse((ROOT / "ws-inside").exists())
        self.assertFalse(self.remembered.exists())

    def test_workspace_symlink_into_repo_refused(self):
        link = self.tmp / "link"
        link.symlink_to(ROOT)
        with self.assertRaises(WorkspaceError):
            resolve_workspace(str(link / "sub"))

    def test_remembered_path_inside_repo_refused(self):
        self.remembered.parent.mkdir(parents=True)
        self.remembered.write_text(str(ROOT / "ws") + "\n")
        with self.assertRaises(WorkspaceError):
            resolve_workspace()


class EnclosingCheckoutTests(TempHome):
    """The workspace must stay out of the whole git checkout the toolkit sits in, not only out of
    the toolkit's folder: whatever else that checkout publishes must never include a workspace."""

    def setUp(self):
        super().setUp()
        self.big = self.tmp / "big"
        self.toolkit = self.big / "agents" / "toolkit"
        self.toolkit.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.big, check=True)
        patcher = mock.patch.object(workspace, "REPO_ROOT", self.toolkit)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_anywhere_in_the_enclosing_checkout_is_refused(self):
        for bad in (self.big, self.big / "ws", self.big / "agents" / "other", self.toolkit / "ws"):
            with self.subTest(path=str(bad)):
                with self.assertRaises(WorkspaceError) as caught:
                    resolve_workspace(str(bad))
                self.assertIn(str(self.big), str(caught.exception))
                with self.assertRaises(WorkspaceError):
                    init_workspace(bad)
        self.assertFalse((self.big / "ws").exists())
        self.assertFalse(self.remembered.exists())

    def test_a_remembered_path_in_the_enclosing_checkout_is_refused(self):
        self.remembered.parent.mkdir(parents=True)
        self.remembered.write_text(str(self.big / "ws") + "\n")
        with self.assertRaises(WorkspaceError):
            resolve_workspace()

    def test_outside_the_checkout_is_allowed(self):
        self.assertEqual(resolve_workspace(str(self.tmp / "ws")), self.tmp / "ws")

    def test_a_toolkit_outside_any_checkout_guards_its_own_folder(self):
        # A copy that is a plain folder (the installed toolkit) has no checkout around it.
        # Needs a TMPDIR outside every checkout; the sibling "big" repo is a separate tree.
        plain_root = folder_outside_any_checkout("workspace-plain-")
        if plain_root is None:
            self.skipTest("no place on this machine is outside every git checkout")
        self.addCleanup(shutil.rmtree, plain_root, True)
        plain = plain_root / "toolkit"
        plain.mkdir()
        with mock.patch.object(workspace, "REPO_ROOT", plain):
            self.assertEqual(resolve_workspace(str(plain_root / "ws")), plain_root / "ws")
            with self.assertRaises(WorkspaceError):
                resolve_workspace(str(plain / "ws"))

    def test_git_variables_of_the_caller_do_not_change_the_answer(self):
        # A git hook runs with GIT_DIR and GIT_WORK_TREE set to its own repository.
        other = self.tmp / "other"
        other.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=other, check=True)
        variables = {"GIT_DIR": str(other / ".git"), "GIT_WORK_TREE": str(other)}
        with mock.patch.dict(os.environ, variables):
            with self.assertRaises(WorkspaceError) as caught:
                resolve_workspace(str(self.big / "ws"))
            self.assertIn(str(self.big), str(caught.exception))
            self.assertEqual(resolve_workspace(str(self.tmp / "ws")), self.tmp / "ws")

    def test_when_git_cannot_answer_the_guard_still_finds_the_checkout(self):
        # Fail closed: git missing, failing (dubious ownership), or hung must not shrink the guard
        # to the toolkit's own folder; the checkout is then found by walking up to its .git.
        empty = self.tmp / "no-git-here"
        empty.mkdir()
        failing = subprocess.CompletedProcess(["git"], 128, b"", b"fatal: detected dubious ownership")
        cases = {
            "no git installed": mock.patch.dict(os.environ, {"PATH": str(empty)}),
            "git fails": mock.patch.object(workspace.subprocess, "run", return_value=failing),
            "git hangs": mock.patch.object(workspace.subprocess, "run",
                                           side_effect=subprocess.TimeoutExpired("git", 30)),
            "git unrunnable": mock.patch.object(workspace.subprocess, "run", side_effect=OSError("denied")),
        }
        for name, patch in cases.items():
            with self.subTest(case=name), patch:
                with self.assertRaises(WorkspaceError) as caught:
                    resolve_workspace(str(self.big / "ws"))
                self.assertIn(str(self.big), str(caught.exception))
                self.assertEqual(resolve_workspace(str(self.tmp / "ws")), self.tmp / "ws")

    def test_a_worktree_or_submodule_marks_its_checkout_with_a_git_file(self):
        linked = self.tmp / "linked"
        toolkit = linked / "sub" / "toolkit"
        toolkit.mkdir(parents=True)
        (linked / ".git").write_text("gitdir: /elsewhere/.git/worktrees/linked\n")
        empty = self.tmp / "no-git-here"
        empty.mkdir()
        with mock.patch.object(workspace, "REPO_ROOT", toolkit), mock.patch.dict(os.environ, {"PATH": str(empty)}):
            with self.assertRaises(WorkspaceError):
                resolve_workspace(str(linked / "ws"))

    def test_the_readme_says_which_checkout_is_guarded(self):
        readme = " ".join((ROOT / "README.md").read_text().split())
        self.assertIn("nearest", readme)  # with nested checkouts the guard protects the nearest one
        self.assertIn("looks for a `.git` above the toolkit", readme)

    def test_the_refusal_says_what_it_protects_and_what_to_do(self):
        with self.assertRaises(WorkspaceError) as caught:
            resolve_workspace(str(self.big / "ws"))
        message = str(caught.exception)
        self.assertIn(str(self.big), message)
        self.assertIn("choose a folder outside it", message)
        self.assertIn("folder of its own", message)


class ResolveTests(TempHome):
    def test_resolve_order(self):
        explicit, from_env, remembered = (self.tmp / n for n in ("a", "b", "c"))
        with self.assertRaises(WorkspaceError):
            resolve_workspace()
        self.remembered.parent.mkdir(parents=True)
        self.remembered.write_text(f"{remembered}\n")
        self.assertEqual(resolve_workspace(), remembered)
        os.environ["FCOS_WORKSPACE"] = str(from_env)
        self.assertEqual(resolve_workspace(), from_env)
        self.assertEqual(resolve_workspace(str(explicit)), explicit)

    def test_unset_is_distinct_error(self):
        with self.assertRaises(workspace.WorkspaceNotSet):
            resolve_workspace()

    def test_tilde_expands_to_temp_home(self):
        self.assertEqual(resolve_workspace("~/ws"), self.home / "ws")


class PrivateValueTests(TempHome):
    def make(self) -> Path:
        ws = self.tmp / "ws"
        init_workspace(ws)
        return ws

    def test_values_a_module_shows_in_its_own_example_are_public(self):
        ws = self.make()
        (ws / "site.yaml").write_text(
            "edge:\n  authentik:\n    uid: 3201\n    postgres_user: authentik\n    postgres_db: authentik\n"
            "    image: ghcr.io/goauthentik/server:2026.8\n    host: my-private-login\n"
            "  traefik:\n    image: docker.io/library/traefik:v3\n")
        values = private_values(ws)
        self.assertEqual(values & {"authentik", "ghcr.io/goauthentik/server:2026.8",
                                   "docker.io/library/traefik:v3"}, set())
        self.assertIn("my-private-login", values)

    def test_private_values_skip_example_defaults(self):
        ws = self.make()
        gateway, domain = j("10", ".9.8.1"), j("myhome.", "duckdns.org")
        (ws / "site.yaml").write_text(
            f"network:\n  gateway: {gateway}   # mine\n  bridge: vmbr0\n"
            f"domain: \"{domain}\"\nhosts:\n  big:\n    name: PVE-BIG\n"
            "updates:\n  zincati_days: [\"Sun\"]\n  keep: 14\nflag: true\nnothing: null\n"
            "acme_email: ASK\n")
        svc = ws / "services" / "app"
        svc.mkdir(parents=True)
        (svc / "service.yaml").write_text(
            "name: app\nhostname: app-private-name\ncontainers:\n  - image: docker.io/library/traefik:v3\n"
            "    env: {APP_ENV: production-mode}\n")
        values = private_values(ws)
        self.assertIn(gateway, values)
        self.assertIn(domain, values)
        self.assertIn("PVE-BIG", values)
        self.assertIn("app-private-name", values)
        self.assertNotIn("production-mode", values)  # an app setting, not identifying
        self.assertNotIn("vmbr0", values)      # same as the public example
        self.assertNotIn("docker.io/library/traefik:v3", values)
        self.assertNotIn("14", values)         # bare numbers are too generic
        self.assertNotIn("true", values)
        self.assertNotIn("ASK", values)
        self.assertNotIn("Sun", values)        # too short to be identifying

    def test_only_identifying_spec_fields_count(self):
        # A public app's image, folders and settings are not private; its web
        # name, titles and file-server paths can be private.
        ws = self.make()
        svc = ws / "services" / "app"
        svc.mkdir(parents=True)
        (svc / "service.yaml").write_text(
            "name: crm\nhostname: secret-crm\ntitle: Grandmas Contacts\ndescription: Family CRM of Mrs X\n"
            "login_reason: only the Example household uses it\naccepted_risks: ['over the 5 GB rule: photos of Kim']\n"
            "containers:\n  - name: app\n    image: docker.io/library/crm:4-apache\n"
            "    env: {APP_ENV: production, DB_HOST: crm-db}\n    add_capabilities: [CHOWN]\n"
            "    volumes:\n      - {path: /var/www/html/storage, class: local}\n"
            "      - {path: /photos, class: nfs, host: /var/mnt/kims-photos/2026}\n")
        values = private_values(ws)
        for public in ("crm", "docker.io/library/crm:4-apache", "production", "crm-db", "CHOWN",
                       "/var/www/html/storage", "/photos"):
            self.assertNotIn(public, values)
        for private in ("secret-crm", "Grandmas Contacts", "Family CRM of Mrs X", "only the Example household uses it",
                        "over the 5 GB rule: photos of Kim", "/var/mnt/kims-photos/2026"):
            self.assertIn(private, values)
        # Env values that carry an address, a domain or free text still count.
        (svc / "service.yaml").write_text(
            "name: crm\ncontainers:\n  - name: app\n    env: {MAIL_FROM: kim@example.net, ADMIN_NAME: Kim Example, "
            "MAIL_HOST: smtp.mailer.example, APP_ENV: production, DB_HOST: crm-db}\n")
        values = private_values(ws)
        for private in ("kim@example.net", "Kim Example", "smtp.mailer.example"):
            self.assertIn(private, values)
        self.assertEqual(values & {"production", "crm-db"}, set())
        # A VM spec's free-text description counts.
        (ws / "vms" / "x").mkdir(parents=True)
        (ws / "vms" / "x" / "vm.yaml").write_text(
            "settings:\n  description: {use: Kims secret box, why: w, source: s}\n  tags: {use: [fcos-agent], why: w, source: s}\n")
        self.assertIn("Kims secret box", private_values(ws))
        self.assertNotIn("fcos-agent", private_values(ws))
        (ws / "vms" / "x" / "vm.yaml").write_text("settings: [1]\n")  # malformed: no crash
        private_values(ws)
        (svc / "service.yaml").write_text("name: crm\ncontainers:\n  - name: app\n    env: {RELAY: 203.0.113.5}\n")
        self.assertIn("203.0.113.5", private_values(ws))
        # A web name or title that is just the app's own name is public too.
        (svc / "service.yaml").write_text("name: crm\nhostname: crm\ntitle: Crm\ncontainers: []\n")
        self.assertEqual(private_values(ws) & {"crm", "Crm"}, set())

    def test_shipped_adapter_names_are_public(self):
        # The roles answer names products the agent ships adapters for; those
        # names are all over the agent's own files and are not private.
        ws = self.make()
        (ws / "site.yaml").write_text(
            "roles:\n  virtualization: {provider: proxmox}\n  router_firewall: {provider: opnsense}\n"
            "  file_server: {provider: truenas}\n  dns_certificates: {provider: duckdns}\n"
            "  other: {provider: homebrew-box}\nhosts:\n  big:\n    name: PVE-BIG\n")
        values = private_values(ws)
        for name in ("proxmox", "opnsense", "truenas", "duckdns"):
            self.assertNotIn(name, values)
        self.assertIn("homebrew-box", values)  # no adapter ships for it
        self.assertIn("PVE-BIG", values)

    def test_fresh_workspace_has_no_private_values(self):
        self.assertEqual(private_values(self.make()), set())

    def test_missing_files_give_empty_set(self):
        self.assertEqual(private_values(self.tmp / "nothing"), set())


class LoadTests(TempHome):
    def test_load_site_and_service(self):
        ws = self.tmp / "ws"
        init_workspace(ws)
        self.assertEqual(load_site(ws)["roles"]["virtualization"], {"provider": "ASK"})
        (ws / "services" / "app").mkdir()
        (ws / "services" / "app" / "service.yaml").write_text("name: app\nvm: apps\n")
        self.assertEqual(load_service(ws, "app"), {"name": "app", "vm": "apps"})

    def test_load_service_rejects_path_names(self):
        ws = self.tmp / "ws"
        init_workspace(ws)
        for bad in ("../x", "a/b", "", ".."):
            with self.subTest(name=bad):
                with self.assertRaises(WorkspaceError):
                    load_service(ws, bad)

    def test_loaders_use_safe_load(self):
        ws = self.tmp / "ws"
        init_workspace(ws)
        (ws / "site.yaml").write_text("x: !!python/object/apply:os.getcwd []\n")
        with self.assertRaises(yaml.YAMLError):
            load_site(ws)


class PreviousTests(TempHome):
    def fake_install(self, name: str, *, uid: int, port: int, host: str, vm: str, secret: bool) -> Path:
        ws = self.tmp / "installs" / name
        init_workspace(ws)
        (ws / "site.yaml").write_text(yaml.safe_dump(
            {"domain": "example.duckdns.org", "hosts": {f"host-{name}": {"node": f"pve-{name}"}}}))
        svc = ws / "services" / f"svc-{name}"
        svc.mkdir()
        (svc / "service.yaml").write_text(yaml.safe_dump(
            {"name": f"svc-{name}", "vm": vm, "uid": uid, "port": port, "hostname": host}))
        if secret:
            (ws / "secrets" / "proxmox-a.token").write_text("SENTINEL-NOT-TO-LEAK")
        return ws

    def test_scan_previous_collects_used_ids(self):
        one = self.fake_install("one", uid=3101, port=4096, host="one.example.duckdns.org", vm="ai", secret=True)
        two = self.fake_install("two", uid=3102, port=4097, host="two.example.duckdns.org", vm="ai", secret=False)
        three = self.fake_install("three", uid=3103, port=8080, host="three.example.duckdns.org", vm="other", secret=False)
        result = scan_previous([one, two, three, self.tmp / "missing"])
        self.assertEqual(result["used"]["uids"], {3101, 3102, 3103})
        self.assertEqual(result["used"]["ports"], {"ai": {4096, 4097}, "other": {8080}})
        self.assertEqual(result["used"]["hostnames"], {
            "one.example.duckdns.org", "two.example.duckdns.org", "three.example.duckdns.org"})
        self.assertEqual(result["site"]["domain"], "example.duckdns.org")
        self.assertEqual(set(result["site"]["hosts"]), {"host-one", "host-two", "host-three"})
        self.assertEqual(result["secret_files"], [one / "secrets" / "proxmox-a.token"])
        self.assertNotIn("SENTINEL", repr(result))

    def test_scan_previous_accepts_folder_of_installs(self):
        self.fake_install("one", uid=3101, port=4096, host="one.example.duckdns.org", vm="ai", secret=False)
        self.fake_install("two", uid=3102, port=4097, host="two.example.duckdns.org", vm="ai", secret=False)
        result = scan_previous([self.tmp / "installs"])
        self.assertEqual(result["used"]["uids"], {3101, 3102})

    def test_scan_previous_ignores_symlinked_secret(self):
        ws = self.fake_install("one", uid=3101, port=4096, host="one.example.duckdns.org", vm="ai", secret=False)
        (ws / "secrets" / "link").symlink_to(self.tmp)
        self.assertEqual(scan_previous([ws])["secret_files"], [])

    def test_cli_previous_prints_flags_not_contents(self):
        one = self.fake_install("one", uid=3101, port=4096, host="one.example.duckdns.org", vm="ai", secret=True)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(workspace.main(["previous", str(one)]), 0)
        data = json.loads(out.getvalue())
        self.assertEqual(data["used"]["uids"], [3101])
        self.assertEqual(data["secret_files"], {str(one / "secrets" / "proxmox-a.token"): True})
        self.assertNotIn("SENTINEL", out.getvalue())

    def test_cli_init_and_where(self):
        ws = self.tmp / "cli-ws"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(workspace.main(["init", str(ws)]), 0)
            self.assertEqual(workspace.main(["where"]), 0)
        self.assertTrue((ws / "site.yaml").is_file())
        self.assertEqual(out.getvalue().split().count(str(ws)), 2)

    def test_cli_where_unset_fails(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(workspace.main(["where"]), 1)
        self.assertIn("workspace", err.getvalue())


class SiteExampleTests(unittest.TestCase):
    def test_site_example_has_no_entries(self):
        site = yaml.safe_load((ROOT / "site.example.yaml").read_text())
        for key in ("vms", "services", "shared_groups"):
            self.assertEqual(site[key], [], key)

    def test_site_example_roles(self):
        site = yaml.safe_load((ROOT / "site.example.yaml").read_text())
        self.assertEqual(
            site["roles"],
            {role: {"provider": "ASK"} for role in
             ("virtualization", "router_firewall", "file_server", "dns_certificates")})

    def test_config_example_is_gone(self):
        self.assertFalse((ROOT / "config.example.yaml").exists())


if __name__ == "__main__":
    unittest.main()
