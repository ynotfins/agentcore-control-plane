"""Deterministic helpers for model-aware context and lossless recovery.

The durable ledger is never bounded by these helpers.  Limits apply only to one
active packet or one chronological retrieval page.
"""

from __future__ import annotations

import base64
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

CURSOR_VERSION = 1
RECOVERY_MODES = frozenset(
    {
        "current_state",
        "current_milestone",
        "session_replay",
        "milestone_replay",
        "time_range_replay",
        "decision_history",
        "failure_fix_reconstruction",
        "complete_project_chronology",
    }
)
EXCLUDED_NORMAL_TRUST_CLASSES = frozenset({"quarantined", "rejected"})


def canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=str
    )


def content_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def estimate_tokens(value: Any) -> int:
    """Return a deterministic conservative estimate when no provider tokenizer is loaded."""
    return max(1, math.ceil(len(canonical_json(value).encode("utf-8")) / 4))


@dataclass(frozen=True)
class ModelContextProfile:
    profile_name: str
    provider: str
    model_id: str
    hard_context_limit: int
    safe_active_context_ceiling: int
    reserved_output_tokens: int
    reserved_tool_schema_tokens: int
    reserved_tool_result_tokens: int
    safety_reserve_tokens: int
    soft_compaction_threshold_tokens: int
    hard_compaction_threshold_tokens: int
    retrieval_page_size: int
    tokenizer: str
    last_validated_date: str
    validation_source: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ModelContextProfile":
        profile = cls(
            profile_name=str(value["profile_name"]),
            provider=str(value["provider"]),
            model_id=str(value["model_id"]),
            hard_context_limit=int(value["hard_context_limit"]),
            safe_active_context_ceiling=int(value["safe_active_context_ceiling"]),
            reserved_output_tokens=int(value["reserved_output_tokens"]),
            reserved_tool_schema_tokens=int(value["reserved_tool_schema_tokens"]),
            reserved_tool_result_tokens=int(value["reserved_tool_result_tokens"]),
            safety_reserve_tokens=int(value["safety_reserve_tokens"]),
            soft_compaction_threshold_tokens=int(
                value["soft_compaction_threshold_tokens"]
            ),
            hard_compaction_threshold_tokens=int(
                value["hard_compaction_threshold_tokens"]
            ),
            retrieval_page_size=int(value["retrieval_page_size"]),
            tokenizer=str(value["tokenizer"]),
            last_validated_date=str(value["last_validated_date"]),
            validation_source=str(value["validation_source"]),
        )
        profile.validate()
        return profile

    @property
    def reserved_tokens(self) -> int:
        return (
            self.reserved_output_tokens
            + self.reserved_tool_schema_tokens
            + self.reserved_tool_result_tokens
            + self.safety_reserve_tokens
        )

    @property
    def usable_hard_limit(self) -> int:
        return self.hard_context_limit - self.reserved_tokens

    @property
    def active_packet_limit(self) -> int:
        return min(self.safe_active_context_ceiling, self.usable_hard_limit)

    def validate(self) -> None:
        positive = {
            "hard_context_limit": self.hard_context_limit,
            "safe_active_context_ceiling": self.safe_active_context_ceiling,
            "retrieval_page_size": self.retrieval_page_size,
        }
        if any(value <= 0 for value in positive.values()):
            raise ValueError(f"profile values must be positive: {positive}")
        if any(
            value < 0
            for value in (
                self.reserved_output_tokens,
                self.reserved_tool_schema_tokens,
                self.reserved_tool_result_tokens,
                self.safety_reserve_tokens,
            )
        ):
            raise ValueError("reserved token fields cannot be negative")
        if self.safe_active_context_ceiling > self.usable_hard_limit:
            raise ValueError("safe active ceiling exceeds hard limit after reserves")
        if not (
            0
            < self.soft_compaction_threshold_tokens
            < self.hard_compaction_threshold_tokens
            <= self.safe_active_context_ceiling
        ):
            raise ValueError(
                "compaction thresholds must be ordered within the safe active ceiling"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            **self.__dict__,
            "reserved_tokens": self.reserved_tokens,
            "active_packet_limit": self.active_packet_limit,
        }


def assemble_active_packet(
    items: Sequence[Mapping[str, Any]], profile: ModelContextProfile
) -> dict[str, Any]:
    """Select a bounded prefix without mutating or deleting durable input."""
    selected: list[dict[str, Any]] = []
    used = 0
    for item in items:
        token_count = max(0, int(item.get("token_count") or estimate_tokens(item)))
        if used + token_count > profile.active_packet_limit:
            break
        selected.append(dict(item))
        used += token_count
    return {
        "items": selected,
        "token_count": used,
        "active_packet_limit": profile.active_packet_limit,
        "omitted_item_count": len(items) - len(selected),
        "durable_item_count": len(items),
    }


