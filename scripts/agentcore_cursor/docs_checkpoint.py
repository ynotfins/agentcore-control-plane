"""Verify a project's lightweight Arabold docs checkpoint against the F: catalog.

Official documentation stays in F:\\AgentCore\\runtime\\docs-store.
Projects record only library, version, official URL, and last verification.
Missing or mismatched coverage is a scrape_docs miss — do not copy the corpus
into Git.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_CATALOG = Path(r"F:\AgentCore\runtime\docs-store\CATALOG.json")
CHECKPOINT_REL = Path(".agentcore") / "docs-checkpoint.json"
SCHEMA = "agentcore-project-docs-checkpoint/v1"


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _catalog_index(catalog: dict[str, Any]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for entry in catalog.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        library = str(entry.get("library") or "").strip().lower()
        version = str(entry.get("version") or "").strip()
        if not library or not version:
            continue
        index.setdefault(library, set()).add(version)
    return index


def _checkpoint_libraries(checkpoint: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for entry in checkpoint.get("libraries") or []:
        if not isinstance(entry, dict):
            continue
        library = str(entry.get("library") or "").strip()
        version = str(entry.get("resolved_version") or entry.get("version") or "").strip()
        if not library or not version:
            continue
        rows.append({"library": library, "resolved_version": version})
    return rows


def verify_project_docs_checkpoint(
    project_root: Path,
    catalog_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    checkpoint_path = root / CHECKPOINT_REL
    catalog_file = Path(catalog_path) if catalog_path else DEFAULT_CATALOG
    checkpoint = _load_json(checkpoint_path)
    if checkpoint is None:
        return {
            "status": "missing_checkpoint",
            "checkpoint_path": str(checkpoint_path),
            "catalog_path": str(catalog_file),
            "missing": [],
            "mismatched": [],
            "verified": [],
            "reminder": (
                "DOCS CHECKPOINT MISSING: create .agentcore/docs-checkpoint.json "
                "for every direct library@version, then scrape_docs any pin that "
                "is absent from F:\\AgentCore\\runtime\\docs-store. Do not copy "
                "the F: corpus into Git."
            ),
        }

    catalog = _load_json(catalog_file)
    if catalog is None:
        return {
            "status": "missing_catalog",
            "checkpoint_path": str(checkpoint_path),
            "catalog_path": str(catalog_file),
            "missing": [],
            "mismatched": [],
            "verified": [],
            "reminder": (
                "DOCS CATALOG MISSING: F:\\AgentCore\\runtime\\docs-store\\CATALOG.json "
                "was not readable. Repair the machine-global Arabold store before "
                "using version-sensitive library facts."
            ),
        }

    index = _catalog_index(catalog)
    missing: list[str] = []
    mismatched: list[str] = []
    verified: list[str] = []
    for row in _checkpoint_libraries(checkpoint):
        pin = f"{row['library']}@{row['resolved_version']}"
        versions = index.get(row["library"].lower(), set())
        if not versions:
            missing.append(pin)
        elif row["resolved_version"] not in versions:
            found = ",".join(sorted(versions))
            mismatched.append(f"{pin} (catalog has {found})")
        else:
            verified.append(pin)

    if missing or mismatched:
        parts = []
        if missing:
            parts.append("DOCS MISSING: " + ", ".join(missing) + ". scrape_docs now.")
        if mismatched:
            parts.append("DOCS VERSION DRIFT: " + "; ".join(mismatched) + ".")
        return {
            "status": "drift",
            "checkpoint_path": str(checkpoint_path),
            "catalog_path": str(catalog_file),
            "missing": missing,
            "mismatched": mismatched,
            "verified": verified,
            "reminder": " ".join(parts) + " Keep durable docs on F:; update the project checkpoint only.",
        }

    if not verified:
        return {
            "status": "empty_checkpoint",
            "checkpoint_path": str(checkpoint_path),
            "catalog_path": str(catalog_file),
            "missing": [],
            "mismatched": [],
            "verified": [],
            "reminder": (
                "DOCS CHECKPOINT EMPTY: inventory direct dependencies and record "
                "each library@version in .agentcore/docs-checkpoint.json, then "
                "verify against the F: catalog."
            ),
        }

    return {
        "status": "ok",
        "checkpoint_path": str(checkpoint_path),
        "catalog_path": str(catalog_file),
        "missing": [],
        "mismatched": [],
        "verified": verified,
        "reminder": (
            "DOCS CHECKPOINT OK: "
            + ", ".join(verified)
            + ". Use arabold-docs search_docs for version facts; do not use training memory."
        ),
    }


def format_docs_checkpoint_reminder(
    project_root: Path,
    catalog_path: Path | None = None,
) -> str:
    try:
        result = verify_project_docs_checkpoint(project_root, catalog_path=catalog_path)
    except Exception as exc:  # noqa: BLE001
        return f"DOCS CHECKPOINT CHECK FAILED: {type(exc).__name__}: {str(exc)[:160]}"
    return str(result.get("reminder") or "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentcore_cursor.docs_checkpoint")
    parser.add_argument("--project-root", default=".", help="Project root that holds .agentcore/docs-checkpoint.json")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Machine-global CATALOG.json path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = verify_project_docs_checkpoint(Path(args.project_root), catalog_path=Path(args.catalog))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["reminder"])
    return 0 if result["status"] == "ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())
