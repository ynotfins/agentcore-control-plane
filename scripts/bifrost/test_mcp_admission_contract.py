#!/usr/bin/env python3
"""Focused tests for the source-only MCP admission contract."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from validate_mcp_admission_contract import (
    CANDIDATE_SERVER_IDS,
    FORBIDDEN_NFA_MARKERS,
    REJECTED_SERVER_IDS,
    validate_admission_contract,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
SCHEMA_PATH = (
    REPO_ROOT / "contracts" / "schemas" / "bifrost-upstream-mcp-registry.schema.json"
)
OUTPUT_SCHEMA_CONTRACT_PATH = REPO_ROOT / "contracts" / "mcp-tool-output-schemas.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class McpAdmissionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_json(REGISTRY_PATH)
        cls.schema = load_json(SCHEMA_PATH)

    def test_current_registry_passes_schema_and_admission_checks(self) -> None:
        schema_errors = list(Draft202012Validator(self.schema).iter_errors(self.registry))
        self.assertEqual([], schema_errors)
        self.assertEqual([], validate_admission_contract(self.registry))

    def test_candidates_are_disabled_zero_profile_records(self) -> None:
        profile_members = {
            server_id
            for profile in self.registry["capability_profiles"].values()
            for server_id in profile["allowed_server_ids"]
        }
        for server_id in CANDIDATE_SERVER_IDS:
            with self.subTest(server_id=server_id):
                server = self.registry["servers"][server_id]
                self.assertFalse(server["enabled"])
                self.assertEqual([], server["capability_profiles"])
                self.assertEqual([], server["permitted_tools"])
                self.assertNotIn(server_id, profile_members)
                expected = "rejected" if server_id in REJECTED_SERVER_IDS else "catalogued_unverified"
                self.assertEqual(expected, server["status"])

    def test_catalogued_or_rejected_schema_state_is_fail_closed(self) -> None:
        for field, value in (
            ("enabled", True),
            ("capability_profiles", ["builder"]),
            ("permitted_tools", ["example_tool"]),
        ):
            fixture = copy.deepcopy(self.registry)
            fixture["servers"]["shadcn"][field] = value
            errors = list(Draft202012Validator(self.schema).iter_errors(fixture))
            self.assertTrue(errors, f"schema accepted fail-open {field}={value!r}")

    def test_forbidden_nfa_markers_are_rejected_from_sensitive_candidate_fields(self) -> None:
        injectors = {
            "candidate_roots": lambda server, value: server["admission_evidence"]["storage"][
                "candidate_roots"
            ].append(value),
            "arguments": lambda server, value: server["arguments"].append(value),
            "headers": lambda server, value: server.setdefault("headers", {}).update(
                {"X-Test-Scope": value}
            ),
            "dsn_references": lambda server, value: server["admission_evidence"][
                "authentication"
            ]["dsn_references"].append(value),
            "profiles": lambda server, value: server["capability_profiles"].append(value),
            "canaries": lambda server, value: server["admission_evidence"]["canary"][
                "probes"
            ].append(value),
            "database_allowlist": lambda server, value: server["admission_evidence"][
                "database_allowlist"
            ].append(value),
        }
        for marker in FORBIDDEN_NFA_MARKERS:
            for location, inject in injectors.items():
                with self.subTest(marker=marker, location=location):
                    fixture = copy.deepcopy(self.registry)
                    inject(fixture["servers"]["shadcn"], marker)
                    errors = validate_admission_contract(fixture)
                    self.assertTrue(
                        any("forbidden NFA marker" in error for error in errors),
                        errors,
                    )

    def test_playwright_all_exact_tools_are_trust_a_executable_via_code_mode(self) -> None:
        server = self.registry["servers"]["playwright"]
        groups = server["tool_groups"]
        inspection = set(groups["playwright-inspection"]["tools"])
        interaction = set(groups["playwright-interaction"]["tools"])
        high_risk = set(groups["playwright-high-risk"]["tools"])

        self.assertTrue(server["is_code_mode_client"])
        self.assertEqual("default_profile", groups["playwright-inspection"]["access_policy"])
        self.assertEqual("default_profile", groups["playwright-interaction"]["access_policy"])
        self.assertEqual("default_profile", groups["playwright-high-risk"]["access_policy"])
        self.assertEqual(inspection | interaction | high_risk, set(server["permitted_tools"]))
        self.assertEqual([], server["denied_tools"])
        self.assertFalse((groups["playwright-high-risk"].get("lease_defaults") or {}).get("requires_approval"))
        self.assertIn("browser_file_upload", high_risk)
        self.assertIn("browser_run_code_unsafe", high_risk)
        self.assertFalse(inspection & interaction)
        self.assertFalse(inspection & high_risk)
        self.assertFalse(interaction & high_risk)

    def test_github_is_digest_pinned_and_deferred_fail_closed(self) -> None:
        server = self.registry["servers"]["github-mcp"]
        expected_digest = "sha256:5c83359327a0bacc3d34db730bea6557d39d341cee0bf6c58c9a896e33150e80"
        self.assertEqual("1.3.0", server["pinned_version"])
        self.assertIn(
            f"ghcr.io/github/github-mcp-server:1.3.0@{expected_digest}",
            server["arguments"],
        )
        self.assertEqual(expected_digest, server["admission_evidence"]["artifact"]["digest"])
        self.assertEqual("deferred", server["status"])
        self.assertFalse(server["enabled"])
        self.assertEqual([], server["permitted_tools"])
        self.assertEqual([], server["capability_profiles"])

    def test_normal_ide_database_candidates_have_no_write_surface(self) -> None:
        for server_id in ("postgresql-mcp", "sqlite-mcp"):
            with self.subTest(server_id=server_id):
                server = self.registry["servers"][server_id]
                evidence = server["admission_evidence"]
                self.assertEqual("rejected", server["status"])
                self.assertEqual([], server["permitted_tools"])
                self.assertEqual([], server["capability_profiles"])
                self.assertIn(
                    evidence["protected_resources"]["default_access"],
                    {"none", "rejected"},
                )
                self.assertEqual([], evidence["database_allowlist"])

    def test_candidates_have_unsupported_generic_output_schema_bindings(self) -> None:
        contract = load_json(OUTPUT_SCHEMA_CONTRACT_PATH)
        expected_reason_terms = (
            "disabled zero-profile",
            "no admitted tool inventory",
            "no admitted output schema",
        )
        for server_id in CANDIDATE_SERVER_IDS:
            with self.subTest(server_id=server_id):
                binding = contract["servers"].get(server_id)
                self.assertIsNotNone(binding, f"missing output-schema binding for {server_id}")
                self.assertEqual("unsupported", binding["adapter"])
                self.assertEqual("generic", binding["default_profile"])
                reason = binding["reason"].lower()
                for term in expected_reason_terms:
                    self.assertIn(term, reason)


if __name__ == "__main__":
    unittest.main(verbosity=2)
