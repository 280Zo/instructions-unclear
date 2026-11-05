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
GENERIC = ("login_frontend.py", "gen_service.py", "modules.py")


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


class GenericCodeTests(unittest.TestCase):
    def test_the_generic_tools_name_no_product(self):
        for name in GENERIC:
            text = (ROOT / "tools" / name).read_text().lower()
            for product in PRODUCTS:
                with self.subTest(file=name, product=product):
                    self.assertNotIn(product, text)


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
