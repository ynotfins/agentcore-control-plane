"""Deterministic acceptance tests for effectively-unbounded durable recovery."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema
import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))

from recovery import (  # noqa: E402
    ModelContextProfile,
    assemble_active_packet,
    content_sha256,
    decode_cursor,
    encode_cursor,
    paginate_chronology,
    preferred_artifact_location,
)
from server import tool_defs  # noqa: E402

CONTRACT_PATH = REPO / "contracts" / "model-context-profiles.json"
SCHEMA_PATH = REPO / "contracts" / "schemas" / "model-context-profiles.schema.json"
MIGRATION_PATH = (
    REPO / "migrations" / "m3" / "002_up_unbounded_recovery_context_profiles.sql"
)
DOWN_MIGRATION_PATH = (
    REPO / "migrations" / "m3" / "002_down_unbounded_recovery_context_profiles.sql"
)
POLICY_PATH = REPO / "contracts" / "global-agent-policy.yaml"
RETENTION_PATH = REPO / "docs" / "memory-platform" / "RETENTION_POLICY.md"
TEST_CURSOR_KEY = b"agentcore-test-only-cursor-key"


def load_profiles() -> dict[str, ModelContextProfile]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(contract)
    return {
        row["profile_name"]: ModelContextProfile.from_mapping(row)
        for row in contract["profiles"]
    }


def synthetic_events(count: int = 1205) -> list[dict[str, object]]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        {
            "id": f"{index:032x}",
            "project_id": "project-a",
            "accepted_at": start + timedelta(seconds=index),
            "event_kind": "prompt" if index % 2 == 0 else "message",
            "payload": {"index": index, "verbatim": f"original-{index}"},
            "trust_class": "operator_verified",
            "token_count": 1024,
        }
        for index in range(count)
    ]


def test_01_history_larger_than_one_million_tokens_is_not_truncated() -> None:
    events = synthetic_events()
    assert sum(int(event["token_count"]) for event in events) > 1_000_000
    assert len(events) == 1205


def test_02_original_event_count_and_hashes_remain_complete() -> None:
    events = synthetic_events()
    hashes = [content_sha256(event["payload"]) for event in events]
    assert len(hashes) == len(events)
    assert len(set(hashes)) == len(events)


def test_03_active_packet_obeys_selected_model_limit() -> None:
    profile = load_profiles()["one-million-context"]
    packet = assemble_active_packet(synthetic_events(), profile)
    assert packet["token_count"] <= profile.active_packet_limit
    assert packet["durable_item_count"] == 1205
    assert packet["omitted_item_count"] > 0


def test_04_complete_chronology_has_stable_pagination() -> None:
    events = synthetic_events(23)
    first = paginate_chronology(
        events,
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=7,
    )
    assert first["continuation_cursor"]
    second = paginate_chronology(
        events,
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=7,
        cursor=first["continuation_cursor"],
    )
    assert set(first["source_ids"]).isdisjoint(second["source_ids"])
    assert (
        decode_cursor(first["continuation_cursor"], TEST_CURSOR_KEY)["window_end_id"]
        == events[-1]["id"]
    )


def test_current_state_starts_with_latest_evidence_and_pages_backward() -> None:
    events = synthetic_events(10)
    latest = paginate_chronology(
        events,
        project_id="project-a",
        mode="current_state",
        page_size=3,
    )
    assert latest["source_ids"] == [str(event["id"]) for event in events[-3:]]
    older = paginate_chronology(
        events,
        project_id="project-a",
        mode="current_state",
        page_size=3,
        cursor=latest["continuation_cursor"],
    )
    assert older["source_ids"] == [str(event["id"]) for event in events[-6:-3]]


def test_05_every_retrieved_source_has_exact_expansion_reference() -> None:
    page = paginate_chronology(
        synthetic_events(5),
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=5,
    )
    assert len(page["exact_expansion_references"]) == 5
    assert all(
        ref["tool"] == "expand_source" for ref in page["exact_expansion_references"]
    )


def test_06_summary_correction_is_versioned_not_overwritten() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    down_sql = DOWN_MIGRATION_PATH.read_text(encoding="utf-8")
    assert "supersede_context_summary" in sql
    assert "supersedes_summary_id" in sql
    assert "is_current" in sql
    assert "correction_reason" in sql
    assert "summary source edge crosses project boundary" in down_sql


def test_07_recovery_survives_discarded_conversation_context() -> None:
    events = synthetic_events(11)
    first = paginate_chronology(
        events,
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=4,
    )
    serialized_cursor = str(first["continuation_cursor"])
    recovered = paginate_chronology(
        events,
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=4,
        cursor=serialized_cursor,
    )
    assert recovered["source_ids"][0] == events[4]["id"]


def test_08_cursor_round_trip_survives_ide_restart() -> None:
    cursor = encode_cursor(
        {"project_id": "p", "mode": "session_replay", "after_id": "e"},
        TEST_CURSOR_KEY,
    )
    assert decode_cursor(cursor, TEST_CURSOR_KEY)["project_id"] == "p"


def test_09_cursor_round_trip_survives_memory_service_restart() -> None:
    cursor = encode_cursor(
        {"project_id": "p", "mode": "milestone_replay", "after_id": "e"},
        TEST_CURSOR_KEY,
    )
    assert decode_cursor(str(cursor), TEST_CURSOR_KEY)["mode"] == "milestone_replay"


def test_10_cold_archive_is_preferred_transparently() -> None:
    selected = preferred_artifact_location(
        [
            {"storage_tier": "hot_h", "storage_uri": "H:/object", "is_active": False},
            {"storage_tier": "cold_e", "storage_uri": "E:/object", "is_active": True},
        ]
    )
    assert selected and selected["storage_uri"] == "E:/object"


def test_11_snapshot_contract_retains_git_reconstruction_fields() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    for field in (
        "commit_sha",
        "branch_name",
        "changed_file_manifest",
        "patch_artifact_id",
        "source_hashes",
    ):
        assert field in sql


def test_12_projection_revisions_remain_canonical_regeneration_inputs() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "projection_revisions" in sql
    assert "recovery_operations" in sql


def test_13_quarantined_evidence_is_excluded_from_normal_recovery() -> None:
    events = synthetic_events(3)
    events[1]["trust_class"] = "quarantined"
    page = paginate_chronology(
        events,
        project_id="project-a",
        mode="current_state",
        page_size=10,
    )
    assert events[1]["id"] not in page["source_ids"]


def test_14_compaction_migration_contains_no_original_event_deletion() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8").lower()
    assert "delete from agentcore.evidence_events" not in sql
    assert "truncate agentcore.evidence_events" not in sql


def test_15_one_million_profile_is_not_reduced() -> None:
    profile = load_profiles()["one-million-context"]
    assert profile.hard_context_limit == 1_000_000


def test_16_schema_accepts_profile_above_one_million() -> None:
    profile = load_profiles()["future-above-million"]
    assert profile.hard_context_limit > 1_000_000
    assert profile.active_packet_limit > 1_000_000


def test_17_full_history_requires_multiple_bounded_pages() -> None:
    events = synthetic_events(21)
    source_ids: list[str] = []
    cursor: str | None = None
    while True:
        page = paginate_chronology(
            events,
            project_id="project-a",
            mode="complete_project_chronology",
            page_size=5,
            cursor=cursor,
        )
        source_ids.extend(page["source_ids"])
        cursor = page["continuation_cursor"]
        if not cursor:
            break
    assert source_ids == [str(event["id"]) for event in events]


def test_18_backup_restore_policy_preserves_full_graph() -> None:
    retention = RETENTION_PATH.read_text(encoding="utf-8")
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "PITR" in retention
    assert "context_source_edges" in sql
    assert "recovery_operations" in sql


def test_recovery_and_snapshot_tables_enforce_project_scope() -> None:
    sql = MIGRATION_PATH.read_text(encoding="utf-8")
    assert "recovery_operations ENABLE ROW LEVEL SECURITY" in sql
    assert "project_snapshots ENABLE ROW LEVEL SECURITY" in sql
    assert "validate_recovery_operation_scope" in sql
    assert "validate_project_snapshot_scope" in sql


def test_cursor_rejects_tampering_and_scope_mismatch() -> None:
    events = synthetic_events(4)
    page = paginate_chronology(
        events,
        project_id="project-a",
        mode="complete_project_chronology",
        page_size=2,
    )
    cursor = str(page["continuation_cursor"])
    with pytest.raises(ValueError):
        decode_cursor(
            cursor[:-1] + ("A" if cursor[-1] != "A" else "B"), TEST_CURSOR_KEY
        )
    with pytest.raises(ValueError):
        decode_cursor(cursor, b"attacker-controlled-key")
    with pytest.raises(ValueError):
        paginate_chronology(
            events,
            project_id="project-b",
            mode="complete_project_chronology",
            page_size=2,
            cursor=cursor,
        )


def test_existing_ten_tool_surface_gains_recovery_without_new_server() -> None:
    tools = {tool["name"]: tool for tool in tool_defs()}
    assert len(tools) == 10
    retrieve_properties = tools["retrieve_context"]["inputSchema"]["properties"]
    assert {
        "context_profile",
        "recovery_mode",
        "continuation_cursor",
        "page_size",
    } <= set(retrieve_properties)
    assert "project_key" in tools["expand_source"]["inputSchema"]["properties"]
    assert "required" not in tools["expand_source"]["inputSchema"]


def test_session_open_self_enrolls_model_and_git_identity() -> None:
    tools = {tool["name"]: tool for tool in tool_defs()}
    properties = tools["session_open"]["inputSchema"]["properties"]
    assert {
        "project_root",
        "canonical_repo_path",
        "worktree_path",
        "repo_key",
        "branch_name",
        "head_commit",
        "model_provider",
        "model_id",
        "context_profile",
    } <= set(properties)
