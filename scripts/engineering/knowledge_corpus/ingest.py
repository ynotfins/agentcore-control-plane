"""CLI: ingest knowledge-corpus files into agentcore.retrieval_documents.

Examples:
  python -m scripts.engineering.knowledge_corpus.ingest --dry-run
  python -m scripts.engineering.knowledge_corpus.ingest --asset-type boilerplate
  set AGENTCORE_EMBEDDING_FORCE=hash && python -m ...  # offline stub embeddings
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import psycopg
from psycopg.rows import dict_row

try:
    from .chunkers import chunk_file
    from .config import (
        ASSET_DIRS,
        CORPUS_ROOT,
        SKIP_DIR_NAMES,
        SKIP_FILE_NAMES,
        SKIP_FILE_SUFFIXES,
    )
    from .embedder import get_embedder
    from .schema_probe import probe
    from .writer import upsert_chunk
except ImportError:  # script-style execution from this directory
    _THIS = Path(__file__).resolve()
    if str(_THIS.parent) not in sys.path:
        sys.path.insert(0, str(_THIS.parent))
    from chunkers import chunk_file  # type: ignore
    from config import (  # type: ignore
        ASSET_DIRS,
        CORPUS_ROOT,
        SKIP_DIR_NAMES,
        SKIP_FILE_NAMES,
        SKIP_FILE_SUFFIXES,
    )
    from embedder import get_embedder  # type: ignore
    from schema_probe import probe  # type: ignore
    from writer import upsert_chunk  # type: ignore


def _log(msg: str) -> None:
    sys.stderr.write(f"[knowledge_corpus] {msg}\n")


def connect() -> psycopg.Connection:
    password = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    if not password:
        raise SystemExit("AGENT_CORE_POSTGRES_PASSWORD is not set (Windows User env).")
    return psycopg.connect(
        host="127.0.0.1",
        port=55433,
        dbname="agent_core",
        user="postgres",
        password=password,
        row_factory=dict_row,
    )


def infer_asset_type(path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(CORPUS_ROOT.resolve())
    except ValueError:
        return None
    top = rel.parts[0] if rel.parts else ""
    mapping = {
        "docs": "docs",
        "boilerplates": "boilerplate",
        "agent-rules": "agent_rule",
        "openapi": "openapi",
    }
    return mapping.get(top)


def should_skip(path: Path) -> bool:
    if path.name in SKIP_FILE_NAMES:
        return True
    if path.suffix.lower() in SKIP_FILE_SUFFIXES:
        return True
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return True
    return False


def iter_files(roots: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if not should_skip(root):
                files.append(root)
            continue
        if not root.exists():
            _log(f"missing root: {root}")
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if should_skip(path):
                continue
            files.append(path)
    return sorted(files)


def file_to_uri(path: Path) -> str:
    # Windows path as file URI
    posix = path.resolve().as_posix()
    if len(posix) >= 2 and posix[1] == ":":
        return "file:///" + quote(posix)
    return path.resolve().as_uri()


def ingest_paths(
    paths: list[Path],
    *,
    framework: str,
    version: str,
    license_id: str,
    trust_class: str,
    dry_run: bool,
    allow_hash_fallback: bool,
    extra_metadata: dict[str, Any] | None = None,
    default_asset_type: str | None = None,
) -> dict[str, Any]:
    embedder = get_embedder(allow_hash_fallback=allow_hash_fallback)
    _log(f"embedder={embedder.model_id} dim={embedder.dim}")

    inserted = 0
    skipped = 0
    errors: list[str] = []
    details: list[dict[str, Any]] = []

    with connect() as conn:
        caps = probe(conn)
        _log(
            "schema "
            f"m5.002={caps.migration_m5002} "
            f"corpus_ready={caps.knowledge_corpus_ready} "
            f"kinds={sorted(caps.source_kinds) or ['(unknown)']}"
        )
        for path in paths:
            asset_type = infer_asset_type(path) or (
                default_asset_type if default_asset_type and default_asset_type != "all" else None
            )
            if asset_type is None:
                errors.append(f"cannot infer asset_type for {path}")
                continue
            try:
                chunks = chunk_file(path, asset_type)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"chunk failed {path}: {exc}")
                continue
            if not chunks:
                skipped += 1
                continue
            source_uri = file_to_uri(path)
            for chunk in chunks:
                try:
                    with conn.transaction():
                        row = upsert_chunk(
                            conn,
                            caps=caps,
                            embedder=embedder,
                            path=str(path.resolve()),
                            source_uri=source_uri,
                            asset_type=asset_type,
                            framework=framework,
                            version=version,
                            license_id=license_id,
                            trust_class=trust_class,
                            chunk=chunk,
                            dry_run=dry_run,
                            extra_metadata=extra_metadata,
                        )
                    inserted += 1
                    details.append(row)
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"write failed {path}::{chunk.chunk_id}: {exc}")
        if not dry_run:
            conn.commit()

    return {
        "ok": not errors,
        "files": len(paths),
        "chunks_written": inserted,
        "files_empty_skipped": skipped,
        "errors": errors,
        "embedder": embedder.model_id,
        "dry_run": dry_run,
        "sample": details[:5],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest AgentCore knowledge corpus into PG18")
    parser.add_argument(
        "--asset-type",
        choices=["docs", "boilerplate", "agent_rule", "openapi", "all"],
        default="all",
    )
    parser.add_argument("--path", action="append", default=[], help="Extra file/dir paths")
    parser.add_argument("--framework", default="agentcore")
    parser.add_argument("--version", default="2026-10-29")
    parser.add_argument("--license", default="operator", dest="license_id")
    parser.add_argument(
        "--trust-class",
        default="operator_verified",
        choices=[
            "operator_verified",
            "system_verified",
            "project_verified",
            "raw_untrusted",
            "quarantined",
            "rejected",
        ],
    )
    parser.add_argument(
        "--extra-metadata",
        default="{}",
        help="JSON object merged into every chunk metadata payload",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--require-nomic",
        action="store_true",
        help="Fail if SentenceTransformers/nomic model cannot load (no hash stub)",
    )
    args = parser.parse_args(argv)

    roots: list[Path] = []
    if args.asset_type == "all":
        roots.extend(ASSET_DIRS.values())
    else:
        roots.append(ASSET_DIRS[args.asset_type])
    for p in args.path:
        roots.append(Path(p))

    files = iter_files(roots)
    _log(f"corpus_root={CORPUS_ROOT} files={len(files)}")
    if not files:
        print(json.dumps({"ok": True, "files": 0, "chunks_written": 0, "note": "nothing to ingest"}))
        return 0

    report = ingest_paths(
        files,
        framework=args.framework,
        version=args.version,
        license_id=args.license_id,
        trust_class=args.trust_class,
        dry_run=args.dry_run,
        allow_hash_fallback=not args.require_nomic,
        extra_metadata=json.loads(args.extra_metadata or "{}"),
        default_asset_type=args.asset_type,
    )
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
