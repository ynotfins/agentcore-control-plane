"""Async job runner + on-disk job store. Idle cost: zero threads, zero polling."""

from __future__ import annotations

import datetime as _dt
import json
import os
import secrets
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Optional

from bifrost.session_identity import EnrollmentRegistry

from . import paperclip
from .backends import BACKENDS, DEFAULT_MODEL
from .policy import RUNTIME_ROOT, WorkdirError, resolve_workdir

JOBS_ROOT = RUNTIME_ROOT / "jobs"
MAX_PARALLEL = int(os.environ.get("AGENTCORE_DISPATCH_MAX_PARALLEL", "4"))
MAX_FANOUT = 8
SUMMARY_WORDS = 300
TERMINAL = {"succeeded", "failed", "timed_out", "cancelled", "interrupted", "rejected"}
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
BELOW_NORMAL = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def _words(text: str, limit: int) -> str:
    w = (text or "").split()
    return " ".join(w) if len(w) <= limit else " ".join(w[:limit]) + " ... [truncated; job_result detail=full]"


def _git_dirty(workdir: Path) -> Optional[set[str]]:
    try:
        r = subprocess.run(["git", "-C", str(workdir), "status", "--porcelain", "-uall"], capture_output=True,
                           text=True, timeout=30, creationflags=NO_WINDOW)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return {l[3:].strip() for l in r.stdout.splitlines() if l.strip()} if r.returncode == 0 else None


def _scan(workdir: Path, since: float, cap: int = 200) -> list[str]:
    out = []
    for p in workdir.rglob("*"):
        if p.is_file() and p.stat().st_mtime >= since:
            out.append(str(p.relative_to(workdir)))
            if len(out) >= cap:
                break
    return out


def _kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)


