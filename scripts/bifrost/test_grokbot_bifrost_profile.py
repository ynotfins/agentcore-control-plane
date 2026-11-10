from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
GATEWAY_PATH = ROOT / "contracts" / "agentcore-gateway-client.json"
ENROLLMENT_PATH = ROOT / "contracts" / "agentcore-project-enrollment.json"
RENDERER_PATH = ROOT / "scripts" / "bifrost" / "render_bifrost_config.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_bifrost_config", RENDERER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_postgresql18_control_plane_is_enrolled() -> None:
    enrollment = load_json(ENROLLMENT_PATH)
    project = next(
        item
        for item in enrollment["projects"]
        if item["project_key"] == "postgresql18-control-plane"
    )
    assert project["paths"] == [r"D:\postgreSQL18-control-plane"]


def test_grokbot_profile_is_builder_minus_cursor_agent() -> None:
    registry = load_json(REGISTRY_PATH)
    builder = set(registry["capability_profiles"]["builder"]["allowed_server_ids"])
    expected = builder - {"cursor-agent-mcp"}
    profile = registry["capability_profiles"]["grokbot"]
    assert set(profile["allowed_server_ids"]) == expected
    assert "cursor-agent-mcp" not in profile["allowed_server_ids"]
    for server_id in expected:
        assert "grokbot" in registry["servers"][server_id]["capability_profiles"]
    assert "grokbot" not in registry["servers"]["cursor-agent-mcp"]["capability_profiles"]


def test_grokbot_virtual_key_uses_env_reference() -> None:
    renderer = load_renderer()
    registry = load_json(REGISTRY_PATH)
    keys = renderer.build_virtual_keys(registry)
    grokbot = next(item for item in keys if item["id"] == "vk-agentcore-grokbot")
    assert grokbot == {
        "id": "vk-agentcore-grokbot",
        "name": "grokbot",
        "value": "env.BIFROST_MCP_VK_GROKBOT",
        "is_active": True,
        "mcp_configs": renderer.profile_mcp_configs(registry, "grokbot"),
    }
    dumped = json.dumps(keys)
    assert "sk-" not in dumped
    assert "BIFROST_MCP_VK_GROKBOT" in dumped


def test_grokbot_client_hint() -> None:
    gateway = load_json(GATEWAY_PATH)
    hint = gateway["client_render_hints"]["grokbot"]
    assert hint["enabled"] is True
    assert hint["config_path"] == r"C:\Users\ynotf\.grokbot\settings.json"
    assert hint["syntax"] == "grokbot_json"
    assert hint["supports_env_headers"] is True
    assert hint["gateway_url"] == "http://127.0.0.1:8080/mcp"
    assert hint["gateway_auth_mode"] == "bearer_env"
    assert "BIFROST_MCP_VK_GROKBOT" in json.dumps(hint)
