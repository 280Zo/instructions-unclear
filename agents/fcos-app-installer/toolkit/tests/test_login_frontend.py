"""The login front end (Traefik + Authentik) built by the generator.

Replaces the v1 edge template tests (EdgeTests, the Traefik ReviewFixTests):
the same promises, checked against generated output.
"""
import copy
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gen_service import SpecError  # noqa: E402
from layout import SKILLS  # noqa: E402
from login_frontend import frontend_specs, generate_login_frontend  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SCRATCH = "/tmp/opencode" if os.path.isdir("/tmp/opencode") else None
SITE = yaml.safe_load((FIXTURES / "site.yaml").read_text())


def spec_fixture(name: str) -> dict:
    return yaml.safe_load((FIXTURES / "services" / f"{name}.yaml").read_text())


def directives(text: str, key: str) -> list[str]:
    return [line.split("=", 1)[1] for line in text.splitlines() if line.startswith(f"{key}=")]


class TagLoader(yaml.SafeLoader):
    """Reads Authentik's custom tags as plain data: (tag, value)."""


for _tag in ("!Find", "!KeyOf", "!Env"):
    TagLoader.add_constructor(_tag, lambda loader, node, tag=_tag: (
        tag, loader.construct_sequence(node, deep=True) if isinstance(node, yaml.SequenceNode)
        else loader.construct_scalar(node)))


class FrontendCase(unittest.TestCase):
    def gen(self, services=("monica", "single"), site=None) -> Path:
        path = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, path, True)
        generate_login_frontend(copy.deepcopy(SITE if site is None else site),
                                [spec_fixture(s) for s in services], path)
        return path

    def read(self, out: Path, rel: str) -> str:
        return (out / "rendered" / rel).read_text()

    def files(self, out: Path, rel: str) -> dict:
        data = yaml.safe_load(self.read(out, rel))
        return {e["path"]: e for e in data.get("storage", {}).get("files", [])}

    def all_containers(self, out: Path) -> dict:
        return {p.name: p.read_text() for p in (out / "rendered" / "files").glob("*.container")}


class SpecTests(FrontendCase):
    def test_specs_are_placeholders_filled_from_the_site(self):
        for module in ("ingress-traefik", "authgw-authentik"):
            text = (SKILLS / module / "spec.yaml").read_text()
            self.assertIn("<site: ", text, module)
        traefik, authentik = frontend_specs(copy.deepcopy(SITE))
        self.assertEqual((traefik["vm"], traefik["uid"], traefik["gid"]), ("edge", 3202, 3202))
        self.assertEqual((authentik["vm"], authentik["uid"], authentik["gid"]), ("edge", 3201, 3201))
        self.assertEqual(traefik["containers"][0]["image"], SITE["edge"]["traefik"]["image"])
        self.assertNotIn("<site: ", yaml.safe_dump([traefik, authentik]))

    def test_missing_site_value_is_named(self):
        for path in (("edge", "vm"), ("edge", "traefik", "image"), ("edge", "authentik", "postgres_image"),
                     ("edge", "authentik", "host"), ("acme_email",)):
            with self.subTest(path=".".join(path)):
                site = copy.deepcopy(SITE)
                node = site
                for key in path[:-1]:
                    node = node[key]
                del node[path[-1]]
                with self.assertRaises(SpecError) as caught:
                    generate_login_frontend(site, [], tempfile.mkdtemp(dir=SCRATCH))
                self.assertIn(".".join(path), str(caught.exception))

    def test_edge_vm_must_be_listed(self):
        site = copy.deepcopy(SITE)
        site["edge"]["vm"] = "nope"
        with self.assertRaises(SpecError):
            generate_login_frontend(site, [], tempfile.mkdtemp(dir=SCRATCH))


