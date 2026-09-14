"""Approach A host-owned Devin signed-memory contract tests."""

from __future__ import annotations

import base64
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from psycopg.errors import UniqueViolation

SCRIPTS_ROOT = Path(__file__).resolve().parents[2]
MEMORY_ROOT = SCRIPTS_ROOT / "agentcore_memory"
for path in (str(SCRIPTS_ROOT), str(MEMORY_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from agentcore_devin.signed_memory import (
    CLIENT_KEY,
    DEFAULT_AGENT_KEY,
    DEVIN_COMPAT_GATEWAY_URL,
    HostSignedMemoryClient,
    default_session_open_arguments,
    inspect_devin_mcp_config,
    is_compat_gateway_url,
    sign_memory_arguments,
)
from agentcore_project_boundary import match_enrolled_path, require_enrolled_path
from device_identity import DeviceIdentityError, verify_tool_identity
import server

NFA_KEY = "nfa-platform"
STAGING = r"D:\agentcore-worktrees\nfa-platform\goal-staging-001"
SIBLING = r"D:\agentcore-worktrees\nfa-platform\goal-staging-002"


def _temp_identity(tmp_path: Path):
    from agentcore_context_engine.security import DeviceIdentityManager, InMemoryCredentialStore

    manager = DeviceIdentityManager(tmp_path / "device.json", InMemoryCredentialStore())
    enrollment = manager.initialize()
    return manager, enrollment


def _public_bytes(enrollment) -> bytes:
    padding = "=" * (-len(enrollment.public_key) % 4)
    return base64.urlsafe_b64decode(enrollment.public_key + padding)


def _device_row(enrollment) -> dict:
    return {
        "device_key_id": "dk-test",
        "key_id": enrollment.key_id,
        "public_key": _public_bytes(enrollment),
        "status": "active",
        "valid_from": datetime.now(UTC) - timedelta(days=1),
        "valid_until": None,
        "revoked_at": None,
        "machine_id": "machine-test",
        "device_id": enrollment.device_id,
        "user_id": "user-test",
        "user_key": "ynotf",
    }


def _conn_for_verify(row: dict, insert_side_effect=None) -> MagicMock:
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    cur.fetchone.return_value = row
    if insert_side_effect is not None:
        def execute(sql, params=None):
            if "INSERT INTO agentcore.device_assertion_nonces" in str(sql):
                raise insert_side_effect

        cur.execute.side_effect = execute
    return conn


def test_unsigned_session_open_fails_closed():
    with pytest.raises(DeviceIdentityError) as exc:
        verify_tool_identity(
            MagicMock(),
            tool_name="session_open",
            arguments={"project_key": NFA_KEY, "project_root": STAGING},
        )
    assert exc.value.code == "device_assertion_required"


def test_unsigned_call_tool_fails_closed(monkeypatch):
    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self) -> None:
            return None

    monkeypatch.setattr(server, "db", lambda: Dummy())
    result = server.call_tool(
        "session_open",
        {"project_key": NFA_KEY, "project_root": STAGING},
    )
    assert result["ok"] is False
    assert result["error"] == "device_assertion_required"
    assert result["identity_verified"] is False


def test_goal_staging_path_is_enrolled_exactly():
    enrolled = require_enrolled_path(STAGING)
    assert enrolled["project_key"] == NFA_KEY
    assert match_enrolled_path(SIBLING) is None
    args = default_session_open_arguments(NFA_KEY, STAGING)
    assert args["client_key"] == CLIENT_KEY
    assert args["agent_key"] == DEFAULT_AGENT_KEY
    assert args["project_root"] == STAGING


def test_signed_arguments_match_gateway_client_shape(tmp_path):
    manager, enrollment = _temp_identity(tmp_path)
    args = default_session_open_arguments(NFA_KEY, STAGING)
    signed = sign_memory_arguments("session_open", args, identity_manager=manager)
    assertion = signed["device_assertion"]
    assert signed["device_id"] == enrollment.device_id
    assert signed["client_key"] == CLIENT_KEY
    assert assertion["schema"] == "agentcore-device-assertion/v1"
    assert assertion["target_tool"] == "session_open"
    assert assertion["project_key"] == NFA_KEY
    assert assertion["device_id"] == enrollment.device_id
    assert assertion["key_id"] == enrollment.key_id
    assert len(assertion["request_sha256"]) == 64


def test_signed_verify_accepts_enrolled_nfa_path(tmp_path):
    manager, enrollment = _temp_identity(tmp_path)
    args = default_session_open_arguments(NFA_KEY, STAGING)
    signed = sign_memory_arguments("session_open", args, identity_manager=manager)
    identity = verify_tool_identity(
        _conn_for_verify(_device_row(enrollment)),
        tool_name="session_open",
        arguments=signed,
    )
    assert identity is not None
    assert identity.legacy_compat is False
    assert identity.device_id == enrollment.device_id
    assert identity.key_id == enrollment.key_id


def test_replay_same_assertion_fails(tmp_path):
    manager, enrollment = _temp_identity(tmp_path)
    args = default_session_open_arguments(NFA_KEY, STAGING)
    signed = sign_memory_arguments("session_open", args, identity_manager=manager)
    first = verify_tool_identity(
        _conn_for_verify(_device_row(enrollment)),
        tool_name="session_open",
        arguments=signed,
    )
    assert first is not None
    with pytest.raises(DeviceIdentityError) as exc:
        verify_tool_identity(
            _conn_for_verify(_device_row(enrollment), UniqueViolation("replay")),
            tool_name="session_open",
            arguments=signed,
        )
    assert exc.value.code == "device_assertion_replay"


def test_project_key_mismatch_fails(tmp_path):
    manager, _enrollment = _temp_identity(tmp_path)
    args = default_session_open_arguments(NFA_KEY, STAGING)
    signed = sign_memory_arguments("session_open", args, identity_manager=manager)
    signed["device_assertion"]["project_key"] = "agentcore-control-plane"
    with pytest.raises(DeviceIdentityError) as exc:
        verify_tool_identity(
            MagicMock(),
            tool_name="session_open",
            arguments=signed,
        )
    assert exc.value.code == "device_assertion_project_mismatch"


def test_compat_url_never_attaches_authorization(tmp_path):
    manager, _enrollment = _temp_identity(tmp_path)
    client = HostSignedMemoryClient(identity_manager=manager)
    headers = client._headers(url=DEVIN_COMPAT_GATEWAY_URL)
    assert "Authorization" not in headers
    assert is_compat_gateway_url(DEVIN_COMPAT_GATEWAY_URL)


def test_source_does_not_write_devin_mcp_or_store_vk():
    source = Path(__file__).resolve().parents[1] / "signed_memory.py"
    text = source.read_text(encoding="utf-8")
    assert "inspect_devin_mcp_config" in text
    assert "write_text" not in text
    assert "mcp_config.json" in text
    launcher = SCRIPTS_ROOT / "devin_signed_memory.py"
    assert launcher.is_file()
    assert "BIFROST_MCP_VIRTUAL_KEY" in text
    assert "Authorization" in text
    assert "is_compat_gateway_url" in text


def test_inspect_live_devin_mcp_json_is_headerless():
    facts = inspect_devin_mcp_config()
    if not facts.get("path_exists"):
        pytest.skip("live Devin mcp_config.json is not present")
    assert facts["ok"] is True
    assert facts["uses_compat_18082"] is True
    assert facts["has_authorization_header"] is False
    assert facts["has_vk_literal"] is False


def test_signed_call_tool_reaches_session_open_for_staging(tmp_path, monkeypatch):
    manager, enrollment = _temp_identity(tmp_path)
    captured = {}

    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def commit(self) -> None:
            return None

    def fake_verify(conn, tool_name, arguments, now=None):
        assert tool_name == "session_open"
        assert "device_assertion" in arguments
        assert arguments["project_key"] == NFA_KEY
        assert arguments["project_root"] == STAGING
        return server.VerifiedIdentity(
            machine_id="machine-test",
            user_id="user-test",
            device_id=enrollment.device_id,
            user_key="ynotf",
            key_id=enrollment.key_id,
            legacy_compat=False,
        )

    def fake_open(args, verified_identity=None):
        captured.update(args)
        return {"ok": True, "session_id": "sess-test", "project_key": NFA_KEY}

    monkeypatch.setattr(server, "db", lambda: Dummy())
    monkeypatch.setattr(server, "verify_tool_identity", fake_verify)
    monkeypatch.setattr(server, "session_open", fake_open)
    signed = sign_memory_arguments(
        "session_open",
        default_session_open_arguments(NFA_KEY, STAGING),
        identity_manager=manager,
    )
    result = server.call_tool("session_open", signed)
    assert result["ok"] is True
    assert captured["project_key"] == NFA_KEY
    assert captured["project_root"] == STAGING
    assert captured["client_key"] == CLIENT_KEY
