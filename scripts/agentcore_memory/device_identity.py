"""Cryptographic device assertions for the existing memory tool facade."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from psycopg.errors import UniqueViolation

ASSERTION_SCHEMA = "agentcore-device-assertion/v1"
MAX_ASSERTION_LIFETIME = timedelta(seconds=300)
CLOCK_SKEW = timedelta(seconds=5)
UNPROTECTED_TOOLS = frozenset({"memory_status"})
UNSIGNED_READ_TOOLS = frozenset(
    {
        "memory_status",
        "startup_context",
        "retrieve_context",
        "expand_source",
        "docs_search",
    }
)
WRITE_TOOLS = frozenset(
    {
        "session_open",
        "session_close",
        "append_event",
        "propose_fact",
        "build_handoff",
    }
)


class DeviceIdentityError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class VerifiedIdentity:
    machine_id: str
    user_id: str
    device_id: str
    user_key: str
    key_id: str | None
    legacy_compat: bool = False


def canonical_request_hash(arguments: Mapping[str, Any]) -> str:
    unsigned = {
        key: value for key, value in arguments.items() if key != "device_assertion"
    }
    raw = json.dumps(
        unsigned,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_tool_identity(
    conn,
    *,
    tool_name: str,
    arguments: Mapping[str, Any],
    now: datetime | None = None,
) -> VerifiedIdentity | None:
    if tool_name in UNPROTECTED_TOOLS:
        return None
    checked_at = (now or datetime.now(UTC)).astimezone(UTC)
    assertion = arguments.get("device_assertion")
    if not isinstance(assertion, dict):
        if tool_name in WRITE_TOOLS:
            raise DeviceIdentityError("device_assertion_required")
        return _legacy_identity(conn, checked_at)

    required = {
        "schema",
        "device_id",
        "key_id",
        "issued_at",
        "expires_at",
        "nonce",
        "target_tool",
        "request_sha256",
        "signature",
    }
    if not required.issubset(assertion):
        raise DeviceIdentityError("device_assertion_incomplete")
    if assertion.get("schema") != ASSERTION_SCHEMA:
        raise DeviceIdentityError("device_assertion_schema")
    if assertion.get("target_tool") != tool_name:
        raise DeviceIdentityError("device_assertion_tool_mismatch")
    if assertion.get("request_sha256") != canonical_request_hash(arguments):
        raise DeviceIdentityError("device_assertion_request_mismatch")

    issued_at = _parse_timestamp(assertion["issued_at"], "issued_at")
    expires_at = _parse_timestamp(assertion["expires_at"], "expires_at")
    if expires_at <= issued_at or expires_at - issued_at > MAX_ASSERTION_LIFETIME:
        raise DeviceIdentityError("device_assertion_lifetime")
    if issued_at > checked_at + CLOCK_SKEW or expires_at < checked_at - CLOCK_SKEW:
        raise DeviceIdentityError("device_assertion_expired")

    argument_project_key = arguments.get("project_key")
    project_key = assertion.get("project_key")
    if (
        argument_project_key is not None
        and project_key != argument_project_key
    ):
        raise DeviceIdentityError("device_assertion_project_mismatch")
    argument_session = arguments.get("session_id")
    if assertion.get("session_id") != argument_session:
        raise DeviceIdentityError("device_assertion_session_mismatch")

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT dk.id AS device_key_id, dk.key_id, dk.public_key, dk.status,
                   dk.valid_from, dk.valid_until, dk.revoked_at,
                   m.id AS machine_id, m.machine_name AS device_id,
                   u.id AS user_id, u.username AS user_key
            FROM agentcore.device_keys dk
            JOIN agentcore.machines m ON m.id = dk.machine_id
            JOIN agentcore.users u ON u.id = dk.user_id
            WHERE dk.key_id = %s
            """,
            (str(assertion["key_id"]),),
        )
        row = cur.fetchone()
        if not row:
            raise DeviceIdentityError("device_key_unknown")
        if str(row["device_id"]) != str(assertion["device_id"]):
            raise DeviceIdentityError("device_id_mismatch")
        if row["status"] not in ("active", "rotating"):
            raise DeviceIdentityError("device_key_disabled")
        if row["revoked_at"] is not None:
            raise DeviceIdentityError("device_key_revoked")
        if row["valid_from"] > checked_at + CLOCK_SKEW:
            raise DeviceIdentityError("device_key_not_yet_valid")
        if row["valid_until"] is not None and row["valid_until"] < checked_at:
            raise DeviceIdentityError("device_key_expired")

        caller_user_key = arguments.get("user_key")
        if caller_user_key is not None and str(caller_user_key) != str(row["user_key"]):
            raise DeviceIdentityError("user_key_mismatch")

        _verify_signature(assertion, bytes(row["public_key"]))
        _verify_bound_session(
            cur,
            session_id=str(argument_session) if argument_session else None,
            machine_id=str(row["machine_id"]),
            user_id=str(row["user_id"]),
            project_key=str(project_key) if project_key else None,
        )

        nonce = str(assertion["nonce"])
        if len(nonce) < 24 or len(nonce) > 256:
            raise DeviceIdentityError("device_assertion_nonce")
        try:
            cur.execute(
                """
                INSERT INTO agentcore.device_assertion_nonces (
                    device_key_id, nonce_sha256, target_tool, request_sha256,
                    issued_at, expires_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    row["device_key_id"],
                    hashlib.sha256(nonce.encode("utf-8")).digest(),
                    tool_name,
                    bytes.fromhex(str(assertion["request_sha256"])),
                    issued_at,
                    expires_at,
                ),
            )
        except UniqueViolation as exc:
            raise DeviceIdentityError("device_assertion_replay") from exc

    return VerifiedIdentity(
        machine_id=str(row["machine_id"]),
        user_id=str(row["user_id"]),
        device_id=str(row["device_id"]),
        user_key=str(row["user_key"]),
        key_id=str(row["key_id"]),
    )


def resolve_legacy_identity(
    conn,
    *,
    now: datetime | None = None,
) -> VerifiedIdentity:
    return _legacy_identity(conn, (now or datetime.now(UTC)).astimezone(UTC))


def device_identity_status(conn) -> dict[str, Any]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT enforcement_mode, migration_window_ends_at, schema_version,
                   legacy_machine_id IS NOT NULL AND legacy_user_id IS NOT NULL
                       AS legacy_default_configured
            FROM agentcore.device_identity_policy
            WHERE singleton = true
            """
        )
        policy = cur.fetchone()
        cur.execute(
            """
            SELECT status, count(*) AS count
            FROM agentcore.device_keys
            GROUP BY status
            ORDER BY status
            """
        )
        counts = {str(row["status"]): int(row["count"]) for row in cur.fetchall()}
    return {
        "schema_version": int(policy["schema_version"]) if policy else None,
        "enforcement_mode": policy["enforcement_mode"] if policy else "missing",
        "migration_window_ends_at": (
            policy["migration_window_ends_at"].isoformat() if policy else None
        ),
        "legacy_default_configured": bool(
            policy and policy["legacy_default_configured"]
        ),
        "key_counts": counts,
    }


