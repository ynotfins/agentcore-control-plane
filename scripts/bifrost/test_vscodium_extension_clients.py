"""Enrollment checks for VSCodium-hosted extension clients: Continue, Cline, Zoo Code (VSCodium).

Trust Class A for these clients is requested by the operator but lives in the governed_mutable
contracts/global-agent-policy.yaml, so this test only requires the proposal to exist and the
profiles to report the pending state honestly. If the policy is later amended, the test also
accepts the admitted state.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
MATRIX = REPO / "ide-profiles" / "IDE_CAPABILITY_MATRIX.yaml"
README = REPO / "ide-profiles" / "README.md"
POLICY = REPO / "contracts" / "global-agent-policy.yaml"
PROPOSAL = REPO / "governance" / "proposals" / "2026-11-15-continue-cline-zoo-trust-class-a.md"
EXPECTED_URL = "http://127.0.0.1:8080/mcp"
SECRETISH = re.compile(r"(sk-bf-|sk-or-|ghp_|github_pat_|xai-|Bearer [A-Za-z0-9]{16,})")

CLIENTS = {
    "continue": {
        "path": r"C:\Users\ynotf\.continue\config.yaml",
        "schema": "continue_config_yaml",
        "auth": "Bearer ${{ secrets.BIFROST_MCP_VK_APP_CONTINUE }}",
        "type": "streamable-http",
    },
    "cline": {
        "path": r"C:\Users\ynotf\.cline\data\settings\cline_mcp_settings.json",
        "schema": "cline_mcp_json",
        "auth": "Bearer ${env:BIFROST_MCP_VK_APP_CLINE}",
        "type": "streamableHttp",
    },
    "zoo-code-vscodium": {
        "path": r"I:\LocalApps\VSCodium\user-data\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json",
        "schema": "zoo_code_mcp_json",
        "auth": "Bearer ${env:BIFROST_MCP_VK_APP_ZOO_CODE}",
        "type": "streamable-http",
    },
}


def _gateway_entries(doc: dict) -> list[dict]:
    servers = doc.get("mcpServers")
    if isinstance(servers, list):  # Continue config.yaml shape
        named = {s["name"]: s for s in servers}
    else:
        named = dict(servers or {})
    agentcore = [n for n in named if "agentcore" in n.lower()]
    assert agentcore == ["agentcore-gateway"], agentcore
    return [named["agentcore-gateway"]]


def test_profiles_exist_and_match_live_targets() -> None:
    for cid, spec in CLIENTS.items():
        d = REPO / "ide-profiles" / cid
        for name in ("IDE_PROFILE.yaml", "GLOBAL_RULES.md", "INSTALL_OR_UPDATE.md", "VALIDATION.md", "MCP_CONFIG_TEMPLATE.json"):
            assert (d / name).is_file(), f"{cid}/{name}"
        profile = yaml.safe_load((d / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
        assert profile["ide_id"] == cid
        assert profile["swarm_managed"] is False
        assert profile["host_application"] == "vscodium"
        assert profile["live_mcp_config_target"] == spec["path"]
        assert profile["mcp_schema"] == spec["schema"]
        assert profile["editability"]["mcp_config"] == "direct_write"
        assert profile["m8_enrollment"] != "live_validated"
        assert profile["requested_trust_class"] == "A"


def test_renderers_and_templates_are_env_backed() -> None:
    for cid, spec in CLIENTS.items():
        for path in (REPO / "renderers" / "gateway-clients" / f"{cid}.json", REPO / "ide-profiles" / cid / "MCP_CONFIG_TEMPLATE.json"):
            raw = path.read_text(encoding="utf-8")
            assert SECRETISH.search(raw) is None, path
            assert "18082" not in raw
            for entry in _gateway_entries(json.loads(raw)):
                assert entry["url"] == EXPECTED_URL
                assert entry["type"] == spec["type"]
                headers = entry.get("headers") or (entry.get("requestOptions") or {}).get("headers")
                assert headers["Authorization"] == spec["auth"]


def test_matrix_and_readme() -> None:
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8"))
    readme = README.read_text(encoding="utf-8")
    for cid in CLIENTS:
        entry = matrix["managed_ides"][cid]
        assert entry["m8_enrollment"] == "configured_restart_required"
        assert entry["requested_trust_class"] == "A"
        assert f"| {cid} |" in readme


def test_trust_class_a_is_proposed_or_admitted() -> None:
    policy = POLICY.read_text(encoding="utf-8")
    rule = next(r for r in yaml.safe_load(policy)["mandatory_rules"] if r["id"] == "client-trust-classes")["rule"]
    admitted = all(name in rule for name in ("Continue", "Cline")) and "Zoo Code" in rule
    if admitted:
        return
    assert PROPOSAL.is_file()
    text = PROPOSAL.read_text(encoding="utf-8")
    for needle in ("client-trust-classes", "Continue", "Cline", "Zoo Code", "client_render_hints"):
        assert needle in text
    for cid in CLIENTS:
        profile = yaml.safe_load((REPO / "ide-profiles" / cid / "IDE_PROFILE.yaml").read_text(encoding="utf-8"))
        assert profile["effective_trust_class"] == "pending_authority_admission"


def test_install_docs_are_client_local() -> None:
    for cid, spec in CLIENTS.items():
        install = (REPO / "ide-profiles" / cid / "INSTALL_OR_UPDATE.md").read_text(encoding="utf-8")
        assert "Do not inspect, back up, repair, restart, validate, or modify another IDE" in install
        assert spec["path"] in install
        for other, ospec in CLIENTS.items():
            if other != cid:
                assert ospec["path"] not in install