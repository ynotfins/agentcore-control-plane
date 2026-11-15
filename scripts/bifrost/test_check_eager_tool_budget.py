"""Unit tests for check_eager_tool_budget (no network)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ceb", Path(__file__).with_name("check_eager_tool_budget.py"))
ceb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ceb)


def test_config_flags_eager_non_essential():
    cfg = {"mcp": {"client_configs": [
        {"name": "agentcore_memory", "tools_to_execute": ["a"] * 10},
        {"name": "eye2byte", "is_code_mode_client": False, "tools_to_execute": ["x"] * 62},
        {"name": "serena", "is_code_mode_client": True},
    ]}}
    v = ceb.config_violations(cfg, ceb.ESSENTIAL_EAGER)
    assert len(v) == 1 and "eye2byte" in v[0]


def test_registry_flags_missing_code_mode():
    reg = {"servers": {
        "depwire": {"enabled": True, "bifrost_client_name": "depwire"},
        "tentra": {"enabled": True, "bifrost_client_name": "tentra", "is_code_mode_client": True},
        "context-fabric": {"enabled": False},
        "sequential-thinking": {"enabled": True, "bifrost_client_name": "sequential_thinking"},
    }}
    v = ceb.registry_violations(reg, ceb.ESSENTIAL_EAGER)
    assert v == ["registry:depwire enabled but is_code_mode_client=None"]


def test_clean_config_passes():
    cfg = {"mcp": {"client_configs": [{"name": "github_mcp", "is_code_mode_client": True}]}}
    assert ceb.config_violations(cfg, ceb.ESSENTIAL_EAGER) == []
