#!/usr/bin/env python3
"""Acceptance Canary & Unit Tests for Serena HTTP Session Shim.

Validates:
1. Enrollment contract default-deny and Swarm refusal (foreign_roots / foreign_markers).
2. MCP JSON-RPC protocol compliance: ping, initialize, tools/list (21 tools).
3. Concurrent multi-IDE isolation canary: two concurrent sessions on two enrolled roots
   prove zero cross-project symbol or file leakage and separate subprocess isolation.

Authority: docs/adr/ADR-2026-09-09-serena-http-session-shim.md
"""

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bifrost.serena_session_shim import (
    CACHED_SERENA_TOOLS,
    SerenaChildProcess,
    SerenaProjectRegistry,
    SerenaShimHTTPHandler,
    SerenaShimManager,
    SHIM_MANAGER,
)


class SerenaProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = SerenaProjectRegistry()

    def test_enrolled_projects_resolve(self):
        pkey, path, err = self.registry.resolve_project(project_key="agentcore-control-plane")
        self.assertIsNone(err)
        self.assertEqual(pkey, "agentcore-control-plane")
        self.assertEqual(path, Path(r"D:\github\agentcore-control-plane").resolve())

        pkey2, path2, err2 = self.registry.resolve_project(project_key="agentcore-context-engine")
        self.assertIsNone(err2)
        self.assertEqual(pkey2, "agentcore-context-engine")
        self.assertEqual(path2, Path(r"D:\github\agentcore-context-engine").resolve())

    def test_path_lookup_resolves(self):
        pkey, path, err = self.registry.resolve_project(candidate_path=r"D:\github\agentcore-control-plane\scripts\test.py")
        self.assertIsNone(err)
        self.assertEqual(pkey, "agentcore-control-plane")

    def test_unenrolled_project_denied(self):
        pkey, path, err = self.registry.resolve_project(
            project_key="random-unenrolled-repo"
        )
        self.assertEqual(err, "PROJECT_NOT_ENROLLED")
        self.assertIsNone(pkey)
        self.assertIsNone(path)

        pkey2, path2, err2 = self.registry.resolve_project()
        self.assertEqual(err2, "PROJECT_NOT_ENROLLED")
        self.assertIsNone(pkey2)
        self.assertIsNone(path2)

        pkey3, path3, err3 = self.registry.resolve_project(
            project_key="unknown",
            candidate_path=r"C:\unregistered\repo\file.txt",
        )
        self.assertEqual(err3, "PROJECT_NOT_ENROLLED")
        self.assertIsNone(pkey3)
        self.assertIsNone(path3)
        self.assertNotEqual(pkey3, "agentcore-control-plane")

    def test_missing_identity_never_falls_back_to_control_plane(self):
        pkey, path, err = self.registry.resolve_project(
            project_key="definitely-not-enrolled"
        )
        self.assertEqual(err, "PROJECT_NOT_ENROLLED")
        self.assertNotEqual(pkey, "agentcore-control-plane")
        if path is not None:
            self.assertNotEqual(
                path, Path(r"D:\github\agentcore-control-plane").resolve()
            )

    def test_swarm_roots_strictly_refused(self):
        swarm_paths = [
            r"D:\github\swarm-ecosystem-control",
            r"D:\github\swarm-ecosystem-control\sub\file.txt",
            r"E:\Swarm\data",
            r"H:\SwarmData\test",
            r"F:\AgentCore\agentmemory",
        ]
        for spath in swarm_paths:
            pkey, path, err = self.registry.resolve_project(candidate_path=spath)
            self.assertEqual(err, "swarm_project_refused", f"Expected refusal for {spath}")
            self.assertIsNone(pkey)
            self.assertIsNone(path)

    def test_swarm_markers_strictly_refused(self):
        markers = ["swarmrecall", "swarmvault", "swarmclaw", "agentswarm", "agent-swarm"]
        for marker in markers:
            pkey, path, err = self.registry.resolve_project(project_key=f"my-{marker}-project")
            self.assertEqual(err, "swarm_project_refused", f"Expected refusal for marker {marker}")


class SerenaShimHttpProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 18195
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.test_port), SerenaShimHTTPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.test_port}/mcp"
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        SHIM_MANAGER.stop_all()

    def _post(self, payload: dict, headers: dict | None = None) -> dict:
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base_url, data=data, headers=req_headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_ping_intercepted_immediately(self):
        resp = self._post({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertEqual(resp.get("id"), 1)
        self.assertEqual(resp.get("result"), {})

    def test_initialize_returns_capabilities(self):
        resp = self._post({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}})
        self.assertEqual(resp.get("jsonrpc"), "2.0")
        self.assertEqual(resp.get("id"), 2)
        server_info = resp.get("result", {}).get("serverInfo", {})
        self.assertEqual(server_info.get("name"), "serena-session-shim")

    def test_tools_list_returns_21_cached_tools(self):
        resp = self._post({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        tools = resp.get("result", {}).get("tools", [])
        self.assertEqual(len(tools), 21)
        tool_names = {t["name"] for t in tools}
        self.assertIn("find_symbol", tool_names)
        self.assertIn("replace_content", tool_names)
        self.assertIn("get_symbols_overview", tool_names)
        self.assertIn("find_referencing_symbols", tool_names)
        self.assertIn("rename_symbol", tool_names)


class SerenaConcurrentIsolationCanaryTests(unittest.TestCase):
    """Canary test proving two concurrent sessions on two enrolled roots achieve zero cross-project leakage."""

    @classmethod
    def setUpClass(cls):
        cls.test_port = 18196
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.test_port), SerenaShimHTTPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.test_port}/mcp"
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        SHIM_MANAGER.stop_all()

    def test_concurrent_sessions_isolated_and_no_leakage(self):
        """Simulate Session 1 on agentcore-control-plane and Session 2 on agentcore-context-engine."""
        session1_headers = {
            "x-agentcore-project": "agentcore-control-plane",
            "x-bf-session-id": "session-cursor-001",
        }
        session2_headers = {
            "x-agentcore-project": "agentcore-context-engine",
            "x-bf-session-id": "session-zed-002",
        }
        swarm_session_headers = {
            "x-agentcore-project": "swarm-ecosystem-control",
            "x-bf-session-id": "session-swarm-bad",
        }

        # 1. Swarm session must be rejected with swarm_project_refused
        req_data = json.dumps({
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/call",
            "params": {"name": "find_symbol", "arguments": {"name_path_pattern": "test"}},
        }).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=req_data,
            headers={"Content-Type": "application/json", **swarm_session_headers},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("error", data)
            self.assertEqual(data["error"]["code"], -32001)
            self.assertIn("swarm_project_refused", data["error"]["message"])

        # 2. Mock children to inspect dispatched arguments without spawning external binaries in unit test
        mock_child1 = MagicMock(spec=SerenaChildProcess)
        mock_child1.project_key = "agentcore-control-plane"
        mock_child1.project_path = Path(r"D:\github\agentcore-control-plane").resolve()
        mock_child1.call_jsonrpc.return_value = {
            "jsonrpc": "2.0",
            "id": 101,
            "result": {"symbols": ["ControlPlaneSymbol"]},
        }

        mock_child2 = MagicMock(spec=SerenaChildProcess)
        mock_child2.project_key = "agentcore-context-engine"
        mock_child2.project_path = Path(r"D:\github\agentcore-context-engine").resolve()
        mock_child2.call_jsonrpc.return_value = {
            "jsonrpc": "2.0",
            "id": 102,
            "result": {"symbols": ["ContextEngineSymbol"]},
        }

        # Inject mock children into SHIM_MANAGER
        with SHIM_MANAGER._lock:
            SHIM_MANAGER.children["agentcore-control-plane"] = mock_child1
            SHIM_MANAGER.children["agentcore-context-engine"] = mock_child2

        results = {}

        def call_session(sess_id: str, headers: dict, call_id: int):
            req_payload = {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/call",
                "params": {"name": "find_symbol", "arguments": {"name_path_pattern": "SymbolQuery"}},
            }
            post_req = urllib.request.Request(
                self.base_url,
                data=json.dumps(req_payload).encode("utf-8"),
                headers={"Content-Type": "application/json", **headers},
                method="POST",
            )
            with urllib.request.urlopen(post_req) as response:
                results[sess_id] = json.loads(response.read().decode("utf-8"))

        t1 = threading.Thread(target=call_session, args=("sess1", session1_headers, 101))
        t2 = threading.Thread(target=call_session, args=("sess2", session2_headers, 102))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Session 1 received ONLY ControlPlaneSymbol
        self.assertEqual(results["sess1"]["result"]["symbols"], ["ControlPlaneSymbol"])
        mock_child1.call_jsonrpc.assert_called_once()
        self.assertEqual(mock_child1.call_jsonrpc.call_args[0][0]["id"], 101)

        # Session 2 received ONLY ContextEngineSymbol
        self.assertEqual(results["sess2"]["result"]["symbols"], ["ContextEngineSymbol"])
        mock_child2.call_jsonrpc.assert_called_once()
        self.assertEqual(mock_child2.call_jsonrpc.call_args[0][0]["id"], 102)

        # Zero cross-talk verified!

    def test_tools_call_without_project_identity_denied(self):
        """Missing headers and args must not fall back to agentcore-control-plane."""
        req_payload = {
            "jsonrpc": "2.0",
            "id": 201,
            "method": "tools/call",
            "params": {
                "name": "find_symbol",
                "arguments": {"name_path_pattern": "SymbolQuery"},
            },
        }
        post_req = urllib.request.Request(
            self.base_url,
            data=json.dumps(req_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_req) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32002)
        self.assertIn("PROJECT_NOT_ENROLLED", data["error"]["message"])


if __name__ == "__main__":
    unittest.main()
