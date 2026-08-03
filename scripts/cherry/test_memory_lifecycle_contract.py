from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch


def _load_validator():
    path = Path(__file__).with_name("validate_cherry_memory_lifecycle.py")
    spec = importlib.util.spec_from_file_location("validate_cherry_memory_lifecycle_contract", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cherry_validator_signs_memory_calls_with_device_identity() -> None:
    module = _load_validator()
    client = object.__new__(module.McpClient)
    assertion = Mock()
    assertion.as_dict.return_value = {"algorithm": "Ed25519", "signature": "test"}
    identity = Mock()
    identity.initialize.return_value = SimpleNamespace(device_id="device-test")
    identity.sign_tool_call.return_value = assertion

    with patch.object(client, "_device_identity_manager", return_value=identity):
        signed = client._signed_tool_arguments(
            "agentcore_memory-session_open",
            {
                "project_key": "agentcore-control-plane",
                "project_root": r"D:\github\agentcore-control-plane",
                "device_id": "caller-controlled-device",
            },
        )

    assert signed["device_id"] == "device-test"
    assert signed["device_assertion"]["algorithm"] == "Ed25519"


def test_cherry_validator_does_not_depend_on_global_project_router() -> None:
    module = _load_validator()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "agentcore_project_router-" not in source
    assert module.PROJECT_B == "agentcore-context-engine"