class TraefikTests(FrontendCase):
    def test_traefik_no_socket(self):
        out = self.gen()
        static = self.read(out, "files/traefik.yml")
        for text in list(self.all_containers(out).values()) + [static]:
            self.assertNotIn("docker.sock", text)
            self.assertNotIn("podman.sock", text)
        providers = yaml.safe_load(static)["providers"]
        self.assertEqual(list(providers), ["file"])
        self.assertEqual(providers["file"]["directory"], "/dynamic")

    def test_traefik_container(self):
        text = self.read(self.gen(), "files/traefik-traefik.container")
        self.assertIn("Network=host", text.splitlines())
        self.assertIn("UserNS=keep-id", text.splitlines())
        self.assertEqual(directives(text, "Volume"), [
            "/var/lib/appdata/traefik/config:/etc/traefik:ro,z",
            "/var/lib/appdata/traefik/dynamic:/dynamic:ro,z",
            "/var/lib/appdata/traefik/acme:/acme:z",
        ])
        self.assertIn("duckdns_token,type=env,target=DUCKDNS_TOKEN", directives(text, "Secret"))
        self.assertNotIn("PublishPort", text)

    def test_wildcard_only_via_duckdns(self):
        static = yaml.safe_load(self.read(self.gen(), "files/traefik.yml"))
        tls = static["entryPoints"]["websecure"]["http"]["tls"]
        self.assertEqual(tls["domains"], [{"main": "*.example.duckdns.org"}])
        acme = static["certificatesResolvers"]["letsencrypt"]["acme"]
        self.assertEqual(acme["dnsChallenge"]["provider"], "duckdns")
        self.assertIn("delayBeforeChecks", acme["dnsChallenge"]["propagation"])
        self.assertEqual(acme["storage"], "/acme/acme.json")
        self.assertEqual(acme["email"], SITE["acme_email"])
        redirect = static["entryPoints"]["web"]["http"]["redirections"]["entryPoint"]
        self.assertEqual((redirect["to"], redirect["scheme"]), ("websecure", "https"))

    def test_forward_auth_middleware(self):
        dynamic = yaml.safe_load(self.read(self.gen(), "files/00-authgw-authentik.yml"))["http"]
        auth = dynamic["middlewares"]["authentik"]["forwardAuth"]
        self.assertEqual(auth["address"], "http://127.0.0.1:9000/outpost.goauthentik.io/auth/traefik")
        self.assertTrue(auth["trustForwardHeader"])
        self.assertIn("X-authentik-username", auth["authResponseHeaders"])
        self.assertEqual(dynamic["routers"]["authentik"]["rule"], "Host(`auth.example.duckdns.org`)")
        self.assertNotIn("middlewares", dynamic["routers"]["authentik"])

    def test_network_host_only_on_traefik(self):
        out = self.gen()
        hosts = [name for name, text in self.all_containers(out).items() if "Network=host" in text.splitlines()]
        self.assertEqual(hosts, ["traefik-traefik.container"])


class AuthentikTests(FrontendCase):
    def test_authentik_matches_the_official_compose(self):
        out = self.gen()
        server = self.read(out, "files/authentik-server.container")
        worker = self.read(out, "files/authentik-worker.container")
        self.assertEqual(directives(server, "PublishPort"), ["127.0.0.1:9000:9000"])
        self.assertNotIn("PublishPort", worker)
        for text, command in ((server, "server"), (worker, "worker")):
            self.assertEqual(directives(text, "Exec"), [command])
            self.assertEqual(directives(text, "ShmSize"), ["512m"])
            self.assertIn("/var/lib/appdata/authentik/data:/data:z", directives(text, "Volume"))
            self.assertIn("/var/lib/appdata/authentik/custom-templates:/templates:z", directives(text, "Volume"))
            self.assertNotIn(":/media", text)
            self.assertIn("authentik_secret_key,type=env,target=AUTHENTIK_SECRET_KEY", directives(text, "Secret"))
            self.assertIn("Requires=authentik-postgres.service", text.splitlines())
        self.assertIn("/var/lib/appdata/authentik/certs:/certs:z", directives(worker, "Volume"))
        self.assertIn("/var/lib/appdata/authentik/blueprints:/blueprints/custom:ro,z", directives(worker, "Volume"))
        self.assertNotIn("redis", "".join(self.all_containers(out).values()).lower())

    def test_authentik_postgres_local_db(self):
        out = self.gen()
        db = self.read(out, "files/authentik-postgres.container")
        self.assertEqual(directives(db, "Volume"), ["/var/lib/appdata/authentik/db/postgres:/var/lib/postgresql/data:z"])
        self.assertIn("Network=authentik.network", db.splitlines())
        self.assertEqual(directives(db, "ExecStartPre"), ["/usr/local/bin/require-mounts /var/lib/appdata"])
        backup = self.read(out, "authentik-backup-postgres.bu")
        self.assertIn("pg_dump", backup)
        self.assertIn("authentik-postgres", backup)


