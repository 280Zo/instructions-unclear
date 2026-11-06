"""Service modules: one skill per product, chosen in site.yaml, never a default.

A module is a skill folder (ingress-<product>, authgw-<product>) with SKILL.md, module.yaml (what it
provides, what it needs, what it pairs with), its service spec and templates. The generic tools read
a module's data and call its code (tools/ingress/<product>.py, tools/authgw/<product>.py); they
name no product themselves.
"""
import io
import re
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from gen_service import SpecError, validate_spec  # noqa: E402
from layout import SKILLS  # noqa: E402
import modules  # noqa: E402

SITE = yaml.safe_load((ROOT / "tests" / "fixtures" / "site.yaml").read_text())
MODULES = {"ingress-traefik": "ingress", "authgw-authentik": "auth_gateway"}
# Names of products the generic code must not know. Lower case; the modules' own files may.
PRODUCTS = ("authentik", "traefik", "duckdns")
GENERIC = ("login_frontend.py", "gen_service.py", "modules.py", "placement.py", "adapters.py",
           "install_notes.py", "check_workspace.py")


class ModuleFilesTests(unittest.TestCase):
    def test_each_module_is_a_skill_with_its_data(self):
        for name, capability in MODULES.items():
            with self.subTest(module=name):
                folder = SKILLS / name
                text = (folder / "SKILL.md").read_text()
                meta = yaml.safe_load(text.split("---", 2)[1])
                self.assertEqual(meta["name"], name)
                self.assertIn("Use when", meta["description"])
                data = yaml.safe_load((folder / "module.yaml").read_text())
                self.assertEqual(data["capability"], capability)
                for key in ("product", "provides", "needs", "pairs_with", "spec", "code"):
                    self.assertIn(key, data, key)
                self.assertTrue((folder / data["spec"]).is_file())
                self.assertTrue((ROOT / "tools" / Path(*data["code"].split(".")).with_suffix(".py")).is_file())

    def test_pairings_name_real_modules_and_say_how_they_fit(self):
        for name in MODULES:
            data = yaml.safe_load((SKILLS / name / "module.yaml").read_text())
            for pairing in data["pairs_with"]:
                with self.subTest(module=name, pairing=pairing.get("module")):
                    self.assertTrue(pairing["how"].strip())
                    self.assertIsInstance(pairing["tested"], bool)

    def test_the_two_modules_pair_with_each_other_and_say_it_is_tested(self):
        ingress = yaml.safe_load((SKILLS / "ingress-traefik" / "module.yaml").read_text())
        gateway = yaml.safe_load((SKILLS / "authgw-authentik" / "module.yaml").read_text())
        self.assertIn(("authgw-authentik", True), [(p["module"], p["tested"]) for p in ingress["pairs_with"]])
        self.assertIn(("ingress-traefik", True), [(p["module"], p["tested"]) for p in gateway["pairs_with"]])

    def test_each_module_names_the_glue_for_every_pairing_it_has_tested(self):
        # The ingress module holds one template set per gateway it has been tested with.
        data = yaml.safe_load((SKILLS / "ingress-traefik" / "module.yaml").read_text())
        for pairing in data["pairs_with"]:
            if pairing["tested"]:
                glue = SKILLS / "ingress-traefik" / "templates" / "gateways" / pairing["module"]
                self.assertTrue((glue / "middleware.yml.tmpl").is_file(), glue)
                self.assertTrue((glue / "route.yml.tmpl").is_file(), glue)


