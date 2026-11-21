from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
ALIGNMENT_VALIDATOR_PATH = REPO / "scripts" / "validate_agentcore_alignment_skill.py"


def load_json(relative_path: str) -> dict:
    return json.loads((REPO / relative_path).read_text(encoding="utf-8"))


def load_yaml(relative_path: str) -> dict:
    return yaml.safe_load((REPO / relative_path).read_text(encoding="utf-8"))


def load_alignment_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_agentcore_alignment_skill", ALIGNMENT_VALIDATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Task2ContractProfileAlignmentTests(unittest.TestCase):
    def test_openclaw_and_clawx_are_agentcore_owned_with_exact_non_live_roots(self):
        policy = load_yaml("contracts/global-agent-policy.yaml")
        matrix = load_yaml("ide-profiles/IDE_CAPABILITY_MATRIX.yaml")
        gateway = load_json("contracts/agentcore-gateway-client.json")
        manifest = load_json("contracts/agentcore-alignment-skill-hosts.json")

        policy_text = json.dumps(policy).lower()
        self.assertNotIn("openclaw/clawx are swarm-managed", policy_text)
        self.assertNotIn("openclaw", matrix.get("swarm_managed_clients", {}))
        self.assertNotIn("clawx", matrix.get("swarm_managed_clients", {}))

        candidates = matrix["managed_candidates"]
        self.assertEqual(candidates["openclaw"]["ownership"], "agentcore")
        self.assertEqual(
            candidates["openclaw"]["certification"],
            "configured_restart_required",
        )
        self.assertEqual(
            candidates["openclaw"]["gateway_url"],
            "http://127.0.0.1:8080/mcp",
        )
        self.assertEqual(
            candidates["openclaw"]["gateway_auth_mode"],
            "dedicated_bearer_env",
        )
        self.assertEqual(candidates["openclaw"]["governed_product_root"], r"D:\github\open--claw")
        self.assertEqual(candidates["openclaw"]["windows_operations_root"], r"D:\openclaw")
        self.assertEqual(candidates["openclaw"]["excluded_live_state_root"], r"C:\Users\ynotf\.openclaw")
        self.assertEqual(candidates["clawx"]["installer_root"], r"C:\Program Files\ClawX")

        for host in ("openclaw", "clawx"):
            entry = next(item for item in manifest["hosts"] if item["host"] == host)
            self.assertEqual(entry["ownership"], "agentcore")
            self.assertEqual(entry["certification"], "unverified")

        openclaw_hint = gateway["client_render_hints"]["openclaw"]
        self.assertTrue(openclaw_hint["enabled"])
        self.assertEqual(openclaw_hint["syntax"], "openclaw_json")
        self.assertEqual(
            openclaw_hint["config_path"], r"C:\Users\ynotf\.openclaw\openclaw.json"
        )
        self.assertTrue(openclaw_hint["supports_env_headers"])

        clawx_hint = gateway["client_render_hints"]["clawx"]
        self.assertFalse(clawx_hint["enabled"])
        self.assertEqual(clawx_hint["syntax"], "skip_openclaw")

        zcode = candidates["zcode"]
        self.assertEqual(zcode["ownership"], "agentcore")
        self.assertEqual(zcode["certification"], "configured_restart_required")
        self.assertEqual(zcode["gateway_url"], "http://127.0.0.1:18082/mcp")
        self.assertEqual(zcode["gateway_auth_mode"], "process_attested_proxy")
        self.assertTrue(gateway["client_render_hints"]["zcode"]["enabled"])

    def test_devin_templates_are_gateway_only_and_never_require_public_tunnel(self):
        template = load_json("ide-profiles/devin/MCP_CONFIG_TEMPLATE.json")
        renderer = load_json("renderers/gateway-clients/devin.json")
        profile_text = (REPO / "ide-profiles/devin/IDE_PROFILE.yaml").read_text(encoding="utf-8")
        combined = "\n".join(
            [json.dumps(template), json.dumps(renderer), profile_text]
        ).lower()

        for artifact in (template, renderer):
            servers = [k for k in artifact["mcpServers"] if k != "claude-context"]
            self.assertEqual(servers, ["agentcore-gateway"])
            self.assertEqual(
                artifact["mcpServers"]["agentcore-gateway"]["url"],
                "http://127.0.0.1:18082/mcp",
            )
            self.assertNotIn("headers", artifact["mcpServers"]["agentcore-gateway"])
        for forbidden in ("public tunnel", "tunnel http", "install directly", "paste_project_root_here"):
            self.assertNotIn(forbidden, combined)

    def test_primary_policy_contains_exact_code_mode_discovery_sequence(self):
        policy = load_yaml("contracts/global-agent-policy.yaml")
        rule = next(
            item["rule"]
            for item in policy["mandatory_rules"]
            if item["id"] == "session-tool-discovery"
        )
        positions = [
            rule.index(name)
            for name in ("listToolFiles", "readToolFile", "getToolDocs", "executeToolCode")
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("Code Mode", rule)
        self.assertIn("operational issue", rule)
        self.assertIn("duplicate", rule)

    def test_reasonix_claims_only_existing_evidence_and_no_hindsight_acceptance(self):
        profile = load_yaml("ide-profiles/reasonix/IDE_PROFILE.yaml")
        profile_text = json.dumps(profile).lower()
        rules_text = (REPO / "ide-profiles/reasonix/GLOBAL_RULES.md").read_text(
            encoding="utf-8"
        ).lower()

        self.assertNotIn("hindsight", profile_text)
        self.assertNotIn("hindsight", rules_text)
        self.assertNotEqual(profile["m8_enrollment"], "live_validated")
        for dimension in profile["dimensions"].values():
            self.assertNotEqual(dimension["status"], "live_validated")
            evidence_path = dimension.get("evidence_path")
            if evidence_path:
                self.assertTrue((REPO / evidence_path).is_file(), evidence_path)

    def test_installed_skill_certification_requires_live_tree_hash_parity(self):
        validator = load_alignment_validator()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            source = temp / "source"
            installed = temp / ".host" / "skills" / "agentcore-project-lifecycle"
            source.mkdir()
            installed.mkdir(parents=True)
            (source / "SKILL.md").write_text("canonical", encoding="utf-8")
            (installed / "SKILL.md").write_text("stale", encoding="utf-8")
            manifest = {
                "certification_states": [
                    "source_ready",
                    "installed_unverified",
                    "configured_restart_required",
                    "live_validated",
                    "manual_import_pending",
                    "UI_only_pending",
                    "unverified",
                    "unsupported_with_reason",
                ],
                "hosts": [
                    {
                        "host": "fixture",
                        "delivery": "native_skill",
                        "target": r"{userprofile}\.host\skills\agentcore-project-lifecycle",
                        "certification": "installed_unverified",
                        "installed_sha256": validator.tree_digest(source),
                    }
                ],
            }

            errors = validator.installed_skill_hash_errors(
                manifest, source, userprofile=temp
            )
            self.assertEqual(len(errors), 1)
            self.assertIn("installed skill hash mismatch", errors[0])

            (installed / "SKILL.md").write_text("canonical", encoding="utf-8")
            self.assertEqual(
                validator.installed_skill_hash_errors(manifest, source, userprofile=temp),
                [],
            )


if __name__ == "__main__":
    unittest.main()
