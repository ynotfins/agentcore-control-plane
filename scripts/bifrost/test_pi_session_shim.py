#!/usr/bin/env python3
"""Acceptance canary and unit tests for the Pi HTTP session shim."""

from __future__ import annotations

import json
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from bifrost.pi_session_shim import (
    CACHED_PI_TOOLS,
    ERROR_CWD_OUT_OF_ENROLLMENT,
    PiChildProcess,
    PiProjectRegistry,
    PiShimHTTPHandler,
    SHIM_MANAGER,
    bind_enrolled_cwd,
    prepare_pi_tool_args,
)


class PiProjectRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = PiProjectRegistry()

    def test_enrolled_projects_resolve(self):
        pkey, path, err = self.registry.resolve_project(project_key="agentcore-control-plane")
        self.assertIsNone(err)
        self.assertEqual(pkey, "agentcore-control-plane")
        self.assertEqual(path, Path(r"D:\github\agentcore-control-plane").resolve())
        pkey2, path2, err2 = self.registry.resolve_project(project_key="agentcore-context-engine")
        self.assertIsNone(err2)
        self.assertEqual(pkey2, "agentcore-context-engine")

    def test_unenrolled_project_denied(self):
        pkey, path, err = self.registry.resolve_project(project_key="random-unenrolled-repo")
        self.assertEqual(err, "PROJECT_NOT_ENROLLED")
        self.assertIsNone(pkey)
        self.assertIsNone(path)

    def test_missing_identity_never_falls_back_to_control_plane(self):
        pkey, path, err = self.registry.resolve_project(project_key="definitely-not-enrolled")
        self.assertEqual(err, "PROJECT_NOT_ENROLLED")
        self.assertNotEqual(pkey, "agentcore-control-plane")

    def test_swarm_roots_strictly_refused(self):
        swarm_paths = [
            r"D:\github\swarm-ecosystem-control",
            r"E:\Swarm\data",
            r"H:\SwarmData\test",
            r"F:\AgentCore\agentmemory",
        ]
        for spath in swarm_paths:
            pkey, path, err = self.registry.resolve_project(candidate_path=spath)
            self.assertEqual(err, "swarm_project_refused", "Expected refusal for %s" % spath)
            self.assertIsNone(pkey)
            self.assertIsNone(path)


class PiCwdBindTests(unittest.TestCase):
    def setUp(self):
        self.enrolled = Path(r"D:\github\agentcore-control-plane").resolve()

    def test_missing_cwd_is_injected(self):
        bound, err = bind_enrolled_cwd({"prompt": "hi"}, self.enrolled)
        self.assertIsNone(err)
        self.assertEqual(bound["cwd"], str(self.enrolled))

    def test_enrolled_cwd_kept_as_root(self):
        bound, err = bind_enrolled_cwd({"cwd": str(self.enrolled / "scripts")}, self.enrolled)
        self.assertIsNone(err)
        self.assertEqual(bound["cwd"], str(self.enrolled))

    def test_out_of_enrollment_cwd_rejected(self):
        bound, err = bind_enrolled_cwd({"cwd": r"D:\github\agentcore-context-engine"}, self.enrolled)
        self.assertEqual(err, ERROR_CWD_OUT_OF_ENROLLMENT)
        self.assertIsNone(bound)

    def test_agentcore_runtime_cwd_rejected(self):
        bound, err = bind_enrolled_cwd({"cwd": r"F:\AgentCore\runtime\bifrost"}, self.enrolled)
        self.assertEqual(err, ERROR_CWD_OUT_OF_ENROLLMENT)
        self.assertIsNone(bound)

    def test_prepare_strips_identity_and_binds_cwd(self):
        prepared, err = prepare_pi_tool_args(
            {"agentcore_project": "agentcore-control-plane", "prompt": "x"},
            self.enrolled,
        )
        self.assertIsNone(err)
        self.assertNotIn("agentcore_project", prepared)
        self.assertEqual(prepared["cwd"], str(self.enrolled))


class PiShimHttpProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 18197
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.test_port), PiShimHTTPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:%s/mcp" % cls.test_port
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        SHIM_MANAGER.stop_all()

    def _post(self, payload, headers=None):
        req_headers = {"Content-Type": "application/json"}
        if headers:
            req_headers.update(headers)
        req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode("utf-8"), headers=req_headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_ping_initialize_and_four_tools(self):
        ping = self._post({"jsonrpc": "2.0", "id": 1, "method": "ping"})
        self.assertEqual(ping.get("result"), {})
        init = self._post({"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}})
        self.assertEqual(init.get("result", {}).get("serverInfo", {}).get("name"), "pi-session-shim")
        listed = self._post({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
        names = {t["name"] for t in listed.get("result", {}).get("tools", [])}
        self.assertEqual(len(CACHED_PI_TOOLS), 4)
        self.assertEqual(names, {"pi_list_agents", "pi_run_agent", "pi_parallel_agents", "pi_chain_workflow"})


class PiConcurrentIsolationCanaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_port = 18198
        cls.server = ThreadingHTTPServer(("127.0.0.1", cls.test_port), PiShimHTTPHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = "http://127.0.0.1:%s/mcp" % cls.test_port
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        SHIM_MANAGER.stop_all()

    def test_concurrent_sessions_isolated_and_no_leakage(self):
        session1_headers = {"x-agentcore-project": "agentcore-control-plane", "x-bf-session-id": "session-cursor-001"}
        session2_headers = {"x-agentcore-project": "agentcore-context-engine", "x-bf-session-id": "session-zed-002"}
        swarm_headers = {"x-agentcore-project": "swarm-ecosystem-control", "x-bf-session-id": "session-swarm-bad"}
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps({"jsonrpc": "2.0", "id": 100, "method": "tools/call", "params": {"name": "pi_list_agents", "arguments": {}}}).encode("utf-8"),
            headers={"Content-Type": "application/json", **swarm_headers},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(data["error"]["code"], -32001)
        self.assertIn("swarm_project_refused", data["error"]["message"])

        mock_child1 = MagicMock(spec=PiChildProcess)
        mock_child1.project_key = "agentcore-control-plane"
        mock_child1.project_path = Path(r"D:\github\agentcore-control-plane").resolve()
        mock_child1.call_jsonrpc.return_value = {"jsonrpc": "2.0", "id": 101, "result": {"agents": ["control-plane"]}}
        mock_child2 = MagicMock(spec=PiChildProcess)
        mock_child2.project_key = "agentcore-context-engine"
        mock_child2.project_path = Path(r"D:\github\agentcore-context-engine").resolve()
        mock_child2.call_jsonrpc.return_value = {"jsonrpc": "2.0", "id": 102, "result": {"agents": ["context-engine"]}}
        with SHIM_MANAGER._lock:
            SHIM_MANAGER.children["agentcore-control-plane"] = mock_child1
            SHIM_MANAGER.children["agentcore-context-engine"] = mock_child2

        results = {}

        def call_session(sess_id, headers, call_id):
            post_req = urllib.request.Request(
                self.base_url,
                data=json.dumps({"jsonrpc": "2.0", "id": call_id, "method": "tools/call", "params": {"name": "pi_list_agents", "arguments": {}}}).encode("utf-8"),
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
        self.assertEqual(results["sess1"]["result"]["agents"], ["control-plane"])
        self.assertEqual(results["sess2"]["result"]["agents"], ["context-engine"])
        forwarded1 = mock_child1.call_jsonrpc.call_args[0][0]["params"]["arguments"]
        forwarded2 = mock_child2.call_jsonrpc.call_args[0][0]["params"]["arguments"]
        self.assertEqual(forwarded1["cwd"], str(mock_child1.project_path))
        self.assertEqual(forwarded2["cwd"], str(mock_child2.project_path))

    def test_tools_call_without_project_identity_denied(self):
        post_req = urllib.request.Request(
            self.base_url,
            data=json.dumps({"jsonrpc": "2.0", "id": 201, "method": "tools/call", "params": {"name": "pi_list_agents", "arguments": {}}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_req) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["error"]["code"], -32002)
        self.assertIn("PROJECT_NOT_ENROLLED", data["error"]["message"])

    def test_tools_call_agentcore_project_arg_routes_and_strips(self):
        mock_child = MagicMock(spec=PiChildProcess)
        mock_child.project_key = "agentcore-control-plane"
        mock_child.project_path = Path(r"D:\github\agentcore-control-plane").resolve()
        mock_child.call_jsonrpc.return_value = {"jsonrpc": "2.0", "id": 301, "result": {"ok": True}}
        with SHIM_MANAGER._lock:
            SHIM_MANAGER.children["agentcore-control-plane"] = mock_child
        post_req = urllib.request.Request(
            self.base_url,
            data=json.dumps({"jsonrpc": "2.0", "id": 301, "method": "tools/call", "params": {"name": "pi_run_agent", "arguments": {"agentcore_project": "agentcore-control-plane", "agent": "scout", "prompt": "map"}}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_req) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertNotIn("error", data)
        forwarded = mock_child.call_jsonrpc.call_args[0][0]["params"]["arguments"]
        self.assertNotIn("agentcore_project", forwarded)
        self.assertEqual(forwarded["cwd"], str(mock_child.project_path))

    def test_forbidden_cwd_rejected_over_http(self):
        post_req = urllib.request.Request(
            self.base_url,
            data=json.dumps({"jsonrpc": "2.0", "id": 401, "method": "tools/call", "params": {"name": "pi_run_agent", "arguments": {"agentcore_project": "agentcore-control-plane", "agent": "scout", "prompt": "x", "cwd": r"F:\AgentCore\runtime\bifrost"}}}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(post_req) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["error"]["code"], -32003)
        self.assertIn(ERROR_CWD_OUT_OF_ENROLLMENT, data["error"]["message"])


if __name__ == "__main__":
    unittest.main()