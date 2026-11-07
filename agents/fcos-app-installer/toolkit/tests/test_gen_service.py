import copy
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gen_service import SpecError, generate, validate_spec  # noqa: E402
from render import load_values, render  # noqa: E402
from secret_scan import scan_text  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None

SITE = {
    "domain": "example.duckdns.org",
    "admin_user": "admin",
    "backups": {"keep": 14, "oncalendar": "*-*-* 02:15:00",
                "sqlite_image": "docker.io/library/python:3-alpine"},
    "roles": {"dns_certificates": {"provider": "duckdns"}},
    "login_frontend": {"ingress": "ingress-traefik", "auth_gateway": "authgw-authentik"},
    "edge": {"traefik": {"uid": 3202, "gid": 3202}, "authentik": {"uid": 3201, "gid": 3201}},
    "vms": [
        {"name": "ai", "ip": "192.0.2.20",
         "nfs_shares": [{"name": "projects", "export": "/mnt/pool/projects"},
                        {"name": "backups", "export": "/mnt/pool/backups"}]},
        {"name": "apps", "ip": "192.0.2.30", "nfs_shares": [{"name": "backups", "export": "/mnt/pool/backups"}]},
        {"name": "edge", "ip": "192.0.2.10", "nfs_shares": [{"name": "backups", "export": "/mnt/pool/backups"}]},
    ],
}


def spec_fixture(name: str) -> dict:
    return yaml.safe_load((FIXTURES / "services" / f"{name}.yaml").read_text())


def directives(text: str, key: str) -> list[str]:
    return [line.split("=", 1)[1] for line in text.splitlines() if line.startswith(f"{key}=")]


def butane_files(text: str) -> dict:
    """Parse a Butane fragment and return {path: file entry}."""
    data = yaml.safe_load(text)
    return {entry["path"]: entry for entry in data.get("storage", {}).get("files", [])}


def inline(entries: dict, path: str) -> str:
    return entries[path]["contents"]["inline"]


class GenCase(unittest.TestCase):
    def tmpdir(self) -> Path:
        path = tempfile.mkdtemp(prefix="gen-service-", dir=SCRATCH)
        self.addCleanup(shutil.rmtree, path, True)
        return Path(path)

    def gen(self, spec, site=None) -> Path:
        if isinstance(spec, str):
            spec = spec_fixture(spec)
        out = self.tmpdir()
        generate(spec, copy.deepcopy(SITE if site is None else site), out)
        return out

    def read(self, out: Path, rel: str) -> str:
        return (out / "rendered" / rel).read_text()

    def fragment(self, out: Path, rel: str) -> dict:
        return butane_files(self.read(out, rel))

    def errors(self, mutate, base="single", site=None) -> list[str]:
        spec = spec_fixture(base)
        mutate(spec)
        return validate_spec(spec, copy.deepcopy(SITE if site is None else site))


class WrongShapeTests(GenCase):
    """A spec or site with a value of the wrong type is an error line, never a traceback, and writes nothing."""

    def run_main(self, spec, site):
        import contextlib
        import io
        import gen_service
        tmp = self.tmpdir()
        (tmp / "spec.yaml").write_text(yaml.safe_dump(spec))
        (tmp / "site.yaml").write_text(yaml.safe_dump(site))
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = gen_service.main(["gen_service.py", str(tmp / "spec.yaml"), str(tmp / "site.yaml"), str(tmp / "out")])
        return code, err.getvalue(), tmp

    def test_wrong_typed_values_give_one_error_line_and_write_nothing(self):
        cases = {
            "container name a list": lambda s, site: s["containers"][0].update(name=["x"]),
            "containers a string": lambda s, site: s.update(containers="x"),
            "vm a list": lambda s, site: s.update(vm=["a"]),
            "volumes a number": lambda s, site: s["containers"][0].update(volumes=5),
            "uid a list": lambda s, site: s.update(uid=[1]),
            "vms in the site a string": lambda s, site: site.update(vms="x"),
            "secrets a number": lambda s, site: s["containers"][0].update(secrets=3),
        }
        for label, mutate in cases.items():
            spec, site = spec_fixture("single"), copy.deepcopy(SITE)
            mutate(spec, site)
            with self.subTest(case=label):
                code, err, tmp = self.run_main(spec, site)
                self.assertEqual(code, 1, err)
                self.assertNotIn("Traceback", err)
                self.assertTrue(err.startswith("gen_service:"), err)
                self.assertFalse((tmp / "out").exists())


class OutputFolderTests(GenCase):
    """The generators run without asking and delete files an earlier run wrote, so their output folder may not
    be the toolkit, a folder in it, or one that holds it (a planted manifest there could name toolkit files)."""

    def test_the_toolkit_its_folders_and_its_parents_are_refused(self):
        for folder in (ROOT, ROOT / "templates", ROOT / "tools", ROOT / "docs", ROOT.parent, ROOT.parent.parent,
                       ROOT / "templates" / ".." / "tools"):
            with self.subTest(folder=str(folder)):
                before = sorted(p.name for p in ROOT.iterdir())
                with self.assertRaises(SpecError) as caught:
                    generate(spec_fixture("single"), copy.deepcopy(SITE), folder)
                self.assertIn("output folder", str(caught.exception))
                self.assertEqual(sorted(p.name for p in ROOT.iterdir()), before)

    def test_a_planted_manifest_cannot_delete_a_toolkit_file(self):
        name = spec_fixture("single")["name"]
        parent = self.tmpdir()
        (parent / "keep.txt").write_text("x")
        (parent / f".gen-service-{name}.json").write_text(json.dumps(["keep.txt"]))
        generate(spec_fixture("single"), copy.deepcopy(SITE), parent)  # an ordinary folder: stale entries go
        self.assertFalse((parent / "keep.txt").exists())
        victim = ROOT / "tools" / "redact.py"
        planted = ROOT.parent / f".gen-service-{name}.json"
        planted.write_text(json.dumps([f"{ROOT.name}/tools/redact.py"]))
        try:
            with self.assertRaises(SpecError):
                generate(spec_fixture("single"), copy.deepcopy(SITE), ROOT.parent)
        finally:
            planted.unlink()
        self.assertTrue(victim.exists())

    def test_a_link_inside_the_output_folder_is_never_written_through(self):
        name = spec_fixture("single")["name"]
        # A manifest that is a link to another file: the link goes, the file is left alone.
        out = self.tmpdir()
        decoy = self.tmpdir() / "decoy.txt"
        decoy.write_text("precious")
        (out / f".gen-service-{name}.json").symlink_to(decoy)
        generate(spec_fixture("single"), copy.deepcopy(SITE), out)
        self.assertEqual(decoy.read_text(), "precious")
        self.assertFalse((out / f".gen-service-{name}.json").is_symlink())
        # A folder inside it that is a link out: nothing is written through it.
        out2, victim = self.tmpdir(), self.tmpdir()
        (out2 / "rendered").symlink_to(victim)
        with self.assertRaises(SpecError) as caught:
            generate(spec_fixture("single"), copy.deepcopy(SITE), out2)
        self.assertIn("link", str(caught.exception))
        self.assertEqual(list(victim.iterdir()), [])
        # Every path is checked before the first file is written: nothing else came out either.
        self.assertEqual([p.name for p in out2.iterdir()], ["rendered"])

    def test_forgetting_a_module_does_not_follow_a_linked_manifest(self):
        from gen_service import forget_other_services
        out, decoy = self.tmpdir(), self.tmpdir() / "decoy.txt"
        decoy.write_text("precious")
        (out / ".gen-service-oldproxy.json").symlink_to(decoy)
        forget_other_services(out, {"keep"})
        self.assertEqual(decoy.read_text(), "precious")
        self.assertFalse(list(out.glob(".gen-service-*")))

    def test_an_ordinary_folder_and_the_scratch_folder_are_fine(self):
        self.assertTrue((self.gen("single") / "rendered").is_dir())


