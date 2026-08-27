"""Session Scope Contract implementation for AgentCore Cursor integration.

Generates and manages noncanonical, ignored session scope state at:
<project>\\.agentcore\\runtime\\session-scope.json
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

AUTHORITY_DOCS = [
    "PROJECT_ANCHOR.md",
    "DOC_AUTHORITY.md",
    "BLUEPRINT.md",
    "CONTEXT_BLOCK.md",
    "MILESTONES.md",
    "AGENTS.md",
    "CLAUDE.md",
    "MASTER_CONFIG_AND_PROMPT.md",
    "contracts/global-agent-policy.yaml",
]

def compute_file_hash(path: Path) -> str:
    if not path.is_file():
        return ""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""

def compute_authority_hashes(repo_root: Path) -> dict[str, str]:
    hashes = {}
    for rel_path in AUTHORITY_DOCS:
        p = repo_root / rel_path
        hashes[rel_path] = compute_file_hash(p)
    return hashes

class SessionScope:
    def __init__(
        self,
        project_root: Path,
        prompt_event_id: Optional[str] = None,
        project_id: Optional[str] = None,
        project_key: Optional[str] = None,
        worktree_id: Optional[str] = None,
        worktree_path: Optional[str] = None,
        session_id: Optional[str] = None,
        session_key: Optional[str] = None,
        projection_revision: int = 0,
        intent: str = "",
        decomposition: Optional[list[str]] = None,
        acceptance: Optional[list[str]] = None,
        declared_files: Optional[list[str]] = None,
        observed_files: Optional[list[str]] = None,
        required_tool_evidence: Optional[dict[str, Any]] = None,
        verifications: Optional[list[dict[str, Any]]] = None,
        final_review: Optional[dict[str, Any]] = None,
    ):
        self.project_root = Path(project_root).resolve()
        self.scope_file = self.project_root / ".agentcore" / "runtime" / "session-scope.json"
        
        self.prompt_event_id = prompt_event_id or ""
        self.identity = {
            "project_id": project_id or "",
            "project_key": project_key or self.project_root.name,
            "worktree_id": worktree_id or "",
            "worktree_path": worktree_path or str(self.project_root),
            "session_id": session_id or "",
            "session_key": session_key or "",
        }
        self.authority_hashes = compute_authority_hashes(self.project_root)
        self.projection_revision = projection_revision
        self.intent = intent
        self.decomposition = decomposition or []
        self.acceptance = acceptance or []
        self.declared_files = declared_files or []
        self.observed_files = observed_files or []
        self.required_tool_evidence = required_tool_evidence or {}
        self.verifications = verifications or []
        self.final_review = final_review or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_event_id": self.prompt_event_id,
            "identity": self.identity,
            "authority_hashes": self.authority_hashes,
            "projection_revision": self.projection_revision,
            "intent": self.intent,
            "decomposition": self.decomposition,
            "acceptance": self.acceptance,
            "declared_files": self.declared_files,
            "observed_files": self.observed_files,
            "required_tool_evidence": self.required_tool_evidence,
            "verifications": self.verifications,
            "final_review": self.final_review,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def save_atomic(self) -> Path:
        self.scope_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.scope_file.with_suffix(".tmp")
        data = json.dumps(self.to_dict(), indent=2) + "\n"
        tmp.write_text(data, encoding="utf-8")
        shutil.move(str(tmp), str(self.scope_file))
        return self.scope_file

    @classmethod
    def load_or_create(cls, project_root: Path) -> SessionScope:
        root = Path(project_root).resolve()
        scope_path = root / ".agentcore" / "runtime" / "session-scope.json"
        if scope_path.is_file():
            try:
                raw = json.loads(scope_path.read_text(encoding="utf-8-sig"))
                ident = raw.get("identity") or {}
                return cls(
                    project_root=root,
                    prompt_event_id=raw.get("prompt_event_id"),
                    project_id=ident.get("project_id"),
                    project_key=ident.get("project_key"),
                    worktree_id=ident.get("worktree_id"),
                    worktree_path=ident.get("worktree_path"),
                    session_id=ident.get("session_id"),
                    session_key=ident.get("session_key"),
                    projection_revision=raw.get("projection_revision", 0),
                    intent=raw.get("intent", ""),
                    decomposition=raw.get("decomposition"),
                    acceptance=raw.get("acceptance"),
                    declared_files=raw.get("declared_files"),
                    observed_files=raw.get("observed_files"),
                    required_tool_evidence=raw.get("required_tool_evidence"),
                    verifications=raw.get("verifications"),
                    final_review=raw.get("final_review"),
                )
            except Exception:
                pass
        scope = cls(project_root=root)
        scope.save_atomic()
        return scope


def init_session_scope(
    project_root: Path,
    prompt_event_id: str,
    project_key: str,
    session_id: str,
    session_key: str,
    projection_revision: int,
    intent: str,
    decomposition: list[str],
    acceptance: list[str],
    declared_files: list[str],
) -> SessionScope:
    scope = SessionScope(
        project_root=project_root,
        prompt_event_id=prompt_event_id,
        project_key=project_key,
        session_id=session_id,
        session_key=session_key,
        projection_revision=projection_revision,
        intent=intent,
        decomposition=decomposition,
        acceptance=acceptance,
        declared_files=declared_files,
    )
    scope.save_atomic()
    return scope
