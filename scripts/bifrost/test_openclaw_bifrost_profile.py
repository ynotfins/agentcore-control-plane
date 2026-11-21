from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
GATEWAY_PATH = ROOT / "contracts" / "agentcore-gateway-client.json"
RENDERER_PATH = ROOT / "scripts" / "bifrost" / "render_bifrost_config.py"

EXPECTED_SERVER_IDS = {
    "agentcore-memory",
    "arabold-docs",
    "context7",
    "mcp-prompt-optimizer",
    "morph-mcp",
    "nia",
    "playwright",
    "sequential-thinking",
    "skills-hub",
}
FORBIDDEN_SERVER_IDS = {"agentcore-project-router", "cursor-agent-mcp"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_bifrost_config", RENDERER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_openclaw_profile_has_exact_server_set_and_reciprocal_membership() -> None:
    registry = load_json(REGISTRY_PATH)
    profile = registry["capability_profiles"]["openclaw"]

    assert set(profile["allowed_server_ids"]) == EXPECTED_SERVER_IDS
    assert FORBIDDEN_SERVER_IDS.isdisjoint(profile["allowed_server_ids"])
    for server_id in EXPECTED_SERVER_IDS:
        server = registry["servers"][server_id]
        assert server["enabled"] is True
        assert "openclaw" in server["capability_profiles"]


def test_openclaw_virtual_key_is_deterministic_and_uses_only_env_reference() -> None:
    renderer = load_renderer()
    registry = load_json(REGISTRY_PATH)

    first = renderer.build_virtual_keys(registry)
    second = renderer.build_virtual_keys(registry)
    assert first == second

    openclaw = next(item for item in first if item["id"] == "vk-agentcore-openclaw")
    assert openclaw == {
        "id": "vk-agentcore-openclaw",
        "name": "openclaw",
        "value": "env.BIFROST_MCP_VK_OPENCLAW",
        "is_active": True,
        "mcp_configs": renderer.profile_mcp_configs(registry, "openclaw"),
    }
    assert {item["mcp_client_name"] for item in openclaw["mcp_configs"]} == {
        registry["servers"][server_id]["bifrost_client_name"]
        for server_id in EXPECTED_SERVER_IDS
    }


def test_openclaw_client_hint_matches_verified_host_native_shape() -> None:
    gateway = load_json(GATEWAY_PATH)
    hint = gateway["client_render_hints"]["openclaw"]

    assert hint["enabled"] is True
    assert hint["config_path"] == r"C:\Users\ynotf\.openclaw\openclaw.json"
    assert hint["syntax"] == "openclaw_json"
    assert hint["supports_env_headers"] is True
    assert "BIFROST_MCP_VK_OPENCLAW" in json.dumps(hint)
    assert "Bearer sk-" not in json.dumps(hint)


def test_clawx_remains_disabled_and_outside_openclaw_profile() -> None:
    registry = load_json(REGISTRY_PATH)
    gateway = load_json(GATEWAY_PATH)
    clawx = gateway["client_render_hints"]["clawx"]

    assert clawx["enabled"] is False
    assert clawx["syntax"] == "skip_openclaw"
    assert "clawx" not in registry["capability_profiles"]
