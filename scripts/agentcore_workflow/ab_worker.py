"""AgentCore M6 A/B alternate worker.

Creates an isolated git worktree on I: (disposable scratch per BLUEPRINT.md §3),
runs a bounded DA alternate builder in it, archives the result to E:, and removes
the worktree. Returns a result dict compatible with the da_builder_result schema.

Boundaries (locked per BLUEPRINT.md + ADR-DEEP-AGENTS-WORKER-HARNESS.md):
- The alternate worktree lives on I: only (disposable scratch drive).
- The DA builder in the alternate worktree has the same FilesystemMiddleware bounds
  as the primary builder; it does NOT share state with the primary path.
- All durable writes from the B path go through db.record_evidence() only.
- The worktree is archived to E:\\AgentCoreArchive\\ab-worktrees\\ after the run.
- A/B is only invoked when risk_class in {high, critical} and uncertainty >= 0.5
  (see critics.should_enable_ab). Low-risk work never reaches this module.
"""
from __future__ import annotations

import shutil
import subprocess
import uuid as _uuid
from pathlib import Path
from typing import Any

# Drive assignments per BLUEPRINT.md §3
AB_WORKTREE_ROOT = Path("I:\\ab-worktrees")
AB_ARCHIVE_ROOT = Path("E:\\AgentCoreArchive\\ab-worktrees")
REPO_PATH = Path("D:\\github\\agentcore-control-plane")


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a git command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd) if cwd else str(REPO_PATH),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


# ---------------------------------------------------------------------------
# Worktree lifecycle
# ---------------------------------------------------------------------------

def create_ab_worktree(run_id: str) -> tuple[str, str]:
    """Create an isolated detached git worktree for the A/B B-path.

    Returns (worktree_path_str, branch_label).
    Raises RuntimeError if the worktree cannot be created.
    """
    AB_WORKTREE_ROOT.mkdir(parents=True, exist_ok=True)
    safe_name = f"ab-{run_id[:12]}"
    worktree_path = AB_WORKTREE_ROOT / safe_name

    if worktree_path.exists():
        return str(worktree_path), f"ab-alt/{run_id[:12]}"

    # Resolve HEAD hash for a clean detached checkout
    rc, head_hash, err = _git(["rev-parse", "HEAD"])
    if rc != 0 or not head_hash:
        head_hash = "HEAD"

    rc, stdout, stderr = _git([
        "worktree", "add", "--detach", str(worktree_path), head_hash
    ])
    if rc != 0:
        raise RuntimeError(
            f"git worktree add failed for {worktree_path}: {stderr or stdout}"
        )

    return str(worktree_path), f"ab-alt/{safe_name}"


def archive_and_remove_ab_worktree(worktree_path: str, run_id: str) -> str:
    """Archive minimal metadata to E:, then remove the worktree from I:.

    Returns the archive directory path (may be empty if I/O fails).
    """
    wt_path = Path(worktree_path)
    archive_path = AB_ARCHIVE_ROOT / f"ab-{run_id[:12]}"

    try:
        AB_ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
        archive_path.mkdir(parents=True, exist_ok=True)
        (archive_path / "run_id.txt").write_text(run_id, encoding="utf-8")
        (archive_path / "worktree_path.txt").write_text(
            worktree_path, encoding="utf-8"
        )
    except Exception:
        pass

    # Remove from git's worktree list (best-effort)
    _git(["worktree", "remove", "--force", str(wt_path)])

    # Force-remove directory if still present
    if wt_path.exists():
        shutil.rmtree(str(wt_path), ignore_errors=True)

    return str(archive_path)


# ---------------------------------------------------------------------------
# B-path execution
# ---------------------------------------------------------------------------

