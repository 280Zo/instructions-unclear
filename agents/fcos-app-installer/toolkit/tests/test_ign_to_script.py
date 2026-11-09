import base64
import copy
import gzip
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from ign_to_script import UnsupportedIgnition, to_script  # noqa: E402


def data_url(text: str, compress: bool = False) -> dict:
    raw = text.encode()
    if compress:
        raw = gzip.compress(raw)
        return {"compression": "gzip", "source": "data:;base64," + base64.b64encode(raw).decode()}
    return {"source": "data:;base64," + base64.b64encode(raw).decode()}


SAMPLE = {
    "ignition": {"version": "3.6.0"},
    "passwd": {
        "groups": [{"name": "opencode", "gid": 3101}],
        "users": [{"name": "opencode", "uid": 3101, "primaryGroup": "opencode",
                   "groups": ["ai-projects"], "shell": "/sbin/nologin"}],
    },
    "storage": {
        "directories": [{"path": "/var/lib/appdata/opencode", "mode": 0o750,
                         "user": {"id": 3101}, "group": {"id": 3101}}],
        "files": [
            {"path": "/etc/containers/systemd/users/3101/opencode.container", "mode": 0o644,
             "contents": data_url("[Container]\nImage=x:1\n$HOME 'quote'\n", compress=True)},
            {"path": "/var/lib/systemd/linger/opencode", "mode": 0o644},
        ],
        "links": [{"path": "/etc/systemd/user/timers.target.wants/a.timer",
                   "target": "/etc/systemd/user/a.timer", "hard": False}],
    },
    "systemd": {"units": [{"name": "virt-use-nfs.service", "enabled": True,
                           "contents": "[Service]\nType=oneshot\n"}]},
}


# FCOS's own layout links (ostree layout): every
# run of a generated script happens in a tree shaped like this.
FCOS_LINKS = {"usr/local": "../var/usrlocal", "home": "var/home", "mnt": "var/mnt", "opt": "var/opt",
              "srv": "var/srv", "root": "var/roothome"}


def fcos_root(root) -> str:
    for link, target in FCOS_LINKS.items():
        path = Path(root, link)
        if not path.exists() and not path.is_symlink():
            path.parent.mkdir(parents=True, exist_ok=True)
            (path.parent / target).mkdir(parents=True, exist_ok=True)
            path.symlink_to(target)
    return str(root)


