from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "ops" / "bifrost" / "Reconcile-AgentCoreTrustAClients.ps1"
FAKE_KEY = "phase2-test-virtual-key-do-not-log"
GATEWAY_URL = "http://127.0.0.1:8080/mcp"
COMPAT_URL = "http://127.0.0.1:18082/mcp"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _fixture(root: Path) -> dict[str, Path]:
    paths = {
        "cursor": root / "cursor" / "mcp.json",
        "codex": root / "codex" / "config.toml",
        "devin": root / "devin" / "mcp_config.json",
        "antigravity_primary": root / "gemini" / "mcp_config.json",
        "antigravity_alternate": root / "antigravity" / "mcp.json",
        "zcode": root / "zcode" / "config.json",
        "minimax": root / "minimax" / "mcp.json",
        "eigent": root / "eigent" / "mcp.json",
        "zed": root / "zed" / "settings.json",
        "interpreter_desktop": root / "open-interpreter-desktop" / "config.json",
        "interpreter_cli": root / "open-interpreter-cli" / "config.toml",
    }
    _write_json(
        paths["cursor"],
        {
            "mcpServers": {
                "agentcore-gateway": {
                    "type": "streamable-http",
                    "url": GATEWAY_URL,
                    "headers": {
                        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
                    },
                    "timeout": 300,
                }
            }
        },
    )
    _write_text(
        paths["codex"],
        """model = "gpt-test"

[mcp_servers.node_repl]
command = "node_repl.exe"

[mcp_servers.agentcore-gateway]
url = "http://old.invalid/mcp"
bearer_token_env_var = "OLD_KEY"
startup_timeout_sec = 12

[mcp_servers.morph-mcp]
command = "npx"
args = ["-y", "@morphllm/morphmcp"]

[mcp_servers.morph-mcp.env]
MORPH_API_KEY = "preserve-by-removing-whole-section"

[mcp_servers.cheap-workers]
command = "node"
args = ["worker.mjs"]

[mcp_servers.devin]
url = "https://mcp.devin.ai/mcp"

[plugins.keep-me]
enabled = true
""",
    )
    _write_json(
        paths["devin"],
        {
            "mcpServers": {
                "agentcore-gateway": {
                    "url": GATEWAY_URL,
                    "headers": {"Authorization": "Bearer stale-key"},
                },
                "devin/github-mcp-server": {
                    "registry": "devin/github-mcp-server",
                    "url": "https://api.githubcopilot.com/mcp",
                },
                "devin/mcp-playwright": {
                    "registry": "devin/mcp-playwright",
                    "command": "npx",
                },
                "devin/vercel": {
                    "registry": "devin/vercel",
                    "url": "https://mcp.vercel.com",
                },
                "github-mcp-server": {"url": "https://api.githubcopilot.com/mcp"},
                "vercel": {"url": "https://mcp.vercel.com"},
            },
            "preserve": {"flag": True},
        },
    )
    for name in ("antigravity_primary", "antigravity_alternate"):
        payload = {
            "mcpServers": {
                "agentcore-gateway": {
                    "serverUrl": GATEWAY_URL,
                    "headers": {"Authorization": "Bearer stale-key"},
                },
                "plugin-extra": {"command": "plugin.exe", "args": ["serve"]},
            },
            "preserve": {"client": name},
        }
        _write_json(paths[name], payload)
    _write_json(
        paths["zcode"],
        {
            "plugins": {"enabledPlugins": {"computer-use": True}},
            "mcp": {
                "servers": {
                    **{name: {"type": "stdio", "command": "npx", "enabled": True}
                    for name in (
                        "sequential-thinking",
                        "arabold-docs",
                        "filesystem",
                        "playwright",
                        "github",
                        "memory",
                        "context7",
                    )},
                    "agentcore-gateway": {
                        "type": "http",
                        "url": GATEWAY_URL,
                        "timeoutMs": 300,
                        "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
                        "enabled": False,
                    },
                }
            },
            "hooks": {"enabled": True, "events": {"Stop": {"hooks": ["keep"]}}},
        },
    )
    _write_json(
        paths["minimax"],
        {
            "mcpServers": {
                "matrix": {"builtin": True},
                "cu": {"builtin": True},
                "trash": {"builtin": True},
                "agentcore-gateway": {
                    "type": "streamable-http",
                    "url": GATEWAY_URL,
                    "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
                    "timeout": 300,
                    "enabled": True,
                    "configured": True,
                },
            }
        },
    )
    _write_json(
        paths["eigent"],
        {
            "mcpServers": {
                "agentcore-gateway": {
                    "url": GATEWAY_URL,
                    "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
                }
            }
        },
    )
    _write_json(
        paths["zed"],
        {
            "context_servers": {
                "agentcore-gateway": {
                    "url": GATEWAY_URL,
                    "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
                }
            }
        },
    )
    _write_json(
        paths["interpreter_desktop"],
        {
            "configVersion": 11,
            "agents": {"preserve": {}},
            "mcpServers": {
                "agentcore-gateway": {
                    "type": "http",
                    "url": GATEWAY_URL,
                    "headers": {"Authorization": f"Bearer {FAKE_KEY}"},
                    "timeout": 300,
                }
            },
        },
    )
    _write_text(
        paths["interpreter_cli"],
        """model = "provider/model"

[model_providers.custom]
base_url = "https://provider.invalid/v1"

[permissions.operator.filesystem]
mode = "read-write"

[mcp_servers.agentcore-gateway]
url = "http://old.invalid/mcp"
bearer_token_env_var = "OLD_KEY"
enabled = false

[mcp_servers.agentcore-gateway.http_headers]
X-Preserve = "yes"

[mcp_servers.morph-mcp]
command = "npx"

[mcp_servers.openrouter]
command = "npx"

[mcp_servers.github]
url = "https://api.githubcopilot.com/mcp/"

[mcp_servers.github.http_headers]
Authorization = "Bearer secret-placeholder"

[interpreter_app]
default_profile_id = "keep"
""",
    )
    return paths


