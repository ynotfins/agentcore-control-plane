#!/usr/bin/env python3
"""Unit tests for shared Bifrost session identity (default-deny)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bifrost.session_identity import (
    ERROR_IDENTITY_MISMATCH,
    ERROR_NOT_ENROLLED,
    ERROR_SWARM_REFUSED,
    EnrollmentRegistry,
    RESERVED_IDENTITY_ARG_NAMES,
    extract_project_arg,
    resolve_request_identity,
    sanitize_tool_args_for_upstream,
)


class EnrollmentRegistryDefaultDenyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = EnrollmentRegistry()

    def test_enrolled_key_resolves(self) -> None:
        result = self.registry.resolve(project_key="agentcore-control-plane")
        self.assertTrue(result.ok)
        self.assertEqual(result.project_key, "agentcore-control-plane")
        self.assertIsNone(result.error)

    def test_unknown_key_denied(self) -> None:
        result = self.registry.resolve(project_key="random-unenrolled-repo")
        self.assertFalse(result.ok)
        self.assertIsNone(result.project_key)
        self.assertIsNone(result.primary_path)
        self.assertEqual(result.error, ERROR_NOT_ENROLLED)

    def test_empty_identity_denied(self) -> None:
        result = self.registry.resolve()
        self.assertFalse(result.ok)
        self.assertEqual(result.error, ERROR_NOT_ENROLLED)
        self.assertNotEqual(result.project_key, "agentcore-control-plane")

    def test_unenrolled_path_denied(self) -> None:
        result = self.registry.resolve(
            candidate_path=r"C:\unregistered\repo\file.txt"
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, ERROR_NOT_ENROLLED)
        self.assertIsNone(result.project_key)

    def test_enrolled_path_resolves(self) -> None:
        result = self.registry.resolve(
            candidate_path=r"D:\github\agentcore-control-plane\scripts\test.py"
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.project_key, "agentcore-control-plane")

    def test_swarm_path_refused(self) -> None:
        result = self.registry.resolve(
            candidate_path=r"D:\github\swarm-ecosystem-control\README.md"
        )
        self.assertEqual(result.error, ERROR_SWARM_REFUSED)

    def test_request_without_headers_denied(self) -> None:
        result = resolve_request_identity(self.registry, headers={}, args={})
        self.assertFalse(result.ok)
        self.assertEqual(result.error, ERROR_NOT_ENROLLED)

    def test_agentcore_project_arg_resolves_without_headers(self) -> None:
        result = resolve_request_identity(
            self.registry,
            headers={},
            args={"agentcore_project": "agentcore-control-plane"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.project_key, "agentcore-control-plane")
        self.assertIsNone(result.error)

    def test_project_key_alias_arg_resolves_without_headers(self) -> None:
        result = resolve_request_identity(
            self.registry,
            headers={},
            args={"project_key": "agentcore-control-plane"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.project_key, "agentcore-control-plane")

    def test_extract_project_arg_prefers_agentcore_project(self) -> None:
        self.assertEqual(
            extract_project_arg(
                {
                    "agentcore_project": "agentcore-control-plane",
                    "project_key": "other",
                }
            ),
            "agentcore-control-plane",
        )
        self.assertEqual(
            set(RESERVED_IDENTITY_ARG_NAMES),
            {"agentcore_project", "project_key"},
        )

    def test_header_beats_matching_tool_arg(self) -> None:
        result = resolve_request_identity(
            self.registry,
            headers={"x-agentcore-project": "agentcore-control-plane"},
            args={"agentcore_project": "agentcore-control-plane"},
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.project_key, "agentcore-control-plane")

    def test_header_arg_mismatch_denied(self) -> None:
        result = resolve_request_identity(
            self.registry,
            headers={"x-agentcore-project": "agentcore-context-engine"},
            args={"agentcore_project": "agentcore-control-plane"},
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.error, ERROR_IDENTITY_MISMATCH)

    def test_sanitize_strips_reserved_and_rewrites_absolute(self) -> None:
        primary = Path(r"D:\github\agentcore-control-plane").resolve()
        abs_file = str(primary / "scripts" / "bifrost" / "session_identity.py")
        sanitized = sanitize_tool_args_for_upstream(
            {
                "agentcore_project": "agentcore-control-plane",
                "project_key": "agentcore-control-plane",
                "name_path_pattern": "EnrollmentRegistry",
                "relative_path": abs_file,
            },
            primary,
        )
        self.assertNotIn("agentcore_project", sanitized)
        self.assertNotIn("project_key", sanitized)
        self.assertEqual(sanitized["name_path_pattern"], "EnrollmentRegistry")
        self.assertEqual(
            sanitized["relative_path"],
            "scripts/bifrost/session_identity.py",
        )
        self.assertFalse(Path(sanitized["relative_path"]).is_absolute())


if __name__ == "__main__":
    unittest.main()