class RouteTests(FrontendCase):
    def test_routes_for_login_services_only(self):
        app_only = spec_fixture("single")
        app_only.update(name="notes", uid=3150, login="app-only", login_reason="It has its own login")
        app_only.pop("hostname")  # no web name: internal only
        open_app = spec_fixture("single")
        open_app.update(name="dav", uid=3151, hostname="dav", login="app-only", login_reason="Phones sync directly")
        path = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, path, True)
        generate_login_frontend(copy.deepcopy(SITE), [spec_fixture("monica"), spec_fixture("single"), app_only,
                                                      open_app], path)
        out = path
        files = self.files(out, "login-frontend.bu")
        self.assertIn("/var/lib/appdata/traefik/dynamic/monica.yml", files)
        self.assertIn("/var/lib/appdata/traefik/dynamic/opencode.yml", files)
        self.assertNotIn("/var/lib/appdata/traefik/dynamic/notes.yml", files)  # app-only, no web name
        self.assertFalse((out / "rendered" / "files" / "route-notes.yml").exists())
        # app-only with a web name: an HTTPS route without the login, and a dashboard link
        self.assertIn("/var/lib/appdata/traefik/dynamic/dav.yml", files)
        self.assertIn("/var/lib/appdata/authentik/blueprints/app-dav.yaml", files)
        route = yaml.safe_load(self.read(out, "files/route-dav.yml"))["http"]["routers"]["dav"]
        self.assertNotIn("middlewares", route)
        link = yaml.safe_load(self.read(out, "files/app-dav.blueprint.yaml"))
        self.assertEqual([e["model"] for e in link["entries"]], ["authentik_core.application"])
        self.assertIsNone(link["entries"][0]["attrs"]["provider"])
        # no outpost entry and no apply-first entry for it
        metas = [e["attrs"]["identifiers"]["name"] for e in yaml.load(
            self.read(out, "files/outpost-providers.blueprint.yaml"), Loader=TagLoader)["entries"]
            if e["model"] == "authentik_blueprints.metaapplyblueprint"]
        self.assertEqual(metas, ["app-monica", "app-opencode"])
        outpost = yaml.load(self.read(out, "files/outpost-providers.blueprint.yaml"), Loader=TagLoader)
        names = [p[1][1][1] for p in outpost["entries"][-1]["attrs"]["providers"]]
        self.assertEqual(names, ["monica", "opencode"])
        route = yaml.safe_load(self.read(out, "files/route-monica.yml"))["http"]
        self.assertEqual(route["routers"]["monica"]["rule"], "Host(`monica.example.duckdns.org`)")
        self.assertEqual(route["routers"]["monica"]["middlewares"], ["authentik"])
        self.assertEqual(route["routers"]["monica-outpost"]["priority"], 15)
        self.assertIn("PathPrefix(`/outpost.goauthentik.io/`)", route["routers"]["monica-outpost"]["rule"])
        self.assertEqual(route["services"]["monica"]["loadBalancer"]["servers"], [{"url": "http://192.0.2.30:8110"}])

    def test_files_land_in_the_mounted_folders_and_survive_rebuilds(self):
        out = self.gen()
        files = self.files(out, "login-frontend.bu")
        expected = {
            "/var/lib/appdata/traefik/config/traefik.yml": (3202, "files/traefik.yml"),
            "/var/lib/appdata/traefik/dynamic/00-authgw-authentik.yml": (3202, "files/00-authgw-authentik.yml"),
            "/var/lib/appdata/traefik/dynamic/monica.yml": (3202, "files/route-monica.yml"),
            "/var/lib/appdata/authentik/blueprints/app-monica.yaml": (3201, "files/app-monica.blueprint.yaml"),
            "/var/lib/appdata/authentik/blueprints/outpost-providers.yaml":
                (3201, "files/outpost-providers.blueprint.yaml"),
        }
        for path, (uid, local) in expected.items():
            with self.subTest(path=path):
                entry = files[path]
                self.assertTrue(entry["overwrite"])
                self.assertEqual(entry["user"]["id"], uid)
                self.assertEqual(entry["group"]["id"], uid)
                self.assertEqual(entry["contents"]["local"], local)
                self.assertTrue((out / "rendered" / local).is_file())

    def test_multiline_api_paths_indented(self):
        # Deferred fix #6: every regex on its own line of the block scalar.
        out = self.gen()
        blueprint = yaml.load(self.read(out, "files/app-monica.blueprint.yaml"), Loader=TagLoader)
        provider = blueprint["entries"][0]
        self.assertEqual(provider["attrs"]["skip_path_regex"].splitlines(),
                         ["^/dav/.*$", r"^/\.well-known/(carddav|caldav)$"])
        self.assertEqual(blueprint["entries"][1]["attrs"]["provider"], ("!KeyOf", provider["id"]))

    def test_outpost_blueprint_applies_apps_first(self):
        # Deferred fix #7: Authentik applies blueprints in no fixed order, so the
        # outpost blueprint applies each app blueprint first (meta model).
        out = self.gen()
        data = yaml.load(self.read(out, "files/outpost-providers.blueprint.yaml"), Loader=TagLoader)
        entries = data["entries"]
        metas = [e for e in entries if e["model"] == "authentik_blueprints.metaapplyblueprint"]
        self.assertEqual([m["attrs"]["identifiers"]["name"] for m in metas], ["app-monica", "app-opencode"])
        self.assertTrue(all(m["attrs"].get("required", True) for m in metas))
        outpost = entries[-1]
        self.assertEqual(outpost["model"], "authentik_outposts.outpost")
        self.assertLess(max(entries.index(m) for m in metas), entries.index(outpost))
        self.assertEqual(outpost["identifiers"], {"managed": "goauthentik.io/outposts/embedded"})
        self.assertEqual(outpost["attrs"]["providers"], [
            ("!Find", ["authentik_providers_proxy.proxyprovider", ["name", "monica"]]),
            ("!Find", ["authentik_providers_proxy.proxyprovider", ["name", "opencode"]]),
        ])

    def test_outpost_names_stay_strings(self):
        spec = spec_fixture("monica")
        spec.update(name="null", hostname="crm")
        path = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, path, True)
        generate_login_frontend(copy.deepcopy(SITE), [spec], path)
        data = yaml.load((path / "rendered" / "files" / "outpost-providers.blueprint.yaml").read_text(),
                         Loader=TagLoader)
        self.assertEqual(data["entries"][-1]["attrs"]["providers"],
                         [("!Find", ["authentik_providers_proxy.proxyprovider", ["name", "null"]])])
        self.assertEqual(data["entries"][0]["attrs"]["identifiers"]["name"], "app-null")

    def test_no_services_gives_an_empty_provider_list(self):
        data = yaml.load(self.read(self.gen(services=()), "files/outpost-providers.blueprint.yaml"),
                         Loader=TagLoader)
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["attrs"]["providers"], [])

    def test_clashing_hostnames_refused(self):
        other = spec_fixture("single")
        other["hostname"] = "monica"
        with self.assertRaises(SpecError) as caught:
            generate_login_frontend(copy.deepcopy(SITE), [spec_fixture("monica"), other],
                                    tempfile.mkdtemp(dir=SCRATCH))
        self.assertIn("monica", str(caught.exception))
        auth_label = SITE["edge"]["authentik"]["host"].split(".")[0]
        other["hostname"] = auth_label
        with self.assertRaises(SpecError):
            generate_login_frontend(copy.deepcopy(SITE), [other], tempfile.mkdtemp(dir=SCRATCH))

    def test_service_names_of_the_front_end_refused(self):
        for name in ("traefik", "authentik"):
            with self.subTest(name=name):
                spec = spec_fixture("single")
                spec["name"] = name
                with self.assertRaises(SpecError) as caught:
                    generate_login_frontend(copy.deepcopy(SITE), [spec], tempfile.mkdtemp(dir=SCRATCH))
                self.assertIn(name, str(caught.exception))

    def test_names_that_clash_with_traefik_routers_refused(self):
        # 00-authgw-authentik.yml defines authentik-server and authentik-outpost; every
        # route adds <svc>-outpost. A duplicate name would break the shared ones.
        for name in ("authentik-server", "authentik-outpost", "monica-outpost", "x-outpost"):
            with self.subTest(name=name):
                spec = spec_fixture("single")
                spec.update(name=name, hostname="other")
                with self.assertRaises(SpecError) as caught:
                    generate_login_frontend(copy.deepcopy(SITE), [spec_fixture("monica"), spec],
                                            tempfile.mkdtemp(dir=SCRATCH))
                self.assertIn(name, str(caught.exception))

    def test_bad_front_end_value_writes_nothing(self):
        site = copy.deepcopy(SITE)
        site["edge"]["authentik"]["postgres_image"] = "postgres:latest"
        out = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        with self.assertRaises(SpecError) as caught:
            generate_login_frontend(site, [], out)
        self.assertIn("authentik", str(caught.exception))
        self.assertEqual(list(out.iterdir()), [])

    def test_app_blueprint_is_a_forward_auth_provider(self):
        blueprint = yaml.load(self.read(self.gen(), "files/app-monica.blueprint.yaml"), Loader=TagLoader)
        self.assertEqual(blueprint["metadata"]["name"], "app-monica")
        provider, app = blueprint["entries"]
        self.assertEqual(provider["model"], "authentik_providers_proxy.proxyprovider")
        self.assertEqual(provider["attrs"]["mode"], "forward_single")
        self.assertEqual(provider["attrs"]["external_host"], "https://monica.example.duckdns.org")
        self.assertEqual(provider["attrs"]["invalidation_flow"],
                         ("!Find", ["authentik_flows.flow", ["slug", "default-provider-invalidation-flow"]]))
        self.assertEqual(app["model"], "authentik_core.application")

    def test_service_list_with_a_non_mapping_refused(self):
        with self.assertRaises(SpecError):
            generate_login_frontend(copy.deepcopy(SITE), ["monica"], tempfile.mkdtemp(dir=SCRATCH))

    def test_invalid_service_spec_refused(self):
        bad = spec_fixture("monica")
        bad["api_paths"] = ["^/a$\u2028  - model: authentik_core.user"]
        with self.assertRaises(SpecError):
            generate_login_frontend(copy.deepcopy(SITE), [bad], tempfile.mkdtemp(dir=SCRATCH))

    def test_loopback_service_only_on_the_edge_vm(self):
        spec = spec_fixture("single")
        spec["bind"] = "loopback"
        with self.assertRaises(SpecError) as caught:
            generate_login_frontend(copy.deepcopy(SITE), [spec], tempfile.mkdtemp(dir=SCRATCH))
        self.assertIn("loopback", str(caught.exception))
        spec["vm"] = "edge"
        spec["containers"][0]["volumes"].pop()  # its NFS share isn't on the edge VM
        out = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        generate_login_frontend(copy.deepcopy(SITE), [spec], out)
        route = yaml.safe_load((out / "rendered" / "files" / "route-opencode.yml").read_text())
        self.assertEqual(route["http"]["services"]["opencode"]["loadBalancer"]["servers"],
                         [{"url": "http://127.0.0.1:4096"}])