def _legacy_identity(conn, checked_at: datetime) -> VerifiedIdentity:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT enforcement_mode, migration_window_ends_at,
                   legacy_machine_id, legacy_user_id
            FROM agentcore.device_identity_policy
            WHERE singleton = true
            """
        )
        policy = cur.fetchone()
        if not policy:
            raise DeviceIdentityError("device_identity_policy_missing")
        if (
            policy["enforcement_mode"] != "legacy_compat"
            or policy["migration_window_ends_at"] < checked_at
        ):
            raise DeviceIdentityError("device_assertion_required")
        if not policy["legacy_machine_id"] or not policy["legacy_user_id"]:
            raise DeviceIdentityError("legacy_identity_not_enrolled")
        cur.execute(
            """
            SELECT m.machine_name AS device_id, u.username AS user_key
            FROM agentcore.machines m, agentcore.users u
            WHERE m.id = %s AND u.id = %s
            """,
            (policy["legacy_machine_id"], policy["legacy_user_id"]),
        )
        row = cur.fetchone()
        if not row:
            raise DeviceIdentityError("legacy_identity_unknown")
    return VerifiedIdentity(
        machine_id=str(policy["legacy_machine_id"]),
        user_id=str(policy["legacy_user_id"]),
        device_id=str(row["device_id"]),
        user_key=str(row["user_key"]),
        key_id=None,
        legacy_compat=True,
    )


def _verify_signature(assertion: Mapping[str, Any], public_key: bytes) -> None:
    claims = dict(assertion)
    signature_text = str(claims.pop("signature"))
    padding = "=" * (-len(signature_text) % 4)
    try:
        signature = base64.urlsafe_b64decode(signature_text + padding)
        payload = json.dumps(
            claims,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, payload)
    except (InvalidSignature, ValueError) as exc:
        raise DeviceIdentityError("device_assertion_signature") from exc


def _parse_timestamp(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            raise ValueError("timezone required")
        return parsed.astimezone(UTC)
    except ValueError as exc:
        raise DeviceIdentityError(f"device_assertion_{field}") from exc


def _verify_bound_session(
    cur,
    *,
    session_id: str | None,
    machine_id: str,
    user_id: str,
    project_key: str | None,
) -> None:
    if not session_id:
        return
    cur.execute(
        """
        SELECT si.machine_id, si.user_id, p.project_key
        FROM agentcore.source_identities si
        JOIN agentcore.projects p ON p.id = si.project_id
        WHERE si.session_id = %s
        ORDER BY si.created_at DESC
        LIMIT 1
        """,
        (session_id,),
    )
    source = cur.fetchone()
    if not source:
        raise DeviceIdentityError("session_identity_unknown")
    if str(source["machine_id"]) != machine_id or str(source["user_id"]) != user_id:
        raise DeviceIdentityError("session_identity_mismatch")
    if project_key is not None and str(source["project_key"]) != project_key:
        raise DeviceIdentityError("session_project_mismatch")