class LoaderTests(unittest.TestCase):
    def test_the_site_must_choose_each_module_and_there_is_no_default(self):
        site = {k: v for k, v in SITE.items() if k != "login_frontend"}
        with self.assertRaises(SpecError) as caught:
            modules.chosen(site)
        self.assertIn("login_frontend.ingress", str(caught.exception))
        self.assertIn("ingress-traefik", str(caught.exception))  # the installed choices are listed

    def test_an_unknown_or_misplaced_module_is_refused_with_the_choices(self):
        for bad in ("ingress-nothing", "authgw-authentik"):
            site = {**SITE, "login_frontend": {"ingress": bad, "auth_gateway": "authgw-authentik"}}
            with self.subTest(ingress=bad), self.assertRaises(SpecError) as caught:
                modules.chosen(site)
            self.assertIn("ingress-traefik", str(caught.exception))

    def test_chosen_returns_the_two_modules(self):
        self.assertEqual(modules.chosen(SITE), {"ingress": "ingress-traefik", "auth_gateway": "authgw-authentik"})

    def test_installed_modules_are_listed_by_capability(self):
        self.assertEqual(modules.installed("ingress"), ["ingress-traefik"])
        self.assertEqual(modules.installed("auth_gateway"), ["authgw-authentik"])

    def test_the_code_of_a_module_loads_by_name(self):
        for name in MODULES:
            self.assertTrue(hasattr(modules.code(name), "__name__"))

    def test_the_list_command_shows_what_a_module_provides_needs_and_pairs_with(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = modules.main(["list"])
        self.assertEqual((code, err.getvalue()), (0, ""))
        text = out.getvalue()
        for needle in ("ingress-traefik", "authgw-authentik", "provides:", "needs:", "pairs with:", "tested"):
            self.assertIn(needle, text)
        out = io.StringIO()
        with redirect_stdout(out):
            modules.main(["list", "--capability", "ingress"])
        listed = [line for line in out.getvalue().splitlines() if line and not line.startswith(" ")]
        self.assertEqual([line.split()[0] for line in listed], ["ingress-traefik"])

    def test_the_list_command_runs_as_the_agent_runs_it(self):
        done = subprocess.run([sys.executable, "tools/modules.py", "list"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("ingress-traefik", done.stdout)


class CraftedModuleTests(unittest.TestCase):
    """A module folder is data an agent may edit; the loader must refuse a bad one with a clear message
    instead of importing whatever it names or failing with a traceback."""

    def setUp(self):
        import shutil
        import tempfile
        scratch = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
        self.tmp = Path(tempfile.mkdtemp(prefix="modules-", dir=scratch))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        for name in MODULES:
            shutil.copytree(SKILLS / name, self.tmp / name)
        self.original = modules.SKILLS
        modules.SKILLS = self.tmp
        self.addCleanup(setattr, modules, "SKILLS", self.original)

    def edit(self, name, **changes):
        path = self.tmp / name / "module.yaml"
        data = yaml.safe_load(path.read_text())
        data.update(changes)
        path.write_text(yaml.safe_dump(data))

    def test_a_code_value_that_is_not_one_of_the_toolkits_packages_is_refused(self):
        for bad in ("os", "login_frontend", ".x", "", "a..b", 5, "ingress.", "ingress.Traefik", "authgw.authentik",
                    "ingress.nothing_here", "ingress.traefik.extra"):
            with self.subTest(code=bad):
                self.edit("ingress-traefik", code=bad)
                with self.assertRaises(SpecError) as caught:
                    modules.code("ingress-traefik")
                self.assertIn("ingress-traefik", str(caught.exception))

    def test_a_module_whose_code_or_spec_fails_to_load_is_a_clear_error(self):
        (self.tmp / "ingress-traefik" / "spec.yaml").write_text("not: a service\n")
        with self.assertRaises(SpecError) as caught:
            modules.service_name("ingress-traefik")
        self.assertIn("ingress-traefik", str(caught.exception))
        (self.tmp / "ingress-traefik" / "spec.yaml").unlink()
        with self.assertRaises(SpecError):
            modules.service_name("ingress-traefik")
        self.assertEqual(modules.frontend_services(SITE), {})  # the workspace tools skip, they don't crash
        original = modules.importlib.import_module
        modules.importlib.import_module = lambda name: (_ for _ in ()).throw(SyntaxError("bad code"))
        self.addCleanup(setattr, modules.importlib, "import_module", original)
        with self.assertRaises(SpecError) as caught:
            modules.code("authgw-authentik")
        self.assertIn("authgw-authentik", str(caught.exception))

    def test_a_folder_whose_prefix_and_declared_capability_disagree_is_reported(self):
        self.edit("ingress-traefik", capability="auth_gateway", code="authgw.traefik")
        self.assertEqual(modules.installed("ingress"), [])
        self.assertEqual([name for name, _ in modules.broken()], ["ingress-traefik"])
        self.assertIn("auth_gateway", dict(modules.broken())["ingress-traefik"])

    def test_a_spec_path_may_not_leave_the_module_folder(self):
        for bad in ("../x.yaml", "/etc/passwd", "a/../../b.yaml", 5):
            with self.subTest(spec=bad):
                self.edit("ingress-traefik", spec=bad)
                with self.assertRaises(SpecError):
                    modules.spec_path("ingress-traefik")

    def test_module_data_is_type_checked_and_the_message_names_the_module(self):
        cases = {"pairs_with": ["authgw-authentik"], "provides": "tls", "needs": [1],
                 "pairs_with ": [{"module": "authgw-authentik", "how": "x"}]}
        for key, bad in cases.items():
            with self.subTest(key=key):
                self.edit("ingress-traefik", **{key.strip(): bad})
                with self.assertRaises(SpecError) as caught:
                    modules.read("ingress-traefik")
                self.assertIn("ingress-traefik", str(caught.exception))

    def test_one_broken_module_does_not_hide_the_others(self):
        self.edit("authgw-authentik", pairs_with="oops")
        self.assertEqual(modules.installed("ingress"), ["ingress-traefik"])
        self.assertEqual(modules.installed("auth_gateway"), [])
        self.assertEqual([name for name, _ in modules.broken()], ["authgw-authentik"])
        with self.assertRaises(SpecError) as caught:
            modules.chosen(SITE)
        self.assertIn("authgw-authentik", str(caught.exception))  # the broken module is named, not hidden
        out = io.StringIO()
        with redirect_stdout(out):
            modules.main(["list"])
        self.assertIn("ingress-traefik", out.getvalue())
        self.assertIn("broken: authgw-authentik", out.getvalue())

    def test_the_code_must_have_the_functions_the_contract_names_with_the_same_parameters(self):
        self.assertEqual(set(modules.CONTRACT), {"ingress", "auth_gateway"})
        for name, capability in MODULES.items():
            code = modules.code(name)
            import inspect
            for function, params in modules.CONTRACT[capability].items():
                with self.subTest(module=name, function=function):
                    self.assertEqual(tuple(inspect.signature(getattr(code, function)).parameters), params)

    def test_a_pairing_that_is_not_marked_tested_is_noted_but_still_works(self):
        self.assertIsNone(modules.pairing_note(modules.chosen(SITE)))
        self.edit("ingress-traefik", pairs_with=[{"module": "authgw-authentik", "tested": False, "how": "x"}])
        note = modules.pairing_note(modules.chosen(SITE))
        self.assertIn("not marked tested", note)
        self.assertIn("ingress-traefik", note)
        self.assertIn("authgw-authentik", note)
        self.edit("ingress-traefik", pairs_with=[])
        self.assertIn("not marked tested", modules.pairing_note(modules.chosen(SITE)))


class UntestedPairingTests(CraftedModuleTests):
    def test_the_generator_prints_the_note_and_still_writes_its_files(self):
        import login_frontend
        self.edit("ingress-traefik", pairs_with=[])
        site = self.tmp / "site.yaml"
        site.write_text(yaml.safe_dump(SITE))
        err = io.StringIO()
        with redirect_stderr(err):
            code = login_frontend.main(["login_frontend.py", str(site), str(self.tmp / "out")])
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("not marked tested", err.getvalue())
        self.assertTrue((self.tmp / "out" / "rendered" / "login-frontend.bu").is_file())


class WorkspaceToolsFollowTheChosenModulesTests(CraftedModuleTests):
    """The workspace tools read the login front end's section under the name the chosen module's
    spec gives its service, so another product with another name is checked the same way."""

    def rename_gateway_service(self, new):
        import copy
        path = self.tmp / "authgw-authentik" / "spec.yaml"
        data = yaml.safe_load(path.read_text())
        data["name"] = new
        path.write_text(yaml.safe_dump(data))
        site = copy.deepcopy(SITE)
        site["edge"][new] = site["edge"].pop("authentik")
        return site

    def test_frontend_services_names_the_edge_sections_of_the_chosen_modules(self):
        self.assertEqual(modules.frontend_services(SITE), {"ingress": "traefik", "auth_gateway": "authentik"})
        self.assertEqual(modules.frontend_services({}), {})
        self.assertEqual(modules.frontend_services({"login_frontend": {"ingress": "nope", "auth_gateway": "x"}}), {})

    def test_the_login_page_name_and_web_ports_are_claimed_whatever_the_products_are_called(self):
        from check_workspace import workspace_problems
        site = self.rename_gateway_service("sso")
        clash = yaml.safe_load((ROOT / "tests" / "fixtures" / "services" / "crm.yaml").read_text())
        clash["hostname"] = site["edge"]["sso"]["host"].split(".")[0]
        problems = workspace_problems(site, [clash])
        self.assertTrue(any(": hostname " in p and "login page" in p for p in problems), problems)
        port = dict(clash, hostname="other", vm=site["edge"]["vm"], port=443)
        self.assertTrue(any(": port " in p for p in workspace_problems(site, [port])))

    def test_the_install_notes_take_the_login_page_and_ids_from_the_same_section(self):
        import install_notes
        site = self.rename_gateway_service("sso")
        ws = self.tmp / "ws"
        ws.mkdir()
        (ws / "site.yaml").write_text(yaml.safe_dump(site))
        text = install_notes.render(ws, [])
        self.assertIn(f"https://{site['edge']['sso']['host']}/", text)
        self.assertIn(str(site["edge"]["sso"]["uid"]), text)


class ScriptErrorTests(unittest.TestCase):
    """Run as scripts (as the agent does), the generators print a module error as one line."""

    def test_gen_service_without_a_chosen_module_exits_with_one_line_not_a_traceback(self):
        import tempfile
        scratch = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
        with tempfile.TemporaryDirectory(dir=scratch) as tmp:
            site = Path(tmp) / "site.yaml"
            site.write_text("domain: example.org\\n")
            result = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "gen_service.py"),
                                     str(ROOT / "tests" / "fixtures" / "services" / "crm.yaml"), str(site),
                                     str(Path(tmp) / "out")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("login_frontend.ingress", result.stderr)

    def test_there_is_one_spec_error_class_whoever_imports_it(self):
        import errors
        import gen_service
        self.assertIs(gen_service.SpecError, errors.SpecError)
        self.assertIs(modules._error("x").__class__, errors.SpecError)


class ServicesCommandTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "tools" / "modules.py"), *args],
                              capture_output=True, text=True)

    def test_services_prints_the_service_names_of_the_chosen_modules(self):
        result = self.run_cli("services", str(ROOT / "tests" / "fixtures" / "site.yaml"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(result.stdout.split()), ["authentik", "traefik"])

    def test_services_fails_with_the_choices_when_the_site_names_none(self):
        import tempfile
        site = Path(tempfile.mkdtemp(prefix="site-", dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None)) / "site.yaml"
        self.addCleanup(lambda: (site.unlink(), site.parent.rmdir()))
        site.write_text("domain: example.org\n")
        result = self.run_cli("services", str(site))
        self.assertEqual(result.returncode, 1)
        self.assertIn("modules.py list", result.stderr)

    def test_validate_script_skips_fixtures_by_the_chosen_modules_not_by_a_product_name(self):
        text = (ROOT / "tools" / "validate.sh").read_text()
        self.assertNotRegex(text.lower(), r"authentik|traefik")
        self.assertRegex(text, r'modules\.py"? services')


class SharedFilesNameNoProductTests(unittest.TestCase):
    """The files a user copies from, and the shared templates, don't name the login front end's products;
    each module shows its own site values in its operations.md."""

    def test_site_example_and_shared_templates_name_no_module_product(self):
        paths = [ROOT / "site.example.yaml", *sorted((ROOT / "templates").rglob("*.tmpl"))]
        for path in paths:
            text = path.read_text().lower()
            for product in PRODUCTS:
                with self.subTest(file=str(path.relative_to(ROOT)), product=product):
                    self.assertNotIn(product, text)

    def test_site_example_names_no_router_or_file_server_product(self):
        text = (ROOT / "site.example.yaml").read_text().lower()
        for product in ("opnsense", "truenas", "duckdns"):
            with self.subTest(product=product):
                self.assertNotIn(product, text)

    def test_site_example_templates_and_prompt_name_no_hypervisor_product(self):
        agent = Path(__file__).resolve().parents[2] / "subagents" / "fcos-app-installer.md"
        paths = [ROOT / "site.example.yaml", *sorted((ROOT / "templates").rglob("*.tmpl"))]
        if agent.is_file():  # in the repository; the installed copy is checked by the agent tests
            paths.append(agent)
        for path in paths:
            with self.subTest(file=path.name):
                self.assertNotIn("proxmox", path.read_text().lower())

    def test_the_proxmox_adapter_ships_the_hosts_example(self):
        data = yaml.safe_load((SKILLS / "hypervisor-proxmox" / "site.example.yaml").read_text())
        self.assertEqual(list(data), ["hosts"])
        for host in data["hosts"].values():
            for key in ("name", "node", "address", "storage", "bridge", "always_on", "max_cores", "max_ram_mib"):
                self.assertIn(key, host)
        shared = yaml.safe_load((ROOT / "site.example.yaml").read_text())["hosts"]
        for host in shared.values():
            self.assertEqual(set(host), {"name", "always_on"})

    def test_each_module_shows_an_example_of_its_site_section(self):
        for name, key in (("ingress-traefik", "traefik"), ("authgw-authentik", "authentik")):
            with self.subTest(module=name):
                data = yaml.safe_load((SKILLS / name / "site.example.yaml").read_text())
                self.assertEqual(list(data)[0], "edge")
                self.assertEqual(list(data["edge"]), [modules.service_name(name)])
                self.assertEqual(modules.service_name(name), key)
                self.assertIn("`site.example.yaml` in this folder", (SKILLS / name / "operations.md").read_text())


class OperationsFileTests(unittest.TestCase):
    """The guide pages stay product-free by handing over to each module's operations.md."""
    SECTIONS = {
        "ingress-traefik": ("Site values", "Ports and the VM", "The certificate and the DNS provider", "Secrets on the login VM",
                            "Start and check", "Applying route changes", "Stop it",
                            "Break-glass: an app's route without the login"),
        "authgw-authentik": ("Site values", "The containers", "Secrets on the login VM", "Start and check",
                             "First login", "Admin recovery", "End-to-end check", "Who may open an app",
                             "The dashboard section and the logo", "Applying the login rules", "Removing an app",
                             "People and access", "Upgrading", "Stop it", "Restoring the database"),
    }

    def test_each_module_has_the_sections_the_guide_cites(self):
        for name, sections in self.SECTIONS.items():
            text = (SKILLS / name / "operations.md").read_text()
            headings = re.findall(r"^#{2,3} (.+)$", text, re.M)
            for section in sections:
                with self.subTest(module=name, section=section):
                    self.assertIn(section, headings)

    def test_each_module_names_its_operations_file_and_guide_12_lists_the_sections(self):
        guide = " ".join((ROOT / "docs" / "guide" / "12-add-a-module.md").read_text().split())
        for name, sections in self.SECTIONS.items():
            with self.subTest(module=name):
                self.assertIn("`operations.md`", (SKILLS / name / "SKILL.md").read_text())
                for section in sections:
                    self.assertIn(f'"{section}"', guide)

    def test_the_wording_test_covers_both_products(self):
        source = (Path(__file__).parent / "test_wording.py").read_text()
        words = source.split("PROVIDER_WORDS = [", 1)[1].split("]", 1)[0].lower()
        self.assertIn("traefik", words)
        self.assertIn("authentik", words)


class ContractDocTests(unittest.TestCase):
    def test_guide_12_lists_exactly_the_functions_and_parameters_the_loader_checks(self):
        guide = " ".join((ROOT / "docs" / "guide" / "12-add-a-module.md").read_text().split())
        for capability, functions in modules.CONTRACT.items():
            for function, params in functions.items():
                with self.subTest(capability=capability, function=function):
                    self.assertIn(f"`{function}({', '.join(params)})`", guide)


class GenericCodeTests(unittest.TestCase):
    def test_the_generic_tools_name_no_product(self):
        for name in GENERIC:
            text = (ROOT / "tools" / name).read_text().lower()
            for product in PRODUCTS:
                with self.subTest(file=name, product=product):
                    self.assertNotIn(product, text)


class SiteKeyOwnershipTests(unittest.TestCase):
    """Which site keys a product needs is the product module's business, checked by its check_site."""

    def test_the_generic_orchestrator_names_no_product_specific_site_key(self):
        text = (ROOT / "tools" / "login_frontend.py").read_text()
        self.assertNotIn("acme_email", text)

    def test_the_ingress_module_checks_its_own_site_keys(self):
        code = modules.code("ingress-traefik")
        code.check_site(SITE)  # the fixture site is fine
        for bad in ({}, {"acme_email": ""}, {"acme_email": "not an email"}, {"acme_email": ["a@example.org"]}):
            with self.subTest(site=bad), self.assertRaises(SpecError) as caught:
                code.check_site(dict(SITE, **bad) if bad else {k: v for k, v in SITE.items() if k != "acme_email"})
            self.assertIn("acme_email", str(caught.exception))

    def test_a_site_without_an_email_stops_the_login_front_end_with_the_modules_message(self):
        import copy
        import login_frontend
        site = copy.deepcopy(SITE)
        del site["acme_email"]
        with self.assertRaises(SpecError) as caught:
            login_frontend.generate_login_frontend(site, [], "/tmp/opencode/x" if Path("/tmp/opencode").is_dir() else "/tmp/x")
        self.assertIn("acme_email", str(caught.exception))


class LoginValueTests(unittest.TestCase):
    def spec(self, **extra):
        data = yaml.safe_load((ROOT / "tests" / "fixtures" / "services" / "single.yaml").read_text())
        data.update(extra)
        return data

    def test_the_value_is_gateway(self):
        self.assertEqual(validate_spec(self.spec(login="gateway"), SITE), [])

    def test_the_old_product_value_is_refused_and_the_message_names_the_new_one(self):
        problems = validate_spec(self.spec(login="authentik"), SITE)
        self.assertTrue(any("gateway" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