class HardeningTests(GenCase):
    def test_fixtures_are_valid(self):
        for name in ("single", "crm", "authentik"):
            with self.subTest(fixture=name):
                self.assertEqual(validate_spec(spec_fixture(name), SITE), [])

    def test_single_container_matches_v1_hardening(self):
        out = self.gen("single")
        container = self.read(out, "files/opencode-app.container")
        lines = container.splitlines()
        for line in ("UserNS=keep-id", "NoNewPrivileges=true", "DropCapability=ALL",
                     "AutoUpdate=registry", "ContainerName=opencode-app"):
            self.assertIn(line, lines)
        self.assertNotIn("AddCapability", container)
        image = directives(container, "Image")[0]
        self.assertRegex(image, r":[^/]+$", "image must carry a tag")
        self.assertFalse(image.endswith(":latest"))
        self.assertEqual(directives(container, "ExecStartPre"),
                         ["/usr/local/bin/require-mounts /var/lib/appdata /var/mnt/projects"])

    def test_volume_mounts_under_checked_roots(self):
        container = self.read(self.gen("single"), "files/opencode-app.container")
        roots = ["/var/lib/appdata", "/var/mnt/projects"]
        volumes = directives(container, "Volume")
        self.assertEqual(len(volumes), 3)
        for volume in volumes:
            host = volume.split(":", 1)[0]
            self.assertTrue(any(host == r or host.startswith(r + "/") for r in roots), host)

    def test_data_disk_volumes_use_z_and_nfs_never_labeled(self):
        volumes = directives(self.read(self.gen("single"), "files/opencode-app.container"), "Volume")
        self.assertIn("/var/lib/appdata/opencode/db/app:/data/db:z", volumes)
        self.assertIn("/var/lib/appdata/opencode/data-config:/data/config:z", volumes)
        self.assertIn("/var/mnt/projects/ai:/projects", volumes)
        for volume in volumes:
            if volume.startswith("/var/mnt/"):
                self.assertNotRegex(volume, r":(?:[^:]*,)?[zZ](?:,|$)")

    def test_publish_on_vm_ip(self):
        container = self.read(self.gen("single"), "files/opencode-app.container")
        self.assertEqual(directives(container, "PublishPort"), ["192.0.2.20:4096:4096"])

    def test_secrets_and_escaped_environment(self):
        container = self.read(self.gen("single"), "files/opencode-app.container")
        self.assertIn("Secret=opencode_model_api,type=env,target=MODEL_API", container.splitlines())
        # systemd would expand $ and % in ExecStart, so both are doubled.
        self.assertIn('Environment="LOG_FORMAT=%%d $$x"', container.splitlines())
        self.assertIn('Environment="TZ=UTC"', container.splitlines())

    def test_command_is_quoted_for_systemd(self):
        spec = spec_fixture("single")
        spec["containers"][0]["command"] = ["sh", "-c", 'echo $HOME 100% "q"']
        container = self.read(self.gen(spec), "files/opencode-app.container")
        self.assertIn(r'Exec=sh -c "echo $$HOME 100%% \"q\""', container.splitlines())

    def test_service_user_not_system(self):
        out = self.gen("single")
        text = self.read(out, "opencode.bu")
        data = yaml.safe_load(text)
        user = data["passwd"]["users"][0]
        self.assertEqual((user["name"], user["uid"], user["primary_group"]), ("opencode", 3101, "opencode"))
        self.assertEqual(user["groups"], ["ai-projects"])
        self.assertNotIn("system: true", text)
        files = butane_files(text)
        self.assertIn("/var/lib/systemd/linger/opencode", files)
        self.assertEqual(files["/etc/containers/systemd/users/3101/opencode-app.container"]["contents"]["local"],
                         "files/opencode-app.container")
        self.assertEqual(files["/etc/containers/systemd/users/3101/opencode.network"]["contents"]["local"],
                         "files/opencode.network")
        dirs = {d["path"]: d for d in data["storage"]["directories"]}
        self.assertEqual(dirs["/var/lib/appdata/opencode"]["user"]["id"], 3101)
        self.assertEqual(dirs["/var/lib/appdata/opencode/db"]["mode"], 0o750)
        self.assertEqual(dirs["/var/lib/appdata/opencode/db/app"]["mode"], 0o700)
        self.assertIn("/var/lib/appdata/opencode/data-config", dirs)
        self.assertEqual(dirs["/etc/containers/systemd/users/3101"]["mode"], 0o755)

    def test_service_port_only_from_edge(self):
        text = self.read(self.gen("single"), "opencode-port.bu")
        self.assertIn("add element inet host_filter edge_tcp { 4096 }", text)
        self.assertNotIn("lan_tcp", text)

    def test_loopback_has_no_port_fragment(self):
        out = self.gen("authentik")
        self.assertFalse((out / "rendered" / "authentik-port.bu").exists())
        server = self.read(out, "files/authentik-server.container")
        self.assertEqual(directives(server, "PublishPort"), ["127.0.0.1:9000:9000"])


class CrmTests(GenCase):
    def test_crm_three_containers(self):
        out = self.gen("crm")
        names = {p.name for p in (out / "rendered" / "files").iterdir()}
        self.assertEqual(names, {"crm-app.container", "crm-cron.container", "crm-db.container",
                                 "crm.network", "route-crm", "rules-crm"})
        self.assertIn("NetworkName=crm", self.read(out, "files/crm.network"))
        app = self.read(out, "files/crm-app.container")
        cron = self.read(out, "files/crm-cron.container")
        db = self.read(out, "files/crm-db.container")
        for text in (app, cron, db):
            self.assertIn("Network=crm.network", text.splitlines())
        for text in (app, cron):
            self.assertIn("Requires=crm-db.service", text.splitlines())
            self.assertIn("After=crm-db.service", text.splitlines())
        self.assertNotIn("Requires=crm", db)
        self.assertEqual(directives(app, "PublishPort"), ["192.0.2.30:8110:80"])
        self.assertNotIn("PublishPort", cron)
        self.assertNotIn("PublishPort", db)
        self.assertIn("Exec=cron.sh", cron.splitlines())
        # the cron and app containers share one storage folder
        self.assertEqual(directives(app, "Volume"), directives(cron, "Volume"))

    def test_root_start_drops_all_and_adds_back_listed(self):
        out = self.gen("crm")
        app = self.read(out, "files/crm-app.container")
        db = self.read(out, "files/crm-db.container")
        for text in (app, db):
            self.assertNotIn("UserNS", text)
            self.assertIn("DropCapability=ALL", text.splitlines())
            self.assertIn("NoNewPrivileges=true", text.splitlines())
        self.assertEqual(directives(app, "AddCapability"),
                         ["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID", "NET_BIND_SERVICE"])
        self.assertEqual(directives(db, "AddCapability"), ["CHOWN", "DAC_OVERRIDE", "FOWNER", "SETUID", "SETGID"])

    def test_crm_backups_and_files(self):
        out = self.gen("crm")
        files = self.fragment(out, "crm-backup-db.bu")
        self.assertIn("/usr/local/bin/crm-db-mariadb-backup", files)
        self.assertTrue((out / "rendered" / "crm-backup-files.bu").exists())
        self.assertFalse((out / "rendered" / "crm-backup-app.bu").exists())

    def test_route_and_blueprint(self):
        out = self.gen("crm")
        route = self.read(out, "files/route-crm")
        self.assertIn("Host(`crm.example.duckdns.org`)", route)
        self.assertIn('url: "http://192.0.2.30:8110"', route)
        self.assertIn("middlewares: [authentik]", route)
        blueprint = self.read(out, "files/rules-crm")
        self.assertIn("^/dav/.*$", blueprint)
        self.assertIn(r"^/\.well-known/(carddav|caldav)$", blueprint)
        # Placing them on the login front end VM is login_frontend.py's job
        # (tests/test_login_frontend.py); the service gets no route fragment.
        self.assertEqual(sorted(p.name for p in (out / "rendered").glob("*route*.bu")), [])

    def test_app_only_without_hostname_has_no_route(self):
        out = self.gen("authentik")
        self.assertFalse((out / "rendered" / "authentik-route.bu").exists())
        self.assertFalse((out / "rendered" / "files" / "route-authentik.yml").exists())

    def test_app_only_with_hostname_gets_https_route_without_login(self):
        spec = spec_fixture("crm")
        spec.update(login="app-only", login_reason="Phones use CalDAV with the app's own password")
        out = self.gen(spec)
        route = yaml.safe_load(self.read(out, "files/route-crm"))["http"]
        self.assertEqual(route["routers"]["crm"]["rule"], "Host(`crm.example.duckdns.org`)")
        self.assertEqual(route["routers"]["crm"]["entryPoints"], ["websecure"])
        self.assertNotIn("middlewares", route["routers"]["crm"])
        self.assertNotIn("crm-outpost", route["routers"])
        self.assertEqual(route["services"]["crm"]["loadBalancer"]["servers"], [{"url": "http://192.0.2.30:8110"}])
        # A dashboard link only: an application with a launch URL and no provider.
        bookmark = yaml.safe_load(self.read(out, "files/rules-crm"))
        self.assertEqual(bookmark["metadata"]["name"], "app-crm")
        (entry,) = bookmark["entries"]
        self.assertEqual(entry["model"], "authentik_core.application")
        self.assertEqual(entry["identifiers"], {"slug": "crm"})
        self.assertEqual(entry["attrs"]["meta_launch_url"], "https://crm.example.duckdns.org")
        self.assertIsNone(entry["attrs"]["provider"])
        self.assertEqual(entry["attrs"]["name"], "Crm")
        # The port stays open only to the login front end.
        self.assertIn("edge_tcp", self.read(out, "crm-port.bu"))

    def test_app_only_hostname_is_checked(self):
        def bad(spec):
            spec.update(login="app-only", login_reason="own login", hostname="Not A Label")
        self.assertTrue(any("hostname" in e for e in self.errors(bad, base="crm")))

        def no_publisher(spec):
            spec.update(login="app-only", login_reason="own login", hostname="x")
            for ctr in spec["containers"]:
                ctr.pop("publish", None)
            spec.pop("port", None)
        self.assertTrue(any("hostname" in e and "publish" in e for e in self.errors(no_publisher)))

    def test_blueprint_with_several_paths_is_valid_yaml(self):
        text = self.read(self.gen("crm"), "files/rules-crm")

        class Loader(yaml.SafeLoader):
            pass

        for tag in ("!Find", "!KeyOf"):
            Loader.add_constructor(tag, lambda loader, node: "tag")
        data = yaml.load(text, Loader=Loader)
        regexes = data["entries"][0]["attrs"]["skip_path_regex"].splitlines()
        self.assertEqual(regexes, ["^/dav/.*$", r"^/\.well-known/(carddav|caldav)$"])