def _cursor_checksum(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def encode_cursor(payload: Mapping[str, Any]) -> str:
    body = {"v": CURSOR_VERSION, **dict(payload)}
    envelope = {"payload": body, "checksum": _cursor_checksum(body)}
    raw = canonical_json(envelope).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_cursor(cursor: str) -> dict[str, Any]:
    try:
        padding = "=" * (-len(cursor) % 4)
        envelope = json.loads(base64.urlsafe_b64decode(cursor + padding))
        payload = envelope["payload"]
        checksum = envelope["checksum"]
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid continuation cursor") from exc
    if payload.get("v") != CURSOR_VERSION or checksum != _cursor_checksum(payload):
        raise ValueError("invalid continuation cursor checksum or version")
    return dict(payload)


def recovery_scope_hash(scope: Mapping[str, Any]) -> str:
    return content_sha256(scope)


def _as_utc_iso(value: Any) -> str:
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def enrich_event(event: Mapping[str, Any]) -> dict[str, Any]:
    event_id = str(event["id"])
    payload = event.get("payload") or {}
    return {
        **dict(event),
        "id": event_id,
        "source_id": event_id,
        "accepted_at": _as_utc_iso(event["accepted_at"]),
        "trust_class": str(event.get("trust_class") or "raw_untrusted"),
        "content_sha256": content_sha256(payload),
        "exact_expansion_reference": {"tool": "expand_source", "event_id": event_id},
    }


def paginate_chronology(
    events: Iterable[Mapping[str, Any]],
    *,
    project_id: str,
    mode: str,
    page_size: int,
    scope: Mapping[str, Any] | None = None,
    cursor: str | None = None,
    include_quarantined: bool = False,
) -> dict[str, Any]:
    """Reference keyset pagination used by deterministic tests and DB adapters."""
    if mode not in RECOVERY_MODES:
        raise ValueError(f"unsupported recovery mode: {mode}")
    if page_size <= 0:
        raise ValueError("page_size must be positive")

    requested_scope = {"project_id": project_id, "mode": mode, **dict(scope or {})}
    scope_digest = recovery_scope_hash(requested_scope)
    rows = [enrich_event(row) for row in events if str(row["project_id"]) == project_id]
    if not include_quarantined:
        rows = [
            row
            for row in rows
            if row["trust_class"] not in EXCLUDED_NORMAL_TRUST_CLASSES
        ]
    rows.sort(key=lambda row: (row["accepted_at"], row["id"]))

    after: tuple[str, str] | None = None
    window_end = (rows[-1]["accepted_at"], rows[-1]["id"]) if rows else None
    if cursor:
        state = decode_cursor(cursor)
        if (
            state.get("project_id") != project_id
            or state.get("mode") != mode
            or state.get("scope_hash") != scope_digest
        ):
            raise ValueError("continuation cursor scope mismatch")
        after = (str(state["after_at"]), str(state["after_id"]))
        window_end = (str(state["window_end_at"]), str(state["window_end_id"]))

    bounded = rows
    if window_end:
        bounded = [
            row for row in bounded if (row["accepted_at"], row["id"]) <= window_end
        ]
    if after:
        bounded = [row for row in bounded if (row["accepted_at"], row["id"]) > after]

    page = bounded[:page_size]
    omitted = max(0, len(bounded) - len(page))
    next_cursor = None
    if omitted and page and window_end:
        last = page[-1]
        next_cursor = encode_cursor(
            {
                "project_id": project_id,
                "mode": mode,
                "scope_hash": scope_digest,
                "after_at": last["accepted_at"],
                "after_id": last["id"],
                "window_end_at": window_end[0],
                "window_end_id": window_end[1],
            }
        )

    return {
        "mode": mode,
        "scope": requested_scope,
        "items": page,
        "source_ids": [row["source_id"] for row in page],
        "trust_classifications": [row["trust_class"] for row in page],
        "content_hashes": [row["content_sha256"] for row in page],
        "exact_expansion_references": [
            row["exact_expansion_reference"] for row in page
        ],
        "continuation_cursor": next_cursor,
        "omitted_item_count": omitted,
        "chronological_boundaries": {
            "page_start": page[0]["accepted_at"] if page else None,
            "page_end": page[-1]["accepted_at"] if page else None,
            "window_end": window_end[0] if window_end else None,
        },
    }


def preferred_artifact_location(
    locations: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    active = [row for row in locations if row.get("is_active", True)]
    if not active:
        return None
    return sorted(
        active,
        key=lambda row: (
            0 if row.get("storage_tier") == "cold_e" else 1,
            str(row.get("created_at") or ""),
        ),
    )[0]
