from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HELPER_PATH = REPO / "scripts" / "bifrost" / "sync_code_mode_live_clients.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("sync_code_mode_live_clients", HELPER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()


class DesiredFlagsTests(unittest.TestCase):
    def test_skips_disabled_registry_servers(self) -> None:
        registry = {
            "servers": {
                "nia": {"enabled": True, "bifrost_client_name": "nia", "is_code_mode_client": True},
                "github-mcp": {"enabled": False, "bifrost_client_name": "github_mcp", "is_code_mode_client": True},
                "memory": {"enabled": True, "bifrost_client_name": "agentcore_memory", "is_code_mode_client": False},
            }
        }
        self.assertEqual(
            HELPER.desired_flags(registry),
            {"nia": True, "agentcore_memory": False},
        )

    def test_rendered_overrides_registry_flag(self) -> None:
        registry = {
            "servers": {
                "nia": {"enabled": True, "bifrost_client_name": "nia", "is_code_mode_client": False},
            }
        }
        rendered = {"mcp": {"client_configs": [{"name": "nia", "is_code_mode_client": True}]}}
        self.assertEqual(HELPER.desired_flags(registry, rendered), {"nia": True})


class PlanSyncTests(unittest.TestCase):
    def test_ok_drift_missing_and_no_id(self) -> None:
        desired = {"nia": True, "skills_hub": True, "ghost": True, "orphan": False}
        live = {
            "nia": {"name": "nia", "client_id": "c1", "is_code_mode_client": True},
            "skills_hub": {"name": "skills_hub", "client_id": "c2", "is_code_mode_client": False},
            "orphan": {"name": "orphan", "is_code_mode_client": True},
        }
        rows = {row["name"]: row for row in HELPER.plan_sync(desired, live)}
        self.assertEqual(rows["nia"]["action"], "ok")
        self.assertEqual(rows["skills_hub"]["action"], "drift")
        self.assertEqual(rows["ghost"]["action"], "skip_missing")
        self.assertEqual(rows["orphan"]["action"], "skip_no_id")

    def test_index_live_clients_uses_config_name(self) -> None:
        payload = {"clients": [{"config": {"name": "nia", "client_id": "abc", "is_code_mode_client": True}}]}
        self.assertEqual(HELPER.index_live_clients(payload)["nia"]["client_id"], "abc")


class ApplyPlanTests(unittest.TestCase):
    def test_check_mode_does_not_put(self) -> None:
        calls = []
        rows = [{"name": "skills_hub", "action": "drift", "want": True, "have": False, "client_id": "c2"}]
        updated = HELPER.apply_plan(rows, mode="check", requester=lambda m, p, b: calls.append((m, p, b)) or {})
        self.assertEqual(updated, [])
        self.assertEqual(calls, [])
        self.assertEqual(rows[0]["action"], "drift")

    def test_apply_puts_only_boolean_on_drift(self) -> None:
        calls = []
        rows = [
            {"name": "nia", "action": "ok", "want": True, "have": True, "client_id": "c1"},
            {"name": "skills_hub", "action": "drift", "want": True, "have": False, "client_id": "c2"},
            {"name": "ghost", "action": "skip_missing", "want": True, "have": None, "client_id": None},
        ]
        updated = HELPER.apply_plan(rows, mode="apply", requester=lambda m, p, b: calls.append((m, p, b)) or {})
        self.assertEqual(updated, ["skills_hub"])
        self.assertEqual(calls, [("PUT", "/api/mcp/client/c2", {"is_code_mode_client": True})])
        self.assertEqual(rows[1]["action"], "updated")

    def test_evidence_omits_secrets(self) -> None:
        rows = [{"name": "nia", "action": "ok", "want": True, "have": True, "client_id": "secret-id"}]
        payload = HELPER.evidence_payload(
            mode="check",
            rendered_path=r"F:\AgentCore\runtime\bifrost\config.json",
            rows=rows,
            updated=[],
        )
        blob = str(payload)
        self.assertNotIn("secret-id", blob)
        self.assertNotIn("Authorization", blob)
        self.assertEqual(payload["rendered_path_kind"], "live")
        self.assertEqual(payload["ok"], ["nia"])

    def test_ops_scripts_wire_sync_helper(self) -> None:
        start = (REPO / "ops" / "bifrost" / "Start-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
        install = (REPO / "ops" / "bifrost" / "Install-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
        test = (REPO / "ops" / "bifrost" / "Test-AgentCoreBifrostGateway.ps1").read_text(encoding="utf-8")
        self.assertIn("sync_code_mode_live_clients.py", start)
        self.assertIn("--mode apply", start)
        self.assertIn("if ($TestMode) { return }", start)
        self.assertIn("sync_code_mode_live_clients.py", install)
        self.assertIn("CODE_MODE_LIVE_SYNC", install)
        self.assertIn("sync_code_mode_live_clients.py", test)
        self.assertIn("--mode check", test)


if __name__ == "__main__":
    unittest.main()
