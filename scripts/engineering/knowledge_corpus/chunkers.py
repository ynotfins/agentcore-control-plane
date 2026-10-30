"""Smart chunkers: Markdown headers, OpenAPI ops, Tree-sitter (or regex fallback)."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Chunk:
    chunk_id: str
    title: str
    body: str
    language: str
    extra_metadata: dict[str, Any] = field(default_factory=dict)


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_chunk_id(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


_MD_HEADER = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def chunk_markdown(path: Path, text: str) -> list[Chunk]:
    matches = list(_MD_HEADER.finditer(text))
    if not matches:
        body = text.strip()
        if not body:
            return []
        cid = stable_chunk_id(str(path), "whole", content_sha256(body))
        return [
            Chunk(
                chunk_id=cid,
                title=path.stem,
                body=body,
                language="markdown",
                extra_metadata={"heading_level": 0},
            )
        ]

    chunks: list[Chunk] = []
    # Leading prose before first header
    if matches[0].start() > 0:
        lead = text[: matches[0].start()].strip()
        if lead:
            cid = stable_chunk_id(str(path), "lead", content_sha256(lead))
            chunks.append(
                Chunk(
                    chunk_id=cid,
                    title=f"{path.stem} (preamble)",
                    body=lead,
                    language="markdown",
                    extra_metadata={"heading_level": 0},
                )
            )

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        level = len(match.group(1))
        heading = match.group(2).strip()
        cid = stable_chunk_id(str(path), heading, str(level), content_sha256(body))
        chunks.append(
            Chunk(
                chunk_id=cid,
                title=heading,
                body=body,
                language="markdown",
                extra_metadata={"heading_level": level},
            )
        )
    return chunks


def chunk_openapi(path: Path, text: str) -> list[Chunk]:
    try:
        import yaml  # type: ignore

        spec = yaml.safe_load(text)
    except Exception:
        try:
            spec = json.loads(text)
        except Exception:
            return chunk_markdown(path, text)

    if not isinstance(spec, dict):
        return chunk_markdown(path, text)

    info = spec.get("info") or {}
    title_base = str(info.get("title") or path.stem)
    version = str(info.get("version") or "unknown")
    paths = spec.get("paths") or {}
    chunks: list[Chunk] = []

    # Spec overview
    overview = {
        "openapi": spec.get("openapi") or spec.get("swagger"),
        "info": info,
        "servers": spec.get("servers"),
        "tags": spec.get("tags"),
    }
    overview_body = json.dumps(overview, indent=2, default=str)
    chunks.append(
        Chunk(
            chunk_id=stable_chunk_id(str(path), "overview", content_sha256(overview_body)),
            title=f"{title_base} overview",
            body=overview_body,
            language="yaml",
            extra_metadata={"openapi_part": "overview", "api_version": version},
        )
    )

    if not isinstance(paths, dict):
        return chunks

    for route, methods in paths.items():
        if not isinstance(methods, dict):
            continue
        for method, op in methods.items():
            if method.startswith("x-") or method == "parameters":
                continue
            if not isinstance(op, dict):
                continue
            op_id = str(op.get("operationId") or f"{method}_{route}")
            body_obj = {
                "path": route,
                "method": method.upper(),
                "operationId": op.get("operationId"),
                "summary": op.get("summary"),
                "description": op.get("description"),
                "parameters": op.get("parameters"),
                "requestBody": op.get("requestBody"),
                "responses": op.get("responses"),
                "tags": op.get("tags"),
            }
            body = json.dumps(body_obj, indent=2, default=str)
            chunks.append(
                Chunk(
                    chunk_id=stable_chunk_id(
                        str(path), method.upper(), route, content_sha256(body)
                    ),
                    title=f"{method.upper()} {route} — {op_id}",
                    body=body,
                    language="yaml",
                    extra_metadata={
                        "openapi_part": "operation",
                        "http_method": method.upper(),
                        "http_path": route,
                        "operation_id": op_id,
                        "api_version": version,
                    },
                )
            )
    return chunks


_PY_DEF = re.compile(
    r"^(?:async\s+)?def\s+(\w+)\s*\(|^class\s+(\w+)\s*[\(:]",
    re.MULTILINE,
)
_TS_DEF = re.compile(
    r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)|"
    r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)|"
    r"^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(",
    re.MULTILINE,
)


def _chunk_by_regex(
    path: Path, text: str, language: str, pattern: re.Pattern[str]
) -> list[Chunk]:
    matches = list(pattern.finditer(text))
    if not matches:
        body = text.strip()
        if not body:
            return []
        return [
            Chunk(
                chunk_id=stable_chunk_id(str(path), "module", content_sha256(body)),
                title=path.name,
                body=body,
                language=language,
                extra_metadata={"symbol": path.stem, "chunk_strategy": "whole_file"},
            )
        ]

    chunks: list[Chunk] = []
    # Module preamble
    if matches[0].start() > 0:
        lead = text[: matches[0].start()].strip()
        if lead:
            chunks.append(
                Chunk(
                    chunk_id=stable_chunk_id(str(path), "module_lead", content_sha256(lead)),
                    title=f"{path.name} (module)",
                    body=lead,
                    language=language,
                    extra_metadata={"symbol": path.stem, "chunk_strategy": "module_lead"},
                )
            )

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        symbol = next((g for g in match.groups() if g), f"sym_{i}")
        chunks.append(
            Chunk(
                chunk_id=stable_chunk_id(str(path), symbol, content_sha256(body)),
                title=f"{path.name}::{symbol}",
                body=body,
                language=language,
                extra_metadata={"symbol": symbol, "chunk_strategy": "regex_scope"},
            )
        )
    return chunks


def _make_tree_sitter_parser(language: str) -> Any | None:
    """Prefer per-language packages (Python 3.13); fall back to tree_sitter_languages."""
    try:
        from tree_sitter import Language, Parser  # type: ignore
    except Exception:
        return None

    lang_obj = None
    try:
        if language == "python":
            import tree_sitter_python as tsp  # type: ignore

            lang_obj = Language(tsp.language())
        elif language == "typescript":
            import tree_sitter_typescript as tst  # type: ignore

            lang_obj = Language(tst.language_typescript())
        elif language == "tsx":
            import tree_sitter_typescript as tst  # type: ignore

            lang_obj = Language(tst.language_tsx())
    except Exception:
        lang_obj = None

    if lang_obj is None:
        try:
            import tree_sitter_languages  # type: ignore

            return tree_sitter_languages.get_parser(language)
        except Exception:
            return None

    parser = Parser(lang_obj)
    return parser


def _chunk_with_tree_sitter(path: Path, text: str, language: str) -> list[Chunk] | None:
    """Return Tree-sitter chunks or None if grammar/runtime unavailable."""
    parser = _make_tree_sitter_parser(language)
    if parser is None:
        return None

    try:
        tree = parser.parse(bytes(text, "utf8"))
    except Exception:
        return None

    root = tree.root_node
    target_types = {
        "python": {"function_definition", "class_definition", "async_function_definition"},
        "typescript": {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "lexical_declaration",
            "export_statement",
        },
        "tsx": {
            "function_declaration",
            "class_declaration",
            "method_definition",
            "lexical_declaration",
            "export_statement",
        },
    }.get(language, set())

    if not target_types:
        return None

    source_bytes = bytes(text, "utf8")
    chunks: list[Chunk] = []

    def walk(node: Any) -> None:
        if node.type in target_types:
            body = source_bytes[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            if len(body.strip()) < 8:
                return
            name = path.stem
            for child in node.children:
                if child.type in {"identifier", "type_identifier", "property_identifier"}:
                    name = source_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    break
            chunks.append(
                Chunk(
                    chunk_id=stable_chunk_id(str(path), name, str(node.start_byte), content_sha256(body)),
                    title=f"{path.name}::{name}",
                    body=body.strip(),
                    language=language,
                    extra_metadata={
                        "symbol": name,
                        "chunk_strategy": "tree_sitter",
                        "node_type": node.type,
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte,
                    },
                )
            )
            return
        for child in node.children:
            walk(child)

    walk(root)
    return chunks or None


def chunk_code(path: Path, text: str) -> list[Chunk]:
    suffix = path.suffix.lower()
    if suffix == ".py":
        language = "python"
        ts = _chunk_with_tree_sitter(path, text, "python")
        if ts:
            return ts
        return _chunk_by_regex(path, text, language, _PY_DEF)
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        language = "tsx" if suffix == ".tsx" else "typescript" if suffix == ".ts" else "javascript"
        grammar = "tsx" if suffix == ".tsx" else "typescript"
        ts = _chunk_with_tree_sitter(path, text, grammar)
        if ts:
            return ts
        return _chunk_by_regex(path, text, language, _TS_DEF)
    # Fallback: treat as markdown-ish text
    return chunk_markdown(path, text)


def chunk_file(path: Path, asset_type: str) -> list[Chunk]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if asset_type == "openapi" or suffix in {".yaml", ".yml", ".json"} and (
        "openapi" in path.name.lower() or asset_type == "openapi"
    ):
        # Prefer OpenAPI parse for openapi asset dir or openapi-named files
        if asset_type == "openapi" or "openapi" in path.name.lower() or "swagger" in path.name.lower():
            return chunk_openapi(path, text)
    if asset_type == "boilerplate" and suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
        return chunk_code(path, text)
    if suffix in {".md", ".mdc", ".txt"} or asset_type in {"docs", "agent_rule"}:
        return chunk_markdown(path, text)
    if suffix in {".py", ".ts", ".tsx", ".js", ".jsx"}:
        return chunk_code(path, text)
    if suffix in {".yaml", ".yml", ".json"}:
        return chunk_openapi(path, text)
    body = text.strip()
    if not body:
        return []
    return [
        Chunk(
            chunk_id=stable_chunk_id(str(path), "raw", content_sha256(body)),
            title=path.name,
            body=body,
            language=suffix.lstrip(".") or "text",
            extra_metadata={"chunk_strategy": "raw"},
        )
    ]