class JobManager:
    def __init__(self, registry: Optional[EnrollmentRegistry] = None):
        self.registry = registry or EnrollmentRegistry()
        self.slots = threading.BoundedSemaphore(MAX_PARALLEL)
        self.lock = threading.Lock()
        self.procs: dict[str, subprocess.Popen] = {}
        self.cancelled: set[str] = set()
        JOBS_ROOT.mkdir(parents=True, exist_ok=True)
        self._mark_interrupted()

    # -- store --------------------------------------------------------------
    def _dir(self, job_id: str) -> Path:
        if not job_id or any(c in job_id for c in "\\/.:"):
            raise KeyError("bad job_id")
        return JOBS_ROOT / job_id

    def load(self, job_id: str) -> dict:
        p = self._dir(job_id) / "job.json"
        if not p.exists():
            raise KeyError(f"unknown job_id: {job_id}")
        return json.loads(p.read_text(encoding="utf-8"))

    def save(self, job: dict) -> None:
        d = self._dir(job["job_id"])
        d.mkdir(parents=True, exist_ok=True)
        tmp = d / "job.json.tmp"
        tmp.write_text(json.dumps(job, indent=2), encoding="utf-8")
        os.replace(tmp, d / "job.json")

    def _update(self, job_id: str, **fields: Any) -> dict:
        with self.lock:
            job = self.load(job_id)
            job.update(fields)
            self.save(job)
            return job

    def _mark_interrupted(self) -> None:
        for p in JOBS_ROOT.glob("*/job.json"):
            try:
                job = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if job.get("backend") == "cli" and job.get("status") in ("queued", "running"):
                job.update(status="interrupted", finished_at=_now(), error="dispatcher restarted while job was active")
                self.save(job)

    @staticmethod
    def new_id() -> str:
        return _dt.datetime.now().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(3)

    # -- submit -------------------------------------------------------------
    def submit(self, agent: str, task: str, workdir: Optional[str] = None, budget: Optional[int] = None,
               model: Optional[str] = None, parent: Optional[str] = None,
               caller_project: Optional[str] = None) -> dict:
        task = (task or "").strip()
        if not task:
            raise ValueError("task is required")
        job_id = self.new_id()
        base = {"job_id": job_id, "agent": agent, "task": task[:2000], "created_at": _now(), "parent": parent,
                "tokens": None, "cost_usd": None, "files_changed": [], "exit_code": None}
        if agent.startswith("paperclip/"):
            return self._submit_paperclip(base, agent, task, workdir)
        backend = BACKENDS.get(agent)
        if backend is None:
            raise ValueError(f"unknown agent '{agent}'; call agents_list")
        if not backend.available():
            raise ValueError(f"agent '{agent}' is disabled on this host; see agents_list")
        wd, project = resolve_workdir(self.registry, workdir, task, job_id)
        if caller_project and project and caller_project != project:
            raise WorkdirError("project_identity_mismatch")
        minutes = max(1, min(int(budget or backend.default_minutes), backend.max_minutes))
        m = (model or DEFAULT_MODEL).strip()
        job = dict(base, backend="cli", status="queued", workdir=str(wd), project_key=project,
                   model=backend.model_label(m), budget_minutes=minutes)
        self.save(job)
        threading.Thread(target=self._run_cli, args=(job_id, backend, task, wd, m, minutes), daemon=True,
                         name=f"job-{job_id}").start()
        return job

    def _submit_paperclip(self, base: dict, agent: str, task: str, workdir: Optional[str]) -> dict:
        pa = paperclip.find_agent(agent)
        ok, why = paperclip.runnable(pa)
        if not ok:
            raise ValueError(f"paperclip agent not runnable: {why}")
        issue = paperclip.create_issue(pa, task, workdir or "(agent default workspace)", base["job_id"])
        job = dict(base, backend="paperclip", status="running", paperclip_agent_id=pa["id"],
                   paperclip_issue_id=issue["id"], paperclip_issue=issue.get("identifier"),
                   model=(pa.get("adapterConfig") or {}).get("model") or pa.get("adapterType"),
                   workdir=(pa.get("adapterConfig") or {}).get("cwd"))
        self.save(job)
        return job

    def submit_parallel(self, tasks: list[dict], caller_project: Optional[str] = None) -> dict:
        if not isinstance(tasks, list) or not 1 <= len(tasks) <= MAX_FANOUT:
            raise ValueError(f"tasks must be a list of 1..{MAX_FANOUT} items")
        parent_id = self.new_id()
        parent = {"job_id": parent_id, "agent": "parallel", "backend": "parallel", "status": "running",
                  "created_at": _now(), "children": [], "rejected": []}
        self.save(parent)
        for i, t in enumerate(tasks):
            try:
                child = self.submit(t.get("agent", ""), t.get("task", ""), t.get("workdir"), t.get("budget"),
                                    t.get("model"), parent=parent_id, caller_project=caller_project)
                parent["children"].append(child["job_id"])
            except (ValueError, WorkdirError, paperclip.PaperclipError) as exc:
                parent["rejected"].append({"index": i, "agent": t.get("agent"), "error": str(exc)})
        self.save(parent)
        return parent

    # -- execution ----------------------------------------------------------
    def _run_cli(self, job_id, backend, task, wd: Path, model: str, minutes: int) -> None:
        jobdir = self._dir(job_id)
        with self.slots:
            if job_id in self.cancelled:
                self._update(job_id, status="cancelled", finished_at=_now())
                return
            launch = backend.build(task, wd, model, jobdir)
            before, t0 = _git_dirty(wd), time.time()
            self._update(job_id, status="running", started_at=_now())
            status, code, err = "failed", None, None
            try:
                with open(jobdir / "stdout.log", "wb") as out, open(jobdir / "stderr.log", "wb") as errf:
                    proc = subprocess.Popen(
                        launch.argv, cwd=str(launch.cwd or wd), env={**os.environ, **launch.env},
                        stdin=subprocess.PIPE if launch.stdin is not None else subprocess.DEVNULL,
                        stdout=out, stderr=errf, creationflags=NO_WINDOW | BELOW_NORMAL)
                    with self.lock:
                        self.procs[job_id] = proc
                    if launch.stdin is not None:
                        proc.stdin.write(launch.stdin.encode("utf-8"))
                        proc.stdin.close()
                    try:
                        code = proc.wait(timeout=minutes * 60)
                        status = "succeeded" if code == 0 else "failed"
                    except subprocess.TimeoutExpired:
                        _kill_tree(proc.pid)
                        proc.wait(timeout=30)
                        status, err = "timed_out", f"exceeded {minutes} min budget"
            except OSError as exc:
                err = f"launch failed: {exc}"
            finally:
                with self.lock:
                    self.procs.pop(job_id, None)
            if job_id in self.cancelled:
                status = "cancelled"
            after = _git_dirty(wd)
            changed = sorted(after - before) if before is not None and after is not None else _scan(wd, t0)
            parsed = backend.parse(jobdir / "stdout.log")
            (jobdir / "final.txt").write_text(parsed.text or "", encoding="utf-8")
            self._update(job_id, status=status, exit_code=code, error=err, finished_at=_now(),
                         duration_s=round(time.time() - t0, 1), files_changed=changed[:200],
                         tokens=parsed.tokens, cost_usd=parsed.cost_usd)

    # -- queries ------------------------------------------------------------
    def _refresh_paperclip(self, job: dict) -> dict:
        if job["status"] in TERMINAL or job["status"] == "needs_review":
            return job
        try:
            state, issue = paperclip.issue_state(job["paperclip_issue_id"])
        except paperclip.PaperclipError as exc:
            job["error"] = str(exc)
            return job
        if state != job["status"]:
            job = self._update(job["job_id"], status=state, paperclip_status=issue.get("status"),
                               finished_at=_now() if state in TERMINAL else None)
        return job

    def status(self, job_id: str) -> dict:
        job = self.load(job_id)
        if job.get("backend") == "paperclip":
            job = self._refresh_paperclip(job)
        if job.get("backend") == "parallel":
            kids = [self.status(c) for c in job["children"]]
            states = [k["status"] for k in kids]
            if not states:
                agg = "rejected"
            elif any(s not in TERMINAL and s != "needs_review" for s in states):
                agg = "running"
            else:
                agg = "succeeded" if all(s == "succeeded" for s in states) else "completed_with_failures"
            return {"job_id": job_id, "status": agg, "children": kids, "rejected": job.get("rejected", [])}
        keys = ("job_id", "agent", "status", "model", "workdir", "created_at", "started_at", "finished_at",
                "duration_s", "exit_code", "tokens", "cost_usd", "error", "paperclip_issue")
        out = {k: job.get(k) for k in keys if job.get(k) is not None}
        out["files_changed_count"] = len(job.get("files_changed") or [])
        return out

    def result(self, job_id: str, detail: str = "summary") -> dict:
        job = self.load(job_id)
        if job.get("backend") == "parallel":
            st = self.status(job_id)
            per = max(40, SUMMARY_WORDS // max(1, len(job["children"])))
            return {"job_id": job_id, "status": st["status"], "rejected": st["rejected"],
                    "results": [self._one(c, detail, per) for c in job["children"]]}
        return self._one(job_id, detail, SUMMARY_WORDS)

    def _one(self, job_id: str, detail: str, words: int) -> dict:
        st = self.status(job_id)
        job = self.load(job_id)
        d = self._dir(job_id)
        if job.get("backend") == "paperclip":
            try:
                comments = paperclip.issue_comments(job["paperclip_issue_id"])
            except paperclip.PaperclipError as exc:
                comments, st["error"] = [], str(exc)
            text = "\n\n".join(str(c.get("body") or "") for c in comments[-5:])
        else:
            text = (d / "final.txt").read_text(encoding="utf-8") if (d / "final.txt").exists() else ""
        if detail == "full":
            st.update(text=text[-20000:], files_changed=job.get("files_changed"),
                      log_dir=str(d), stdout_log=str(d / "stdout.log"), stderr_log=str(d / "stderr.log"))
        else:
            pending = st["status"] not in TERMINAL and st["status"] != "needs_review"
            st["summary"] = _words(text, words) if text else ("(still running)" if pending else "(no output)")
            st["files_changed"] = (job.get("files_changed") or [])[:15]
        return st

    def cancel(self, job_id: str) -> dict:
        job = self.load(job_id)
        if job.get("backend") == "parallel":
            for c in job["children"]:
                self.cancel(c)
            return self.status(job_id)
        if job["status"] in TERMINAL:
            return self.status(job_id)
        if job.get("backend") == "paperclip":
            paperclip.cancel_issue(job["paperclip_issue_id"])
            self._update(job_id, status="cancelled", finished_at=_now())
            return self.status(job_id)
        self.cancelled.add(job_id)
        with self.lock:
            proc = self.procs.get(job_id)
        if proc is not None:
            _kill_tree(proc.pid)
        elif job["status"] == "queued":
            self._update(job_id, status="cancelled", finished_at=_now())
        return self.status(job_id)

    def list_agents(self) -> list[dict]:
        out = [{"agent": b.name, "backend": "cli", "good_for": b.summary, "runnable": b.available(),
                "default_budget_min": b.default_minutes, "max_budget_min": b.max_minutes} for b in BACKENDS.values()]
        try:
            for a in paperclip.list_agents():
                out.append({"agent": a["agent"], "backend": "paperclip",
                            "good_for": f"Paperclip {a['role']} ({a['adapter']}): tracked ticket, budget, audit trail.",
                            "runnable": a["runnable"], "blocked_reason": a["blocked_reason"]})
        except paperclip.PaperclipError as exc:
            out.append({"agent": "paperclip/*", "backend": "paperclip", "runnable": False, "blocked_reason": str(exc)})
        return out