class IgnToScriptTests(unittest.TestCase):
    def setUp(self):
        self.script = to_script(SAMPLE)

    def test_strict_shell(self):
        self.assertTrue(self.script.startswith("#!/bin/bash\nset -euo pipefail\n"))

    def test_groups_and_users_idempotent(self):
        self.assertIn("getent group opencode >/dev/null || priv groupadd -g 3101 opencode", self.script)
        self.assertIn("id -u opencode >/dev/null 2>&1 || priv useradd -u 3101 -g opencode -G ai-projects -s /sbin/nologin -m opencode", self.script)

    def test_existing_account_gets_missing_extra_groups(self):
        # An account created by an earlier push lacked a group added to its spec later (an app and
        # its library's group): useradd is skipped for an existing account, so the group must be added.
        line = '[[ " $(id -nG opencode) " == *" ai-projects "* ]] || priv usermod -aG ai-projects opencode'
        self.assertIn(line, self.script)
        self.assertLess(self.script.index("priv groupadd -g 3101 opencode"), self.script.index(line))
        self.assertLess(self.script.index("priv useradd -u 3101"), self.script.index(line))
        for groups, ran in (("opencode ai-projects", ""), ("opencode", "usermod -aG ai-projects opencode"),
                            ("opencode ai-projects-old", "usermod -aG ai-projects opencode")):
            with self.subTest(groups=groups):
                fake = f'id() {{ echo "{groups}"; }}; priv() {{ echo "$*"; }}; set -euo pipefail; {line}'
                result = subprocess.run(["bash", "-c", fake], capture_output=True, text=True)
                self.assertEqual(result.stdout.strip(), ran, result.stderr)
        no_extra = copy.deepcopy(SAMPLE)
        for user in no_extra["passwd"]["users"]:
            user.pop("groups", None)
        self.assertNotIn("usermod", to_script(no_extra))

    def test_directories(self):
        self.assertIn("newdir 0750 3101:3101 /var/lib/appdata/opencode", self.script)

    def test_existing_directory_keeps_its_owner_and_mode(self):
        # MariaDB had taken over its data folder; re-applying the
        # fragment's owner on a push locked it out. Ignition only sets them on creation.
        with tempfile.TemporaryDirectory() as root:
            data = Path(root, "var/lib/appdata/opencode")
            data.mkdir(parents=True)
            data.chmod(0o700)
            result = self.run_in(root, SAMPLE)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"kept: {data}", result.stdout)
            self.assertEqual(data.stat().st_mode & 0o777, 0o700)
            self.assertNotIn(f"skip: chown -h 3101:3101 {data}", result.stdout)

    def test_missing_directory_is_created_with_owner_and_mode(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.run_in(root, SAMPLE)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = Path(root, "var/lib/appdata/opencode")
            self.assertEqual(data.stat().st_mode & 0o777, 0o750)
            self.assertIn(f"skip: chown -h 3101:3101 {data}", result.stdout)

    def test_fcos_layout_links_are_followed(self):
        # On FCOS /usr/local is a symlink to ../var/usrlocal (owned by root),
        # so every /usr/local/bin file was refused.
        with tempfile.TemporaryDirectory() as root:
            Path(root, "usr").mkdir()
            Path(root, "var/usrlocal/bin").mkdir(parents=True)
            Path(root, "usr/local").symlink_to("../var/usrlocal")
            config = {"storage": {"files": [{"path": "/usr/local/bin/backup", "overwrite": True, "mode": 0o755,
                                             "contents": data_url("#!/bin/sh\n")}],
                                  "directories": [{"path": "/usr/local/lib/x"}]}}
            result = self.run_in(root, config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(root, "var/usrlocal/bin/backup").read_text(), "#!/bin/sh\n")
            self.assertTrue(Path(root, "var/usrlocal/lib/x").is_dir())

    def test_declared_folders_come_first_across_fragments(self):
        # A later fragment's declared folder must not be pre-created
        # (root, 0755) by an earlier fragment's file and then "kept".
        a = {"storage": {"files": [{"path": "/var/lib/appdata/x/sub/f", "overwrite": True, "contents": data_url("1")}]}}
        b = {"storage": {"directories": [{"path": "/var/lib/appdata/x", "mode": 0o750,
                                          "user": {"id": 3101}, "group": {"id": 3101}}]}}
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as tmp:
            files = []
            for name, cfg in (("a.ign", a), ("b.ign", b)):
                Path(tmp, name).write_text(json.dumps(cfg))
                files.append(str(Path(tmp, name)))
            script = subprocess.run([sys.executable, str(ROOT / "tools" / "ign_to_script.py"), "--root", root, *files],
                                    capture_output=True, text=True, check=True).stdout
            result = subprocess.run(["bash", "-c", script], capture_output=True, text=True,
                                    env={"PATH": "/usr/bin:/bin", "IGN_DRY_RUN": "1"})
            self.assertEqual(result.returncode, 0, result.stderr)
            x = Path(root, "var/lib/appdata/x")
            self.assertEqual(x.stat().st_mode & 0o777, 0o750)
            self.assertIn(f"skip: chown -h 3101:3101 {x}", result.stdout)

    def test_accounts_come_before_the_shared_folders(self):
        # A folder owned by name needs its account first, even from a later fragment.
        a = {"storage": {"directories": [{"path": "/var/lib/appdata/y", "user": {"name": "svcy"},
                                          "group": {"name": "svcy"}}]}}
        b = {"passwd": {"groups": [{"name": "svcy", "gid": 3150}],
                        "users": [{"name": "svcy", "uid": 3150, "primaryGroup": "svcy"}]}}
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for name, cfg in (("a.ign", a), ("b.ign", b)):
                Path(tmp, name).write_text(json.dumps(cfg))
                files.append(str(Path(tmp, name)))
            script = subprocess.run([sys.executable, str(ROOT / "tools" / "ign_to_script.py"), *files],
                                    capture_output=True, text=True, check=True).stdout
        self.assertLess(script.index("priv useradd -u 3150"), script.index("newdir 0755 svcy:svcy /var/lib/appdata/y"))
        self.assertEqual(script.count("priv useradd -u 3150"), 1)

    def test_the_same_folder_in_two_fragments_uses_the_last(self):
        a = {"storage": {"directories": [{"path": "/var/lib/appdata/z", "mode": 0o755}]}}
        b = {"storage": {"directories": [{"path": "/var/lib/appdata/z", "mode": 0o750}]}}
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for name, cfg in (("a.ign", a), ("b.ign", b)):
                Path(tmp, name).write_text(json.dumps(cfg))
                files.append(str(Path(tmp, name)))
            script = subprocess.run([sys.executable, str(ROOT / "tools" / "ign_to_script.py"), *files],
                                    capture_output=True, text=True, check=True).stdout
        self.assertEqual(script.count("/var/lib/appdata/z"), 1)
        self.assertIn("newdir 0750 '' /var/lib/appdata/z", script)

    def test_declared_folders_shallowest_first(self):
        cfg = {"storage": {"directories": [{"path": "/var/lib/appdata/x/deep", "mode": 0o700},
                                           {"path": "/var/lib/appdata/x", "mode": 0o750}]}}
        with tempfile.TemporaryDirectory() as root:
            result = self.run_in(root, cfg)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(root, "var/lib/appdata/x").stat().st_mode & 0o777, 0o750)

    def test_kept_says_what_differs(self):
        with tempfile.TemporaryDirectory() as root:
            data = Path(root, "var/lib/appdata/opencode")
            data.mkdir(parents=True)
            data.chmod(0o755)
            result = self.run_in(root, SAMPLE)
            self.assertIn(f"kept: {data} (is 755", result.stdout)
            self.assertIn("fragment says 750 3101:3101)", result.stdout)

    def run_as_root_runner(self, root, config):
        # Pretend the runner is root: folders the test user owns then count as a service's.
        fcos_root(root)
        return subprocess.run(["bash", "-c", to_script(config, root=root)], capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin", "IGN_DRY_RUN": "1", "IGN_TEST_RUNNER_UID": "0"})

    def test_writes_inside_a_service_folder_happen_as_that_account(self):
        # Root writing by path into a folder a service owns can be raced
        # with a planted symlink; writing as the service account limits it to what that account can write.
        import os
        me = f"{os.getuid()}:{os.getgid()}"
        with tempfile.TemporaryDirectory() as root:
            Path(root, "var/lib/appdata/svc").mkdir(parents=True)
            config = {"storage": {"files": [{"path": "/var/lib/appdata/svc/conf/a.yml", "overwrite": True,
                                             "contents": data_url("x")}],
                                  "directories": [{"path": "/var/lib/appdata/svc/new"}]}}
            result = self.run_as_root_runner(root, config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"as {me}: mv -f", result.stdout)
            self.assertIn(f"as {me}: install -d", result.stdout)
            self.assertEqual(Path(root, "var/lib/appdata/svc/conf/a.yml").read_text(), "x")

    def test_a_service_folder_file_for_another_account_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "var/lib/appdata/svc").mkdir(parents=True)
            config = {"storage": {"files": [{"path": "/var/lib/appdata/svc/a.yml", "overwrite": True,
                                             "user": {"id": 4242}, "group": {"id": 4242}, "contents": data_url("x")}]}}
            result = self.run_as_root_runner(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STOP", result.stderr)
            self.assertFalse(Path(root, "var/lib/appdata/svc/a.yml").exists())

    def test_a_runner_folder_others_can_write_stops(self):
        # Never "write as uid 0" in a folder a group or everyone can write.
        with tempfile.TemporaryDirectory() as root:
            shared = Path(root, "var/lib/appdata/shared")
            shared.mkdir(parents=True)
            shared.chmod(0o770)
            config = {"storage": {"files": [{"path": "/var/lib/appdata/shared/a", "overwrite": True,
                                             "contents": data_url("x")}]}}
            result = self.run_in(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("writable by others", result.stderr)
            self.assertFalse(Path(shared, "a").exists())

    def test_a_service_folder_others_can_write_stops(self):
        with tempfile.TemporaryDirectory() as root:
            svc = Path(root, "var/lib/appdata/svc")
            svc.mkdir(parents=True)
            svc.chmod(0o770)
            config = {"storage": {"files": [{"path": "/var/lib/appdata/svc/a", "overwrite": True,
                                             "contents": data_url("x")}]}}
            result = self.run_as_root_runner(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("writable by others", result.stderr)

    def test_links_inside_a_service_folder_are_made_as_that_account(self):
        import os
        with tempfile.TemporaryDirectory() as root:
            Path(root, "var/lib/appdata/svc").mkdir(parents=True)
            config = {"storage": {"links": [{"path": "/var/lib/appdata/svc/l", "target": "/var/lib/appdata/svc/t"}]}}
            result = self.run_as_root_runner(root, config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"as {os.getuid()}:{os.getgid()}: ln -sfn", result.stdout)

    def test_bad_folder_entries_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.ign").write_text(json.dumps({"storage": {"directories": ["not-a-mapping"]}}))
            result = subprocess.run([sys.executable, str(ROOT / "tools" / "ign_to_script.py"), str(Path(tmp, "a.ign"))],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_guide_push_uses_a_unique_temp_file(self):
        guide = (ROOT / "docs" / "guide" / "03-add-a-service.md").read_text()
        for line in guide.splitlines():
            if "sudo bash" in line and "vmssh.py run" in line:
                with self.subTest(line=line[:60]):
                    self.assertNotIn("/tmp/apply.sh", line)
                    self.assertIn("mktemp", line)

    def test_root_owned_paths_are_written_by_the_runner(self):
        with tempfile.TemporaryDirectory() as root:
            config = {"storage": {"files": [{"path": "/etc/x.conf", "overwrite": True, "contents": data_url("x")}]}}
            result = self.run_in(root, config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("as ", result.stdout)

    def test_runs_happen_in_an_fcos_shaped_tree(self):
        with tempfile.TemporaryDirectory() as root:
            self.run_in(root, {"storage": {}})
            self.assertEqual(Path(root, "usr/local").readlink(), Path("../var/usrlocal"))
            config = {"storage": {"files": [{"path": "/usr/local/bin/x", "overwrite": True, "contents": data_url("1")}]}}
            result = self.run_in(root, config)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(Path(root, "var/usrlocal/bin/x").read_text(), "1")

    def test_a_layout_link_whose_target_is_a_link_is_refused(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as elsewhere:
            Path(root, "usr").mkdir()
            Path(root, "var").mkdir()
            Path(root, "var/usrlocal").symlink_to(elsewhere)
            Path(root, "usr/local").symlink_to("../var/usrlocal")
            config = {"storage": {"files": [{"path": "/usr/local/bin/backup", "overwrite": True,
                                             "contents": data_url("x")}]}}
            result = self.run_in(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(elsewhere).iterdir()), [])

    def test_a_layout_link_pointing_elsewhere_is_refused(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as elsewhere:
            Path(root, "usr").mkdir()
            Path(root, "usr/local").symlink_to(elsewhere)
            config = {"storage": {"files": [{"path": "/usr/local/bin/backup", "overwrite": True,
                                             "contents": data_url("x")}]}}
            result = self.run_in(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STOP", result.stderr)
            self.assertEqual(list(Path(elsewhere).iterdir()), [])

    def test_file_contents_roundtrip(self):
        with tempfile.TemporaryDirectory() as root:
            script = to_script(SAMPLE, root=fcos_root(root))
            subprocess.run(["bash", "-c", script], check=True,
                           env={"PATH": "/usr/bin:/bin", "IGN_DRY_RUN": "1"})
            written = Path(root, "etc/containers/systemd/users/3101/opencode.container").read_text()
            self.assertEqual(written, "[Container]\nImage=x:1\n$HOME 'quote'\n")
            self.assertTrue(Path(root, "var/lib/systemd/linger/opencode").exists())
            self.assertEqual(Path(root, "etc/systemd/user/timers.target.wants/a.timer").readlink(),
                             Path("/etc/systemd/user/a.timer"))

    def test_units_enabled(self):
        self.assertIn("/etc/systemd/system/virt-use-nfs.service", self.script)
        self.assertIn("priv systemctl enable virt-use-nfs.service", self.script)
        self.assertIn("priv systemctl daemon-reload", self.script)

    def run_in(self, root, config, fcos=True):
        if fcos:
            fcos_root(root)
        return subprocess.run(["bash", "-c", to_script(config, root=root)], capture_output=True, text=True,
                              env={"PATH": "/usr/bin:/bin", "IGN_DRY_RUN": "1"})

    def test_ign_script_refuses_symlinked_path(self):
        # A container could plant a symlink in a folder its user owns; root must not follow it.
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as elsewhere:
            appdata = Path(root, "var/lib/appdata")
            appdata.mkdir(parents=True)
            Path(appdata, "opencode").symlink_to(elsewhere)
            config = {"storage": {"files": [{"path": "/var/lib/appdata/opencode/x.yml", "overwrite": True,
                                             "contents": data_url("hi")}]}}
            result = self.run_in(root, config)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("STOP", result.stderr)
            self.assertEqual(list(Path(elsewhere).iterdir()), [])
            config = {"storage": {"directories": [{"path": "/var/lib/appdata/opencode/sub"}]}}
            self.assertNotEqual(self.run_in(root, config).returncode, 0)
            self.assertEqual(list(Path(elsewhere).iterdir()), [])
            # A symlink at the file itself is refused too.
            Path(appdata, "opencode").unlink()
            Path(appdata, "opencode").mkdir()
            Path(appdata, "opencode", "x.yml").symlink_to(Path(elsewhere, "target"))
            config = {"storage": {"files": [{"path": "/var/lib/appdata/opencode/x.yml", "overwrite": True,
                                             "contents": data_url("hi")}]}}
            self.assertNotEqual(self.run_in(root, config).returncode, 0)
            self.assertFalse(Path(elsewhere, "target").exists())

    def test_temp_file_is_owned_before_it_is_moved_in_place(self):
        script = to_script({"storage": {"files": [{"path": "/var/lib/appdata/x/a", "user": {"id": 3101},
                                                   "group": {"id": 3101}, "overwrite": True}]}})
        self.assertIn("put 0644 3101:3101 1 /var/lib/appdata/x/a ''", script)
        header = script.split("put()", 1)[1]
        self.assertLess(header.index('priv chown "$owner" "$tmp"'), header.index('mv -f "$tmp" "$path"'))

    def test_ign_script_honours_overwrite_false(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root, "etc/x.conf")
            target.parent.mkdir(parents=True)
            keep = {"storage": {"files": [{"path": "/etc/x.conf", "contents": data_url("same")}]}}
            target.write_text("same")
            result = self.run_in(root, keep)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("unchanged: ", result.stdout)
            target.write_text("different")
            result = self.run_in(root, keep)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overwrite: false", result.stderr)
            self.assertEqual(target.read_text(), "different")
            replace = {"storage": {"files": [{"path": "/etc/x.conf", "overwrite": True,
                                              "contents": data_url("new")}]}}
            self.assertEqual(self.run_in(root, replace).returncode, 0)
            self.assertEqual(target.read_text(), "new")

    def test_ign_script_disables_units(self):
        script = to_script({"systemd": {"units": [{"name": "old.timer", "enabled": False},
                                                  {"name": "new.timer", "enabled": True},
                                                  {"name": "plain.service"}]}})
        self.assertIn("priv systemctl disable old.timer", script)
        self.assertIn("priv systemctl enable new.timer", script)
        self.assertNotIn("plain.service", script.split("daemon-reload", 1)[1])

    def test_rejects_disks_and_credentials(self):
        for bad in ({"storage": {"filesystems": [{}]}}, {"storage": {"disks": [{}]}},
                    {"passwd": {"users": [{"name": "x", "passwordHash": "h"}]}},
                    {"passwd": {"users": [{"name": "x", "sshAuthorizedKeys": ["k"]}]}},
                    {"ignition": {"config": {"merge": [{}]}}},
                    {"storage": {"files": [{"path": "/x", "contents": {"source": "https://evil"}}]}},
                    {"storage": {"files": [{"path": "relative/x"}]}},
                    {"storage": {"files": [{"path": "/etc/../x"}]}}):
            with self.subTest(bad=bad):
                with self.assertRaises(UnsupportedIgnition):
                    to_script(bad)

    def test_cli_combines_and_fails_whole(self):
        good = tempfile.NamedTemporaryFile("w", suffix=".ign", delete=False)
        json.dump(SAMPLE, good)
        good.close()
        bad = tempfile.NamedTemporaryFile("w", suffix=".ign", delete=False)
        json.dump({"storage": {"filesystems": [{}]}}, bad)
        bad.close()
        tool = str(ROOT / "tools/ign_to_script.py")
        both = subprocess.run([sys.executable, tool, good.name, good.name],
                              check=True, capture_output=True, text=True).stdout
        self.assertEqual(both.count("#!/bin/bash"), 1)
        self.assertEqual(both.count("groupadd -g 3101 opencode"), 2)
        failed = subprocess.run([sys.executable, tool, good.name, bad.name],
                                capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(failed.stdout, "")

    def test_a_name_with_a_trailing_newline_is_refused_not_split_into_two_commands(self):
        for bad in ({"passwd": {"groups": [{"name": "foo\n", "gid": 3101}]}},
                    {"passwd": {"users": [{"name": "foo\n", "uid": 3101}]}},
                    {"systemd": {"units": [{"name": "x.service\n", "enabled": True}]}}):
            with self.subTest(bad=bad), self.assertRaises(UnsupportedIgnition):
                to_script(bad)

    def test_ids_must_be_plain_non_negative_numbers_and_base64_must_be_valid(self):
        owner = lambda ident: {"storage": {"files": [{"path": "/etc/x", "user": {"id": ident}}]}}  # noqa: E731
        for bad in (owner(-1), owner(True), owner("1"), owner(1.5), owner(None),
                    {"storage": {"files": [{"path": "/etc/x", "group": {"id": -5}}]}},
                    {"passwd": {"groups": [{"name": "g", "gid": -1}]}},
                    {"passwd": {"groups": [{"name": "g", "gid": True}]}},
                    {"passwd": {"users": [{"name": "u", "uid": -1}]}},
                    {"passwd": {"users": [{"name": "u", "uid": True}]}},
                    {"storage": {"files": [{"path": "/etc/x", "contents": {"source": "data:;base64,@@@@"}}]}},
                    {"storage": {"files": [{"path": "/etc/x", "contents": {"source": "data:;base64,QUJD!"}}]}}):
            with self.subTest(bad=bad), self.assertRaises(UnsupportedIgnition):
                to_script(bad)
        to_script(owner(0))
        to_script({"passwd": {"users": [{"name": "u", "uid": 3101}], "groups": [{"name": "g", "gid": 3101}]}})

    def test_wrong_typed_or_broken_fragments_are_an_error_line_not_a_traceback(self):
        import base64
        bad_gzip = "data:;base64," + base64.b64encode(b"not gzip").decode()
        cases = {"source a number": {"storage": {"files": [{"path": "/etc/x", "contents": {"source": 5}}]}},
                 "config a list": [],
                 "unit contents a number": {"systemd": {"units": [{"name": "x.service", "contents": 5}]}},
                 "bad gzip": {"storage": {"files": [{"path": "/etc/x", "contents": {
                     "source": bad_gzip, "compression": "gzip"}}]}}}
        tool = str(ROOT / "tools/ign_to_script.py")
        for label, config in cases.items():
            with self.subTest(case=label), tempfile.NamedTemporaryFile("w", suffix=".ign") as handle:
                json.dump(config, handle)
                handle.flush()
                result = subprocess.run([sys.executable, tool, handle.name], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("ign_to_script:", result.stderr)

    def test_cli_reads_ign(self):
        with tempfile.NamedTemporaryFile("w", suffix=".ign", delete=False) as handle:
            json.dump(SAMPLE, handle)
        out = subprocess.run([sys.executable, str(ROOT / "tools/ign_to_script.py"), handle.name],
                             check=True, capture_output=True, text=True).stdout
        self.assertIn("groupadd -g 3101 opencode", out)


if __name__ == "__main__":
    unittest.main()
