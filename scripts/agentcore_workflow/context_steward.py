"""AgentCore Context Steward — bounded monitoring worker (Phase 7B).

Reads contracts/context-steward-policy.json. Records findings/proposals in
agent_core. Never auto-edits authority docs or Bifrost/IDE configs.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = REPO_ROOT / "contracts" / "context-steward-policy.json"
MIGRATION = REPO_ROOT / "migrations" / "m6" / "002_up_context_steward.sql"


def _dsn() -> str:
    pw = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    return (
        f"host=127.0.0.1 port=55433 dbname=agent_core "
        f"user=postgres password={pw}"
    )


def load_policy() -> dict[str, Any]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def ensure_tables() -> None:
    import psycopg

    sql = MIGRATION.read_text(encoding="utf-8")
    with psycopg.connect(_dsn(), autocommit=True) as conn:
        conn.execute(sql)


def record_finding(
    project_id: str,
    check_type: str,
    severity: str,
    summary: str,
    detail: dict[str, Any] | None = None,
) -> str:
    import psycopg

    with psycopg.connect(_dsn(), autocommit=True) as conn:
        row = conn.execute(
            """
            INSERT INTO agentcore.context_steward_findings
              (project_id, check_type, severity, summary, detail)
            VALUES (%s, %s, %s, %s, %s::jsonb)
            RETURNING finding_id::text
            """,
            (
                project_id,
                check_type,
                severity,
                summary,
                json.dumps(detail or {}),
            ),
        ).fetchone()
    return row[0]


def record_proposal(
    project_id: str,
    proposal_kind: str,
    proposal: dict[str, Any],
    finding_id: str | None = None,
) -> str:
    import psycopg

    with psycopg.connect(_dsn(), autocommit=True) as conn:
        row = conn.execute(
            """
            INSERT INTO agentcore.context_steward_proposals
              (project_id, finding_id, proposal_kind, proposal)
            VALUES (%s, %s::uuid, %s, %s::jsonb)
            RETURNING proposal_id::text
            """,
            (
                project_id,
                finding_id,
                proposal_kind,
                json.dumps(proposal),
            ),
        ).fetchone()
    return row[0]


def write_milestone_delta(project_root: Path, lines: list[str]) -> Path:
    """Non-canonical projection — agents may regenerate; never authority."""
    out = project_root / ".agentcore" / "MILESTONE_DELTA.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# MILESTONE_DELTA (non-canonical Context Steward projection)",
        "",
        f"generated_at: {datetime.now(UTC).isoformat()}",
        "",
        "This file is a steward proposal surface. It does not replace STATE.md,",
        "DECISIONS.md, CONTEXT_INDEX.md, or BLUEPRINT.md.",
        "",
        *lines,
        "",
    ]
    out.write_text("\n".join(body), encoding="utf-8")
    return out


def run_checks(project_id: str, project_root: Path) -> dict[str, Any]:
    policy = load_policy()
    findings: list[dict[str, Any]] = []
    # Wrong-drive path: durable assets outside registered roots (heuristic)
    forbidden_prefixes = ["C:\\", "I:\\"]
    agentcore_dir = project_root / ".agentcore"
    if not agentcore_dir.is_dir():
        fid = record_finding(
            project_id,
            "stale_projection",
            "warn",
            ".agentcore directory missing",
            {"path": str(agentcore_dir)},
        )
        findings.append({"finding_id": fid, "check_type": "stale_projection"})
    else:
        state = agentcore_dir / "STATE.md"
        if not state.exists():
            fid = record_finding(
                project_id,
                "stale_projection",
                "warn",
                "STATE.md projection missing",
                {"path": str(state)},
            )
            pid = record_proposal(
                project_id,
                "regenerate_projections",
                {"action": "run projection worker", "forbidden_authority": policy["forbidden_authority"]},
                finding_id=fid,
            )
            findings.append({"finding_id": fid, "proposal_id": pid})

    delta = write_milestone_delta(
        project_root,
        [
            f"- project_id: `{project_id}`",
            f"- findings_this_run: {len(findings)}",
            f"- policy: `{POLICY_PATH.name}`",
            f"- check_types: {', '.join(policy.get('check_types', []))}",
            "- note: deep 48h audit is silent when clean (policy)",
        ],
    )
    return {
        "ok": True,
        "project_id": project_id,
        "findings": findings,
        "milestone_delta": str(delta),
        "policy_id": policy.get("policy_id"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentCore Context Steward")
    parser.add_argument("--ensure-tables", action="store_true")
    parser.add_argument("--project-id", default="agentcore-control-plane")
    parser.add_argument("--project-root", default=str(REPO_ROOT))
    parser.add_argument("--check", action="store_true", help="Run steward checks")
    args = parser.parse_args(argv)

    if not os.environ.get("AGENT_CORE_POSTGRES_PASSWORD"):
        print("ERROR: AGENT_CORE_POSTGRES_PASSWORD missing from env", file=sys.stderr)
        return 2

    if args.ensure_tables:
        ensure_tables()
        print("tables_ok")

    if args.check:
        result = run_checks(args.project_id, Path(args.project_root))
        print(json.dumps(result, indent=2))
        return 0

    if not args.ensure_tables:
        parser.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
