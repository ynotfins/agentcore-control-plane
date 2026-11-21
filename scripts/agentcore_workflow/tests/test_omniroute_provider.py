"""OmniRoute provider path for the M6 workflow (AUTH-2026-11-20-AGENT-DISPATCH-LIVE)."""

import os

import pytest

from agentcore_workflow import deepagents_worker as dw


def test_default_worker_model_is_omniroute():
    assert dw.DEFAULT_WORKER_MODEL_SPEC == "omniroute:deepseek-v4-pro"


def test_omniroute_spec_builds_openai_compatible_client():
    pytest.importorskip("langchain_openai")
    model = dw._resolve_model("omniroute:deepseek-v4-pro")
    assert type(model).__name__ == "ChatOpenAI"
    assert str(model.openai_api_base).rstrip("/") == dw.OMNIROUTE_API_V1.rstrip("/")
    assert model.model_name == "deepseek-v4-pro"


def test_omniroute_base_url_is_loopback_by_default(monkeypatch):
    assert dw.OMNIROUTE_API_V1.startswith("http://127.0.0.1:20128")


def test_omniroute_requires_model_id():
    with pytest.raises(ValueError):
        dw._resolve_model("omniroute:")


def test_openrouter_remains_explicit_opt_in():
    pytest.importorskip("langchain_openrouter")
    model = dw._resolve_model("openrouter:deepseek/deepseek-v4-pro")
    assert type(model).__name__ == "ChatOpenRouter"
    base = getattr(model, "openrouter_api_base", None) or getattr(model, "openai_api_base", "")
    assert "openrouter.ai" in str(base)


def test_unknown_spec_passes_through():
    assert dw._resolve_model("plain-string-model") == "plain-string-model"


def test_api_key_default_is_loopback_placeholder(monkeypatch):
    pytest.importorskip("langchain_openai")
    monkeypatch.delenv("OMNIROUTE_API_KEY", raising=False)
    model = dw._resolve_model("omniroute:deepseek-v4-pro")
    assert model.openai_api_key.get_secret_value() == "omniroute-loopback"
