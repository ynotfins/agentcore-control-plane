from __future__ import annotations

import importlib.util
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

    assert verifier.main() == 1
