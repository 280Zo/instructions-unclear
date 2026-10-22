"""Checks for repo-owned routing, preference and precedence rules."""

import unittest

from test_security_re_context import ROOT, read_jsonc

HOME_GROUPS = ["default", "work", "writing_reporting"]
OLD_ROUTING_RULES = [
    "skills/diagram-design/rules/diagram-design.md",
    "skills/frontend-slides/rules/frontend-slides.md",
    "skills/visual-explainer/rules/visual-explainer.md",
    "skills/anthropic-design/rules/theme-factory.md",
    "skills/humanizer/rules/humanizer.md",
]


def rule_text(name):
    return (ROOT / f"rules/{name}/rules/{name}.md").read_text()


class RuleTests(unittest.TestCase):
    def test_one_routing_rule_owns_every_job(self):
        text = rule_text("routing")
        for skill in [
            "frontend-slides",
            "documents",
            "diagram-design",
            "visual-explainer",
            "theme-factory",
            "humanizer",
            "security-threat-model",
            "security-best-practices",
            "Docling",
        ]:
            self.assertIn(skill, text)
        for path in OLD_ROUTING_RULES:
            self.assertFalse((ROOT / path).exists(), path)

    def test_preferences_rule_sets_editor_and_shell(self):
        text = rule_text("preferences").lower()
        for word in [
            "nano",
            "vim",
            "fish",
            "pnpm",
            "uv",
            "zellij",
            "firefox",
            "yyyy-mm-dd",
            "us english",
        ]:
            self.assertIn(word, text)

    def test_owned_rules_override_skill_steps(self):
        package = (
            ROOT / "skills/package-management/rules/package-management.md"
        ).read_text()
        self.assertIn("don't override this", package)
        scope = rule_text("scope-secrets-approvals")
        for action in ["commit", "push", "deploy", "scan"]:
            self.assertIn(action, scope)
        self.assertIn("is not approval", scope)

    def test_home_groups_load_new_rules_inside_the_preamble_pair(self):
        for group in HOME_GROUPS:
            roots = read_jsonc(ROOT / f"groups/{group}.jsonc")["inputRoots"]
            for rule in ["rules/routing", "rules/preferences"]:
                self.assertIn(rule, roots, group)
            self.assertEqual(roots[0], "rules/shell-preamble", group)
            self.assertEqual(roots[-1], "rules/shell-preamble-reminder", group)


if __name__ == "__main__":
    unittest.main()