def _blueprint(text):
    class Loader(yaml.SafeLoader):
        pass

    Loader.add_constructor("!Find", lambda loader, node: ["!Find", loader.construct_sequence(node, deep=True)])
    Loader.add_constructor("!KeyOf", lambda loader, node: ["!KeyOf", loader.construct_scalar(node)])
    return yaml.load(text, Loader=Loader)


class AccessGroupTests(GenCase):
    """An app with no bindings is open to every Authentik user
    (docs.goauthentik.io/add-secure-apps/applications/manage_apps/); `groups` binds it."""

    def test_app_rules_never_create_groups(self):
        # Two rules files creating the same group race on its unique name;
        # groups and bindings live only in the login front end's access.yaml.
        spec = spec_fixture("crm")
        spec["groups"] = ["family", "guests"]
        data = _blueprint(self.read(self.gen(spec), "files/rules-crm"))
        models = [e["model"] for e in data["entries"]]
        self.assertNotIn("authentik_core.group", models)
        # Review: until access.yaml binds the groups, the app refuses everyone: a deny policy of
        # its own (policy engine "any": a member's group binding still lets them in).
        deny = [e for e in data["entries"] if e["model"] == "authentik_policies_expression.expressionpolicy"]
        self.assertEqual(len(deny), 1)
        self.assertEqual(deny[0]["attrs"]["expression"], "return False")
        binds = [e for e in data["entries"] if e["model"] == "authentik_policies.policybinding"]
        self.assertEqual(len(binds), 1)
        self.assertEqual(binds[0]["identifiers"]["policy"], ["!KeyOf", deny[0]["id"]])
        plain = _blueprint(self.read(self.gen("crm"), "files/rules-crm"))
        self.assertFalse([e for e in plain["entries"] if e["model"] == "authentik_policies.policybinding"])

    def test_groups_refused_for_an_app_on_its_own_login(self):
        # Its route skips the login page; a binding would only hide the dashboard link.
        def mutate(spec):
            spec.update(login="app-only", login_reason="own login", groups=["family"])
        errors = self.errors(mutate, base="crm")
        self.assertTrue(any("groups" in e and "login page" in e for e in errors), errors)

    def test_guide_and_prompt_ask_for_groups(self):
        root = Path(__file__).resolve().parents[1]
        guide = " ".join((root / "docs" / "guide" / "03-add-a-service.md").read_text().split())
        self.assertIn("Ask who may open it", guide)
        self.assertIn("apps behind the login page", guide)
        self.assertIn("`groups:`", guide)
        from layout import SKILLS
        operations = " ".join((SKILLS / "authgw-authentik" / "operations.md").read_text().split())
        self.assertIn("capital letters", operations)
        prompt = " ".join((root / ".opencode" / "agents" / "fcos-app-installer.md").read_text().split())
        self.assertIn("ask which groups of the auth gateway may open it", prompt)

    def test_bad_groups_refused(self):
        for bad in ("family", ["Family"], ["a b"], ["x", "x"], [f"g{i}" for i in range(11)], ["-x"], [""]):
            with self.subTest(bad=bad):
                errors = self.errors(lambda s: s.update(groups=bad), base="crm")
                self.assertTrue(any("groups" in e for e in errors), errors)


class SectionTests(GenCase):
    """Apps grouped by section on Authentik's dashboard. The dashboard draws each
    application's `group` as a heading over its apps, all on one page (authentik 2026.8.5
    web/src/user/LibraryPage/ApplicationList.ts; core/models.py Application.group)."""

    def test_section_sets_the_application_group(self):
        spec = spec_fixture("crm")
        spec["section"] = "Relationships"
        data = _blueprint(self.read(self.gen(spec), "files/rules-crm"))
        app = next(e for e in data["entries"] if e["model"] == "authentik_core.application")
        self.assertEqual(app["attrs"]["group"], "Relationships")

    def test_without_section_no_group(self):
        data = _blueprint(self.read(self.gen("crm"), "files/rules-crm"))
        app = next(e for e in data["entries"] if e["model"] == "authentik_core.application")
        self.assertNotIn("group", app["attrs"])

    def test_bad_sections_refused(self):
        for bad in ("", "a" * 51, "Line\nbreak", 'Quote"s', 5):
            with self.subTest(bad=bad):
                errors = self.errors(lambda s: s.update(section=bad), base="crm")
                self.assertTrue(any("section" in e for e in errors), errors)


class RedirectTests(GenCase):
    """Crm's public/.htaccess redirects /.well-known/carddav with an
    Apache rewrite that builds http:// behind the proxy; Traefik answers these paths itself
    with https (redirectRegex: doc.traefik.io .../middlewares/redirectregex/)."""

    def route(self, spec):
        return yaml.safe_load(self.read(self.gen(spec), "files/route-crm"))["http"]

    def test_redirects_are_answered_by_traefik_with_https(self):
        spec = spec_fixture("crm")
        spec["redirects"] = [{"path": "/.well-known/carddav", "to": "/dav/"},
                             {"path": "/.well-known/caldav", "to": "/dav/"}]
        http = self.route(spec)
        host = f"{spec['hostname']}.{SITE['domain']}"
        router = http["routers"]["crm-redirect-0"]
        self.assertEqual(router["rule"], f"Host(`{host}`) && Path(`/.well-known/carddav`)")
        self.assertEqual(router["middlewares"], ["crm-redirect-0"])
        self.assertGreater(router["priority"], http["routers"]["crm-outpost"]["priority"])
        mw = http["middlewares"]["crm-redirect-1"]["redirectRegex"]
        self.assertEqual(mw, {"regex": "^.*$", "replacement": f"https://{host}/dav/", "permanent": True})

    def test_without_redirects_nothing_is_added(self):
        http = self.route(spec_fixture("crm"))
        self.assertNotIn("crm-redirect-0", http["routers"])
        self.assertFalse(http.get("middlewares"))

    def test_bad_redirects_refused(self):
        for bad in ([{"path": "dav", "to": "/dav/"}], [{"path": "/a b", "to": "/x"}], [{"path": "/x", "to": "http://evil/"}],
                    [{"path": "/x"}], "nope", [{"path": "/x", "to": "/y", "extra": 1}], [{"path": "/x`)", "to": "/y"}],
                    # review: a loop, the login's own path, duplicates
                    [{"path": "/dav/", "to": "/dav/"}], [{"path": "/outpost.goauthentik.io/x", "to": "/dav/"}],
                    [{"path": "/a", "to": "/dav/"}, {"path": "/a", "to": "/dav/"}],
                    # behind the login page, the target must be one of the app's api_paths
                    [{"path": "/.well-known/carddav", "to": "/settings/"}]):
            with self.subTest(bad=bad):
                errors = self.errors(lambda s: s.update(redirects=bad), base="crm")
                self.assertTrue(any("redirects" in e for e in errors), errors)


class RouteNameTests(unittest.TestCase):
    def test_names_that_would_clash_with_route_names_are_refused(self):
        # Review: routers are named <svc>-outpost and <svc>-redirect-<n>.
        import login_frontend
        for name in ("crm-redirect-0", "x-outpost"):
            spec = spec_fixture("crm")
            spec["name"] = name
            with self.subTest(name=name), self.assertRaisesRegex(Exception, "clashes"):
                login_frontend._routed(copy.deepcopy(SITE), [spec], spec["vm"], "auth")


