from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_verifier():
    path = Path(__file__).with_name("verify_chatgpt_profile.py")
    spec = importlib.util.spec_from_file_location("verify_chatgpt_profile_contract", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_chatgpt_profile_is_exactly_the_current_18_tool_surface() -> None:
    verifier = _load_verifier()
    tools = verifier.EXPECTED_APPROVED_TOOLS
    assert len(tools) == 18
    assert not any(name.startswith("agentcore_project_router-") for name in tools)
    assert sum(name.startswith("agentcore_memory-") for name in tools) == 9


def test_verifier_returns_failure_when_any_required_layer_fails(monkeypatch) -> None:
    verifier = _load_verifier()
    monkeypatch.setattr(verifier, "get_chatgpt_vk", lambda: "test-key")
    health_results = iter([(True, "ok"), (False, "proxy down")])
    monkeypatch.setattr(verifier, "check_health", lambda *_args, **_kwargs: next(health_results))
    monkeypatch.setattr(verifier, "check_profile_config", lambda: (True, {}, []))
    tool_results = iter([(True, [], []), (False, [], ["proxy down"])])
    monkeypatch.setattr(verifier, "test_mcp_tools_list", lambda *_args: next(tool_results))
    monkeypatch.setattr(verifier, "test_proxy_deny_paths", lambda: (False, ["proxy down"]))
    monkeypatch.setattr(verifier, "run_contract_validator", lambda: (True, "exit=0"))

    assert verifier.main() == 1


def test_profile_rejects_router_client_even_when_tool_list_is_empty(tmp_path, monkeypatch) -> None:
    verifier = _load_verifier()
    config = {
        "governance": {
            "virtual_keys": [
                {
                    "id": "vk-agentcore-chatgpt",
                    "mcp_configs": [
                        {"mcp_client_name": "agentcore_memory", "tools_to_execute": sorted(name.split("-", 1)[1] for name in verifier.EXPECTED_APPROVED_TOOLS if name.startswith("agentcore_memory-"))},
                        {"mcp_client_name": "agentcore_project_router", "tools_to_execute": []},
                        {"mcp_client_name": "skills_hub", "tools_to_execute": sorted(name.split("-", 1)[1] for name in verifier.EXPECTED_APPROVED_TOOLS if name.startswith("skills_hub-"))},
                        {"mcp_client_name": "arabold_docs", "tools_to_execute": sorted(name.split("-", 1)[1] for name in verifier.EXPECTED_APPROVED_TOOLS if name.startswith("arabold_docs-"))},
                        {"mcp_client_name": "sequential_thinking", "tools_to_execute": sorted(name.split("-", 1)[1] for name in verifier.EXPECTED_APPROVED_TOOLS if name.startswith("sequential_thinking-"))},
                    ],
                }
            ]
        }
    }
    runtime_config = tmp_path / "config.json"
    runtime_config.write_text(json.dumps(config), encoding="utf-8")
    monkeypatch.setattr(verifier, "RUNTIME_CONFIG", runtime_config)

    ok, _profile, errors = verifier.check_profile_config()

    assert not ok
    assert any("agentcore_project_router must be absent" in error for error in errors)
