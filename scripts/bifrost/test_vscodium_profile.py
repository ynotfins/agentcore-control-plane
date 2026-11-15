from __future__ import annotations

import json
import re
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
PROFILE = REPO / "ide-profiles" / "vscodium"
RENDERER = REPO / "renderers" / "gateway-clients" / "vscodium.json"
CONTRACT = REPO / "contracts" / "agentcore-gateway-client.json"
MATRIX = REPO / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"
README = REPO / "ide-profiles" / "README.md"

EXPECTED_URL = "http://127.0.0.1:8080/mcp"
EXPECTED_AUTH = "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
NATIVE_PATH = r"I:\LocalApps\VSCodium\user-data\User\mcp.json"
ZOO_PATH = r"I:\LocalApps\VSCodium\user-data\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json"
SECRETISH = re.compile(r"(sk-bf-|sk-or-|ghp_|github_pat_|xai-|Bearer [A-Za-z0-9]{16,})")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _gateway_entry(doc: dict) -> dict:
    servers = doc.get("mcpServers") or {}
    assert "agentcore-gateway" in servers, "missing agentcore-gateway entry"
    extra_agentcore = [name for name in servers if name != "agentcore-gateway" and "agentcore" in name.lower()]
    assert extra_agentcore == [], extra_agentcore
    return servers["agentcore-gateway"]


def test_vscodium_profile_paths_and_schema() -> None:
    profile = yaml.safe_load((PROFILE / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
    assert profile["ide_id"] == "vscodium"
    assert profile["swarm_managed"] is False
    assert profile["live_mcp_config_target"] == NATIVE_PATH
    assert ZOO_PATH not in profile.get("live_alternate_mcp_targets", [])  # moved to zoo-code-vscodium
    assert profile["mcp_schema"] == "vscodium_mcp_json"
    assert profile["mcp_transport"] == "http/streamable"
    assert "${env:VAR}" in profile["env_var_handling"]
    assert profile["editability"]["mcp_config"] == "direct_write"
    assert profile["m8_enrollment"] != "live_validated"


def test_vscodium_templates_use_env_backed_direct_gateway() -> None:
    for path in (RENDERER, PROFILE / "MCP_CONFIG_TEMPLATE.json"):
        doc = _load_json(path)
        entry = _gateway_entry(doc)
        assert entry["type"] in {"http", "streamable-http"}
        assert entry["url"] == EXPECTED_URL
        assert entry["headers"]["Authorization"] == EXPECTED_AUTH
        assert entry["timeout"] == 300
        raw = path.read_text(encoding="utf-8")
        assert SECRETISH.search(raw) is None
        assert "18082" not in raw


def test_vscodium_matrix_and_readme_enrollment() -> None:
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    entry = matrix["managed_ides"]["vscodium"]
    assert entry["mcp_schema"] == "vscodium_mcp_json"
    assert entry["env_var_handling"] == "env-headers-supported"
    assert entry["m8_enrollment"] == "configured_restart_required"
    assert entry["editability"]["mcp_config"] == "direct_write"
    readme = README.read_text(encoding="utf-8")
    assert "| vscodium |" in readme


def test_vscodium_install_docs_are_client_local() -> None:
    install = (PROFILE / "INSTALL_OR_UPDATE.md").read_text(encoding="utf-8")
    for phrase in (
        "may inspect and modify only its own live",
        "Configuration examples for other IDEs are reference material only",
        "Do not inspect, back up, repair, restart, validate, or modify another IDE",
        "Cross-IDE reconciliation is a separate AgentCore control-plane task",
    ):
        assert phrase in install
    assert NATIVE_PATH in install
    assert r"C:\Users\ynotf\.cursor\mcp.json" not in install


def test_vscodium_contract_hint_is_proposed_not_required() -> None:
    """The gateway client contract is governed_mutable; this PR proposes the hint.

    If the hint is later admitted, it must match the VSCodium env-backed :8080 route.
    """
    contract = _load_json(CONTRACT)
    hints = contract.get("client_render_hints") or {}
    if "vscodium" not in hints:
        return
    hint = hints["vscodium"]
    assert hint["enabled"] is True
    assert hint["supports_env_headers"] is True
    assert hint["config_path"] == NATIVE_PATH
    assert hint.get("gateway_url", EXPECTED_URL) == EXPECTED_URL
    assert hint.get("gateway_auth_mode") == "bearer_env"
