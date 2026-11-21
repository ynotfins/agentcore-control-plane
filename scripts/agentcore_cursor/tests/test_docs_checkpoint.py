from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2]
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from agentcore_cursor.docs_checkpoint import (  # noqa: E402
    format_docs_checkpoint_reminder,
    verify_project_docs_checkpoint,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class DocsCheckpointTests(unittest.TestCase):
    def test_missing_checkpoint_is_a_hard_miss(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog = root / "CATALOG.json"
            _write_json(catalog, {"entries": [{"library": "bifrost", "version": "2.0.0"}]})
            result = verify_project_docs_checkpoint(root, catalog_path=catalog)
        self.assertEqual(result["status"], "missing_checkpoint")
        self.assertIn("DOCS CHECKPOINT MISSING", result["reminder"])

    def test_version_mismatch_and_missing_library(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog = root / "CATALOG.json"
            _write_json(
                catalog,
                {"entries": [{"library": "bifrost", "version": "2.0.0"}]},
            )
            _write_json(
                root / ".agentcore" / "docs-checkpoint.json",
                {
                    "schema": "agentcore-project-docs-checkpoint/v1",
                    "libraries": [
                        {"library": "bifrost", "resolved_version": "1.9.0"},
                        {"library": "serena", "resolved_version": "1.5.4.dev0"},
                    ],
                },
            )
            result = verify_project_docs_checkpoint(root, catalog_path=catalog)
        self.assertEqual(result["status"], "drift")
        self.assertTrue(any(item.startswith("serena@") for item in result["missing"]))
        self.assertTrue(any(item.startswith("bifrost@1.9.0") for item in result["mismatched"]))
        self.assertIn("scrape_docs", result["reminder"])

    def test_matching_pin_is_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog = root / "CATALOG.json"
            _write_json(
                catalog,
                {"entries": [{"library": "bifrost", "version": "2.0.0"}]},
            )
            _write_json(
                root / ".agentcore" / "docs-checkpoint.json",
                {
                    "schema": "agentcore-project-docs-checkpoint/v1",
                    "libraries": [{"library": "bifrost", "resolved_version": "2.0.0"}],
                },
            )
            result = verify_project_docs_checkpoint(root, catalog_path=catalog)
            reminder = format_docs_checkpoint_reminder(root, catalog_path=catalog)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["verified"], ["bifrost@2.0.0"])
        self.assertIn("DOCS CHECKPOINT OK", reminder)


if __name__ == "__main__":
    unittest.main()
