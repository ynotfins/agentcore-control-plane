"""Trusted admin runner for device enrollment and proof-policy lifecycle.

This command is not exposed through MCP. It reads PostgreSQL credentials from
the existing Windows User environment and never prints secret values.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "m2" / "002_up_device_identity_proof.sql"


def _connection(*, autocommit: bool = False):
    password = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD")
    if not password:
        raise RuntimeError("AGENT_CORE_POSTGRES_PASSWORD is not set")
    return psycopg.connect(
        host=os.environ.get("AGENTCORE_PG_HOST", "127.0.0.1"),
        port=int(os.environ.get("AGENTCORE_PG_PORT", "55433")),
        dbname=os.environ.get("AGENTCORE_PG_DATABASE", "agent_core"),
        user=os.environ.get("AGENTCORE_PG_USER", "postgres"),
        password=password,
        sslmode="require",
        row_factory=dict_row,
        autocommit=autocommit,
    )


def _request(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("enrollment request must be a JSON object")
    if value.get("operation") != "device_enrollment_request":
        raise ValueError("not a device enrollment request")
    device_id = str(value.get("device_id") or "")
    key_id = str(value.get("key_id") or "")
    if not re.fullmatch(r"device-[0-9a-f-]{36}", device_id):
        raise ValueError("invalid device_id")
    if not re.fullmatch(r"ed25519-[0-9a-f]{24}", key_id):
        raise ValueError("invalid key_id")
    public_text = str(value.get("public_key") or "")
    public = base64.urlsafe_b64decode(public_text + "=" * (-len(public_text) % 4))
    if len(public) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return {**value, "public_key_bytes": public}


def migrate(*, backup_evidence: Path) -> dict[str, Any]:
    if not backup_evidence.exists():
        raise RuntimeError("verified backup evidence path does not exist")
    sql = MIGRATION.read_text(encoding="utf-8")
    with _connection(autocommit=True) as conn:
        conn.execute(sql)
    return {
        "ok": True,
        "action": "migrate",
        "version": "m2.002",
        "backup_evidence": str(backup_evidence),
    }


def enroll(
    request_path: Path,
    *,
    user_key: str,
    set_legacy_default: bool,
) -> dict[str, Any]:
    request = _request(request_path)
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM agentcore.users WHERE username = %s",
            (user_key,),
        )
        user = cur.fetchone()
        if not user:
            raise RuntimeError("canonical user_key is not enrolled")
        cur.execute(
            """
            INSERT INTO agentcore.machines (machine_name, hardware_ref)
            VALUES (%s, NULL)
            ON CONFLICT (machine_name) DO UPDATE
              SET hardware_ref = COALESCE(agentcore.machines.hardware_ref, EXCLUDED.hardware_ref)
            RETURNING id
            """,
            (request["device_id"],),
        )
        machine = cur.fetchone()
        cur.execute(
            """
            SELECT id, machine_id, user_id, public_key, algorithm, status
            FROM agentcore.device_keys WHERE key_id = %s
            """,
            (request["key_id"],),
        )
        existing = cur.fetchone()
        if existing:
            same = (
                str(existing["machine_id"]) == str(machine["id"])
                and str(existing["user_id"]) == str(user["id"])
                and bytes(existing["public_key"]) == request["public_key_bytes"]
                and existing["algorithm"] == "Ed25519"
            )
            if not same:
                raise RuntimeError("key_id already exists with a different identity")
            key_id = existing["id"]
            idempotent = True
        else:
            cur.execute(
                """
                INSERT INTO agentcore.device_keys (
                    machine_id, user_id, key_id, algorithm, public_key, status
                )
                VALUES (%s, %s, %s, 'Ed25519', %s, 'active')
                RETURNING id
                """,
                (
                    machine["id"],
                    user["id"],
                    request["key_id"],
                    request["public_key_bytes"],
                ),
            )
            key_id = cur.fetchone()["id"]
            idempotent = False
        if set_legacy_default:
            cur.execute(
                """
                UPDATE agentcore.device_identity_policy
                SET legacy_machine_id = %s, legacy_user_id = %s, updated_at = now()
                WHERE singleton = true
                """,
                (machine["id"], user["id"]),
            )
            _audit(
                cur,
                "legacy_default_set",
                key_id,
                machine["id"],
                user["id"],
                {},
            )
        _audit(
            cur,
            "enrolled",
            key_id,
            machine["id"],
            user["id"],
            {"idempotent": idempotent},
        )
        conn.commit()
    return {
        "ok": True,
        "action": "enroll",
        "device_id": request["device_id"],
        "key_id": request["key_id"],
        "user_key": user_key,
        "idempotent": idempotent,
        "legacy_default": set_legacy_default,
    }


def rotate(
    request_path: Path,
    *,
    old_key_id: str,
    overlap_hours: int,
) -> dict[str, Any]:
    request = _request(request_path)
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT dk.*, m.machine_name
            FROM agentcore.device_keys dk
            JOIN agentcore.machines m ON m.id = dk.machine_id
            WHERE dk.key_id = %s FOR UPDATE
            """,
            (old_key_id,),
        )
        old = cur.fetchone()
        if not old or old["status"] not in ("active", "rotating"):
            raise RuntimeError("old device key is not active")
        if old["machine_name"] != request["device_id"]:
            raise RuntimeError("rotation request device_id does not match old key")
        cur.execute(
            "SELECT id FROM agentcore.device_keys WHERE key_id = %s",
            (request["key_id"],),
        )
        if cur.fetchone():
            raise RuntimeError("replacement key_id already exists")
        cur.execute(
            """
            INSERT INTO agentcore.device_keys (
                machine_id, user_id, key_id, algorithm, public_key, status,
                rotated_from_key_id
            )
            VALUES (%s, %s, %s, 'Ed25519', %s, 'active', %s)
            RETURNING id
            """,
            (
                old["machine_id"],
                old["user_id"],
                request["key_id"],
                request["public_key_bytes"],
                old_key_id,
            ),
        )
        new_id = cur.fetchone()["id"]
        cur.execute(
            """
            UPDATE agentcore.device_keys
            SET status = 'rotating',
                valid_until = now() + (%s * interval '1 hour'),
                updated_at = now()
            WHERE id = %s
            """,
            (overlap_hours, old["id"]),
        )
        _audit(
            cur,
            "rotated",
            new_id,
            old["machine_id"],
            old["user_id"],
            {"old_key_id": old_key_id, "overlap_hours": overlap_hours},
        )
        conn.commit()
    return {
        "ok": True,
        "action": "rotate",
        "device_id": request["device_id"],
        "old_key_id": old_key_id,
        "new_key_id": request["key_id"],
        "overlap_hours": overlap_hours,
    }