class AcmeTests(FrontendCase):
    """The certificate provider comes from the DNS adapter the site names, not from Traefik's files."""

    def other_provider(self):
        import adapters
        folder = Path(tempfile.mkdtemp(prefix="adapters-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, folder, True)
        (folder / "adapter-exampledns").mkdir()
        step = {"title": "t", "steps": ["do it"], "uses": [], "report_back": ["done"]}
        (folder / "adapter-exampledns" / "adapter.yaml").write_text(yaml.safe_dump({
            "role": "dns_certificates", "provider": "exampledns", "name": "ExampleDNS",
            "docs": ["https://example.org/dns"],
            "acme": {"provider": "exampledns", "env": "EXAMPLEDNS_API_KEY", "store_as": "exampledns_key",
                     "notes": "Example DNS allows several TXT records."},
            "owner_steps": {"api_token": step, "acme_provider": step}}))
        original = adapters.ADAPTERS
        adapters.ADAPTERS = folder
        self.addCleanup(setattr, adapters, "ADAPTERS", original)

    def site(self, provider):
        site = copy.deepcopy(SITE)
        site["roles"] = {"dns_certificates": {"provider": provider}}
        if provider != "duckdns":  # a domain with the other provider, so nothing else mentions the first
            site["domain"] = "example.org"
            site["edge"]["authentik"]["host"] = "auth.example.org"
        return site

    def test_the_default_site_uses_the_provider_it_names(self):
        out = self.gen(site=self.site("duckdns"))
        self.assertIn("provider: duckdns", self.read(out, "files/traefik.yml"))
        self.assertIn("DUCKDNS_TOKEN", "".join(self.all_containers(out).values()))

    def test_another_dns_provider_changes_the_settings_secret_and_variable(self):
        self.other_provider()
        out = self.gen(site=self.site("exampledns"))
        static = self.read(out, "files/traefik.yml")
        self.assertIn("provider: exampledns", static)
        self.assertIn("Example DNS allows several TXT records.", static)
        text = "".join(self.all_containers(out).values()) + (out / "secrets.md").read_text()
        self.assertIn("EXAMPLEDNS_API_KEY", text)
        self.assertIn("exampledns_key", text)
        everything = "".join(p.read_text() for p in out.rglob("*") if p.is_file())
        self.assertNotIn("duckdns", everything.lower())

    def test_no_dns_provider_chosen_stops_the_generator_with_the_fix(self):
        site = copy.deepcopy(SITE)
        site.pop("roles", None)
        with self.assertRaises(SpecError) as caught:
            self.gen(site=site)
        self.assertIn("roles.dns_certificates.provider", str(caught.exception))

    def test_the_traefik_module_names_no_dns_provider(self):
        for path in (SKILLS / "ingress-traefik").rglob("*"):
            if path.is_file() and path.suffix != ".md":
                self.assertNotIn("duckdns", path.read_text().lower(), str(path))
        self.assertNotIn("duckdns", (ROOT / "tools" / "ingress" / "traefik.py").read_text().lower())


class OldTemplatesGoneTests(unittest.TestCase):
    def test_replaced_templates_deleted(self):
        # The product templates live with their modules, not in the shared templates folder.
        self.assertFalse((ROOT / "templates" / "edge").exists())
        for module, names in {"ingress-traefik": ("traefik.yml.tmpl", "route-open.yml.tmpl",
                                                  "gateways/authgw-authentik/route.yml.tmpl",
                                                  "gateways/authgw-authentik/middleware.yml.tmpl"),
                              "authgw-authentik": ("app.blueprint.yaml.tmpl", "bookmark.blueprint.yaml.tmpl",
                                                   "outpost-providers.blueprint.yaml.tmpl")}.items():
            for name in names:
                self.assertTrue((SKILLS / module / "templates" / name).is_file(), f"{module}/{name}")


if __name__ == "__main__":
    unittest.main()


class PeopleAndIconTests(FrontendCase):
    """Users are created locally (no email, no outside connection);
    groups decide which apps each person gets; app logos are stored on the VM."""

    def people_site(self, people):
        site = copy.deepcopy(SITE)
        site["people"] = people
        return site

    def blueprint(self, out):
        return yaml.load(self.read(out, "files/access.blueprint.yaml"), Loader=TagLoader)

    def test_people_become_authentik_users_created_once(self):
        # authentik 2026.8.5 core/models.py: User.groups (ak_groups deprecated). state: created, so
        # the owner's later group changes in the admin interface are never overwritten.
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        site = self.people_site([{"username": "sam", "name": "Sam Example", "groups": ["family"]},
                                 {"username": "guest1", "name": "A Guest", "groups": ["guests"]}])
        generate_login_frontend(site, [spec_fixture("monica")], out)
        entries = self.blueprint(out)["entries"]
        groups = {e["identifiers"]["name"] for e in entries if e["model"] == "authentik_core.group"}
        self.assertEqual(groups, {"family", "guests"})
        users = [e for e in entries if e["model"] == "authentik_core.user"]
        sam = next(u for u in users if u["identifiers"]["username"] == "sam")
        self.assertEqual(sam["state"], "created")
        self.assertEqual(sam["attrs"]["name"], "Sam Example")
        self.assertEqual(sam["attrs"]["groups"], [("!KeyOf", "group-family")])
        for user in users:
            self.assertNotIn("password", user["attrs"])
            self.assertNotIn("password_hash", user["attrs"])
            self.assertNotIn("email", user["attrs"])
        placed = self.files(out, "login-frontend.bu")
        self.assertTrue(any(p.endswith("/access.yaml") for p in placed))

    def test_bad_people_refused(self):
        for bad in ([{"username": "Sam", "name": "x", "groups": []}], [{"username": "sam", "name": "a\nb", "groups": []}],
                    [{"username": "sam", "name": "x", "groups": ["Family"]}], [{"username": "sam", "name": "x"}],
                    [{"username": "sam", "name": "x", "groups": [], "password": "p"}],
                    [{"username": "sam", "name": "x", "groups": []}, {"username": "sam", "name": "y", "groups": []}],
                    [{"username": "akadmin", "name": "x", "groups": []}]):
            with self.subTest(bad=bad), self.assertRaisesRegex(SpecError, "people"):
                generate_login_frontend(self.people_site(bad), [], tempfile.mkdtemp(dir=SCRATCH))

    def test_without_people_or_groups_no_access_file(self):
        out = self.gen()
        self.assertFalse((out / "rendered" / "files" / "access.blueprint.yaml").exists())

    def test_every_group_is_created_once_and_bound_after_its_app(self):
        # One file creates each group (people's and apps'), so nothing races on the unique name.
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        spec = spec_fixture("monica")
        spec["groups"] = ["family", "guests"]
        site = self.people_site([{"username": "sam", "name": "Sam 😀 Example", "groups": ["family"]}])
        generate_login_frontend(site, [spec], out)
        text = self.read(out, "files/access.blueprint.yaml")
        self.assertIn("Sam 😀 Example", text)  # kept as text, not escaped surrogates
        entries = self.blueprint(out)["entries"]
        groups = [e["identifiers"]["name"] for e in entries if e["model"] == "authentik_core.group"]
        self.assertEqual(sorted(groups), ["family", "guests"])
        meta = [e for e in entries if e["model"] == "authentik_blueprints.metaapplyblueprint"]
        self.assertEqual([m["attrs"]["identifiers"]["name"] for m in meta], ["app-monica"])
        self.assertTrue(all(m["attrs"]["required"] for m in meta))
        binds = [e for e in entries if e["model"] == "authentik_policies.policybinding"]
        self.assertEqual(len(binds), 2)
        for order, bind in enumerate(binds):
            self.assertEqual(bind["identifiers"]["target"], ("!Find", ["authentik_core.application", ["slug", "monica"]]))
            self.assertEqual(bind["identifiers"]["group"][0], "!KeyOf")
            self.assertEqual(bind["attrs"], {"order": order})
        self.assertLess(entries.index(meta[0]), entries.index(binds[0]))
        # Names like "yes" stay text.
        spec["groups"] = ["yes"]
        generate_login_frontend(self.people_site([]), [spec], out)
        names = [e["identifiers"]["name"] for e in self.blueprint(out)["entries"] if e["model"] == "authentik_core.group"]
        self.assertEqual(names, ["yes"])

    def test_scripted_svg_icons_refused(self):
        for svg in ("<svg><script>x</script></svg>", '<svg onload="x"/>', '<svg><a href="javascript:x"/></svg>',
                    "<svg><foreignObject/></svg>"):
            src = Path(tempfile.mkdtemp(dir=SCRATCH))
            self.addCleanup(shutil.rmtree, src, True)
            (src / "monica.svg").write_text(svg)
            spec = spec_fixture("monica")
            spec["icon"] = "monica.svg"
            with self.subTest(svg=svg), self.assertRaisesRegex(SpecError, "icon"):
                generate_login_frontend(copy.deepcopy(SITE), [spec], tempfile.mkdtemp(dir=SCRATCH),
                                        icon_dirs={"monica": src})

    def test_icon_is_stored_on_the_vm_and_referenced_locally(self):
        # docs.goauthentik.io/customize/file-picker/: /data/media/public/<rel> is referenced as <rel>.
        src = Path(tempfile.mkdtemp(dir=SCRATCH))
        self.addCleanup(shutil.rmtree, src, True)
        (src / "monica.svg").write_text("<svg/>")
        spec = spec_fixture("monica")
        spec["icon"] = "monica.svg"
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        generate_login_frontend(copy.deepcopy(SITE), [spec], out, icon_dirs={"monica": src})
        app = yaml.load(self.read(out, "files/app-monica.blueprint.yaml"), Loader=TagLoader)
        application = next(e for e in app["entries"] if e["model"] == "authentik_core.application")
        self.assertEqual(application["attrs"]["icon"], "app-icons/monica.svg")
        self.assertEqual((out / "rendered" / "files" / "icon-monica.svg").read_text(), "<svg/>")
        bu = yaml.safe_load(self.read(out, "login-frontend.bu"))
        icon = next(f for f in bu["storage"]["files"] if f["path"].endswith("/media/public/app-icons/monica.svg"))
        dirs = {d["path"]: d for d in bu["storage"].get("directories", [])}
        media = next(p for p in dirs if p.endswith("/media"))
        # Folders Authentik writes to keep its own owner (else its uploads would break).
        for path in (media, media + "/public", media + "/public/app-icons"):
            self.assertEqual(dirs[path]["user"]["id"], icon["user"]["id"])

    def test_bad_icon_refused(self):
        for bad in ("../x.svg", "x.exe", "a b.png", "/etc/x.png"):
            spec = spec_fixture("monica")
            spec["icon"] = bad
            with self.subTest(bad=bad):
                from gen_service import validate_spec
                self.assertTrue(any("icon" in e for e in validate_spec(spec, copy.deepcopy(SITE))))


class SignupTests(FrontendCase):
    """Anyone who can reach the login page may create an account (no email,
    nothing outside), landing in a default group. Official example: blueprints/example/
    flows-enrollment-2-stage.yaml; fields from authentik 2026.8.5 stages/user_write/models.py
    (create_users_group) and stages/identification/models.py (enrollment_flow)."""

    def gen_signup(self, signup, services=("monica",)):
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        site = copy.deepcopy(SITE)
        site["signup"] = signup
        generate_login_frontend(site, [spec_fixture(s) for s in services], out)
        return out

    def entries(self, out):
        return yaml.load(self.read(out, "files/signup.blueprint.yaml"), Loader=TagLoader)["entries"]

    def test_signup_flow_puts_new_accounts_in_the_default_group(self):
        entries = self.entries(self.gen_signup({"group": "guests"}))
        by = {}
        for e in entries:
            by.setdefault(e["model"], []).append(e)
        # Review: in its own file, so a failure here can't roll back access.yaml's bindings;
        # the group itself is created there (applied first).
        self.assertNotIn("authentik_core.group", by)
        meta = by["authentik_blueprints.metaapplyblueprint"][0]["attrs"]
        self.assertEqual((meta["identifiers"]["name"], meta["required"]), ("access", True))
        access = yaml.load(self.read(self.gen_signup({"group": "guests"}), "files/access.blueprint.yaml"), Loader=TagLoader)
        self.assertIn("guests", [e["identifiers"]["name"] for e in access["entries"] if e["model"] == "authentik_core.group"])
        self.assertFalse([e for e in access["entries"] if e["model"] in ("authentik_flows.flow", "authentik_sources_oauth.oauthsource")])
        flow = by["authentik_flows.flow"][0]
        self.assertEqual(flow["attrs"]["designation"], "enrollment")
        self.assertEqual(flow["attrs"]["authentication"], "require_unauthenticated")
        write = by["authentik_stages_user_write.userwritestage"][0]["attrs"]
        self.assertEqual(write["user_creation_mode"], "always_create")
        self.assertEqual(write["create_users_group"], ("!Find", ["authentik_core.group", ["name", "guests"]]))
        self.assertFalse(write["create_users_as_inactive"])
        self.assertEqual(write["user_type"], "internal")  # may use the user interface (own password)
        # Review: a password policy on the sign-up prompt (nothing checked online).
        policy = by["authentik_policies_password.passwordpolicy"][0]["attrs"]
        self.assertGreaterEqual(policy["length_min"], 12)
        self.assertTrue(policy["check_zxcvbn"])
        self.assertFalse(policy["check_have_i_been_pwned"])
        self.assertTrue(policy["error_message"])
        first = next(e for e in by["authentik_stages_prompt.promptstage"] if e["identifiers"]["name"] == "signup-prompt-first")
        self.assertEqual(first["attrs"]["validation_policies"], [("!KeyOf", "signup-password-policy")])
        fields = [p["attrs"]["field_key"] for p in by["authentik_stages_prompt.prompt"]]
        self.assertEqual(sorted(fields), ["name", "password", "password_repeat", "username"])  # no email
        ident = by["authentik_stages_identification.identificationstage"][0]
        self.assertEqual(ident["identifiers"], {"name": "default-authentication-identification"})
        # The serializer requires user_fields on every update ("When no user
        # fields are selected, at least one source must be selected"); the default flow's values.
        self.assertEqual(set(ident["attrs"]), {"enrollment_flow", "user_fields"})
        self.assertEqual(ident["attrs"]["user_fields"], ["email", "username"])
        orders = [b["identifiers"]["order"] for b in by["authentik_flows.flowstagebinding"]]
        self.assertEqual(orders, sorted(orders))

    def test_approval_mode_creates_inactive_accounts(self):
        write = next(e for e in self.entries(self.gen_signup({"group": "guests", "approve": True}))
                     if e["model"] == "authentik_stages_user_write.userwritestage")["attrs"]
        self.assertTrue(write["create_users_as_inactive"])

    def test_without_signup_no_flow(self):
        out = self.gen_signup(None)
        self.assertFalse((out / "rendered/files/signup.blueprint.yaml").exists())

    def test_bad_signup_refused(self):
        for bad in ({"group": "Guests"}, {"group": "guests", "approve": "yes"}, {"group": "guests", "x": 1}, "on"):
            with self.subTest(bad=bad), self.assertRaisesRegex(SpecError, "signup"):
                self.gen_signup(bad)


class SigninSourceTests(FrontendCase):
    """Sign in with an existing Google or Apple account (OAuth 2.0 / OIDC);
    no mail is ever sent. Authentik 2026.8.5: sources/oauth/models.py (provider_type,
    consumer_key, consumer_secret), blueprints/default/flow-default-source-enrollment.yaml,
    blueprint tag !Env; docs social-logins/google/cloud and apple."""

    SOURCES = {"google": {"client_id": "123-abc.apps.googleusercontent.com"},
               "apple": {"client_id": "com.example.login.signin;TEAM123456;KEY1234567"}}

    def gen_sources(self, sources, signup={"group": "guests"}):
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        site = copy.deepcopy(SITE)
        site["signup"] = signup
        site["signin_sources"] = sources
        generate_login_frontend(site, [spec_fixture("monica")], out)
        return out

    def test_sources_are_created_with_secrets_from_the_environment(self):
        out = self.gen_sources(self.SOURCES)
        entries = yaml.load(self.read(out, "files/signup.blueprint.yaml"), Loader=TagLoader)["entries"]
        src = {e["identifiers"]["slug"]: e for e in entries if e["model"] == "authentik_sources_oauth.oauthsource"}
        self.assertEqual(set(src), {"google", "apple"})  # slugs match the providers' return URLs
        g = src["google"]["attrs"]
        self.assertEqual(g["provider_type"], "google")
        self.assertEqual(g["consumer_key"], "123-abc.apps.googleusercontent.com")
        self.assertEqual(g["consumer_secret"], ("!Env", "SOURCE_GOOGLE_SECRET"))
        self.assertEqual(g["enrollment_flow"], ("!KeyOf", "signup-source-flow"))
        self.assertEqual(g["authentication_flow"], ("!Find", ["authentik_flows.flow", ["slug", "default-source-authentication"]]))
        self.assertEqual(src["apple"]["attrs"]["consumer_secret"], ("!Env", "SOURCE_APPLE_KEY"))
        write = next(e for e in entries if e.get("identifiers", {}).get("name") == "signup-source-write")
        self.assertEqual(write["attrs"]["create_users_group"], ("!Find", ["authentik_core.group", ["name", "guests"]]))
        self.assertEqual(write["attrs"]["user_type"], "internal")
        ident = next(e for e in entries if e["model"] == "authentik_stages_identification.identificationstage")
        self.assertEqual(ident["attrs"]["sources"], [("!KeyOf", "source-google"), ("!KeyOf", "source-apple")])
        # The worker gets the secrets as environment variables; secrets.md tells the owner how.
        worker = self.read(out, "files/authentik-worker.container")
        self.assertIn("Secret=authentik_google_secret,type=env,target=SOURCE_GOOGLE_SECRET", worker)
        self.assertIn("Secret=authentik_apple_key,type=env,target=SOURCE_APPLE_KEY", worker)
        secrets = (out / "secrets.md").read_text()
        self.assertIn("## authentik_google_secret", secrets)
        self.assertIn('read -rs -p "value for authentik_google_secret', secrets)
        self.assertIn("## authentik_apple_key", secrets)
        self.assertIn("shred -u", secrets)  # the key file is loaded, then the copy removed
        self.assertIn("/dev/shm", secrets)  # copied to memory, not the VM's disk

    def test_sources_need_the_signup_group(self):
        with self.assertRaisesRegex(SpecError, "signin_sources"):
            self.gen_sources(self.SOURCES, signup=None)

    def test_bad_sources_refused(self):
        for bad in ({"facebook": {"client_id": "x"}}, {"google": {}}, {"google": {"client_id": "a b"}},
                    {"google": {"client_id": "x", "secret": "s"}}, {"apple": {"client_id": "only-one-part"}}):
            with self.subTest(bad=bad), self.assertRaisesRegex(SpecError, "signin_sources"):
                self.gen_sources(bad)


class NoProfilePictureTests(FrontendCase):
    """No uploaded pictures. Authentik has no built-in upload page, and a picture
    stored as a user attribute lands in the ID token (proxy scope ak_proxy, include_claims_in_id_token),
    which the outpost's sign-out puts into its redirect URL (proxyv2/application/application.go,
    handleSignOut, id_token_hint). The Avatars setting stays the owner's choice in the admin interface."""

    def gen(self, site):
        out = Path(tempfile.mkdtemp(prefix="login-frontend-", dir=SCRATCH))
        self.addCleanup(shutil.rmtree, out, True)
        generate_login_frontend(site, [spec_fixture("monica")], out)
        return out

    def test_user_pictures_refused_with_the_reason(self):
        for value in (True, False):
            site = copy.deepcopy(SITE)
            site["user_pictures"] = value
            with self.subTest(value=value), self.assertRaisesRegex(SpecError, "user_pictures.*removed"):
                self.gen(site)

    def test_no_picture_flow(self):
        out = self.gen(copy.deepcopy(SITE))
        self.assertFalse((out / "rendered/files/profile.blueprint.yaml").exists())
        self.assertNotIn("profile", self.read(out, "login-frontend.bu"))

    def test_the_jwt_header_is_not_passed_to_apps(self):
        # The proxy scope puts every user attribute into X-authentik-jwt; no app here uses it.
        middleware = self.read(self.gen(copy.deepcopy(SITE)), "files/00-authgw-authentik.yml")
        self.assertNotIn("X-authentik-jwt", middleware)
        self.assertIn("X-authentik-username", middleware)
