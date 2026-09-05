from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Get-AgentCoreBifrostFeatureAdoption.ps1"
FAKE_OPENROUTER_SECRET = "sk-" + "or-test-secret-value"
FAKE_VK_SECRET = "vk-" + "secret-test-value"
FAKE_ENV_REFERENCE = "env" + ".OPENAI_API_KEY"
FAKE_PROVIDER_KEY_ID = "secret" + "-key-id"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run_reporter(*args: str) -> dict:
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _base_config() -> dict:
    return {
        "version": 2,
        "client": {
            "enforce_auth_on_inference": True,
            "mcp_disable_auto_tool_inject": True,
        },
        "providers": {
            "openai": {"keys": [{"name": "openai-primary", "value": FAKE_ENV_REFERENCE}]},
            "openrouter": {"keys": [{"name": "openrouter-primary", "value": FAKE_OPENROUTER_SECRET}]},
        },
        "mcp": {
            "client_configs": [
                {"name": "agentcore_memory", "tools_to_execute": ["startup_context"]},
                {"name": "skills_hub", "tools_to_execute": ["listSkills"]},
            ],
            "tool_manager_config": {"disable_auto_tool_inject": True},
        },
        "governance": {
            "virtual_keys": [
                {
                    "id": "vk-agentcore-builder",
                    "name": "builder",
                    "value": FAKE_VK_SECRET,
                    "is_active": True,
                    "provider_configs": [{"provider": "openai", "key_ids": [FAKE_PROVIDER_KEY_ID]}],
                    "mcp_configs": [
                        {
                            "mcp_client": {"name": "agentcore_memory"},
                            "tools_to_execute": ["startup_context", "retrieve_context"],
                        }
                    ],
                }
            ]
        },
        "plugins": [
            {
                "enabled": True,
                "name": "semantic_cache",
                "config": {
                    "dimension": 1,
                    "ttl": "30m",
                    "cache_by_model": True,
                    "cache_by_provider": True,
                    "default_cache_key": "agentcore-global",
                },
            }
        ],
    }


def _fixture_args(tmp_path: Path, config: dict | None = None) -> list[str]:
    config_path = _write_json(tmp_path / "config.json", config or _base_config())
    return [
        "-TestMode",
        "-RuntimeRoot",
        str(tmp_path),
        "-TestHealthPath",
        str(_write_json(tmp_path / "health.json", {"status": "ok"})),
        "-TestVersionPath",
        str(_write_json(tmp_path / "version.json", {"version": "v2.0.0"})),
        "-TestConfigPath",
        str(_write_json(tmp_path / "api_config.json", {"config": config or _base_config()})),
        "-TestPluginsPath",
        str(
            _write_json(
                tmp_path / "plugins.json",
                {
                    "plugins": [
                        {"name": "semantic_cache", "enabled": True, "status": {"status": "ok"}}
                    ]
                },
            )
        ),
        "-TestVirtualKeysPath",
        str(_write_json(tmp_path / "virtual_keys.json", {"virtual_keys": _base_config()["governance"]["virtual_keys"]})),
        "-TestRoutingRulesPath",
        str(_write_json(tmp_path / "routing_rules.json", {"routing_rules": []})),
        "-TestSkillsPath",
        str(_write_json(tmp_path / "skills.json", {"repositories": []})),
        "-TestProvidersPath",
        str(_write_json(tmp_path / "providers.json", {"providers": [{"name": "openai"}, {"name": "openrouter"}]})),
        "-TestLogsPath",
        str(_write_json(tmp_path / "logs.json", {"total_requests": 0, "logs": []})),
    ]


def test_feature_adoption_reporter_script_exists_and_parses() -> None:
    assert SCRIPT.is_file()
    command = (
        "$errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{SCRIPT}', [ref]$null, [ref]$errors) | Out-Null; "
        "if ($errors.Count) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }"
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_feature_adoption_reporter_does_not_emit_secret_like_values(tmp_path: Path) -> None:
    args = _fixture_args(tmp_path)
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    forbidden = [
        FAKE_OPENROUTER_SECRET,
        FAKE_VK_SECRET,
        FAKE_ENV_REFERENCE,
        FAKE_PROVIDER_KEY_ID,
    ]
    for pattern in forbidden:
        assert re.search(pattern, result.stdout) is None
    report = json.loads(result.stdout)
    assert report["virtual_key_names"] == ["builder"]
    assert report["virtual_key_mcp_config_summary"][0]["mcp_client_names"] == ["agentcore_memory"]


def test_empty_skills_routing_and_logs_classify_as_not_adopted(tmp_path: Path) -> None:
    report = _run_reporter(*_fixture_args(tmp_path))

    assert report["routing_rule_count"] == 0
    assert report["routing_rules_adopted"] is False
    assert report["skills_repository_count"] == 0
    assert report["skills_repository_adopted"] is False
    assert report["logs_total_requests"] == 0
    assert report["inference_traffic_observed"] is False


def test_semantic_cache_active_is_detected(tmp_path: Path) -> None:
    report = _run_reporter(*_fixture_args(tmp_path))

    assert report["semantic_cache"]["active"] is True
    assert report["semantic_cache"]["configured"] is True
    assert report["semantic_cache"]["config_summary"]["dimension"] == 1


def test_no_admin_api_path_reports_admin_unavailable(tmp_path: Path) -> None:
    _write_json(tmp_path / "config.json", _base_config())
    report = _run_reporter(
        "-TestMode",
        "-NoAdminApi",
        "-RuntimeRoot",
        str(tmp_path),
        "-TestHealthPath",
        str(_write_json(tmp_path / "health.json", {"status": "ok"})),
    )

    assert report["admin_api_available"] is False
    assert report["admin_api_skipped"] is True
    assert report["provider_names"] == ["openai", "openrouter"]


def test_enterprise_only_features_not_enabled_from_oss_config(tmp_path: Path) -> None:
    config = _base_config()
    config["plugins"] = [{"enabled": True, "name": "semantic_cache", "config": {"dimension": 1}}]
    report = _run_reporter(*_fixture_args(tmp_path, config=config))

    assert set(report["enterprise_only_not_enabled"]) == {
        "guardrails",
        "secret_management",
        "edge",
        "alerting",
    }
    assert "guardrails" not in report["plugin_names"]
