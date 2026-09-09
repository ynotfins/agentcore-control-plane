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
    ERROR_NOT_ENROLLED,
    ERROR_SWARM_REFUSED,
    EnrollmentRegistry,
    resolve_request_identity,
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


if __name__ == "__main__":
    unittest.main()
