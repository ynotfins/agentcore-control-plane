from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
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
    def test_shared_gateway_keeps_implicit_project_servers_dormant(self) -> None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        implicit_project_servers = {
            "serena",
            "depwire",
            "tentra",
            "filesystem",
            "context-fabric",
        }

        for server_id in implicit_project_servers:
            server = registry["servers"][server_id]
            self.assertFalse(server["enabled"], server_id)
            self.assertEqual(server["capability_profiles"], [], server_id)

    def test_only_operator_profile_can_mutate_global_project_router(self) -> None:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        profiles = registry["capability_profiles"]

        self.assertIn("agentcore-project-router", profiles["operator"]["allowed_server_ids"])
        for profile_id, profile in profiles.items():
            if profile_id != "operator":
                self.assertNotIn(
                    "agentcore-project-router",
                    profile["allowed_server_ids"],
                    profile_id,
                )

    def test_child_launcher_defaults_to_current_agentcore_runtime(self) -> None:
        launcher = load_module("agentcore_child_launcher_test", HERE / "child_launcher.py")

        normal = lambda path: str(path).replace("\\", "/")  # noqa: E731
        self.assertEqual(normal(launcher.RUNTIME_ROOT), "F:/AgentCore/runtime")
        self.assertEqual(
            normal(launcher.STATE_PATH),
            "F:/AgentCore/runtime/bifrost/state/active-project.json",
        )
        self.assertEqual(
            normal(launcher.PROCESS_REGISTRY),
            "F:/AgentCore/runtime/mcp-processes/registry.json",
        )
        self.assertEqual(
            normal(launcher.TENTRA_DATA),
            "F:/AgentCore/runtime/tentra/data",
        )

    def test_swarm_control_plane_is_rejected_by_router_and_child(self) -> None:
        server = load_module("agentcore_project_router_swarm_test", HERE / "server.py")
        launcher = load_module("agentcore_child_launcher_swarm_test", HERE / "child_launcher.py")
        swarm_path = Path(r"D:\github\swarm-ecosystem-control")

        self.assertIsNotNone(server._rejected_path(swarm_path))
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.object(launcher, "STATE_PATH", Path(temp_dir) / "active-project.json"),
        ):
            launcher.STATE_PATH.write_text(
                json.dumps({"id": "swarm-ecosystem-control", "path": str(swarm_path)}),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                launcher.load_active_project()

    def test_proxy_reads_small_message_without_waiting_for_chunk_fill(self) -> None:
        launcher = load_module("agentcore_child_launcher_proxy_test", HERE / "child_launcher.py")
        read_fd, write_fd = os.pipe()
        received: list[bytes] = []
        reader = os.fdopen(read_fd, "rb", buffering=0)
        try:
            thread = threading.Thread(
                target=lambda: received.append(launcher.read_stream_chunk(reader)),
                daemon=True,
            )
            thread.start()
            os.write(write_fd, b'{"jsonrpc":"2.0"}\n')
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive(), "small MCP message stalled waiting for 64 KiB")
            self.assertEqual(received, [b'{"jsonrpc":"2.0"}\n'])
        finally:
            os.close(write_fd)
            reader.close()

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

    def test_router_client_inventory_excludes_dormant_project_servers(self) -> None:
        server = load_module("agentcore_project_router_inventory_test", HERE / "server.py")

        self.assertEqual(server._router_client_names(), [])

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

    def test_project_clear_fails_and_restores_state_when_reconnect_fails(self) -> None:
        server = load_module("agentcore_project_router_clear_test", HERE / "server.py")
        previous = {
            "id": "previous",
            "path": r"D:\github\previous",
            "name": "previous",
        }
        reconnect = {
            "ok": False,
            "status": "unavailable",
            "clients": [],
            "error": "no_active_project",
        }

        with (
            patch.object(server, "scan_registered_projects", return_value=[]),
            patch.object(server, "load_state", return_value=previous),
            patch.object(server, "save_state") as save_state,
            patch.object(
                server,
                "reconnect_router_clients",
                side_effect=[reconnect, {"ok": True, "status": "reconnected", "clients": []}],
            ) as reconnect_call,
        ):
            result = server.call_tool("project_clear", {})

        self.assertFalse(result["ok"])
        self.assertEqual(result["active"], previous)
        self.assertEqual(result["project_scoped_reconnect"], reconnect)
        self.assertEqual(save_state.call_args_list[0].args, (None,))
        self.assertEqual(save_state.call_args_list[1].args, (previous,))
        self.assertEqual(reconnect_call.call_count, 2)

    def test_project_activate_fails_and_restores_state_when_reconnect_fails(self) -> None:
        server = load_module("agentcore_project_router_rollback_test", HERE / "server.py")
        previous = {"id": "previous", "path": r"D:\github\previous", "name": "previous"}
        project = {"id": "next", "path": str(REPO_ROOT), "name": "next"}
        failed = {"ok": False, "status": "unavailable", "clients": []}
        restored = {"ok": True, "status": "reconnected", "clients": []}

        with (
            patch.object(server, "scan_registered_projects", return_value=[project]),
            patch.object(server, "load_state", return_value=previous),
            patch.object(server, "save_state") as save_state,
            patch.object(server, "reconnect_router_clients", side_effect=[failed, restored]),
        ):
            result = server.call_tool("project_activate", {"id": "next"})

        self.assertFalse(result["ok"])
        self.assertEqual(result["active"], previous)
        self.assertEqual(result["project_scoped_reconnect"], failed)
        self.assertEqual(result["rollback_reconnect"], restored)
        self.assertEqual(save_state.call_args_list[1].args, (previous,))

    def test_bifrost_admin_base_must_be_loopback(self) -> None:
        server = load_module("agentcore_project_router_loopback_test", HERE / "server.py")

        with patch.object(server, "BIFROST_BASE", "https://example.com:8080"):
            with self.assertRaisesRegex(RuntimeError, "loopback"):
                server._validated_bifrost_base()

    def test_child_proxy_does_not_rewrite_registry_per_byte(self) -> None:
        source = (HERE / "child_launcher.py").read_text(encoding="utf-8")

        self.assertNotIn("read(1)", source)
        self.assertNotIn("touch_activity(server, project_path)", source)


if __name__ == "__main__":
    unittest.main()
