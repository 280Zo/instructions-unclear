"""tools/hypervisor.py: the one entry point for the virtualization adapter's tool.

The adapter names its tool in adapter.yaml (`code: virtualization.<product>`); the generic entry point
reads the product from the site file, loads that code and hands the arguments over. It names no product.
"""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import adapters  # noqa: E402
import hypervisor  # noqa: E402
from adapters import AdapterError, load_adapter, load_tool  # noqa: E402
from layout import SKILLS  # noqa: E402

PROVIDER = "proxmox"  # the one shipped adapter that has a tool


class EntryPointTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.ws = Path(self._tmp.name).resolve() / "ws"
        self.ws.mkdir()

    def site(self, provider="proxmox", **extra):
        data = {"roles": {"virtualization": {"provider": provider}}, **extra}
        (self.ws / "site.yaml").write_text(yaml.safe_dump(data))

    def run_tool(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = hypervisor.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_the_arguments_reach_the_adapters_tool_unchanged_and_its_exit_code_comes_back(self):
        self.site()
        from virtualization import proxmox
        with mock.patch.object(proxmox, "main", return_value=7) as tool:
            code, _out, err = self.run_tool("check", "--host", "host-a", "--workspace", str(self.ws))
        self.assertEqual(code, 7, err)
        tool.assert_called_once_with(["check", "--host", "host-a", "--workspace", str(self.ws)])

    def test_a_workspace_from_the_environment_works_too(self):
        self.site()
        from virtualization import proxmox
        with mock.patch.dict("os.environ", {"FCOS_WORKSPACE": str(self.ws)}), \
                mock.patch.object(proxmox, "main", return_value=0) as tool:
            code, _out, err = self.run_tool("list")
        self.assertEqual(code, 0, err)
        tool.assert_called_once_with(["list"])

    def test_no_arguments_print_the_usage_and_the_verbs(self):
        code, _out, err = self.run_tool()
        self.assertEqual(code, 2)
        for verb in ("check", "list", "create", "start", "status"):
            self.assertIn(verb, err)

    def test_a_verb_the_contract_does_not_have_is_refused_before_anything_is_loaded(self):
        self.site()
        for verb in ("delete", "destroy", "rebuild", "--help-me", ""):
            with self.subTest(verb=verb):
                code, _out, err = self.run_tool(verb, "--workspace", str(self.ws))
                self.assertEqual(code, 2)
                self.assertIn("check", err)

    def test_a_site_without_a_virtualization_provider_says_what_to_do(self):
        for data in ({}, {"roles": {}}, {"roles": {"virtualization": {"provider": "ASK"}}},
                     {"roles": {"virtualization": {}}}, {"roles": []}):
            with self.subTest(site=data):
                (self.ws / "site.yaml").write_text(yaml.safe_dump(data))
                code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
                self.assertEqual(code, 1)
                self.assertIn("roles.virtualization.provider", err)
                self.assertIn("adapters.py", err)

    def test_an_adapter_without_a_tool_is_a_clear_error(self):
        self.site(provider="generic")
        code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
        self.assertEqual(code, 1)
        self.assertIn("no tool", err)

    def test_a_provider_that_is_not_a_plain_word_is_refused(self):
        for provider in ("../x", "a b", 5, ["proxmox"]):
            with self.subTest(provider=provider):
                self.site(provider=provider)
                code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
                self.assertEqual(code, 1)
                self.assertNotIn("Traceback", err)

    def test_an_unreadable_site_file_is_an_error_not_a_traceback(self):
        (self.ws / "site.yaml").write_text("roles: [unclosed\n")
        code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
        self.assertEqual(code, 1)
        self.assertNotIn("Traceback", err)

    def test_a_missing_site_file_or_one_that_is_a_folder_is_an_error_not_a_traceback(self):
        code, _out, err = self.run_tool("check", "--workspace", str(self.ws))  # no site.yaml yet
        self.assertEqual(code, 1)
        self.assertIn("can't read", err)
        self.assertNotIn("Traceback", err)
        (self.ws / "site.yaml").mkdir()
        code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
        self.assertEqual(code, 1)
        self.assertIn("can't read", err)

    def test_help_prints_the_usage_and_succeeds(self):
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                code, out, _err = self.run_tool(flag)
                self.assertEqual(code, 0)
                self.assertIn("hypervisor.py check", out)

    def test_the_hint_for_an_unset_provider_names_the_provider_option(self):
        self.site(provider="ASK")
        _code, _out, err = self.run_tool("check", "--workspace", str(self.ws))
        self.assertIn("--provider <name>", err)

    def test_run_as_a_script_it_prints_the_usage_without_a_traceback(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / "hypervisor.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("Traceback", result.stderr)


class AdapterToolTests(unittest.TestCase):
    def test_the_proxmox_adapter_names_its_tool_and_it_has_the_contract(self):
        adapter = load_adapter("virtualization", PROVIDER)
        self.assertEqual(adapter["code"], "virtualization.proxmox")
        tool = load_tool(adapter)
        self.assertEqual(tool.VERBS, adapters.TOOL_VERBS["virtualization"])
        self.assertTrue(callable(tool.main))

    def test_an_adapter_without_code_has_no_tool(self):
        with self.assertRaises(AdapterError) as caught:
            load_tool(load_adapter("virtualization", "generic"))
        self.assertIn("no tool", str(caught.exception))

    def check(self, **changes):
        data = yaml.safe_load((SKILLS / "hypervisor-proxmox" / "adapter.yaml").read_text())
        data.update(changes)
        return adapters._check_adapter(data, "virtualization", "proxmox")

    def test_the_code_name_is_checked(self):
        self.check(code="virtualization.proxmox")
        for bad in ("os", "virtualization.", "virtualization.a.b", "../x", "ingress.traefik", "virtualization.other",
                    "Virtualization.proxmox", 5, ["virtualization.proxmox"], ""):
            with self.subTest(code=bad), self.assertRaises(AdapterError):
                self.check(code=bad)

    def test_only_a_role_with_a_tool_contract_may_name_code(self):
        data = yaml.safe_load((SKILLS / "dns-duckdns" / "adapter.yaml").read_text())
        data["code"] = "virtualization.duckdns"
        with self.assertRaises(AdapterError):
            adapters._check_adapter(data, "dns_certificates", "duckdns")

    def test_a_tool_missing_a_verb_or_main_is_refused(self):
        adapter = load_adapter("virtualization", PROVIDER)
        broken = mock.Mock(spec=["main"])
        broken.main = lambda argv: 0
        with mock.patch.object(adapters.importlib, "import_module", return_value=broken):
            with self.assertRaises(AdapterError) as caught:
                load_tool(adapter)
        self.assertIn("VERBS", str(caught.exception))
        no_main = mock.Mock(spec=["VERBS"])
        no_main.VERBS = adapters.TOOL_VERBS["virtualization"]
        with mock.patch.object(adapters.importlib, "import_module", return_value=no_main):
            with self.assertRaises(AdapterError):
                load_tool(adapter)

    def test_a_tool_that_fails_to_load_is_a_clear_error(self):
        adapter = load_adapter("virtualization", PROVIDER)
        with mock.patch.object(adapters.importlib, "import_module", side_effect=SyntaxError("bad")):
            with self.assertRaises(AdapterError) as caught:
                load_tool(adapter)
        self.assertIn("proxmox", str(caught.exception))


class ContractDocTests(unittest.TestCase):
    def test_guide_12_states_the_code_key_and_every_verb(self):
        guide = " ".join((ROOT / "docs" / "guide" / "12-add-a-module.md").read_text().split())
        self.assertIn("## 12.4 An adapter with a tool", guide)
        self.assertIn("`code: virtualization.<provider>`", guide)
        self.assertIn("VERBS = (" + ", ".join(f'"{v}"' for v in adapters.TOOL_VERBS["virtualization"]) + ")", guide)
        self.assertIn("python3 tools/hypervisor.py", guide)

    def test_no_guide_page_or_prompt_names_the_old_tool(self):
        agent = ROOT.parent / "subagents" / "fcos-app-installer.md"
        paths = list((ROOT / "docs" / "guide").glob("*.md")) + [ROOT / "README.md"] + ([agent] if agent.is_file() else [])
        for path in paths:
            with self.subTest(file=path.name):
                self.assertNotIn("pve.py", path.read_text())


class GenericCodeTests(unittest.TestCase):
    def test_the_entry_point_names_no_hypervisor_product(self):
        text = (ROOT / "tools" / "hypervisor.py").read_text().lower()
        for word in ("proxmox", "pve", "pveum", "qm "):
            self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
