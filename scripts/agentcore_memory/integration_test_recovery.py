"""Bounded PostgreSQL integration proof for the AgentCore recovery tool surface.

Run only against a disposable database after applying M2, M3.001, and M3.002:

    set AGENTCORE_PG_DATABASE=<disposable-db>
    python scripts/agentcore_memory/integration_test_recovery.py
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

if not os.environ.get("AGENTCORE_PG_DATABASE"):
    raise SystemExit(
        "AGENTCORE_PG_DATABASE must name a disposable integration database"
    )

import server  # noqa: E402


def require(condition: object, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    run_id = uuid.uuid4().hex
    project_key = f"recovery-integration-{run_id}"
    session = server.session_open(
        {
            "project_key": project_key,
            "project_name": "Recovery Integration",
            "client_key": f"cursor-{run_id}",
            "agent_key": f"agent-{run_id}",
            "session_key": f"session-{run_id}",
            "project_root": str(Path.cwd()),
            "canonical_repo_path": str(Path.cwd()),
            "worktree_path": str(Path.cwd()),
            "repo_key": "agentcore-control-plane-integration",
            "branch_name": "test/recovery-integration",
            "head_commit": "0" * 40,
            "milestone": "M4",
            "model_provider": "generic",
            "model_id": "capability/one-million",
            "context_profile": "one-million-context",
        }
    )
    require(session["ok"], "session_open failed")
    alternate = server.session_open(
        {
            "project_key": f"{project_key}-alternate",
            "project_name": "Recovery Integration Alternate Worktree",
            "client_key": f"cursor-alt-{run_id}",
            "agent_key": f"agent-alt-{run_id}",
            "session_key": f"session-alt-{run_id}",
            "project_root": str(Path.cwd() / "alternate-worktree"),
            "canonical_repo_path": str(Path.cwd()),
            "worktree_path": str(Path.cwd() / "alternate-worktree"),
            "repo_key": "agentcore-control-plane-integration",
            "branch_name": "test/recovery-alternate",
            "head_commit": "1" * 40,
            "milestone": "M4",
            "model_provider": "generic",
            "model_id": "capability/standard-128k",
            "context_profile": "standard-context",
        }
    )
    require(
        alternate["ok"], "same repository could not self-enroll an alternate worktree"
    )
    try:
        server.session_open(
            {
                "project_key": project_key,
                "project_name": "Invalid Repository Rebinding",
                "client_key": f"cursor-invalid-{run_id}",
                "agent_key": f"agent-invalid-{run_id}",
                "session_key": f"session-invalid-{run_id}",
                "project_root": str(Path.cwd() / "invalid-repo"),
                "canonical_repo_path": str(Path.cwd() / "invalid-repo"),
                "worktree_path": str(Path.cwd() / "invalid-repo"),
                "repo_key": f"invalid-repo-{run_id}",
                "context_profile": "standard-context",
            }
        )
    except ValueError:
        pass
    else:
        raise AssertionError("project identity was rebound across repositories")

    server.append_event(
        {
            "session_id": alternate["session_id"],
            "event_kind": "prompt",
            "idempotency_key": f"{run_id}-alternate-source",
            "payload": {
                "verbatim": "cross-project rollback sentinel",
                "milestone": "M4",
            },
            "trust_class": "project_verified",
        }
    )

    expected_ids: list[str] = []
    for index in range(9):
        result = server.append_event(
            {
                "session_id": session["session_id"],
                "event_kind": "prompt" if index == 0 else "message",
                "idempotency_key": f"{run_id}-{index}",
                "payload": {
                    "index": index,
                    "verbatim": f"integration-original-{run_id}-{index}",
                    "milestone": "M4",
                },
                "trust_class": "operator_verified",
            }
        )
        expected_ids.append(result["event_id"])
    quarantined = server.append_event(
        {
            "session_id": session["session_id"],
            "event_kind": "message",
            "idempotency_key": f"{run_id}-quarantined",
            "payload": {
                "verbatim": "must-not-enter-normal-recovery",
                "milestone": "M4",
            },
            "trust_class": "quarantined",
        }
    )

    synthetic_chunk = "durable-project-history-" + ("x" * 16384)
    bulk_ids: list[str] = []
    for index in range(257):
        result = server.append_event(
            {
                "session_id": session["session_id"],
                "event_kind": "tool_event",
                "idempotency_key": f"{run_id}-bulk-{index}",
                "payload": {
                    "index": index,
                    "verbatim": synthetic_chunk,
                    "milestone": "M4",
                },
                "trust_class": "project_verified",
            }
        )
        bulk_ids.append(result["event_id"])

    archived_original = "archived-original-" + ("z" * 70000)
    archived_result = server.append_event(
        {
            "session_id": session["session_id"],
            "event_kind": "output",
            "idempotency_key": f"{run_id}-archived",
            "payload": {"artifact_note": "archived exact original", "milestone": "M4"},
            "large_text": archived_original,
            "trust_class": "project_verified",
        }
    )
    archived_event_id = archived_result["event_id"]
    archived_retry = server.append_event(
        {
            "session_id": session["session_id"],
            "event_kind": "output",
            "idempotency_key": f"{run_id}-archived",
            "payload": {
                "artifact_note": "must not replace original",
                "milestone": "M4",
            },
            "large_text": "different-content-must-not-create-an-orphan",
            "trust_class": "project_verified",
        }
    )
    require(
        archived_retry["event_id"] == archived_event_id
        and archived_retry["artifact_id"] == archived_result["artifact_id"]
        and archived_retry["idempotent_replay"],
        "idempotent event retry changed its linked artifact",
    )

    with server.db() as conn, conn.cursor() as cur:
        server.set_project(conn, str(session["project_id"]))
        cur.execute(
            """
            SELECT a.id::text, a.sha256, a.storage_uri
            FROM agentcore.evidence_events e
            JOIN agentcore.artifact_objects a ON a.id = e.artifact_id
            WHERE e.id = %s AND e.project_id = %s
            """,
            (archived_event_id, session["project_id"]),
        )
        artifact = cur.fetchone()
        require(
            artifact, "large original was not stored as a content-addressed artifact"
        )
        hot_path = Path(artifact["storage_uri"])
        cold_root = Path(os.environ["AGENTCORE_HOT_ARTIFACT_ROOT"]).with_name(
            f"{server.PG_DATABASE}-cold-e"
        )
        cold_path = cold_root / artifact["sha256"][:2] / artifact["sha256"]
        cold_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(hot_path, cold_path)
        cur.execute(
            """
            INSERT INTO agentcore.artifact_locations (
                artifact_id, storage_tier, storage_uri, sha256, is_active
            ) VALUES (%s, 'cold_e', %s, %s, true)
            """,
            (artifact["id"], str(cold_path), artifact["sha256"]),
        )
        cur.execute(
            """
            SELECT count(*) AS event_count, sum(octet_length(payload::text)) AS durable_bytes
            FROM agentcore.evidence_events
            WHERE project_id = %s AND trust_class <> 'quarantined'
            """,
            (session["project_id"],),
        )
        durable = cur.fetchone()
        require(
            int(durable["durable_bytes"]) // 4 > 1_000_000,
            "synthetic PostgreSQL history did not exceed one million conservative tokens",
        )
        cur.execute(
            """
            SELECT agentcore.create_context_summary(
                %s, %s, 'L3', 'static_stable', 'Deliberately incomplete chronology',
                'incorrect summary', 2, 1.0, %s::uuid[]
            ) AS summary_id
            """,
            (session["project_id"], session["session_id"], expected_ids),
        )
        incorrect_summary_id = str(cur.fetchone()["summary_id"])
        cur.execute(
            """
            SELECT agentcore.supersede_context_summary(
                %s, %s, %s, 32, 'integration correction rebuilt from exact originals'
            ) AS summary_id
            """,
            (
                session["project_id"],
                incorrect_summary_id,
                f"corrected summary from {len(expected_ids)} originals",
            ),
        )
        corrected_summary_id = str(cur.fetchone()["summary_id"])
        cur.execute(
            """
            INSERT INTO agentcore.project_snapshots (
                project_id, repository_id, worktree_id, snapshot_kind, milestone,
                commit_sha, branch_name, changed_file_manifest, source_hashes,
                test_evidence_event_ids
            )
            SELECT p.id, p.repository_id, p.primary_worktree_id, 'recovery', 'M4',
                   %s, %s, %s::jsonb, %s::jsonb, %s::uuid[]
            FROM agentcore.projects p
            WHERE p.id = %s
            """,
            (
                "0" * 40,
                "test/recovery-integration",
                json.dumps(["scripts/agentcore_memory/server.py"]),
                json.dumps({"server.py": "0" * 64}),
                expected_ids,
                session["project_id"],
            ),
        )
        conn.commit()

    def create_concurrent_summary() -> str:
        with server.db() as concurrent_conn, concurrent_conn.cursor() as concurrent_cur:
            server.set_project(concurrent_conn, str(session["project_id"]))
            concurrent_cur.execute(
                """
                SELECT agentcore.create_context_summary(
                    %s, %s, 'L2', 'active_dynamic', 'Concurrent summary',
                    'same deterministic body', 4, 1.0, %s::uuid[], NULL,
                    'integration.concurrent.v1'
                ) AS summary_id
                """,
                (session["project_id"], session["session_id"], expected_ids),
            )
            summary_id = str(concurrent_cur.fetchone()["summary_id"])
            concurrent_conn.commit()
            return summary_id

    with ThreadPoolExecutor(max_workers=2) as executor:
        concurrent_ids = list(
            executor.map(lambda _: create_concurrent_summary(), range(2))
        )
    require(
        len(set(concurrent_ids)) == 1,
        "concurrent summary creation was not idempotent",
    )

    retrieved_ids: list[str] = []
    cursor: str | None = None
    page_number = 0
    while True:
        response = server.retrieve_context(
            {
                "project_key": project_key,
                "context_profile": "one-million-context",
                "recovery_mode": "complete_project_chronology",
                "page_size": 3,
                "continuation_cursor": cursor,
            }
        )
        require(response["ok"], "retrieve_context failed")
        page = response["recovery"]
        retrieved_ids.extend(page["source_ids"])
        cursor = page["continuation_cursor"]
        page_number += 1
        if not cursor:
            break
        if page_number == 1:
            cursor = json.loads(json.dumps({"cursor": cursor}))["cursor"]
            importlib.reload(server)
    require(
        retrieved_ids == [*expected_ids, *bulk_ids, archived_event_id],
        "chronology pagination was not count/order complete above one million tokens",
    )
    require(
        quarantined["event_id"] not in retrieved_ids,
        "quarantined event entered normal recovery",
    )

    expanded = server.expand_source({"event_id": expected_ids[0]})
    require(expanded["ok"], "expand_source failed")
    require(expanded["event"]["content_sha256"], "exact source hash missing")
    require(
        run_id in expanded["event"]["payload"]["verbatim"],
        "exact original payload was not recovered",
    )
    expanded_summary = server.expand_source(
        {
            "project_key": project_key,
            "summary_id": corrected_summary_id,
            "page_size": 20,
        }
    )
    require(
        expanded_summary["source_ids"] == sorted(expected_ids),
        "corrected summary did not retain all exact original source edges",
    )
    archived_event = server.expand_source(
        {"project_key": project_key, "event_id": archived_event_id}
    )
    archived_artifact = server.expand_source(
        {
            "project_key": project_key,
            "artifact_id": archived_event["event"]["artifact_id"],
            "max_bytes": 100000,
        }
    )
    require(
        archived_artifact["content_sha256_verified"]
        and "archived-original-" in archived_artifact["content"],
        "exact original did not expand after H:-to-E: archival",
    )

    startup = server.startup_context(
        {"project_key": project_key, "context_profile": "one-million-context"}
    )
    require(
        startup["context_profile"]["hard_context_limit"] == 1_000_000,
        "one-million profile was reduced",
    )
    require(
        max((int(item["cumulative_tokens"]) for item in startup["items"]), default=0)
        <= startup["context_profile"]["active_packet_limit"],
        "active packet exceeded the selected model limit",
    )
    require(
        len(startup["items"]) < len(retrieved_ids),
        "active packet incorrectly required loading the entire durable history",
    )
    default_context = server.retrieve_context({"project_key": project_key})
    require(
        default_context["context_profile"]["profile_name"] == "standard-context",
        "production default fell back to a small/4096 acceptance budget",
    )
    require(
        default_context["budget_name"] == "standard-context",
        "legacy budget_name response compatibility was not preserved",
    )
    try:
        server.retrieve_context(
            {"project_key": project_key, "context_profile": "unknown-profile"}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("unknown explicit context profile was silently lowered")

    handoff = server.build_handoff(
        {
            "project_key": project_key,
            "context_profile": "one-million-context",
            "recovery_mode": "current_state",
            "page_size": 3,
        }
    )
    require(handoff["ok"] and handoff["identity"], "build_handoff failed")
    require(handoff["recovery"]["source_ids"], "handoff recovery page is empty")
    require(
        archived_event_id in handoff["recovery"]["source_ids"],
        "current-state handoff omitted the latest project evidence",
    )
    require(
        handoff["continuation_cursor"], "bounded handoff omitted stable continuation"
    )
    require(
        handoff["governed_snapshots"],
        "governed Git snapshot metadata missing from handoff",
    )

    with server.db() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM agentcore.projects WHERE project_key = %s",
            (f"{project_key}-alternate",),
        )
        alternate_project_id = cur.fetchone()["id"]
        cur.execute("SET ROLE agentcore_worker")
        cur.execute(
            "SELECT set_config('agentcore.current_project_id', %s, true)",
            (str(session["project_id"]),),
        )
        cur.execute("SELECT count(*) AS count FROM agentcore.recovery_operations")
        require(
            cur.fetchone()["count"] > 0, "worker cannot read in-project recovery rows"
        )
        cur.execute("SELECT count(*) AS count FROM agentcore.project_snapshots")
        require(
            cur.fetchone()["count"] == 1, "worker cannot read in-project snapshot rows"
        )
        cur.execute(
            "SELECT set_config('agentcore.current_project_id', %s, true)",
            (str(alternate_project_id),),
        )
        cur.execute("SELECT count(*) AS count FROM agentcore.recovery_operations")
        require(cur.fetchone()["count"] == 0, "RLS leaked cross-project recovery rows")
        cur.execute("SELECT count(*) AS count FROM agentcore.project_snapshots")
        require(cur.fetchone()["count"] == 0, "RLS leaked cross-project snapshot rows")
        cur.execute(
            "SELECT set_config('agentcore.current_project_id', %s, true)",
            (str(session["project_id"]),),
        )
        cur.execute("SAVEPOINT cross_project_recovery")
        try:
            cur.execute(
                """
                INSERT INTO agentcore.recovery_operations (
                    project_id, recovery_mode, result_sha256
                ) VALUES (%s, 'current_state', %s)
                """,
                (alternate_project_id, "0" * 64),
            )
        except Exception:
            cur.execute("ROLLBACK TO SAVEPOINT cross_project_recovery")
        else:
            raise AssertionError("cross-project recovery insert was not rejected")
        cur.execute("RESET ROLE")
        conn.commit()

    closed = server.session_close({"session_id": session["session_id"]})
    require(closed["ok"], "session_close failed")
    alternate_closed = server.session_close({"session_id": alternate["session_id"]})
    require(alternate_closed["ok"], "alternate session_close failed")
    print(
        "PASS recovery integration: self-enroll, append, paginate, expand, startup, handoff"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