def set_key_status(key_id: str, status: str) -> dict[str, Any]:
    action = {"revoked": "revoked", "disabled": "disabled", "active": "enabled"}[status]
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE agentcore.device_keys
            SET status = %s,
                revoked_at = CASE WHEN %s = 'revoked' THEN now() ELSE NULL END,
                updated_at = now()
            WHERE key_id = %s
            RETURNING id, machine_id, user_id
            """,
            (status, status, key_id),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("device key not found")
        _audit(cur, action, row["id"], row["machine_id"], row["user_id"], {})
        conn.commit()
    return {"ok": True, "action": action, "key_id": key_id, "status": status}


def set_enforcement(mode: str, *, window_hours: int) -> dict[str, Any]:
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE agentcore.device_identity_policy
            SET enforcement_mode = %s,
                migration_window_ends_at = CASE
                  WHEN %s = 'legacy_compat'
                  THEN now() + (%s * interval '1 hour')
                  ELSE now()
                END,
                updated_at = now()
            WHERE singleton = true
            RETURNING migration_window_ends_at
            """,
            (mode, mode, window_hours),
        )
        row = cur.fetchone()
        _audit(cur, "enforcement_changed", None, None, None, {"mode": mode})
        conn.commit()
    return {
        "ok": True,
        "action": "enforcement",
        "mode": mode,
        "migration_window_ends_at": row["migration_window_ends_at"].isoformat(),
    }


def status() -> dict[str, Any]:
    with _connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT enforcement_mode, migration_window_ends_at,
                   legacy_machine_id IS NOT NULL AND legacy_user_id IS NOT NULL
                     AS legacy_default_configured
            FROM agentcore.device_identity_policy WHERE singleton = true
            """
        )
        policy = cur.fetchone()
        cur.execute(
            "SELECT status, count(*) AS count FROM agentcore.device_keys GROUP BY status"
        )
        counts = {row["status"]: row["count"] for row in cur.fetchall()}
    return {
        "ok": True,
        "action": "status",
        "enforcement_mode": policy["enforcement_mode"],
        "migration_window_ends_at": policy["migration_window_ends_at"].isoformat(),
        "legacy_default_configured": policy["legacy_default_configured"],
        "key_counts": counts,
    }


def _audit(cur, action, key_id, machine_id, user_id, detail: dict[str, Any]) -> None:
    cur.execute(
        """
        INSERT INTO agentcore.device_identity_audit (
            action, device_key_id, machine_id, user_id, detail
        )
        VALUES (%s, %s, %s, %s, %s::jsonb)
        """,
        (action, key_id, machine_id, user_id, json.dumps(detail)),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("migrate")
    command.add_argument("--backup-evidence", type=Path, required=True)
    command = sub.add_parser("enroll")
    command.add_argument("--request", type=Path, required=True)
    command.add_argument("--user-key", required=True)
    command.add_argument("--set-legacy-default", action="store_true")
    command = sub.add_parser("rotate")
    command.add_argument("--request", type=Path, required=True)
    command.add_argument("--old-key-id", required=True)
    command.add_argument("--overlap-hours", type=int, default=24)
    for name, status_value in (
        ("revoke", "revoked"),
        ("disable", "disabled"),
        ("enable", "active"),
    ):
        command = sub.add_parser(name)
        command.add_argument("--key-id", required=True)
        command.set_defaults(status_value=status_value)
    command = sub.add_parser("enforcement")
    command.add_argument("--mode", choices=("legacy_compat", "required"), required=True)
    command.add_argument("--window-hours", type=int, default=168)
    sub.add_parser("status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "migrate":
            result = migrate(backup_evidence=args.backup_evidence)
        elif args.command == "enroll":
            result = enroll(
                args.request,
                user_key=args.user_key,
                set_legacy_default=args.set_legacy_default,
            )
        elif args.command == "rotate":
            result = rotate(
                args.request,
                old_key_id=args.old_key_id,
                overlap_hours=args.overlap_hours,
            )
        elif args.command in {"revoke", "disable", "enable"}:
            result = set_key_status(args.key_id, args.status_value)
        elif args.command == "enforcement":
            result = set_enforcement(args.mode, window_hours=args.window_hours)
        else:
            result = status()
        print(json.dumps(result, indent=2, default=str))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {"ok": False, "error": type(exc).__name__, "message": str(exc)[:240]},
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
