"""Exercise the packaged documents validator without native rendering."""

import json
import subprocess
import sys
import unittest

from test_security_re_context import ROOT, read_jsonc


class DocumentsSkillTests(unittest.TestCase):
    def test_bundled_formats_validate_through_the_packaged_cli(self):
        skill = ROOT / "skills/documents/skills/documents"
        cli = skill / "scripts/validate-documents.py"
        self.assertTrue(cli.is_file())
        formats = ["pdf", "docx", "xlsx", "pptx"]
        fixtures = [skill / "fixtures" / f"sample.{ext}" for ext in formats]
        for path in fixtures:
            self.assertTrue(path.is_file(), path)
        result = subprocess.run(
            [sys.executable, str(cli), "--json", *map(str, fixtures)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "ok")
        self.assertEqual([item["format"] for item in report["files"]], formats)
        self.assertTrue(all(item["status"] == "pass" for item in report["files"]))

    def test_document_groups_discover_one_complete_family_skill(self):
        for group in ["default", "work", "writing_reporting"]:
            config = read_jsonc(ROOT / f"groups/{group}.jsonc")
            self.assertIn("skills/documents", config["inputRoots"])
        skill = ROOT / "skills/documents/skills/documents"
        for name in ["pdf", "word", "excel", "powerpoint"]:
            self.assertTrue((skill / "references" / f"{name}.md").is_file())
            self.assertTrue((skill / "templates" / f"{name}-template.md").is_file())
        self.assertTrue((skill / "references/output-quality.md").is_file())
        self.assertTrue((skill / "evals/evals.json").is_file())
        self.assertTrue((skill / "tests/test_validate_documents.py").is_file())


if __name__ == "__main__":
    unittest.main()