class RuleTests(GenCase):
    def test_root_start_rejects_nfs(self):
        def mutate(spec):
            spec["containers"][0]["user_mode"] = "root-start"
        errors = self.errors(mutate)
        self.assertTrue(any("root-start" in e and "NFS" in e for e in errors), errors)

    def test_rejects_unlisted_capability(self):
        def mutate(spec):
            spec["containers"][0].update(user_mode="root-start", add_capabilities=["SYS_ADMIN"])
            spec["containers"][0]["volumes"] = spec["containers"][0]["volumes"][:2]
        errors = self.errors(mutate)
        self.assertTrue(any("SYS_ADMIN" in e for e in errors), errors)

    def test_map_user_rejects_capabilities(self):
        def mutate(spec):
            spec["containers"][0]["add_capabilities"] = ["CHOWN"]
        errors = self.errors(mutate)
        self.assertTrue(any("map-user" in e and "capabilit" in e for e in errors), errors)

    def test_rejects_latest_tag(self):
        for image in ("ghcr.io/example/opencode:latest", "ghcr.io/example/opencode",
                      "ghcr.io/example/opencode@sha256:" + "a" * 64):
            with self.subTest(image=image):
                errors = self.errors(lambda s: s["containers"][0].update(image=image))
                self.assertTrue(any("image" in e for e in errors), errors)

    def test_accepts_digest_pinned_tag(self):
        image = "ghcr.io/example/opencode:1@sha256:" + "a" * 64
        self.assertEqual(self.errors(lambda s: s["containers"][0].update(image=image)), [])

    def test_one_publisher_only(self):
        def mutate(spec):
            spec["containers"].append(dict(copy.deepcopy(spec["containers"][0]), name="second", volumes=[]))
        errors = self.errors(mutate)
        self.assertTrue(any("publish" in e and "one" in e for e in errors), errors)

    def test_publish_needs_port_and_login_needs_publisher(self):
        self.assertTrue(any("port" in e for e in self.errors(lambda s: s.pop("port"))))

        def mutate(spec):
            del spec["containers"][0]["publish"]
            del spec["port"]
        self.assertTrue(any("login" in e and "publish" in e for e in self.errors(mutate)))

    def test_five_gb_rule_flag(self):
        def over(spec):
            spec["containers"][0]["volumes"][0]["expected_gib"] = 4
            spec["containers"][0]["volumes"][1]["expected_gib"] = 2
        errors = self.errors(over)
        self.assertTrue(any("5 GB" in e for e in errors), errors)

        def accepted(spec):
            over(spec)
            spec["accepted_risks"] = ["over the 5 GB rule: data disk grown to 40 GB, accepted 2026-10-29"]
        self.assertEqual(self.errors(accepted), [])

        def exactly_five(spec):
            spec["containers"][0]["volumes"][0]["expected_gib"] = 3
            spec["containers"][0]["volumes"][1]["expected_gib"] = 2
        self.assertEqual(self.errors(exactly_five), [])

    def test_read_only_volume(self):
        spec = spec_fixture("single")
        spec["containers"][0]["volumes"][1]["read_only"] = True  # local
        spec["containers"][0]["volumes"][2]["read_only"] = True  # nfs
        text = self.read(self.gen(spec), "files/opencode-app.container")
        volumes = directives(text, "Volume")
        self.assertTrue(volumes[0].endswith(":z") and ":ro" not in volumes[0], volumes)
        self.assertTrue(volumes[1].endswith("/data/config:ro,z"), volumes)
        self.assertTrue(volumes[2].endswith("/projects:ro"), volumes)  # NFS: never relabelled
        self.assertEqual(self.errors(lambda s: s["containers"][0]["volumes"][1].update(read_only=False)), [])
        for bad in (1, "yes", None):
            with self.subTest(bad=bad):
                self.assertTrue(self.errors(lambda s, bad=bad: s["containers"][0]["volumes"][1].update(read_only=bad)))
        # A database volume must stay writable.
        errors = self.errors(lambda s: s["containers"][0]["volumes"][0].update(read_only=True))
        self.assertTrue(any("read_only" in e for e in errors), errors)

    def test_shm_size(self):
        spec = spec_fixture("single")
        spec["containers"][0]["shm_size_mib"] = 512
        text = self.read(self.gen(spec), "files/opencode-app.container")
        self.assertEqual(directives(text, "ShmSize"), ["512m"])
        self.assertEqual(directives(self.read(self.gen("single"), "files/opencode-app.container"), "ShmSize"), [])
        for bad in (0, -1, 65537, "512m", True, 1.5):
            with self.subTest(bad=bad):
                self.assertTrue(self.errors(lambda s, bad=bad: s["containers"][0].update(shm_size_mib=bad)))

    def test_subuid_ranges_pinned(self):
        # Deferred fix 4: each service's sub-ID range comes from its UID/GID, so
        # creation order (rebuilds, pushes) never changes it.
        out = self.gen("crm")
        unit = next(u for u in yaml.safe_load(self.read(out, "crm.bu"))["systemd"]["units"]
                    if u["name"] == "subids-crm.service")
        self.assertTrue(unit["enabled"])
        text = unit["contents"]
        first = 600113152 + (3110 - 1000) * 65536
        self.assertIn(f"--add-subuids {first}-{first + 65535}", text)
        self.assertIn(f"--add-subgids {first}-{first + 65535}", text)
        self.assertIn("--del-subuids 1-4294967294", text)
        # Serialized: several apps' units run at the same boot and usermod locks /etc/subuid.
        self.assertIn("ExecStart=/usr/bin/flock -w 60 /run/subids.lock /usr/sbin/usermod ", text)
        self.assertIn("TimeoutStartSec=2min", text)  # oneshot has no start timeout by default
        uid = 3110  # built from a variable so the publish check doesn't read user@<n> as an address
        self.assertIn(f"Before=user@{uid}.service", text)
        # Hard dependency: if pinning fails, the user's containers must not start on other ranges.
        self.assertIn(f"RequiredBy=user@{uid}.service", text)
        self.assertNotIn("WantedBy=", text)
        self.assertIn("Type=oneshot", text)
        spec = spec_fixture("single")
        spec["gid"] = 3150
        text = next(u for u in yaml.safe_load(self.read(self.gen(spec), "opencode.bu"))["systemd"]["units"]
                    if u["name"] == "subids-opencode.service")["contents"]
        u, g = 600113152 + 2101 * 65536, 600113152 + 2150 * 65536
        self.assertIn(f"--add-subuids {u}-{u + 65535}", text)
        self.assertIn(f"--add-subgids {g}-{g + 65535}", text)

    def test_ranges_never_overlap_and_fit(self):
        from gen_service import MAX_ID, subid_range
        # Fedora's login.defs: useradd's own ranges lie in SUB_UID_MIN 524288 ..
        # SUB_UID_MAX 600100000. Pinned ranges sit above all of it, so they can't
        # collide however many accounts a VM has.
        self.assertGreater(subid_range(1000)[0], 600100000)
        self.assertEqual(subid_range(1000)[0] % 65536, 0)
        # Lasting: disk owners depend on these numbers; a change must fail here first.
        self.assertEqual(subid_range(1000), (600113152, 600113152 + 65535))
        # systemd.io/UIDS-GIDS: 2147352576 and up is the foreign range (open to
        # every user), then IDs a signed 32-bit int can't hold.
        self.assertEqual(MAX_ID, 24608)
        self.assertLess(subid_range(MAX_ID)[1], 2147352576)
        self.assertGreaterEqual(subid_range(MAX_ID + 1)[1], 2147352576)
        self.assertEqual(subid_range(3111)[0], subid_range(3110)[1] + 1)

    def test_ids_above_the_pinnable_range_refused(self):
        from gen_service import MAX_ID
        self.assertEqual(self.errors(lambda s: s.update(uid=MAX_ID, gid=MAX_ID)), [])
        self.assertTrue(any("uid" in e for e in self.errors(lambda s: s.update(uid=MAX_ID + 1))))
        self.assertTrue(any("gid" in e for e in self.errors(lambda s: s.update(gid=MAX_ID + 1))))
        self.assertTrue(any("uid" in e for e in self.errors(lambda s: s.update(uid=999))))

    def test_ids_record(self):
        out = self.gen("crm")
        text = (out / "ids.md").read_text()
        first = 600113152 + 2110 * 65536
        for needle in ("crm", "3110", f"{first}-{first + 65535}", "container root",
                       "first ID + n - 1", "same for groups", "uid_map", "Lasting"):
            self.assertIn(needle, text)
        self.assertEqual(scan_text(text), [])

    def test_no_network_online_in_user_units(self):
        # Podman docs (podman-systemd.unit, "Implicit network dependencies"): user units
        # can't wait for system targets; Quadlet adds podman-user-wait-network-online.service.
        for fixture in ("single", "crm", "authentik"):
            out = self.gen(fixture)
            for path in (out / "rendered").rglob("*"):
                if path.is_file() and path.suffix in (".container", ".bu", ".network"):
                    with self.subTest(fixture=fixture, file=path.name):
                        self.assertNotIn("network-online.target", path.read_text())

    def test_every_generated_file_may_be_replaced(self):
        # The push tool honours overwrite: false like Ignition, so a re-push of an
        # updated service needs every generated file marked overwrite: true.
        for fixture in ("single", "crm", "authentik"):
            out = self.gen(fixture)
            for fragment in sorted((out / "rendered").glob("*.bu")):
                for path, entry in self.fragment(out, fragment.name).items():
                    with self.subTest(fixture=fixture, path=path):
                        if path.startswith("/var/lib/systemd/linger/"):
                            # Ignition allows overwrite only with contents; empty file: no overwrite.
                            self.assertNotIn("contents", entry)
                            self.assertFalse(entry.get("overwrite"))
                        else:
                            self.assertIs(entry.get("overwrite"), True)

    def test_route_names_and_titles_stay_strings(self):
        class Loader(yaml.SafeLoader):
            pass

        for tag in ("!Find", "!KeyOf"):
            Loader.add_constructor(tag, lambda loader, node: "tag")
        for name, title in (("null", "yes"), ("on", "123"), ("no", "0x1A"), ("true", "1.5")):
            with self.subTest(name=name, title=title):
                spec = spec_fixture("crm")
                spec.update(name=name, title=title, hostname="crm")
                out = self.gen(spec)
                blueprint = yaml.load(self.read(out, f"files/rules-{name}"), Loader=Loader)
                provider, app = blueprint["entries"]
                self.assertEqual(provider["identifiers"]["name"], name)
                self.assertEqual(app["identifiers"]["slug"], name)
                self.assertEqual(app["attrs"]["name"], title)
                route = yaml.safe_load(self.read(out, f"files/route-{name}"))
                self.assertIn(name, route["http"]["routers"])
                self.assertEqual(route["http"]["routers"][name]["service"], name)
                self.assertIn(name, route["http"]["services"])

    def test_accepted_risk_needs_its_exact_opening_phrase(self):
        def over(spec):
            spec["containers"][0]["volumes"][0]["expected_gib"] = 4
            spec["containers"][0]["volumes"][1]["expected_gib"] = 2
        for sentence in ("data is about 15 GB, fine", "we accept the 5 GB rule", "not over the 5 GB rule: no",
                         "over the 5 GB rule"):  # no colon and reason
            with self.subTest(sentence=sentence):
                def mutate(spec, sentence=sentence):
                    over(spec)
                    spec["accepted_risks"] = [sentence]
                self.assertTrue(any("5 GB" in e for e in self.errors(mutate)))

        def accepted(spec):
            over(spec)
            spec["accepted_risks"] = ["Over the 5 GB rule: data disk grown"]
        self.assertEqual(self.errors(accepted), [])

        site = copy.deepcopy(SITE)
        for vm in site["vms"]:
            vm["nfs_shares"] = [s for s in vm.get("nfs_shares", []) if s["name"] != "backups"]
        for sentence, ok in (("we have no backup share yet", False), ("no backups: test VM, accepted", True)):
            with self.subTest(sentence=sentence):
                errors = self.errors(lambda s, sentence=sentence: s.update(accepted_risks=[sentence]), site=site)
                self.assertEqual(ok, not any("backups" in e for e in errors), errors)

    def test_shared_folder_needs_one_user_mode(self):
        def mutate(spec):
            cron = spec["containers"][1]
            cron["user_mode"] = "map-user"
            cron.pop("add_capabilities")
        errors = self.errors(mutate, base="crm")
        self.assertTrue(any("user_mode" in e and "shared" in e for e in errors), errors)

        def separate(spec):
            mutate(spec)
            spec["containers"][1]["volumes"][0]["name"] = "cron-storage"
        self.assertEqual(self.errors(separate, base="crm"), [])

    def test_shared_volume_counted_once(self):
        def mutate(spec):
            for container in spec["containers"][:2]:
                container["volumes"][0]["expected_gib"] = 2.5
            spec["containers"][2]["volumes"][0]["expected_gib"] = 0.1
        self.assertEqual(self.errors(mutate, base="crm"), [])

    def test_dependency_problems(self):
        def unknown(spec):
            spec["containers"][0]["depends_on"] = ["nope"]
        self.assertTrue(any("nope" in e for e in self.errors(unknown, base="crm")))

        def cycle(spec):
            spec["containers"][2]["depends_on"] = ["app"]
        self.assertTrue(any("cycle" in e for e in self.errors(cycle, base="crm")))

    def test_host_network_container(self):
        def mutate(spec):
            spec["containers"].append({"name": "proxy", "image": "docker.io/library/traefik:v3",
                                       "user_mode": "map-user", "network": "host"})
        self.assertEqual(self.errors(mutate), [])
        spec = spec_fixture("single")
        spec["containers"].append({"name": "proxy", "image": "docker.io/library/traefik:v3",
                                   "user_mode": "map-user", "network": "host"})
        out = self.gen(spec)
        proxy = self.read(out, "files/opencode-proxy.container")
        self.assertIn("Network=host", proxy.splitlines())
        self.assertNotIn("opencode.network", proxy)
        self.assertIn("Network=opencode.network", self.read(out, "files/opencode-app.container"))
        self.assertTrue(any("publish" in e for e in self.errors(
            lambda s: s["containers"].append({"name": "proxy", "image": "docker.io/library/traefik:v3",
                                              "user_mode": "map-user", "network": "host", "publish": 80}))))

    def test_nfs_share_must_exist_on_the_vm(self):
        errors = self.errors(lambda s: s["containers"][0]["volumes"][2].update(host="/var/mnt/media/x"))
        self.assertTrue(any("media" in e for e in errors), errors)
        errors = self.errors(lambda s: s["containers"][0]["volumes"][2].update(host="/srv/x"))
        self.assertTrue(any("/var/mnt/" in e for e in errors), errors)

    def test_missing_fields(self):
        checks = {
            "vm not in site": lambda s: s.update(vm="ghost"),
            "login missing": lambda s: s.pop("login"),
            "hostname for login": lambda s: s.pop("hostname"),
            "uid": lambda s: s.pop("uid"),
            "engine": lambda s: s["containers"][0]["volumes"][0].pop("engine"),
            "sqlite file": lambda s: s["containers"][0]["volumes"][0].pop("file"),
            "expected_gib": lambda s: s["containers"][0]["volumes"][1].pop("expected_gib"),
            "user_mode": lambda s: s["containers"][0].pop("user_mode"),
            "undeclared secret": lambda s: s.update(secrets=[]),
            "unused secret": lambda s: s["secrets"].append({"name": "unused_one"}),
        }
        for label, mutate in checks.items():
            with self.subTest(label):
                self.assertTrue(self.errors(mutate), label)

    def test_app_only_needs_reason(self):
        self.assertTrue(self.errors(lambda s: s.pop("login_reason"), base="authentik"))

    def test_mariadb_needs_its_variables(self):
        def mutate(spec):
            del spec["containers"][2]["env"]["MARIADB_USER"]
        self.assertTrue(any("MARIADB_USER" in e for e in self.errors(mutate, base="crm")))

    def test_custom_engine_needs_command(self):
        def mutate(spec):
            spec["containers"][0]["volumes"][0].update(engine="custom")
            spec["containers"][0]["volumes"][0].pop("file")
        self.assertTrue(any("command" in e for e in self.errors(mutate)))

    def test_nested_volume_targets_rejected(self):
        def mutate(spec):
            spec["containers"][0]["volumes"][1]["path"] = "/data/db/inner"
        self.assertTrue(any("inside" in e for e in self.errors(mutate)))

    def test_reserved_container_names(self):
        for name in ("files", "network", "backup-x"):
            with self.subTest(name):
                self.assertTrue(self.errors(lambda s: s["containers"][0].update(name=name)))

    def test_secret_map_form_is_accepted(self):
        def mutate(spec):
            spec["containers"][0]["secrets"] = {"MODEL_API": "opencode_model_api"}
        self.assertEqual(self.errors(mutate), [])


