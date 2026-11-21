from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_openclaw_profile_is_source_ready_and_not_live_certified() -> None:
    profile = yaml.safe_load(
        (ROOT / "ide-profiles/openclaw/IDE_PROFILE.yaml").read_text(encoding="utf-8")
    )
    assert profile["ownership"] == "agentcore"
    assert profile["installed_version"] == "2026.6.10"
    assert profile["certification"] == "source_ready"
    assert profile["live_state_root"] == r"C:\Users\ynotf\.openclaw"
    assert all(
        details["status"] != "live_validated"
        for details in profile["dimensions"].values()
    )


def test_openclaw_template_has_one_gateway_and_no_forbidden_routes() -> None:
    template = json.loads(
        (ROOT / "ide-profiles/openclaw/MCP_CONFIG_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )
    servers = template["mcp"]["servers"]
    assert list(servers) == ["agentcore-gateway"]
    gateway = servers["agentcore-gateway"]
    assert gateway["url"] == "http://127.0.0.1:8080/mcp"
    assert gateway["transport"] == "streamable-http"
    assert gateway["headers"]["Authorization"] == "Bearer ${BIFROST_MCP_VK_OPENCLAW}"
    body = json.dumps(template).lower()
    for forbidden in ("swarmrecall", "swarmvault", "postgres", "filesystem"):
        assert forbidden not in body


def test_openclaw_renderer_is_sanitized_and_matches_template() -> None:
    template = json.loads(
        (ROOT / "ide-profiles/openclaw/MCP_CONFIG_TEMPLATE.json").read_text(
            encoding="utf-8"
        )
    )
    renderer = json.loads(
        (ROOT / "renderers/gateway-clients/openclaw.json").read_text(
            encoding="utf-8"
        )
    )
    assert renderer["merge"] == template
    assert renderer["status"] == "source_ready_live_unverified"
    assert "${BIFROST_MCP_VK_OPENCLAW}" in json.dumps(renderer)
