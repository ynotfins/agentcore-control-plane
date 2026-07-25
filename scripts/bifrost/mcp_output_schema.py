#!/usr/bin/env python3
"""AgentCore MCP output-schema builder and result normalizer.

Single source of truth:
  schemas/tools/_shared/mcp-output-envelope.schema.json   (envelope + family data shapes)
  contracts/mcp-tool-output-schemas.json                  (server/tool -> profile binding)

This module is intentionally dependency-free (stdlib only) because it is imported by
scripts/bifrost/mcp_output_schema_adapter.py, which runs inside every upstream MCP
stdio launch. A missing third-party import there would take the whole gateway surface
down. Validation-only helpers that need `jsonschema` live in validate_output_schemas.py.

MCP 2025-06-18+ semantics:
  tool.outputSchema  describes CallToolResult.structuredContent
  content[]          stays human-readable and is never rewritten here
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = REPO_ROOT / "contracts" / "mcp-tool-output-schemas.json"

ENVELOPE_KEYS: tuple[str, ...] = (
    "success",
    "status",
    "summary",
    "data",
    "evidence",
    "warnings",
    "errors",
    "next_actions",
    "meta",
)

# Keys removed from every emitted outputSchema (never valid inside an MCP tool schema
# or purely authoring metadata).
_ALWAYS_STRIP = {"$schema", "$id", "envelope_version", "$comment", "examples"}
# Keys removed additionally when detail == "compact" (bounds tools/list size).
_DOC_STRIP = {"description", "title"}
# Sub-objects whose *keys* are names, not schema keywords.
_NAME_KEYED = {"properties", "$defs", "definitions", "patternProperties", "dependentSchemas"}

_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}"),
    re.compile(r"(?i)\b(?:api[_-]?key|password|passwd|secret|access[_-]?token)\b\s*[:=]\s*\S{6,}"),
)
_REDACTION = "[REDACTED]"

_WS = re.compile(r"\s+")


# --------------------------------------------------------------------------- loading


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_contract(contract_path: Path | str | None = None) -> dict[str, Any]:
    path = Path(contract_path) if contract_path else DEFAULT_CONTRACT_PATH
    return load_json(path)


def load_envelope_source(contract: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or REPO_ROOT
    rel = str(contract["envelope_schema_path"]).replace("\\", "/")
    return load_json(root / rel)


# ------------------------------------------------------------------- schema building


def _inline_refs(node: Any, defs: dict[str, Any], depth: int = 0) -> Any:
    if depth > 12:
        return node
    if isinstance(node, list):
        return [_inline_refs(item, defs, depth + 1) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/$defs/"):
        target: Any = defs
        for part in ref[len("#/$defs/"):].split("/"):
            if not isinstance(target, dict) or part not in target:
                target = None
                break
            target = target[part]
        if isinstance(target, dict):
            merged = copy.deepcopy(target)
            for key, value in node.items():
                if key != "$ref":
                    merged[key] = value
            return _inline_refs(merged, defs, depth + 1)
    return {key: _inline_refs(value, defs, depth + 1) for key, value in node.items()}


def _strip_schema(node: Any, keep_docs: bool) -> Any:
    if isinstance(node, list):
        return [_strip_schema(item, keep_docs) for item in node]
    if not isinstance(node, dict):
        return node
    out: dict[str, Any] = {}
    for key, value in node.items():
        if key in _ALWAYS_STRIP:
            continue
        if not keep_docs and key in _DOC_STRIP:
            continue
        if key in _NAME_KEYED and isinstance(value, dict):
            out[key] = {name: _strip_schema(sub, keep_docs) for name, sub in value.items()}
        else:
            out[key] = _strip_schema(value, keep_docs)
    return out


def family_names(envelope_src: dict[str, Any]) -> list[str]:
    families = (envelope_src.get("$defs") or {}).get("family_data") or {}
    return [name for name, value in families.items() if isinstance(value, dict) and "type" in value]


def build_output_schema(
    envelope_src: dict[str, Any],
    family: str,
    detail: str = "compact",
) -> dict[str, Any]:
    """Return a self-contained outputSchema for one family.

    Self-contained matters: MCP clients receive each tool definition in isolation and
    cannot resolve cross-document $ref, so all internal $defs are inlined and dropped.
    """
    defs = envelope_src.get("$defs") or {}
    families = defs.get("family_data") or {}
    shape = families.get(family)
    if not isinstance(shape, dict) or "type" not in shape:
        raise KeyError(f"unknown output-schema family: {family!r}")

    root = {key: value for key, value in envelope_src.items() if key != "$defs"}
    root = copy.deepcopy(root)
    data_shape = copy.deepcopy(shape)
    if "description" not in data_shape:
        existing = (envelope_src.get("properties") or {}).get("data") or {}
        if isinstance(existing, dict) and "description" in existing:
            data_shape["description"] = existing["description"]
    root["properties"]["data"] = data_shape

    inlined = _inline_refs(root, defs)
    built = _strip_schema(inlined, keep_docs=(detail == "full"))
    if detail == "minimal":
        built = _minimize(built)
    return built


def _minimize(schema: dict[str, Any]) -> dict[str, Any]:
    """Collapse boilerplate sub-schemas that repeat identically on every tool.

    Envelope keys and their top-level types survive, so structuredContent still
    validates; only the evidence/error/meta item shapes and the family data hints
    are dropped. Roughly 460B per tool instead of ~1.5KB — use when tools/list size
    matters more than per-tool schema detail.
    """
    props = schema.get("properties") or {}
    for key in ("evidence", "warnings", "errors", "next_actions"):
        if key in props:
            props[key] = {"type": "array"}
    if "meta" in props:
        props["meta"] = {"type": "object"}
    if "data" in props:
        props["data"] = {"type": props["data"].get("type", ["object", "array", "null"])}
    return schema


class OutputSchemaResolver:
    """Resolves (server, tool) -> advertised outputSchema, with per-family caching."""

    def __init__(
        self,
        contract: dict[str, Any] | None = None,
        envelope_src: dict[str, Any] | None = None,
        repo_root: Path | None = None,
        contract_path: Path | str | None = None,
    ) -> None:
        self.contract = contract if contract is not None else load_contract(contract_path)
        self.repo_root = repo_root or REPO_ROOT
        self.envelope_src = (
            envelope_src
            if envelope_src is not None
            else load_envelope_source(self.contract, self.repo_root)
        )
        self.defaults: dict[str, Any] = dict(self.contract.get("defaults") or {})
        self.envelope_version: str = str(
            self.contract.get("envelope_version")
            or self.envelope_src.get("envelope_version")
            or "1.0.0"
        )
        self._cache: dict[str, dict[str, Any]] = {}

    # -- profile resolution -------------------------------------------------
    def server_entry(self, server_id: str) -> dict[str, Any]:
        return (self.contract.get("servers") or {}).get(server_id) or {}

    def adapter_mode(self, server_id: str) -> str:
        return str(self.server_entry(server_id).get("adapter") or "unsupported")

    def profile_for(self, server_id: str, tool_name: str) -> str:
        entry = self.server_entry(server_id)
        overrides = entry.get("tool_profiles") or {}
        profile = overrides.get(tool_name) or entry.get("default_profile") or "generic"
        if profile not in (self.contract.get("profiles") or {}):
            profile = "generic"
        return str(profile)

    def family_for(self, server_id: str, tool_name: str) -> str:
        profile = self.profile_for(server_id, tool_name)
        profiles = self.contract.get("profiles") or {}
        return str((profiles.get(profile) or {}).get("family") or "generic")

    # -- schema -------------------------------------------------------------
    def schema_for_family(self, family: str) -> dict[str, Any]:
        detail = str(self.defaults.get("detail") or "compact")
        cache_key = f"{family}:{detail}"
        if cache_key not in self._cache:
            self._cache[cache_key] = build_output_schema(self.envelope_src, family, detail)
        return self._cache[cache_key]

    def output_schema(self, server_id: str, tool_name: str) -> dict[str, Any]:
        return copy.deepcopy(self.schema_for_family(self.family_for(server_id, tool_name)))

    # -- result normalization ----------------------------------------------
    def envelope(
        self,
        *,
        tool: str,
        server: str,
        content: Any,
        structured: Any,
        is_error: bool,
    ) -> dict[str, Any]:
        return build_envelope(
            tool=tool,
            server=server,
            content=content,
            structured=structured,
            is_error=is_error,
            defaults=self.defaults,
            envelope_version=self.envelope_version,
        )


# --------------------------------------------------------------- result normalization


def looks_like_envelope(value: Any) -> bool:
    return isinstance(value, dict) and all(key in value for key in ENVELOPE_KEYS)


def redact(text: str) -> tuple[str, bool]:
    redacted = False
    for pattern in _SECRET_PATTERNS:
        text, count = pattern.subn(_REDACTION, text)
        redacted = redacted or bool(count)
    return text, redacted


def _text_blocks(content: Any) -> str:
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            value = block.get("text")
            if isinstance(value, str) and value:
                parts.append(value)
    return "\n".join(parts)


def _first_str(source: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _describe(data: Any, tool: str) -> str:
    """Compact, non-duplicating description of a structured payload."""
    if isinstance(data, dict):
        keys = [str(k) for k in list(data.keys())[:8]]
        extra = len(data) - len(keys)
        listed = ", ".join(keys) if keys else "no keys"
        suffix = f" (+{extra} more)" if extra > 0 else ""
        return f"{tool} returned an object with keys: {listed}{suffix}."
    if isinstance(data, list):
        return f"{tool} returned {len(data)} item(s)."
    return f"{tool} completed."


def _derive_summary(tool: str, data: Any, text: str) -> str:
    """Explicit upstream summary > prose text > payload shape description.

    A serialized-JSON text block is never copied into summary: the same payload is
    already carried as structuredContent.data and duplicating it wastes context.
    """
    if isinstance(data, dict):
        explicit = _first_str(data, "summary", "message", "status_text")
        if explicit:
            return explicit
    prose = text.strip()
    if prose and not prose.startswith(("{", "[")):
        return prose
    if data is not None:
        return _describe(data, tool)
    if prose:
        return prose
    return f"{tool} returned no textual content."


def build_envelope(
    *,
    tool: str,
    server: str,
    content: Any,
    structured: Any,
    is_error: bool,
    defaults: dict[str, Any] | None = None,
    envelope_version: str = "1.0.0",
) -> dict[str, Any]:
    """Wrap one CallToolResult payload into the canonical envelope.

    `content` is read-only here — callers keep the original human-readable blocks.
    """
    cfg = defaults or {}
    max_summary = int(cfg.get("max_summary_chars") or 400)
    max_bytes = int(cfg.get("max_structured_bytes") or 131072)
    promote_json = bool(cfg.get("structured_from_text_json", True))

    warnings: list[str] = []
    data: Any = None

    if isinstance(structured, (dict, list)):
        data = structured
    elif structured is not None:
        data = {"value": structured}

    text = _text_blocks(content)

    if data is None and promote_json and text:
        stripped = text.strip()
        if len(stripped) > max_bytes:
            warnings.append(
                "structured_data_omitted: upstream text exceeded max_structured_bytes"
            )
        elif stripped[:1] in ("{", "["):
            try:
                parsed = json.loads(stripped)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, (dict, list)):
                data = parsed

    summary_source = _derive_summary(tool, data, text)

    summary = _WS.sub(" ", summary_source).strip()
    if len(summary) > max_summary:
        summary = summary[: max_summary - 1].rstrip() + "\u2026"
    summary, redacted = redact(summary)

    errors: list[dict[str, Any]] = []
    if is_error:
        errors.append(
            {
                "code": "upstream_tool_error",
                "message": summary or "upstream tool reported an error",
                "retryable": False,
            }
        )

    if is_error:
        status = "error"
    elif warnings:
        status = "partial"
    else:
        status = "ok"

    meta: dict[str, Any] = {
        "tool": tool,
        "server": server,
        "schema_version": envelope_version,
        "redacted": redacted,
    }
    if isinstance(data, dict):
        project_key = _first_str(data, "project_key", "projectKey")
        if project_key:
            meta["project_key"] = project_key
        session_key = _first_str(data, "session_key", "sessionKey")
        if session_key:
            meta["session_key"] = session_key
        event_id = _first_str(data, "event_id", "eventId")
        if event_id:
            meta["event_id"] = event_id
        cursor = _first_str(data, "continuation_cursor", "cursor", "nextCursor")
        if cursor:
            meta["cursor"] = cursor

    return {
        "success": not is_error,
        "status": status,
        "summary": summary,
        "data": data,
        "evidence": [],
        "warnings": warnings,
        "errors": errors,
        "next_actions": [],
        "meta": meta,
    }


def normalize_call_result(
    result: Any,
    *,
    tool: str,
    server: str,
    resolver: OutputSchemaResolver,
) -> Any:
    """Attach a conforming structuredContent to a tools/call result (idempotent)."""
    if not isinstance(result, dict):
        return result
    existing = result.get("structuredContent")
    if looks_like_envelope(existing):
        return result
    result["structuredContent"] = resolver.envelope(
        tool=tool,
        server=server,
        content=result.get("content"),
        structured=existing,
        is_error=bool(result.get("isError")),
    )
    return result


def inject_output_schemas(
    result: Any,
    *,
    server: str,
    resolver: OutputSchemaResolver,
) -> Any:
    """Add tool.outputSchema to a tools/list result for tools that lack one."""
    if not isinstance(result, dict):
        return result
    tools = result.get("tools")
    if not isinstance(tools, list):
        return result
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        if not isinstance(name, str) or not name:
            continue
        if isinstance(tool.get("outputSchema"), dict):
            continue
        tool["outputSchema"] = resolver.output_schema(server, name)
    return result


# ------------------------------------------------------------------------- self test


def self_test(resolver: OutputSchemaResolver | None = None) -> list[str]:
    """Offline proof that emitted envelopes satisfy the emitted schemas.

    Returns a list of failure strings (empty == pass). Uses jsonschema when available;
    otherwise falls back to structural key checks so the adapter can self-test without
    third-party packages.
    """
    failures: list[str] = []
    res = resolver or OutputSchemaResolver()

    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except ImportError:  # pragma: no cover - adapter host may lack jsonschema
        Draft202012Validator = None  # type: ignore[assignment]

    samples: list[tuple[str, Any, Any, bool]] = [
        ("text_only", [{"type": "text", "text": "plain human readable output"}], None, False),
        ("json_text", [{"type": "text", "text": '{"ok": true, "count": 2}'}], None, False),
        ("structured", [{"type": "text", "text": "{}"}], {"ok": True, "project_key": "p"}, False),
        ("error", [{"type": "text", "text": "boom: sk-abcdefghijklmnop"}], None, True),
        ("empty", [], None, False),
        ("array_struct", [{"type": "text", "text": "[]"}], [1, 2, 3], False),
    ]

    for family in family_names(res.envelope_src):
        schema = res.schema_for_family(family)
        if Draft202012Validator is not None:
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:  # noqa: BLE001 - report any invalid schema
                failures.append(f"{family}: emitted schema is not valid JSON Schema: {exc}")
                continue
        for label, content, structured, is_error in samples:
            envelope = build_envelope(
                tool="sample_tool",
                server="sample-server",
                content=content,
                structured=structured,
                is_error=is_error,
                defaults=res.defaults,
                envelope_version=res.envelope_version,
            )
            missing = [key for key in ENVELOPE_KEYS if key not in envelope]
            if missing:
                failures.append(f"{family}/{label}: envelope missing keys {missing}")
                continue
            extra = [key for key in envelope if key not in ENVELOPE_KEYS]
            if extra:
                failures.append(f"{family}/{label}: envelope has extra keys {extra}")
            if Draft202012Validator is not None:
                errors = sorted(
                    Draft202012Validator(schema).iter_errors(envelope),
                    key=lambda e: list(e.path),
                )
                for err in errors[:3]:
                    path = ".".join(str(p) for p in err.path) or "<root>"
                    failures.append(f"{family}/{label}: {path}: {err.message}")

    # Redaction proof: a secret-looking token must never reach envelope.summary.
    leak_probe = build_envelope(
        tool="redaction_probe",
        server="sample-server",
        content=[{"type": "text", "text": "token sk-abcdefghijklmnopqrst leaked"}],
        structured=None,
        is_error=False,
        defaults=res.defaults,
        envelope_version=res.envelope_version,
    )
    if "sk-abcdefghijklmnopqrst" in leak_probe["summary"]:
        failures.append("redaction: secret-looking token survived into envelope.summary")
    if not leak_probe["meta"]["redacted"]:
        failures.append("redaction: meta.redacted not set after masking")

    # Idempotency proof: an already-normalized envelope is never double-wrapped.
    if not looks_like_envelope(leak_probe):
        failures.append("envelope: looks_like_envelope() rejected a freshly built envelope")

    return failures


if __name__ == "__main__":  # pragma: no cover - manual invocation
    import sys

    problems = self_test()
    if problems:
        print(f"FAILED ({len(problems)})")
        for item in problems:
            print(f"  - {item}")
        sys.exit(1)
    print("OK: mcp_output_schema self-test passed")
