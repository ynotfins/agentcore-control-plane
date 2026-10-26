from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "contracts" / "bifrost-upstream-mcp-registry.json"
GATEWAY_PATH = ROOT / "contracts" / "agentcore-gateway-client.json"
ENROLLMENT_PATH = ROOT / "contracts" / "agentcore-project-enrollment.json"
RENDERER_PATH = ROOT / "scripts" / "bifrost" / "render_bifrost_config.py"

EXPECTED_SERVER_IDS = {
    "arabold-docs",
    "context7",
    "mcp-prompt-optimizer",
    "morph-mcp",
    "playwright",
    "sequential-thinking",
    "skills-hub",
}
FORBIDDEN_SERVER_IDS = {
    "agentcore-memory",
    "agentcore-project-router",
    "cursor-agent-mcp",
    "openrouter",
}
FORBIDDEN_PATHS = {
    r"C:\Users\ynotf\.raven",
    r"C:\Users\ynotf\.dsh",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_renderer():
    spec = importlib.util.spec_from_file_location("render_bifrost_config", RENDERER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_raven_project_is_exact_d_raven_only() -> None:
    enrollment = load_json(ENROLLMENT_PATH)
    raven = next(item for item in enrollment["projects"] if item["project_key"] == "raven")
    assert raven["paths"] == [r"D:\raven"]
    dumped = json.dumps(enrollment)
    for forbidden in FORBIDDEN_PATHS:
        assert forbidden not in dumped


def test_raven_profile_has_exact_server_set_and_reciprocal_membership() -> None:
    registry = load_json(REGISTRY_PATH)
    profile = registry["capability_profiles"]["raven"]

    assert set(profile["allowed_server_ids"]) == EXPECTED_SERVER_IDS
    assert FORBIDDEN_SERVER_IDS.isdisjoint(profile["allowed_server_ids"])
    for server_id in EXPECTED_SERVER_IDS:
        server = registry["servers"][server_id]
        assert server["enabled"] is True
        assert "raven" in server["capability_profiles"]
    assert "raven" not in registry["servers"]["agentcore-memory"]["capability_profiles"]


def test_raven_virtual_key_is_deterministic_and_uses_only_env_reference() -> None:
    renderer = load_renderer()
    registry = load_json(REGISTRY_PATH)

    first = renderer.build_virtual_keys(registry)
    second = renderer.build_virtual_keys(registry)
    assert first == second

    raven = next(item for item in first if item["id"] == "vk-agentcore-raven")
    assert raven == {
        "id": "vk-agentcore-raven",
        "name": "raven",
        "value": "env.BIFROST_MCP_VK_RAVEN",
        "is_active": True,
        "mcp_configs": renderer.profile_mcp_configs(registry, "raven"),
    }
    assert "provider_configs" not in raven
    assert {item["mcp_client_name"] for item in raven["mcp_configs"]} == {
        registry["servers"][server_id]["bifrost_client_name"]
        for server_id in EXPECTED_SERVER_IDS
    }


def test_raven_client_hint_is_env_header_pending_schema() -> None:
    gateway = load_json(GATEWAY_PATH)
    hint = gateway["client_render_hints"]["raven"]

    assert hint["enabled"] is True
    assert hint["config_path"] == "not_applicable_raven_mcp_schema_pending_install"
    assert hint["syntax"] == "raven_pending"
    assert hint["supports_env_headers"] is True
    assert hint["gateway_url"] == "http://127.0.0.1:8080/mcp"
    assert hint["gateway_auth_mode"] == "bearer_env"
    body = json.dumps(hint)
    assert "BIFROST_MCP_VK_RAVEN" in body
    assert "Bearer sk-" not in body
    assert "Trust Class A" in body
    assert json.dumps(r"I:\LocalApps\Raven")[1:-1] in body
    assert json.dumps(r"C:\Users\ynotf\.raven")[1:-1] in body
    dumped = json.dumps(gateway)
    assert "BIFROST_MCP_VK_RAVEN" in dumped
    assert "sk-b" not in dumped


def test_raven_is_not_trust_class_a() -> None:
    gateway = load_json(GATEWAY_PATH)
    hint = gateway["client_render_hints"]["raven"]
    assert hint.get("gateway_auth_mode") != "process_attested_proxy"
    assert hint.get("gateway_url") != "http://127.0.0.1:18082/mcp"


if __name__ == "__main__":
    test_raven_project_is_exact_d_raven_only()
    test_raven_profile_has_exact_server_set_and_reciprocal_membership()
    test_raven_virtual_key_is_deterministic_and_uses_only_env_reference()
    test_raven_client_hint_is_env_header_pending_schema()
    test_raven_is_not_trust_class_a()
    print("test_raven_bifrost_profile: PASS")
