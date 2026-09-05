from __future__ import annotations

import copy
import json
from pathlib import Path

import render_bifrost_config as renderer
import validate_output_schemas as validator


def _expected() -> tuple[dict, dict]:
    registry = validator.load(validator.REGISTRY)
    gateway_client = validator.load(validator.GATEWAY_CLIENT)
    wiring = renderer.OutputSchemaWiring(registry)
    runtime = renderer.build_bifrost_config(registry, gateway_client, None, wiring)
    return registry, renderer.build_sanitized_sidecar(
        registry,
        runtime,
        oauth_state_present=False,
        output_schema=wiring,
    )


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _openrouter_client(config: dict) -> dict:
    return next(
        client
        for client in config["mcp"]["client_configs"]
        if client["name"] == "openrouter"
    )


def _has_key(payload: object, key: str) -> bool:
    if isinstance(payload, dict):
        return key in payload or any(_has_key(value, key) for value in payload.values())
    if isinstance(payload, list):
        return any(_has_key(value, key) for value in payload)
    return False


def test_oauth_runtime_state_never_renders_oauth_config_id() -> None:
    registry = validator.load(validator.REGISTRY)
    gateway_client = validator.load(validator.GATEWAY_CLIENT)
    wiring = renderer.OutputSchemaWiring(registry)
    config = renderer.build_bifrost_config(
        registry,
        gateway_client,
        {"openrouter": {"oauth_config_id": "ocfg_fake_runtime_id", "mcp_client_id": "mcp_fake_id"}},
        wiring,
    )
    openrouter = _openrouter_client(config)
    sanitized = renderer.build_sanitized_sidecar(
        registry,
        config,
        oauth_state_present=True,
        output_schema=wiring,
    )

    assert not _has_key(config["mcp"]["client_configs"], "oauth_config_id")
    assert not _has_key(sanitized["mcp"]["client_configs"], "oauth_config_id")
    assert openrouter["oauth_config"] == {
        "server_url": "https://openrouter.ai",
        "scopes": ["mcp"],
    }


def test_gate_rendered_accepts_complete_renderer_output(tmp_path, monkeypatch) -> None:
    registry, expected = _expected()
    target = tmp_path / "config.sanitized.json"
    _write(target, expected)
    monkeypatch.setattr(validator, "RENDERED_SANITIZED", target)

    errors: list[str] = []
    validator.gate_rendered(registry, errors, [])

    assert errors == []


def test_gate_rendered_rejects_non_launch_client_drift(tmp_path, monkeypatch) -> None:
    registry, expected = _expected()
    stale = copy.deepcopy(expected)
    stale["mcp"]["client_configs"][0]["tools_to_execute"] = ["memory_status"]
    target = tmp_path / "config.sanitized.json"
    _write(target, stale)
    monkeypatch.setattr(validator, "RENDERED_SANITIZED", target)

    errors: list[str] = []
    validator.gate_rendered(registry, errors, [])

    assert len(errors) == 1
    assert "complete non-secret config" in errors[0]


def test_gate_rendered_rejects_governance_drift(tmp_path, monkeypatch) -> None:
    registry, expected = _expected()
    stale = copy.deepcopy(expected)
    stale["governance"]["virtual_keys"][0]["mcp_configs"] = []
    target = tmp_path / "config.sanitized.json"
    _write(target, stale)
    monkeypatch.setattr(validator, "RENDERED_SANITIZED", target)

    errors: list[str] = []
    validator.gate_rendered(registry, errors, [])

    assert len(errors) == 1
    assert "complete non-secret config" in errors[0]
