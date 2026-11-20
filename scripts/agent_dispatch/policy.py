"""Workdir allowlist for dispatched jobs (default-deny)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from bifrost.session_identity import EnrollmentRegistry

RUNTIME_ROOT = Path(os.environ.get("AGENTCORE_DISPATCH_ROOT", r"I:\LocalApps\AgentDispatch"))
SCRATCH_ROOT = RUNTIME_ROOT / "scratch"
WORKTREES_ROOT = Path(r"D:\agentcore-worktrees")

FORBIDDEN_PREFIXES = (
    r"c:",
    r"f:\postgresql18",
    r"f:\agentcore",
    r"h:",
    r"e:\swarm",
    r"r:",
)
NFA_MARKER = re.compile(r"nfa", re.IGNORECASE)


class WorkdirError(ValueError):
    pass


def _norm(p: Path) -> str:
    return str(p.resolve()).lower().rstrip("\\/")


def _under(child: str, parent: str) -> bool:
    return child == parent or child.startswith(parent + os.sep)


def resolve_workdir(registry: EnrollmentRegistry, workdir: Optional[str], task: str, job_id: str) -> tuple[Path, Optional[str]]:
    r"""Return (absolute workdir, project_key). Raises WorkdirError when denied.

    Allowed: enrolled project paths, D:\agentcore-worktrees\<enrolled-key>\..., or a
    per-job scratch dir (default when workdir is omitted). nfa repos need the task
    text to name "nfa" explicitly.
    """
    if not workdir or not str(workdir).strip():
        path = SCRATCH_ROOT / job_id
        path.mkdir(parents=True, exist_ok=True)
        return path.resolve(), None
    try:
        path = Path(str(workdir).strip()).resolve()
    except (OSError, ValueError) as exc:
        raise WorkdirError(f"invalid workdir: {exc}") from exc
    norm = _norm(path)
    if any(_under(norm, p) for p in FORBIDDEN_PREFIXES):
        raise WorkdirError("workdir_forbidden_root")
    if registry.is_swarm_refused(str(path)):
        raise WorkdirError("swarm_project_refused")
    if NFA_MARKER.search(norm) and not NFA_MARKER.search(task or ""):
        raise WorkdirError("nfa_workdir_requires_explicit_task_mention")
    if not path.is_dir():
        raise WorkdirError("workdir_not_found")
    if _under(norm, _norm(SCRATCH_ROOT)):
        return path, None
    res = registry.resolve(candidate_path=str(path))
    if res.error is None:
        return path, res.project_key
    wt = _norm(WORKTREES_ROOT)
    if _under(norm, wt):
        parts = Path(norm[len(wt):].lstrip("\\/")).parts
        if len(parts) >= 2:
            key_res = registry.resolve(project_key=parts[0])
            if key_res.error is None:
                return path, key_res.project_key
    raise WorkdirError("workdir_not_enrolled")