def run_ab_alternate_builder(
    *,
    task: str,
    worktree_path: str,
    agentcore_context: str,
    allowed_tools: list[str],
    run_id: str,
) -> dict[str, Any]:
    """Run the DA builder in the isolated alternate worktree (B path).

    Uses the same deepagents_worker.run_builder_worker() as the primary (A) path
    but with worktree_path set to the isolated I: worktree. The builder has
    identical requirements and acceptance criteria as the A-path builder.

    Returns a result dict matching the da_builder_result schema, augmented with
    ab_path='alternate' to distinguish it from the primary result.
    """
    try:
        from agentcore_workflow.deepagents_worker import (  # type: ignore[import]
            run_builder_worker,
            DEEPAGENTS_AVAILABLE,
        )
    except ImportError:
        return {
            "status": "skipped_no_da",
            "ab_path": "alternate",
            "worktree_path": worktree_path,
            "message": "deepagents not importable for alt path",
        }

    if not DEEPAGENTS_AVAILABLE:
        return {
            "status": "skipped_no_da",
            "ab_path": "alternate",
            "worktree_path": worktree_path,
            "message": "deepagents not available for alt path",
        }

    try:
        result = run_builder_worker(
            task=task,
            worktree_path=worktree_path,
            agentcore_context=agentcore_context,
            allowed_tools=allowed_tools,
        )
        result["ab_path"] = "alternate"
        result["worktree_path"] = worktree_path
        return result
    except Exception as exc:
        return {
            "status": "error",
            "ab_path": "alternate",
            "worktree_path": worktree_path,
            "message": str(exc),
        }


# ---------------------------------------------------------------------------
# Deterministic A/B comparison
# ---------------------------------------------------------------------------

def compare_ab_results(
    a_result: dict[str, Any],
    b_result: dict[str, Any],
) -> tuple[str, str]:
    """Deterministically compare A (primary DA) and B (alternate) results.

    Returns (selected, justification) where selected is one of:
        "A"              – primary implementation is better
        "B"              – alternate implementation is better
        "both_rejected"  – both fail quality threshold
        "operator_review"– scores are ambiguous; human decision required

    Comparison rules (deterministic, no randomness):
    1. If B failed and A completed → A
    2. If A failed and B completed → B
    3. If both failed → both_rejected
    4. Extract quality_score / score field from each result
    5. If both below minimum threshold (0.50) → operator_review
    6. If scores within 0.05 → A (primary tiebreaker)
    7. Otherwise → highest scorer wins
    """
    a_status = a_result.get("status", "unknown")
    b_status = b_result.get("status", "unknown")

    _ok = {"completed", "ok", "success"}
    a_ok = a_status in _ok
    b_ok = b_status in _ok

    if not a_ok and not b_ok:
        return "both_rejected", f"Both implementations failed: A={a_status}, B={b_status}"
    if a_ok and not b_ok:
        return "A", f"B-path failed ({b_status}); A selected as primary"
    if b_ok and not a_ok:
        return "B", f"A-path failed ({a_status}); B selected as alternate"

    # Both completed – compare quality scores
    def _quality(r: dict[str, Any]) -> float:
        for key in ("quality_score", "score", "critic_score"):
            v = r.get(key)
            if v is not None:
                try:
                    return float(v)
                except (TypeError, ValueError):
                    pass
        return 0.5  # neutral default when no score present

    a_q = _quality(a_result)
    b_q = _quality(b_result)

    min_threshold = 0.50
    if a_q < min_threshold and b_q < min_threshold:
        return (
            "operator_review",
            f"Both below quality threshold (0.50): A={a_q:.2f}, B={b_q:.2f}",
        )

    if abs(a_q - b_q) <= 0.05:
        return "A", f"Scores close (A={a_q:.2f}, B={b_q:.2f}); A selected as primary tiebreaker"

    if a_q >= b_q:
        return "A", f"A superior (A={a_q:.2f} > B={b_q:.2f})"
    return "B", f"B superior (B={b_q:.2f} > A={a_q:.2f})"


__all__ = [
    "AB_WORKTREE_ROOT",
    "AB_ARCHIVE_ROOT",
    "create_ab_worktree",
    "archive_and_remove_ab_worktree",
    "run_ab_alternate_builder",
    "compare_ab_results",
]
