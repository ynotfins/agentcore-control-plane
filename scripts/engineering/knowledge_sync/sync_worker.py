"""Nightly outbound knowledge-corpus sync: detect, quarantine, QA, hold or promote."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .qa import evaluate_breaking_change, qa_paths
except ImportError:  # pytest loading this file as a loose module
    from qa import evaluate_breaking_change, qa_paths

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = REPO_ROOT / "contracts" / "knowledge-corpus-catalog.json"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_catalog(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_state(path: Path) -> dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"remotes": {}}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def run_git(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=True,
        text=True,
    )


def ls_remote_sha(url: str, ref: str) -> str | None:
    result = run_git(["ls-remote", url, ref])
    if result.returncode != 0:
        return None
    line = (result.stdout or "").strip().splitlines()
    if not line:
        return None
    return line[0].split()[0]


def parse_major(version: str | None) -> str | None:
    if not version:
        return None
    text = version.lstrip("v")
    parts = text.split(".")
    return parts[0] if parts and parts[0].isdigit() else None


def filter_changed_files(files: list[Path], include_globs: list[str], root: Path) -> tuple[list[Path], list[str]]:
    allowed: list[Path] = []
    unexpected: list[str] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        matched = any(
            Path(rel).match(pattern) or fnmatch.fnmatch(rel, pattern)
            for pattern in include_globs
        )
        if matched:
            allowed.append(path)
        else:
            unexpected.append(rel)
    return allowed, unexpected


def write_hold(hold_root: Path, remote_id: str, payload: dict[str, Any]) -> Path:
    dest_dir = hold_root / remote_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{_now()}-hold.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return dest


def maybe_ingest(promoted_paths: list[Path], remote: dict[str, Any], dry_run: bool) -> dict[str, Any]:
    ingest = REPO_ROOT / "scripts" / "engineering" / "knowledge_corpus" / "ingest.py"
    if not ingest.is_file():
        return {
            "ok": False,
            "skipped": True,
            "reason": "ingest_runner_absent_on_this_branch",
            "hint": "DB agent ingest lives on feat/local-agent-knowledge-corpus",
        }
    if dry_run:
        return {"ok": True, "dry_run": True, "files": [str(p) for p in promoted_paths]}
    cmd = [
        sys.executable,
        "-m",
        "scripts.engineering.knowledge_corpus.ingest",
        "--framework",
        str(remote.get("framework") or "agentcore"),
        "--asset-type",
        str(remote.get("asset_type") or "docs"),
        "--trust-class",
        "system_verified",
    ]
    for path in promoted_paths:
        cmd.extend(["--path", str(path)])
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False, capture_output=True, text=True)
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": (result.stdout or "")[-2000:],
        "stderr": (result.stderr or "")[-2000:],
    }


def sync_remote(
    remote: dict[str, Any],
    catalog: dict[str, Any],
    state: dict[str, Any],
    *,
    apply: bool,
    rollback_id: str | None = None,
) -> dict[str, Any]:
    remote_id = str(remote["id"])
    prior = (state.get("remotes") or {}).get(remote_id) or {}
    if rollback_id == remote_id:
        return {
            "id": remote_id,
            "action": "rollback_requested",
            "last_good_sha": prior.get("last_good_sha"),
            "note": "Restore last-good E: tree and re-ingest that SHA. Live rows stay until restore completes.",
        }

    sha = ls_remote_sha(str(remote["url"]), str(remote.get("ref") or "HEAD"))
    if not sha:
        return {"id": remote_id, "action": "hold", "reasons": ["ls_remote_failed"]}
    if sha == prior.get("last_good_sha"):
        return {"id": remote_id, "action": "unchanged", "sha": sha}

    quarantine_root = Path(catalog["quarantine_root"]) / remote_id / f"{_now()}-{sha[:12]}"
    quarantine_root.mkdir(parents=True, exist_ok=True)
    fetch = run_git(
        [
            "clone",
            "--depth",
            "1",
            "--branch",
            str(remote.get("ref") or "HEAD").removeprefix("refs/heads/").removeprefix("refs/tags/"),
            str(remote["url"]),
            str(quarantine_root / "src"),
        ]
    )
    src = quarantine_root / "src"
    if fetch.returncode != 0 or not src.exists():
        hold = write_hold(
            Path(catalog["hold_root"]),
            remote_id,
            {"sha": sha, "reasons": ["fetch_failed"], "stderr": (fetch.stderr or "")[-1500:]},
        )
        return {"id": remote_id, "action": "hold", "reasons": ["fetch_failed"], "hold": str(hold)}

    files = [p for p in src.rglob("*") if p.is_file() and ".git" not in p.parts]
    include = list(remote.get("include_globs") or ["**/*"])
    allowed, unexpected = filter_changed_files(files, include, src)
    qa = qa_paths(allowed, root=src)
    pinned_major = parse_major(str(remote.get("pinned_version") or ""))
    observed_major = parse_major(str(remote.get("observed_version") or prior.get("version") or ""))
    major_jump = bool(pinned_major and observed_major and pinned_major != observed_major)
    decision = evaluate_breaking_change(
        enrolled=bool(remote.get("enrolled")),
        first_ingest=not bool(prior.get("last_good_sha")),
        major_jump=major_jump,
        changed_file_count=len(allowed),
        max_changed_files=int(remote.get("max_changed_files") or catalog.get("max_changed_files") or 50),
        unexpected_paths=unexpected,
        qa_ok=qa.ok,
        auto_promote=bool(remote.get("auto_promote", catalog.get("auto_promote_default", False))),
    )
    payload = {
        "id": remote_id,
        "sha": sha,
        "qa_ok": qa.ok,
        "findings": [f.__dict__ for f in qa.findings],
        **decision,
    }
    if decision["action"] == "hold" or not apply:
        hold = write_hold(Path(catalog["hold_root"]), remote_id, payload)
        payload["hold"] = str(hold)
        payload["applied"] = False
        return payload

    promoted_root = Path(catalog["promoted_root"]) / str(remote.get("asset_type") or "docs") / remote_id
    promoted_root.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for path in allowed:
        dest = promoted_root / path.relative_to(src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(path.read_bytes())
        copied.append(dest)
    ingest = maybe_ingest(copied, remote, dry_run=False)
    payload["ingest"] = ingest
    if ingest.get("ok"):
        state.setdefault("remotes", {})[remote_id] = {
            "last_good_sha": sha,
            "promoted_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(copied),
        }
        payload["applied"] = True
    else:
        payload["action"] = "hold"
        payload["reasons"] = list(payload.get("reasons") or []) + ["ingest_failed"]
        payload["applied"] = False
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Knowledge corpus quarantine sync")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    parser.add_argument("--apply", action="store_true", help="Promote passing remotes. Default is dry-run hold.")
    parser.add_argument("--rollback", default=None, help="Corpus id to mark for last-good restore")
    args = parser.parse_args(argv)

    catalog = load_catalog(Path(args.catalog))
    state_path = Path(catalog.get("state_path") or (Path(catalog["quarantine_root"]) / "sync-state.json"))
    state = load_state(state_path)
    remotes = list(catalog.get("remotes") or [])
    reports = [
        sync_remote(remote, catalog, state, apply=args.apply, rollback_id=args.rollback)
        for remote in remotes
    ]
    if args.apply:
        save_state(state_path, state)
    print(json.dumps({"ok": True, "dry_run": not args.apply, "reports": reports}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
