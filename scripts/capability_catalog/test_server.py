#!/usr/bin/env python3
"""Focused contract tests for the AgentCore capability catalog MCP."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import yaml

from scripts.capability_catalog import server


REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
POLICY_PATH = REPO_ROOT / "contracts" / "global-agent-policy.yaml"


class CapabilityCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.policy = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))

    def test_mcp_surface_is_exactly_two_read_only_tools(self) -> None:
        tools = server.tool_defs()
        self.assertEqual(
            ["list_capabilities", "get_capability_detail"],
            [tool["name"] for tool in tools],
        )
        self.assertTrue(all(tool["annotations"]["readOnlyHint"] for tool in tools))
        self.assertTrue(all(not tool["annotations"]["destructiveHint"] for tool in tools))

    def test_list_and_detail_project_only_safe_capability_metadata(self) -> None:
        fixture = copy.deepcopy(self.registry)
        fixture["servers"]["playwright"]["headers"] = {
            "Authorization": "Bearer should-never-appear"
        }
        fixture["servers"]["playwright"]["arguments"].append("secret-argument")
        fixture["servers"]["playwright"]["env_var_names"] = ["SECRET_NAME"]

        listed = server.list_capabilities({"query": "playwright"}, registry=fixture)
        detail = server.get_capability_detail(
            {"capability_id": "playwright"}, registry=fixture
        )
        payload = json.dumps({"listed": listed, "detail": detail}, sort_keys=True)

        self.assertTrue(listed["ok"])
        self.assertEqual(1, listed["count"])
        self.assertTrue(detail["ok"])
        self.assertEqual("playwright", detail["capability"]["capability_id"])
        self.assertIn("permitted_tools", detail["capability"])
        self.assertIn("denied_tools", detail["capability"])
        for forbidden in (
            "should-never-appear",
            "secret-argument",
            "SECRET_NAME",
            "executable_or_url",
            "headers",
            "arguments",
            "env_var_names",
            "inputSchema",
            "outputSchema",
        ):
            self.assertNotIn(forbidden, payload)

    def test_catalog_is_granted_to_every_profile_with_operator_elevation_route(self) -> None:
        expected_profiles = set(self.registry["capability_profiles"]) - {"openclaw"}
        catalog = self.registry["servers"]["agentcore-capability-catalog"]
        self.assertEqual(expected_profiles, set(catalog["capability_profiles"]))
        for profile_id, profile in self.registry["capability_profiles"].items():
            if profile_id == "openclaw":
                self.assertNotIn("agentcore-capability-catalog", profile["allowed_server_ids"])
                continue
            self.assertIn("agentcore-capability-catalog", profile["allowed_server_ids"])

        detail = server.get_capability_detail(
            {"capability_id": "agentcore-project-router"}, registry=self.registry
        )
        self.assertEqual("operator", detail["capability"]["elevation"]["profile"])
        self.assertEqual(
            "existing_operator_authority_path",
            detail["capability"]["elevation"]["route"],
        )

    def test_trust_class_a_spelling_and_class_b_boundary_are_explicit(self) -> None:
        rules = {rule["id"]: rule["rule"] for rule in self.policy["mandatory_rules"]}
        trust_rule = rules["client-trust-classes"]
        for client in (
            "Cursor",
            "Codex",
            "Devin",
            "Antigravity",
            "ZCode",
            "MiniMax coding clients",
            "Open Interpreter",
        ):
            self.assertIn(client, trust_rule)
        self.assertIn("Zoo-Code is a separate extension", trust_rule)
        self.assertIn("Trust Class B", trust_rule)
        self.assertIn("operator", trust_rule)
        self.assertIn("host-native", trust_rule)
        self.assertIn("whole-drive filesystem MCP roots remain forbidden", trust_rule)

    def test_playwright_all_24_tools_are_builder_executable_with_zero_auto(self) -> None:
        playwright = self.registry["servers"]["playwright"]
        inventory = playwright["admission_evidence"]["tool_inventory"]
        self.assertEqual(24, inventory["reported_tool_count"])
        self.assertEqual(set(inventory["tools"]), set(playwright["permitted_tools"]))
        self.assertEqual([], playwright["denied_tools"])
        self.assertTrue(playwright["is_code_mode_client"])
        self.assertIn("builder", playwright["capability_profiles"])
        self.assertNotIn("tools_to_auto_execute", playwright)
        self.assertIn("browser_file_upload", playwright["permitted_tools"])
        self.assertIn("browser_run_code_unsafe", playwright["permitted_tools"])
        for group in playwright["tool_groups"].values():
            self.assertEqual("default_profile", group["access_policy"])
            self.assertFalse((group.get("lease_defaults") or {}).get("requires_approval", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)
