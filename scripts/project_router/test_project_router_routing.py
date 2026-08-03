from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
REGISTRY_PATH = REPO_ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProjectRouterRoutingTests(unittest.TestCase):
    def test_context_fabric_is_rendered_through_project_router_wrapper(self) -> None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        context_fabric = registry["servers"]["context-fabric"]

        self.assertEqual(context_fabric["connection_type"], "router")
        self.assertEqual(
            context_fabric["wrapper_script"],
            "scripts/project_router/wrappers/context-fabric.cmd",
        )

    def test_child_launcher_defaults_to_current_agentcore_runtime(self) -> None:
        launcher = load_module("agentcore_child_launcher_test", HERE / "child_launcher.py")

        self.assertEqual(launcher.RUNTIME_ROOT, Path(r"F:\AgentCore\runtime"))
        self.assertEqual(
            launcher.STATE_PATH,
            Path(r"F:\AgentCore\runtime\bifrost\state\active-project.json"),
        )
        self.assertEqual(
            launcher.PROCESS_REGISTRY,
            Path(r"F:\AgentCore\runtime\mcp-processes\registry.json"),
        )
        self.assertEqual(
            launcher.TENTRA_DATA,
            Path(r"F:\AgentCore\runtime\tentra\data"),
        )

    def test_project_activation_reports_router_client_reconnect(self) -> None:
        server = load_module("agentcore_project_router_test", HERE / "server.py")
        project = {
            "id": "agentcore-control-plane",
            "name": "agentcore-control-plane",
            "path": str(REPO_ROOT),
        }
        reconnect = {
            "ok": True,
            "status": "reconnected",
            "clients": ["context_fabric"],
        }

        with (
            patch.object(server, "scan_registered_projects", return_value=[project]),
            patch.object(server, "save_state") as save_state,
            patch.object(server, "reconnect_router_clients", return_value=reconnect) as reconnect_call,
        ):
            result = server.call_tool("project_activate", {"id": project["id"]})

        self.assertTrue(result["ok"])
        self.assertEqual(result["project_scoped_reconnect"], reconnect)
        save_state.assert_called_once()
        reconnect_call.assert_called_once_with()

    def test_router_client_inventory_comes_from_enabled_router_contracts(self) -> None:
        server = load_module("agentcore_project_router_inventory_test", HERE / "server.py")

        self.assertEqual(server._router_client_names(), ["context_fabric"])

    def test_failed_state_write_preserves_previous_active_project(self) -> None:
        server = load_module("agentcore_project_router_atomic_test", HERE / "server.py")
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "active-project.json"
            original = {"id": "previous", "path": r"D:\github\previous"}
            state_path.write_text(json.dumps(original), encoding="utf-8")

            with (
                patch.object(server, "STATE_PATH", state_path),
                patch.object(server.json, "dump", side_effect=OSError("simulated write failure")),
            ):
                with self.assertRaises(OSError):
                    server.save_state({"id": "next", "path": str(REPO_ROOT)})

            self.assertEqual(json.loads(state_path.read_text(encoding="utf-8")), original)

    def test_project_clear_reconnects_router_clients_to_fail_closed_state(self) -> None:
        server = load_module("agentcore_project_router_clear_test", HERE / "server.py")
        reconnect = {
            "ok": False,
            "status": "unavailable",
            "clients": [],
            "error": "no_active_project",
        }

        with (
            patch.object(server, "scan_registered_projects", return_value=[]),
            patch.object(server, "save_state") as save_state,
            patch.object(server, "reconnect_router_clients", return_value=reconnect) as reconnect_call,
        ):
            result = server.call_tool("project_clear", {})

        self.assertTrue(result["ok"])
        self.assertEqual(result["project_scoped_reconnect"], reconnect)
        save_state.assert_called_once_with(None)
        reconnect_call.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
