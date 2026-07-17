"""Deterministic tests for Copier template source and generated-output validation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.engineering.admission_gate import validate_generated_project, validate_template_source

REPO_ROOT = Path(__file__).resolve().parents[2]
GOVERNED_TEMPLATES = ("mcp-server-python", "agent-langgraph-postgres-checkpointer")


class CopierTemplateSourceTests(unittest.TestCase):
    """Protect parser-sensitive template sources from unresolved Jinja."""

    def _template(self, suffix: str = ".jinja") -> Path:
        root = Path(tempfile.mkdtemp())
        (root / "copier.yml").write_text(
            f'_subdirectory: "template"\n_templates_suffix: "{suffix}"\n',
            encoding="utf-8",
        )
        (root / "template").mkdir()
        return root

    def test_rejects_parser_sensitive_jinja_without_suffix(self) -> None:
        root = self._template()
        (root / "template" / "pyproject.toml").write_text(
            'name = "{{ project_slug }}"\n',
            encoding="utf-8",
        )

        findings = validate_template_source(root)

        self.assertTrue(any("pyproject.toml" in finding for finding in findings))

    def test_rejects_any_jinja_bearing_source_without_suffix(self) -> None:
        root = self._template()
        (root / "template" / "README.md").write_text("# {{ project_name }}\n", encoding="utf-8")

        findings = validate_template_source(root)

        self.assertTrue(any("README.md" in finding for finding in findings))

    def test_rejects_suffix_inside_conditional_filename(self) -> None:
        root = self._template()
        path = root / "template" / "settings.jinja{% if enabled %}.yaml{% endif %}"
        path.write_text("enabled: {{ enabled }}\n", encoding="utf-8")

        findings = validate_template_source(root)

        self.assertTrue(any("declared suffix must be the final filename suffix" in item for item in findings))

    def test_accepts_jinja_bearing_sources_with_final_suffix(self) -> None:
        root = self._template()
        (root / "template" / "pyproject.toml.jinja").write_text(
            'name = "{{ project_slug }}"\n',
            encoding="utf-8",
        )
        conditional = root / "template" / "settings{% if enabled %}.yaml{% endif %}.jinja"
        conditional.write_text("enabled: {{ enabled }}\n", encoding="utf-8")
        (root / "template" / "LICENSE").write_text("Static text\n", encoding="utf-8")

        self.assertEqual(validate_template_source(root), [])

    def test_generated_project_requires_valid_toml_and_no_jinja(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "pyproject.toml").write_text(
            '[project]\nname = "{{ unresolved }}"\n',
            encoding="utf-8",
        )

        findings = validate_generated_project(root)

        self.assertTrue(any("unresolved Jinja" in finding for finding in findings))

    def test_generated_project_accepts_valid_rendered_toml(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "pyproject.toml").write_text(
            '[project]\nname = "rendered-project"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )

        self.assertEqual(validate_generated_project(root), [])

    def test_governed_templates_use_explicit_jinja_suffix(self) -> None:
        for name in GOVERNED_TEMPLATES:
            root = REPO_ROOT / "templates" / name
            config = (root / "copier.yml").read_text(encoding="utf-8")
            self.assertIn('_templates_suffix: ".jinja"', config, name)
            self.assertEqual(validate_template_source(root), [], name)

    def test_governance_requires_explicit_template_suffix(self) -> None:
        required = "must use an explicit template suffix"
        for relative in ("AGENTS.md", "docs/engineering/CONSTITUTION.md"):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(required, text, relative)
            self.assertNotIn('must set `_templates_suffix: ""`', text, relative)

    def test_governed_templates_use_importable_setuptools_backend(self) -> None:
        expected = 'build-backend = "setuptools.build_meta:__legacy__"'
        for name in GOVERNED_TEMPLATES:
            source = REPO_ROOT / "templates" / name / "template" / "pyproject.toml.jinja"
            self.assertIn(expected, source.read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