class NetworkRuleTests(GenCase):
    """Host network values and storage come only from the site config; a gap is an error that names it."""

    def site_without(self, mutate):
        site = copy.deepcopy(SITE)
        mutate(site)
        return site

    def test_missing_vm_ip_names_the_vm_and_field(self):
        site = self.site_without(lambda s: s["vms"][1].pop("ip"))
        errors = self.errors(lambda s: None, base="crm", site=site)
        self.assertTrue(any("apps" in e and "ip" in e for e in errors), errors)

    def test_loopback_needs_no_vm_ip(self):
        site = self.site_without(lambda s: s["vms"][2].pop("ip"))
        self.assertEqual(self.errors(lambda s: None, base="authentik", site=site), [])

    def test_missing_domain_and_edge_ids_are_named(self):
        errors = self.errors(lambda s: None, base="crm", site=self.site_without(lambda s: s.pop("domain")))
        self.assertTrue(any("domain" in e for e in errors), errors)
        errors = self.errors(lambda s: None, base="crm",
                             site=self.site_without(lambda s: s["edge"]["traefik"].pop("uid")))
        self.assertTrue(any("edge.traefik.uid" in e for e in errors), errors)

    def test_missing_backup_settings_are_named(self):
        errors = self.errors(lambda s: s.pop("backups"),
                             site=self.site_without(lambda s: s.pop("backups")))
        self.assertTrue(any("backups.keep" in e for e in errors), errors)
        self.assertTrue(any("oncalendar" in e for e in errors), errors)

    def test_nfs_share_comes_only_from_the_site(self):
        errors = self.errors(lambda s: None, site=self.site_without(lambda s: s["vms"][0].pop("nfs_shares")))
        self.assertTrue(any("projects" in e for e in errors), errors)

    def test_vm_without_backups_share_is_flagged(self):
        site = self.site_without(lambda s: s["vms"][1].update(nfs_shares=[]))
        errors = self.errors(lambda s: None, base="crm", site=site)
        self.assertTrue(any("backups" in e for e in errors), errors)

    def test_output_holds_no_address_that_is_not_from_the_site(self):
        for name in ("single", "crm", "authentik"):
            with self.subTest(name):
                out = self.gen(name)
                allowed = {"127.0.0.1", "192.0.2.20", "192.0.2.30"}
                for path in (out / "rendered").rglob("*"):
                    if path.is_file():
                        found = set(re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", path.read_text()))
                        self.assertLessEqual(found, allowed, path.name)

    def test_changing_the_site_ip_changes_the_output(self):
        site = copy.deepcopy(SITE)
        site["vms"][1]["ip"] = "192.0.2.77"
        out = self.gen("crm", site=site)
        self.assertEqual(directives(self.read(out, "files/crm-app.container"), "PublishPort"),
                         ["192.0.2.77:8110:80"])
        self.assertIn('url: "http://192.0.2.77:8110"', self.read(out, "files/route-crm"))


class InjectionTests(GenCase):
    def test_untrusted_values_are_refused(self):
        cases = {
            "service name with newline": lambda s: s.update(name="a\nb"),
            "service name uppercase": lambda s: s.update(name="Opencode"),
            "service name too long": lambda s: s.update(name="a" * 32),
            "container name dot": lambda s: s["containers"][0].update(name="a.b"),
            "image with newline": lambda s: s["containers"][0].update(image="ghcr.io/x/y:1\nExec=evil"),
            "image with brace": lambda s: s["containers"][0].update(image="ghcr.io/{{X}}/y:1"),
            "env key lowercase": lambda s: s["containers"][0]["env"].update(bad="1"),
            "env key with equals": lambda s: s["containers"][0]["env"].update({"A=B": "1"}),
            "env value newline": lambda s: s["containers"][0]["env"].update(TZ="UTC\nExec=evil"),
            "env value brace": lambda s: s["containers"][0]["env"].update(TZ="{{SVC_NAME}}"),
            "env value bool": lambda s: s["containers"][0]["env"].update(TZ=True),
            "path relative": lambda s: s["containers"][0]["volumes"][0].update(path="data/db"),
            "path dotdot": lambda s: s["containers"][0]["volumes"][0].update(path="/data/../etc"),
            "path colon": lambda s: s["containers"][0]["volumes"][0].update(path="/data:/etc"),
            "path double slash": lambda s: s["containers"][0]["volumes"][0].update(path="/data//db"),
            "path trailing slash": lambda s: s["containers"][0]["volumes"][0].update(path="/data/db/"),
            "nfs host dotdot": lambda s: s["containers"][0]["volumes"][2].update(host="/var/mnt/projects/../backups"),
            "volume name slash": lambda s: s["containers"][0]["volumes"][1].update(name="a/b"),
            "command newline": lambda s: s["containers"][0].update(command=["a\nb"]),
            "secret name newline": lambda s: (s["secrets"][0].update(name="x\ny"),
                                              s["containers"][0].update(secrets={"MODEL_API": "x\ny"})),
            "description newline": lambda s: s.update(description="a\nExec=evil"),
            "title colon": lambda s: s.update(title="a: b"),
            "hostname dots": lambda s: s.update(hostname="a.b"),
            "api path newline": lambda s: s.update(api_paths=["^/a$\nevil: 1"]),
            "api path bad regex": lambda s: s.update(api_paths=["^/(a"]),
            "extra group newline": lambda s: s.update(extra_groups=["a\nb"]),
            "schedule newline": lambda s: s.update(backups={"schedule": "daily\nExec=x", "keep": 3}),
            "uid string": lambda s: s.update(uid="3101"),
            "port string": lambda s: s.update(port="4096; evil"),
            "unknown top-level key": lambda s: s.update(surprise=1),
            "unknown container key": lambda s: s["containers"][0].update(surprise=1),
        }
        for label, mutate in cases.items():
            with self.subTest(label):
                spec = spec_fixture("single")
                mutate(spec)
                self.assertTrue(validate_spec(spec, SITE), label)

    LINE_BREAKS = ["\x85", "\u2028", "\u2029", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\r", "\n", "\x00", "\x9f"]

    def test_unicode_line_breaks_are_refused_everywhere(self):
        def custom(spec, ch):
            volume = spec["containers"][0]["volumes"][0]
            volume.pop("file")
            volume.update(engine="custom", command=f"mydump{ch}evil")

        fields = {
            "api_paths": lambda s, c: s.update(api_paths=[f"^/a$ {c}  - model: authentik_core.user"]),
            "custom command": custom,
            "env key": lambda s, c: s["containers"][0]["env"].update({f"A{c}B": "1"}),
            "env value": lambda s, c: s["containers"][0]["env"].update(TZ=f"UTC{c}Exec=evil"),
            "image": lambda s, c: s["containers"][0].update(image=f"ghcr.io/x/y:1{c}Exec=evil"),
            "volume path": lambda s, c: s["containers"][0]["volumes"][0].update(path=f"/data{c}x"),
            "nfs host": lambda s, c: s["containers"][0]["volumes"][2].update(host=f"/var/mnt/projects/a{c}b"),
            "service name": lambda s, c: s.update(name=f"a{c}b"),
            "container name": lambda s, c: s["containers"][0].update(name=f"a{c}b"),
            "command word": lambda s, c: s["containers"][0].update(command=[f"a{c}b"]),
            "title": lambda s, c: s.update(title=f"a{c}b"),
            "hostname": lambda s, c: s.update(hostname=f"a{c}b"),
            "schedule": lambda s, c: s.update(backups={"schedule": f"daily{c}x", "keep": 3}),
            "extra group": lambda s, c: s.update(extra_groups=[f"a{c}b"]),
            "description": lambda s, c: s.update(description=f"a{c}b"),
            "accepted_risks": lambda s, c: s.update(accepted_risks=[f"over the 5 GB rule: a{c}b"]),
            "login_reason": lambda s, c: s.update(login="app-only", login_reason=f"a{c}b"),
        }
        for label, mutate in fields.items():
            for char in self.LINE_BREAKS:
                with self.subTest(field=label, char=repr(char)):
                    spec = spec_fixture("single")
                    mutate(spec, char)
                    self.assertTrue(validate_spec(spec, SITE))
                    with self.assertRaises(SpecError):
                        generate(spec, SITE, self.tmpdir())

    def test_non_ascii_only_in_human_text_fields(self):
        spec = spec_fixture("single")
        spec.update(description="Caf\u00e9 server", accepted_risks=["no backups: caf\u00e9 \u2013 accepted"])
        self.assertEqual(validate_spec(spec, SITE), [])
        for label, mutate in {
            "env value": lambda s: s["containers"][0]["env"].update(TZ="caf\u00e9"),
            "api_paths": lambda s: s.update(api_paths=["^/caf\u00e9$"]),
            "title": lambda s: s.update(title="Caf\u00e9"),
            "command word": lambda s: s["containers"][0].update(command=["caf\u00e9"]),
        }.items():
            with self.subTest(label):
                spec = spec_fixture("single")
                mutate(spec)
                self.assertTrue(validate_spec(spec, SITE))

    def test_hostile_api_paths_cannot_add_blueprint_entries(self):
        spec = spec_fixture("crm")
        spec["api_paths"] = ["^/dav/.*$\u2028  - model: authentik_core.user\u2028    identifiers: {username: evil}"]
        self.assertTrue(validate_spec(spec, SITE))
        text = self.read(self.gen("crm"), "files/rules-crm")

        class Loader(yaml.SafeLoader):
            pass

        for tag in ("!Find", "!KeyOf"):
            Loader.add_constructor(tag, lambda loader, node: "tag")
        models = [entry["model"] for entry in yaml.load(text, Loader=Loader)["entries"]]
        self.assertEqual(models, ["authentik_providers_proxy.proxyprovider", "authentik_core.application"])

    def test_hostile_custom_command_cannot_add_butane_files(self):
        def mutate(spec, command):
            volume = spec["containers"][0]["volumes"][0]
            volume.pop("file")
            volume.update(engine="custom", command=command)

        spec = spec_fixture("single")
        mutate(spec, "mydump\u2028    - path: /etc/evil\u2028      mode: 0755")
        self.assertTrue(validate_spec(spec, SITE))
        spec = spec_fixture("single")
        mutate(spec, "mydump --all")
        files = self.fragment(self.gen(spec), "opencode-backup-app.bu")
        self.assertEqual(sorted(files), ["/etc/systemd/user/opencode-backup-app.service",
                                         "/etc/systemd/user/opencode-backup-app.timer",
                                         "/usr/local/bin/opencode-app-dump"])

    def test_vm_name_is_checked(self):
        site = copy.deepcopy(SITE)
        site["vms"][1]["name"] = "apps\nevil"
        spec = spec_fixture("crm")
        spec["vm"] = "apps\nevil"
        self.assertTrue(validate_spec(spec, site))

    def test_vm_ip_must_be_text(self):
        site = copy.deepcopy(SITE)
        site["vms"][1]["ip"] = 3232235777
        self.assertTrue(any("ip" in e for e in self.errors(lambda s: None, base="crm", site=site)))

    def test_site_values_are_checked_too(self):
        site = copy.deepcopy(SITE)
        site["domain"] = "example.org\nevil"
        self.assertTrue(self.errors(lambda s: None, base="crm", site=site))
        site = copy.deepcopy(SITE)
        site["vms"][1]["ip"] = "192.0.2.30\nevil"
        self.assertTrue(self.errors(lambda s: None, base="crm", site=site))

    def test_generate_refuses_and_writes_nothing(self):
        spec = spec_fixture("single")
        spec["name"] = "bad\nname"
        out = self.tmpdir()
        with self.assertRaises(SpecError):
            generate(spec, SITE, out)
        self.assertEqual(list(out.iterdir()), [])

    def test_spec_must_be_a_mapping(self):
        self.assertTrue(validate_spec([], SITE))
        self.assertTrue(validate_spec(spec_fixture("single"), []))


class BackupTests(GenCase):
    def assert_skips_without_nas(self, text: str, svc: str):
        self.assertIn("ExecCondition=/usr/local/bin/require-mounts /var/mnt/backups", text)
        self.assertIn(f"ConditionUser={svc}", text)

    def test_backup_by_engine(self):
        # sqlite
        out = self.gen("single")
        files = self.fragment(out, "opencode-backup-app.bu")
        unit = inline(files, "/etc/containers/systemd/users/3101/opencode-backup-app.container")
        self.assertIn(".backup(", unit)
        self.assertNotRegex(unit, r"\bcp\b[^\n]*\.db")
        self.assertIn("Type=oneshot", unit)
        self.assertIn("%%Y%%m%%dT%%H%%M%%S", unit)
        self.assert_skips_without_nas(unit, "opencode")
        self.assertIn("Volume=/var/lib/appdata/opencode/db/app:/src:z", unit)
        self.assertIn("Volume=/var/mnt/backups/ai/opencode:/dest", unit)
        self.assertIn("Network=none", unit)
        timer = inline(files, "/etc/systemd/user/opencode-backup-app.timer")
        self.assertIn("OnCalendar=*-*-* 02:15:00", timer)
        self.assertIn("ConditionUser=opencode", timer)
        links = {l["path"]: l["target"] for l in yaml.safe_load(self.read(out, "opencode-backup-app.bu"))["storage"]["links"]}
        self.assertEqual(links["/etc/systemd/user/timers.target.wants/opencode-backup-app.timer"],
                         "/etc/systemd/user/opencode-backup-app.timer")

        # postgres
        out = self.gen("authentik")
        files = self.fragment(out, "authentik-backup-postgres.bu")
        unit = inline(files, "/etc/systemd/user/authentik-backup-postgres.service")
        self.assertIn("pg_dump -Fc -U authentik authentik", unit)
        self.assertIn("podman exec authentik-postgres", unit)
        self.assert_skips_without_nas(unit, "authentik")
        self.assertIn("OnCalendar=Sun *-*-* 02:15:00",
                      inline(files, "/etc/systemd/user/authentik-backup-postgres.timer"))

        # mariadb and mysql
        for engine in ("mariadb", "mysql"):
            spec = spec_fixture("crm")
            spec["containers"][2]["volumes"][0]["engine"] = engine
            out = self.gen(spec)
            files = self.fragment(out, "crm-backup-db.bu")
            script = files["/usr/local/bin/crm-db-mariadb-backup"]
            self.assertEqual(script["mode"], 0o755)
            body = script["contents"]["inline"]
            self.assertIn("podman exec crm-db sh -c", body)
            self.assertIn('mariadb-dump --single-transaction --quick "-u$MARIADB_USER" '
                          '"-p$MARIADB_PASSWORD" "$MARIADB_DATABASE"', body)
            self.assertIn("gzip", body)
            self.assertIn('.tmp', body)
            self.assertIn("mv ", body)
            self.assertIn("tail -n +$((14 + 1))", body)
            unit = inline(files, "/etc/systemd/user/crm-backup-db.service")
            self.assertIn("ExecStart=/usr/local/bin/crm-db-mariadb-backup", unit)
            self.assertNotIn("MARIADB_", unit, "credentials must not pass through systemd quoting")
            self.assert_skips_without_nas(unit, "crm")

        # custom
        spec = spec_fixture("single")
        volume = spec["containers"][0]["volumes"][0]
        volume.pop("file")
        volume.update(engine="custom", command="mydump --all --quiet")
        files = self.fragment(self.gen(spec), "opencode-backup-app.bu")
        body = inline(files, "/usr/local/bin/opencode-app-dump")
        self.assertIn("podman exec -i opencode-app sh -s", body)
        self.assertIn("mydump --all --quiet", body)
        unit = inline(files, "/etc/systemd/user/opencode-backup-app.service")
        self.assert_skips_without_nas(unit, "opencode")

    def test_postgres_defaults_to_the_image_defaults(self):
        spec = spec_fixture("authentik")
        spec["containers"][0]["env"] = {}
        files = self.fragment(self.gen(spec), "authentik-backup-postgres.bu")
        self.assertIn("pg_dump -Fc -U postgres postgres",
                      inline(files, "/etc/systemd/user/authentik-backup-postgres.service"))

    def test_sqlite_backup_safe(self):
        files = self.fragment(self.gen("single"), "opencode-backup-app.bu")
        unit = inline(files, "/etc/containers/systemd/users/3101/opencode-backup-app.container")
        for needle in ("mode=rw", "uri=True", "os.replace(", ".tmp"):
            self.assertIn(needle, unit)

    def test_sqlite_backup_of_a_root_start_app_can_read_subordinate_files(self):
        spec = spec_fixture("single")
        spec["containers"][0].update(user_mode="root-start", add_capabilities=["CHOWN"])
        spec["containers"][0]["volumes"] = spec["containers"][0]["volumes"][:2]
        unit = inline(self.fragment(self.gen(spec), "opencode-backup-app.bu"),
                      "/etc/containers/systemd/users/3101/opencode-backup-app.container")
        self.assertNotIn("UserNS", unit)
        self.assertIn("AddCapability=DAC_OVERRIDE", unit)
        self.assertIn("DropCapability=ALL", unit)

    def test_files_backup_uses_unshare_tar(self):
        out = self.gen("single")
        files = self.fragment(out, "opencode-backup-files.bu")
        unit = inline(files, "/etc/systemd/user/opencode-backup-files.service")
        self.assertIn('/usr/bin/podman unshare tar -C /var/lib/appdata/opencode --exclude=./db '
                      '-czf - . > "$$f.tmp"', unit)
        self.assertIn("/var/mnt/backups/ai/opencode", unit)
        self.assert_skips_without_nas(unit, "opencode")
        self.assertIn("opencode-backup-files.timer", "".join(files))
        self.assertIn("$$((14 + 1))", unit)

    def test_no_files_backup_without_local_volumes(self):
        spec = spec_fixture("single")
        spec["containers"][0]["volumes"] = [spec["containers"][0]["volumes"][0]]
        out = self.gen(spec)
        self.assertFalse((out / "rendered" / "opencode-backup-files.bu").exists())
        self.assertTrue((out / "rendered" / "opencode-backup-app.bu").exists())

    def test_retention_and_schedule_come_from_the_spec(self):
        spec = spec_fixture("single")
        spec["backups"] = {"schedule": "Mon *-*-* 03:00:00", "keep": 7}
        out = self.gen(spec)
        files = self.fragment(out, "opencode-backup-files.bu")
        self.assertIn("$$((7 + 1))", inline(files, "/etc/systemd/user/opencode-backup-files.service"))
        self.assertIn("OnCalendar=Mon *-*-* 03:00:00", inline(files, "/etc/systemd/user/opencode-backup-files.timer"))
        unit = inline(self.fragment(out, "opencode-backup-app.bu"),
                      "/etc/containers/systemd/users/3101/opencode-backup-app.container")
        self.assertIn(" /dest 7 app-", unit)

    def test_backups_default_to_the_site_settings(self):
        spec = spec_fixture("single")
        del spec["backups"]
        files = self.fragment(self.gen(spec), "opencode-backup-files.bu")
        self.assertIn("OnCalendar=*-*-* 02:15:00", inline(files, "/etc/systemd/user/opencode-backup-files.timer"))
        self.assertIn("$$((14 + 1))", inline(files, "/etc/systemd/user/opencode-backup-files.service"))


class OwnerTablesTests(GenCase):
    """Several items of one kind (folders, secrets) are one table, one row each."""

    def test_file_server_folders_are_one_table(self):
        site = copy.deepcopy(SITE)
        site["shared_groups"] = [{"name": "ai-projects", "gid": 3100}]
        text = (self.gen("single", site=site) / "file-server.md").read_text()
        self.assertIn("| Folder on the file server | User | Group | Mode | What it holds |", text)
        rows = [l for l in text.splitlines() if l.startswith("| `")]
        self.assertEqual(rows, [
            "| `/mnt/pool/backups/ai/` | the share's admin account | its own group | 0755 | one folder per service on VM ai; not group-writable |",
            "| `/mnt/pool/backups/ai/opencode/` | `opencode` (UID 3101) | `opencode` (GID 3101) | 0750 | backups of opencode |",
            "| `/mnt/pool/projects/ai` | `opencode` (UID 3101) | `ai-projects` (GID 3100) | 2775 | /projects in container app |",
        ])
        self.assertIn("numbers", text)  # the VM sends UIDs and GIDs; names don't matter

    def test_file_server_table_for_a_service_without_nfs_folders(self):
        rows = [l for l in (self.gen("crm") / "file-server.md").read_text().splitlines() if l.startswith("| `")]
        self.assertEqual([r.split(" | ")[0] for r in rows], ["| `/mnt/pool/backups/apps/`", "| `/mnt/pool/backups/apps/crm/`"])

    def test_secrets_are_one_table_with_what_to_enter(self):
        spec = spec_fixture("crm")
        spec["secrets"][1]["value"] = "base64: followed by 32 random bytes in base64 (Crm's .env.example)"
        text = (self.gen(spec) / "secrets.md").read_text()
        self.assertIn("| Secret | Used by | What to enter | Keep it |", text)
        rows = {l.split(" | ")[0]: l for l in text.splitlines() if l.startswith("| `")}
        self.assertIn("base64: followed by 32 random bytes", rows["| `crm_app_key`"])
        self.assertIn("password manager", rows["| `crm_app_key`"])
        self.assertIn("a long random value", rows["| `crm_db_password`"])
        self.assertLess(text.index("| Secret |"), text.index("```bash"))

    def test_bad_secret_values_refused(self):
        for bad in ("", "a" * 201, "two\nlines", "pipe | here", 5):
            with self.subTest(bad=bad):
                errors = self.errors(lambda s: s["secrets"][0].update(value=bad), base="crm")
                self.assertTrue(any("value" in e for e in errors), errors)


class BackupsReportTests(GenCase):
    """The final report says how backups work, when they run and how to restore."""

    def test_backups_report_names_what_when_where_and_restore(self):
        text = (self.gen("crm") / "backups.md").read_text()
        self.assertIn("| What | Unit | File | When |", text)
        rows = [l for l in text.splitlines() if l.startswith("| ")][1:]
        self.assertEqual(rows, [
            "| database of db (mariadb) | `crm-backup-db.timer` | `db-<UTC time>.sql.gz` | *-*-* 02:15:00 |",
            "| files of crm (data disk, without the database) | `crm-backup-files.timer` | "
            "`files-<UTC time>.tar.gz` | *-*-* 02:15:00 |",
        ])
        for needle in ("/mnt/pool/backups/apps/crm/", "newest 14", "Persistent", "skips",
                       "guide 4, Check a backup", "guide 4, Test a restore", "guide 4, Restore"):
            self.assertIn(needle, text)
        self.assertNotIn("](", text)  # the file lives in the workspace: no repo-relative links

    def test_no_backups_share_says_backups_cannot_run(self):
        site = copy.deepcopy(SITE)
        site["vms"][1]["nfs_shares"] = []
        spec = spec_fixture("crm")
        spec["accepted_risks"] = ["no backups: test VM"]
        text = (self.gen(spec, site=site) / "backups.md").read_text()
        self.assertIn("can't run", text)

    def test_no_backups_says_so(self):
        spec = spec_fixture("single")
        for ctr in spec["containers"]:
            ctr["volumes"] = [v for v in ctr.get("volumes") or [] if v["class"] == "nfs"]
        text = (self.gen(spec) / "backups.md").read_text()
        self.assertIn("nothing to back up", text.lower())


class SecretsReportTests(GenCase):
    def test_secrets_report_marks_durable(self):
        text = (self.gen("crm") / "secrets.md").read_text()
        durable_line = "save this value in your password manager; a rebuild must re-enter the same value"
        for name in ("crm_db_password", "crm_app_key"):
            section = text.split(f"## {name}", 1)[1].split("\n## ", 1)[0]
            self.assertIn(durable_line, section)
            self.assertIn("user `crm`", section)
            self.assertIn(f"podman secret create {name} -", section)
        self.assertIn("XDG_RUNTIME_DIR=/run/user/3110", text)
        self.assertIn("# vm apps (bash, admin)", text)

    def test_non_durable_secret_is_not_marked(self):
        text = (self.gen("single") / "secrets.md").read_text()
        self.assertIn("## opencode_model_api", text)
        self.assertNotIn("password manager", text)

    def test_generated_vs_prompted_secrets(self):
        text = (self.gen("crm") / "secrets.md").read_text()
        app_key = text.split("## crm_app_key", 1)[1].split("\n## ", 1)[0]
        self.assertIn('read -rs -p "value for crm_app_key: "', app_key)
        spec = spec_fixture("authentik")
        spec["secrets"][1].update(durable=False)
        text = (self.gen(spec) / "secrets.md").read_text()
        key = text.split("## authentik_secret_key", 1)[1].split("\n## ", 1)[0]
        self.assertIn("/dev/urandom", key)
        self.assertNotIn("read -rs", key)

    def test_no_secret_value_anywhere(self):
        for name in ("single", "crm", "authentik"):
            with self.subTest(name):
                out = self.gen(name)
                self.assertEqual(scan_text((out / "secrets.md").read_text()), [])
                for path in (out / "rendered").rglob("*"):
                    if path.is_file():
                        self.assertEqual(scan_text(path.read_text()), [], path.name)


class OutputTests(GenCase):
    def test_returns_every_written_path_inside_out(self):
        out = self.tmpdir()
        written = generate(spec_fixture("crm"), SITE, out)
        on_disk = {p for p in out.rglob("*") if p.is_file()}
        self.assertEqual(set(written), on_disk)
        for path in written:
            self.assertIn(out, path.parents)

    def test_regenerating_removes_stale_files(self):
        out = self.tmpdir()
        generate(spec_fixture("crm"), SITE, out)
        spec = spec_fixture("crm")
        spec["backups"] = {"schedule": "daily", "keep": 3}
        spec["containers"][2]["volumes"][0]["engine"] = "custom"
        spec["containers"][2]["volumes"][0]["command"] = "dump-it"
        written = generate(spec, SITE, out)
        self.assertFalse((out / "rendered" / "crm-backup-db.bu").exists() and
                         "mariadb-backup" in (out / "rendered" / "crm-backup-db.bu").read_text())
        self.assertEqual(set(written), {p for p in out.rglob("*") if p.is_file()})


class SafetyTests(GenCase):
    def test_durable_secret_cannot_be_generated(self):
        errors = self.errors(lambda s: s["secrets"][0].update(durable=True, source="generate"))
        self.assertTrue(any("durable" in e for e in errors), errors)

    def test_rerun_never_deletes_outside_the_output_folder(self):
        out = self.tmpdir()
        victim = self.tmpdir() / "victim.txt"
        victim.write_text("keep")
        generate(spec_fixture("single"), SITE, out)
        manifest = out / ".gen-service-opencode.json"
        manifest.write_text(json.dumps(["../" + victim.parent.name + "/victim.txt", "/etc/hostname"]))
        generate(spec_fixture("single"), SITE, out)
        self.assertEqual(victim.read_text(), "keep")

    def test_rerun_removes_files_the_spec_no_longer_produces(self):
        out = self.tmpdir()
        generate(spec_fixture("crm"), SITE, out)
        spec = spec_fixture("crm")
        spec["login"], spec["login_reason"] = "app-only", "test"
        generate(spec, SITE, out)  # own login, still a hostname: open route and a dashboard link
        self.assertTrue((out / "rendered" / "files" / "route-crm").exists())
        self.assertNotIn("proxyprovider", self.read(out, "files/rules-crm"))
        spec.pop("hostname")
        generate(spec, SITE, out)  # no hostname: no route, no link
        self.assertFalse((out / "rendered" / "files" / "route-crm").exists())
        self.assertFalse((out / "rendered" / "files" / "rules-crm").exists())

    def test_command_line(self):
        work = self.tmpdir()
        (work / "site.yaml").write_text(yaml.safe_dump(SITE))
        run = lambda *args: subprocess.run([sys.executable, str(ROOT / "tools" / "gen_service.py"), *args],
                                           capture_output=True, text=True)
        good = run(str(FIXTURES / "services" / "crm.yaml"), str(work / "site.yaml"), str(work / "out"))
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertTrue((work / "out" / "secrets.md").is_file())
        bad_spec = spec_fixture("crm")
        bad_spec["containers"][0]["image"] = "docker.io/library/crm:latest"
        (work / "bad.yaml").write_text(yaml.safe_dump(bad_spec))
        bad = run(str(work / "bad.yaml"), str(work / "site.yaml"), str(work / "out2"))
        self.assertEqual(bad.returncode, 1)
        self.assertIn("latest", bad.stderr)
        self.assertFalse((work / "out2").exists())
        self.assertEqual(run().returncode, 2)


class BuildTests(GenCase):
    # The pins in tools/images.env, as build-vm.sh runs them.
    IMAGES = tuple(line.split("=", 1)[1] for line in (ROOT / "tools" / "images.env").read_text().splitlines()
                   if line and not line.startswith("#"))

    def runtime(self):
        for name in ("podman", "docker"):
            exe = shutil.which(name)
            if not exe:
                continue
            if all(subprocess.run([exe, "image", "inspect", image], capture_output=True).returncode == 0
                   for image in self.IMAGES):
                return exe
        return None

    def test_generated_passes_build(self):
        if not self.runtime():
            self.skipTest("no container runtime with the Butane and Podman images already pulled")
        base = load_values(str(FIXTURES / "ai-vm.values"))
        for name in ("single", "crm", "authentik"):
            with self.subTest(fixture=name):
                spec = spec_fixture(name)
                out = self.tmpdir()
                generate(spec, SITE, out)
                vm_dir = self.tmpdir() / spec["vm"]
                shutil.copytree(out / "rendered", vm_dir)
                fragments = sorted(p.stem for p in vm_dir.glob("*.bu"))
                values = dict(base, VM_NAME=spec["vm"], NFS_MOUNT_NAME="backups", NFS_EXPORT="/mnt/pool/backups")
                for template, target in (("base/base-config.bu.tmpl", "base-config"),
                                         ("base/firewall.bu.tmpl", "firewall"),
                                         ("base/nfs-share.bu.tmpl", "nfs-share")):
                    text = render((ROOT / "templates" / template).read_text(), values)
                    (vm_dir / f"{target}.bu").write_text(text)
                    fragments.append(target)
                order = ["base-config"] + sorted(f for f in fragments if f != "base-config")  # build-vm.sh rule
                values["MERGE_ENTRIES"] = "\n".join(f"      - local: igns/{f}.ign" for f in order)
                (vm_dir / "config.bu").write_text(
                    render((ROOT / "templates" / "base" / "config.bu.tmpl").read_text(), values))
                result = subprocess.run(["bash", str(ROOT / "tools" / "build-vm.sh"), str(vm_dir)],
                                        capture_output=True, text=True, timeout=600)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("ok    quadlet", result.stdout)
                self.assertIn("ok    nft", result.stdout)
                # Live push: the pinning unit is written and enabled after daemon-reload,
                # so loginctl enable-linger (guide 3.7) starts it before the user's systemd.
                from ign_to_script import to_script
                svc = spec["name"]
                script = to_script(json.loads((vm_dir / "igns" / f"{svc}.ign").read_text()))
                after = script.split("priv systemctl daemon-reload", 1)[1]
                self.assertIn(f"priv systemctl enable subids-{svc}.service", after)
                self.assertIn(f"/etc/systemd/system/subids-{svc}.service", script)


if __name__ == "__main__":
    unittest.main()
