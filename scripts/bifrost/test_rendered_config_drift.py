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