def _run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["BIFROST_MCP_VIRTUAL_KEY"] = FAKE_KEY
    return subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(SCRIPT),
            "-TestMode",
            "-FixtureRoot",
            str(root),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
        env=env,
    )


def _snapshot(paths: dict[str, Path]) -> dict[str, bytes]:
    return {name: path.read_bytes() for name, path in paths.items()}


def test_default_dry_run_makes_no_writes_and_emits_secret_safe_plan(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    before = _snapshot(paths)

    result = _run(tmp_path)

    assert result.returncode == 0, result.stderr
    assert _snapshot(paths) == before
    assert not list(tmp_path.rglob("*.phase2-*.bak"))
    assert FAKE_KEY not in result.stdout
    assert FAKE_KEY not in result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "DryRun"
    assert report["changed_count"] == 10
    assert {item["client"] for item in report["files"] if item["changed"]} == {
        "codex",
        "devin",
        "antigravity-primary",
        "antigravity-alternate",
        "zcode",
        "minimax",
        "eigent",
        "zed",
        "open-interpreter-desktop",
        "open-interpreter-cli",
    }


def test_explicit_dry_run_switch_is_supported(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    before = _snapshot(paths)

    result = _run(tmp_path, "-DryRun")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["mode"] == "DryRun"
    assert _snapshot(paths) == before


def test_apply_performs_exact_reconciliation_and_preserves_unrelated_state(
    tmp_path: Path,
) -> None:
    paths = _fixture(tmp_path)

    result = _run(tmp_path, "-Apply")

    assert result.returncode == 0, result.stderr
    assert FAKE_KEY not in result.stdout
    assert FAKE_KEY not in result.stderr
    report = json.loads(result.stdout)
    assert report["mode"] == "Apply"
    assert report["changed_count"] == 10
    assert len(list(tmp_path.rglob("*.phase2-*.bak"))) == 10

    codex = paths["codex"].read_text(encoding="utf-8")
    assert "[mcp_servers.node_repl]" in codex
    assert "[mcp_servers.cheap-workers]" in codex
    assert "[mcp_servers.devin]" in codex
    assert "[plugins.keep-me]" in codex
    assert "mcp_servers.morph-mcp" not in codex
    assert codex.count("[mcp_servers.agentcore-gateway]") == 1
    assert f'url = "{GATEWAY_URL}"' in codex
    assert 'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"' in codex
    assert "startup_timeout_sec = 300.0" in codex
    assert "tool_timeout_sec = 300.0" in codex

    devin = json.loads(paths["devin"].read_text(encoding="utf-8"))
    assert set(devin["mcpServers"]) == {
        "agentcore-gateway",
        "devin/github-mcp-server",
        "devin/vercel",
    }
    assert devin["preserve"] == {"flag": True}
    assert devin["mcpServers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert "headers" not in devin["mcpServers"]["agentcore-gateway"]

    for name in ("antigravity_primary", "antigravity_alternate"):
        config = json.loads(paths[name].read_text(encoding="utf-8"))
        assert config["preserve"] == {"client": name}
        assert config["mcpServers"]["plugin-extra"] == {
            "command": "plugin.exe",
            "args": ["serve"],
        }
        assert config["mcpServers"]["agentcore-gateway"] == {
            "serverUrl": COMPAT_URL,
        }

    zcode = json.loads(paths["zcode"].read_text(encoding="utf-8"))
    assert zcode["plugins"] == {"enabledPlugins": {"computer-use": True}}
    assert zcode["hooks"] == {
        "enabled": True,
        "events": {"Stop": {"hooks": ["keep"]}},
    }
    assert zcode["mcp"]["servers"]["agentcore-gateway"] == {
        "type": "http",
        "url": COMPAT_URL,
        "timeoutMs": 300000,
        "enabled": True,
    }
    # Companion MCP servers are preserved; only the gateway entry is reconciled.
    assert "sequential-thinking" in zcode["mcp"]["servers"]
    assert "context7" in zcode["mcp"]["servers"]

    minimax = json.loads(paths["minimax"].read_text(encoding="utf-8"))
    assert minimax["mcpServers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert "headers" not in minimax["mcpServers"]["agentcore-gateway"]
    # MiniMax reads the MCP timeout field in milliseconds; the reconciled value must be
    # 300000 rather than a seconds-denominated 300.
    assert minimax["mcpServers"]["agentcore-gateway"]["timeout"] == 300000
    assert minimax["mcpServers"]["agentcore-gateway"]["enabled"] is True
    # Companion servers are preserved; only the gateway entry is reconciled.
    assert minimax["mcpServers"]["matrix"] == {"builtin": True}
    assert minimax["mcpServers"]["cu"] == {"builtin": True}
    assert minimax["mcpServers"]["trash"] == {"builtin": True}
    eigent = json.loads(paths["eigent"].read_text(encoding="utf-8"))
    assert eigent["mcpServers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert "headers" not in eigent["mcpServers"]["agentcore-gateway"]
    zed = json.loads(paths["zed"].read_text(encoding="utf-8"))
    assert zed["context_servers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert "headers" not in zed["context_servers"]["agentcore-gateway"]
    desktop = json.loads(paths["interpreter_desktop"].read_text(encoding="utf-8"))
    assert desktop["mcpServers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert "headers" not in desktop["mcpServers"]["agentcore-gateway"]
    for path in paths.values():
        assert FAKE_KEY not in path.read_text(encoding="utf-8")

    interpreter = paths["interpreter_cli"].read_text(encoding="utf-8")
    assert "[model_providers.custom]" in interpreter
    assert "[permissions.operator.filesystem]" in interpreter
    assert "[interpreter_app]" in interpreter
    assert "mcp_servers.morph-mcp" not in interpreter
    assert "mcp_servers.openrouter" not in interpreter
    assert "mcp_servers.github" not in interpreter
    assert interpreter.count("[mcp_servers.agentcore-gateway]") == 1
    assert 'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"' in interpreter


def test_minimax_reconcile_accepts_the_effective_root_config_shape(tmp_path: Path) -> None:
    """C:\\Users\\ynotf\\.minimax\\mcp.json carries only agentcore-gateway; the matrix, cu
    and trash servers are application builtins merged at runtime, so the reconciler must
    not require them to be present in the file it manages."""
    paths = _fixture(tmp_path)
    payload = json.loads(paths["minimax"].read_text(encoding="utf-8"))
    payload["mcpServers"] = {"agentcore-gateway": payload["mcpServers"]["agentcore-gateway"]}
    paths["minimax"].write_text(json.dumps(payload, indent=2), encoding="utf-8")

    result = _run(tmp_path, "-Apply")

    assert result.returncode == 0, result.stderr
    reconciled = json.loads(paths["minimax"].read_text(encoding="utf-8"))
    assert reconciled["mcpServers"]["agentcore-gateway"]["url"] == COMPAT_URL
    assert reconciled["mcpServers"]["agentcore-gateway"]["timeout"] == 300000
    assert reconciled["mcpServers"]["agentcore-gateway"]["enabled"] is True
    assert "headers" not in reconciled["mcpServers"]["agentcore-gateway"]


def test_second_apply_is_idempotent_and_creates_no_new_backups(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    first = _run(tmp_path, "-Apply")
    assert first.returncode == 0, first.stderr
    before = _snapshot(paths)
    backups = sorted(tmp_path.rglob("*.phase2-*.bak"))

    second = _run(tmp_path, "-Apply")

    assert second.returncode == 0, second.stderr
    assert json.loads(second.stdout)["changed_count"] == 0
    assert _snapshot(paths) == before
    assert sorted(tmp_path.rglob("*.phase2-*.bak")) == backups


def test_batch_failure_restores_every_written_file(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    before = _snapshot(paths)

    result = _run(tmp_path, "-Apply", "-TestFailAfterWrites", "2")

    assert result.returncode != 0
    assert _snapshot(paths) == before
    assert FAKE_KEY not in result.stdout + result.stderr


def test_invalid_json_fails_closed_before_any_write(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["devin"].write_text('{"mcpServers": ', encoding="utf-8")
    before = _snapshot(paths)

    result = _run(tmp_path, "-Apply")

    assert result.returncode != 0
    assert _snapshot(paths) == before
    assert not list(tmp_path.rglob("*.phase2-*.bak"))
    assert FAKE_KEY not in result.stdout + result.stderr


def test_invalid_toml_fails_closed_before_any_write(tmp_path: Path) -> None:
    paths = _fixture(tmp_path)
    paths["interpreter_cli"].write_text("[unclosed\nvalue = true\n", encoding="utf-8")
    before = _snapshot(paths)

    result = _run(tmp_path, "-Apply")

    assert result.returncode != 0
    assert _snapshot(paths) == before
    assert not list(tmp_path.rglob("*.phase2-*.bak"))
    assert FAKE_KEY not in result.stdout + result.stderr
