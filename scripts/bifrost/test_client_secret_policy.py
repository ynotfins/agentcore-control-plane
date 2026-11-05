from __future__ import annotations

import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]
UNSUPPORTED = (
    "claude-desktop",
    "cherry-studio",
    "zoo-code",
    "minimax-classic",
)
TRUST_A_MANAGED_IDES = (
    "zed",
    "eigent",
)
TRUST_A_PROCESS_ATTESTED = TRUST_A_MANAGED_IDES + ("opencode",)
RENDERER_CONTAINERS = {
    "zed": "context_servers",
    "eigent": "mcpServers",
    "claude-desktop": "mcpServers",
    "cherry-studio": "mcpServers",
    "zoo-code": "mcpServers",
}
FORBIDDEN_CREDENTIAL_TOKENS = (
    "BIFROST_MCP_VIRTUAL_KEY",
    "Bearer ${env:",
    "http://127.0.0.1:8080/mcp",
    '"Authorization"',
    "sk-bf-",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_header_hostile_contract_hints_fail_closed() -> None:
    contract = load_json(REPO / "contracts/agentcore-gateway-client.json")
    for client in UNSUPPORTED:
        hint = contract["client_render_hints"][client]
        assert hint["enabled"] is False
        assert hint["supports_env_headers"] is False
        assert hint["gateway_auth_mode"] == "unverified"
        assert "gateway_url" not in hint
        combined = " ".join(hint["notes"]).lower()
        assert "never paste or persist" in combined
        assert "legacy drift" in combined or client == "minimax-classic"


def test_trust_a_contract_hints_are_process_attested() -> None:
    contract = load_json(REPO / "contracts/agentcore-gateway-client.json")
    for client in TRUST_A_PROCESS_ATTESTED:
        hint = contract["client_render_hints"][client]
        assert hint["enabled"] is True
        assert hint["supports_env_headers"] is False
        assert hint["gateway_auth_mode"] == "process_attested_proxy"
        assert hint["gateway_url"] == "http://127.0.0.1:18082/mcp"
        combined = " ".join(hint["notes"]).lower()
        assert "legacy drift" in combined or ":18082" in combined
        assert (
            "virtual key" in combined
            or "never paste or persist" in combined
            or "headerless" in combined
        )


def test_profiles_and_matrix_report_unsupported_without_losing_history() -> None:
    matrix = yaml.safe_load((REPO / "ide-profiles/IDE_CAPABILITY_MATRIX.yaml").read_text(encoding="utf-8"))
    for client in UNSUPPORTED:
        profile = yaml.safe_load((REPO / "ide-profiles" / client / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
        entry = matrix["managed_ides"][client]
        for record in (profile, entry):
            assert record["m8_enrollment"] == "unsupported_with_reason"
            assert record["editability"]["mcp_config"] == "unsupported"
            assert record["legacy_gateway_state"]["classification"] == "legacy_drift"
            assert record["legacy_gateway_state"]["mutation_in_this_task"] is False
            assert record["legacy_gateway_state"]["evidence_paths"]
        assert profile["dimensions"] == entry["dimensions"]
        assert entry["legacy_m8_notes"]

    assert matrix["managed_candidates"]["opencode"]["certification"] == "configured_restart_required"
    assert matrix["managed_candidates"]["opencode"]["gateway_auth_mode"] == "process_attested_proxy"


def test_profiles_and_matrix_report_trust_a_enrollment() -> None:
    matrix = yaml.safe_load((REPO / "ide-profiles/IDE_CAPABILITY_MATRIX.yaml").read_text(encoding="utf-8"))
    for client in TRUST_A_MANAGED_IDES:
        profile = yaml.safe_load((REPO / "ide-profiles" / client / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
        entry = matrix["managed_ides"][client]
        for record in (profile, entry):
            assert record["m8_enrollment"] == "configured_restart_required"
            assert record["editability"]["mcp_config"] == "direct_write"
            assert record["legacy_gateway_state"]["classification"] == "legacy_drift"
            assert record["legacy_gateway_state"]["evidence_paths"]
        assert profile["dimensions"] == entry["dimensions"]
        assert profile["gateway_url"] == "http://127.0.0.1:18082/mcp"
        assert profile["gateway_auth_mode"] == "process_attested_proxy"
        assert entry["gateway_url"] == "http://127.0.0.1:18082/mcp"
        assert entry["gateway_auth_mode"] == "process_attested_proxy"

    profile = yaml.safe_load((REPO / "ide-profiles/opencode/IDE_PROFILE.yaml").read_text(encoding="utf-8"))
    assert profile["m8_enrollment"] == "configured_restart_required"
    assert profile["editability"]["mcp_config"] == "direct_write"
    assert profile["gateway_url"] == "http://127.0.0.1:18082/mcp"
    assert profile["gateway_auth_mode"] == "process_attested_proxy"


def test_active_templates_contain_no_gateway_or_credential() -> None:
    for client in UNSUPPORTED:
        template = REPO / "ide-profiles" / client / "MCP_CONFIG_TEMPLATE.json"
        template_text = template.read_text(encoding="utf-8")
        data = json.loads(template_text)
        assert data["_agentcore"]["active_template"] is False
        assert data["_agentcore"]["gateway_enrollment_status"] == "unsupported_with_reason"
        for token in FORBIDDEN_CREDENTIAL_TOKENS:
            assert token not in template_text

        if client in RENDERER_CONTAINERS and client != "zoo-code":
            renderer = REPO / "renderers/gateway-clients" / f"{client}.json"
            renderer_text = renderer.read_text(encoding="utf-8")
            assert json.loads(renderer_text) == data
            assert data[RENDERER_CONTAINERS[client]] == {}
            for token in FORBIDDEN_CREDENTIAL_TOKENS:
                assert token not in renderer_text
        elif client == "zoo-code":
            renderer = load_json(REPO / "renderers/gateway-clients/zoo-code.json")
            assert renderer.get("mcpServers") == {}
            assert renderer["_agentcore"]["active_template"] is False


def test_trust_a_templates_are_headerless_18082() -> None:
    for client in TRUST_A_PROCESS_ATTESTED:
        template = REPO / "ide-profiles" / client / "MCP_CONFIG_TEMPLATE.json"
        renderer = REPO / "renderers/gateway-clients" / f"{client}.json"
        template_text = template.read_text(encoding="utf-8")
        renderer_text = renderer.read_text(encoding="utf-8")
        data = json.loads(template_text)
        assert json.loads(renderer_text) == data
        assert data["_agentcore"]["active_template"] is True
        assert data["_agentcore"]["gateway_enrollment_status"] == "process_attested_proxy"
        assert data["_agentcore"]["gateway_auth_mode"] == "process_attested_proxy"
        assert data["_agentcore"]["gateway_url"] == "http://127.0.0.1:18082/mcp"
        if client == "opencode":
            gateway = data["mcp"]["servers"]["agentcore-gateway"]
        else:
            gateway = data[RENDERER_CONTAINERS[client]]["agentcore-gateway"]
        assert gateway["url"] == "http://127.0.0.1:18082/mcp"
        assert "headers" not in gateway
        for token in ("sk-bf-", '"Authorization"', "Bearer ${env:"):
            assert token not in template_text
            assert token not in renderer_text


def test_ui_guidance_forbids_enrollment_and_secret_persistence() -> None:
    for client in ("cherry-studio", "minimax-classic"):
        text = (REPO / "ide-profiles" / client / "MCP_ENROLLMENT_UI.md").read_text(encoding="utf-8")
        lowered = text.lower()
        assert "unsupported/unverified" in lowered
        assert "do not" in lowered
        assert "paste or persist" in lowered
        assert "BIFROST_MCP_VIRTUAL_KEY" not in text


def test_direct_companion_policy_is_evidence_gated_not_zoo_code_only() -> None:
    matrix = yaml.safe_load(
        (REPO / "ide-profiles/IDE_CAPABILITY_MATRIX.yaml").read_text(encoding="utf-8")
    )
    policy = matrix["direct_mcp_companion_policy"]
    assert policy["status"] == "evidence_gated"
    requirements = " ".join(policy["requirements"]).lower()
    for required in (
        "documented bifrost parity failure",
        "exact host and tool scope",
        "security review",
        "rollback proof",
        "no duplication",
    ):
        assert required in requirements
    assert (
        policy["historical_approvals"]["zoo-code"]["status"]
        == "subject_to_current_policy"
    )

    sources = [
        REPO / "scripts/render_ide_rules.py",
        REPO / "renderers/gateway-clients/open-interpreter-cli.toml",
        REPO / "ide-profiles/open-interpreter/MCP_CONFIG_TEMPLATE.toml",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    for forbidden in (
        "The only allowed additional direct MCP entry is the Zoo-Code-owned companion",
        "may include exactly one additional Zoo-Code-owned direct MCP",
    ):
        assert forbidden not in combined
    for required in (
        "documented Bifrost parity failure",
        "exact host/tool scope",
        "security review",
        "rollback proof",
    ):
        assert required in combined
