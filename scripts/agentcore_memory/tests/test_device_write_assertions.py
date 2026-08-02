"""Option B device identity: write tools always require device assertions."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from device_identity import (
    DeviceIdentityError,
    UNSIGNED_READ_TOOLS,
    WRITE_TOOLS,
    verify_tool_identity,
)


def _legacy_policy_row(*, ends_in_days: int = 30) -> dict:
    return {
        "enforcement_mode": "legacy_compat",
        "migration_window_ends_at": datetime.now(UTC) + timedelta(days=ends_in_days),
        "legacy_machine_id": "machine-uuid",
        "legacy_user_id": "user-uuid",
    }


def _legacy_identity_row() -> dict:
    return {"device_id": "legacy-device", "user_key": "legacy-user"}


def _mock_conn(policy_row: dict, identity_row: dict | None = None) -> MagicMock:
    conn = MagicMock()
    cur = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    cur.fetchone.side_effect = [policy_row, identity_row]
    return conn


def test_write_tools_reject_unsigned_even_in_legacy_compat() -> None:
    for tool_name in WRITE_TOOLS:
        conn = _mock_conn(_legacy_policy_row())
        with pytest.raises(DeviceIdentityError) as exc:
            verify_tool_identity(
                conn,
                tool_name=tool_name,
                arguments={"project_key": "fixture-project"},
            )
        assert exc.value.code == "device_assertion_required"


def test_unsigned_read_tools_allow_legacy_compat() -> None:
    read_tools = UNSIGNED_READ_TOOLS - {"memory_status"}
    for tool_name in read_tools:
        conn = _mock_conn(_legacy_policy_row(), _legacy_identity_row())
        identity = verify_tool_identity(
            conn,
            tool_name=tool_name,
            arguments={"project_key": "fixture-project"},
        )
        assert identity is not None
        assert identity.legacy_compat is True
        assert identity.device_id == "legacy-device"


def test_memory_status_skips_identity_verification() -> None:
    conn = MagicMock()
    assert (
        verify_tool_identity(
            conn,
            tool_name="memory_status",
            arguments={},
        )
        is None
    )
    conn.cursor.assert_not_called()
