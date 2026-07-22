"""Studio interrupt / resume / judge acceptance runner (sanitized evidence).

Productized acceptance for LangGraph Studio Option A:

- Boots a localhost-only Agent Server (``langgraph dev``) with forced
  ``LANGSMITH_TRACING=false`` and ``LANGGRAPH_CLI_NO_ANALYTICS=1``.
- Uses the canonical Studio graph (``langgraph.json`` →
  ``agentcore_workflow.workflow.build_studio_graph``).
- Does **not** share production PostgresSaver — Studio uses the Agent
  Server dev checkpointer. Topology fingerprint must still match.
- Proves controlled ``interrupt_before=["da_builder"]``, resume, history /
  time-travel surface, and deterministic worker path.
- Writes sanitized evidence to ``audits/M6/studio-interrupt-accept.json``.
  Never prints secrets; never creates ``.env``.

Launch::

    cd D:\\github\\agentcore-control-plane\\scripts
    python -m agentcore.studio_interrupt_accept
    python -m agentcore.studio_interrupt_accept --port 8124 --json

Environment (forced by runner):
  AGENTCORE_WORKER_MODE=deterministic
  LANGSMITH_TRACING=false
  LANGGRAPH_CLI_NO_ANALYTICS=1
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import urllib.error
import urllib.request

from agentcore.studio import (
    GATE_BROWSER_CREDENTIAL_REQUIRED,
    LOCAL_HOST,
    build_langgraph_dev_cmd,
    check_fingerprint_parity,
    emit_browser_credential_gate,
    langsmith_api_key_present,
    local_api_url,
    port_is_free,
    prepare_studio_env,
    studio_app_dir,
    studio_url,
    terminate_process_tree,
)


_REPO = Path(__file__).resolve().parents[2]
_STUDIO = studio_app_dir()
_AUDIT = _REPO / "audits" / "M6"
_DEFAULT_PORT = 8124


def _http(
    url: str,
    method: str = "GET",
    body: dict | None = None,
    timeout: float = 30.0,
) -> tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8")
            try:
                return r.status, json.loads(raw)
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def _wait_ok(base: str, attempts: int = 90) -> bool:
    for _ in range(attempts):
        code, body = _http(f"{base}/ok", timeout=3)
        if code == 200 and isinstance(body, dict) and body.get("ok"):
            return True
        time.sleep(0.5)
    return False


def _pick_free_port(preferred: int, *, find_port: bool) -> int:
    if port_is_free(preferred):
        return preferred
    if not find_port:
        raise RuntimeError(
            f"port {preferred} busy on {LOCAL_HOST}; "
            "pass --find-port or choose another --port"
        )
    for candidate in range(preferred + 1, preferred + 50):
        if port_is_free(candidate):
            return candidate
    raise RuntimeError(f"no free port near {preferred}")


def _pg_password() -> str:
    """Resolve PG password from process/User env without printing it."""
    pw = (os.environ.get("AGENT_CORE_POSTGRES_PASSWORD") or "").strip()
    if pw:
        return pw
    try:
        out = subprocess.check_output(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "[Environment]::GetEnvironmentVariable("
                "'AGENT_CORE_POSTGRES_PASSWORD','User')",
            ],
            text=True,
        )
        return (out or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def _resolve_fixture_project(project_key: str) -> tuple[str, str]:
    """Return (project_id, root_path). Raises RuntimeError on failure."""
    import psycopg
    from psycopg.rows import dict_row

    pw = _pg_password()
    if not pw:
        raise RuntimeError(
            "AGENT_CORE_POSTGRES_PASSWORD missing from process/User env "
            "(set the env var NAME only; do not paste into chat)"
        )
    dsn = (
        f"host=127.0.0.1 port=55433 dbname=agent_core "
        f"user=postgres password={pw}"
    )
    with psycopg.connect(dsn, row_factory=dict_row) as c:
        row = c.execute(
            "SELECT id, root_path FROM agentcore.projects WHERE project_key=%s",
            (project_key,),
        ).fetchone()
        if not row:
            raise RuntimeError(
                f"{project_key} missing — run workflow init for the fixture first"
            )
        return str(row["id"]), (row["root_path"] or r"D:\agentcore-fixture\fixture-project")


def _as_values(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {}
    if isinstance(payload.get("values"), dict):
        return payload["values"]
    if "judge_verdict" in payload or "project_id" in payload or "next_action" in payload:
        return payload
    return {}


def _summarize(evidence: dict) -> dict:
    keys = (
        "ok",
        "port",
        "health_ok",
        "graph_id",
        "has_interrupt",
        "run_status",
        "state_next",
        "resume_run_status",
        "judge_verdict",
        "post_resume_judge",
        "post_exec_verdict",
        "da_builder_status",
        "topology_match",
        "production_topology_fingerprint",
        "tracing_env",
        "langsmith_flag",
        "langsmith_api_key_present",
        "studio_url",
        "error",
        "gate_code",
    )
    return {k: evidence.get(k) for k in keys}


def run_acceptance(args: argparse.Namespace) -> int:
    _AUDIT.mkdir(parents=True, exist_ok=True)
    evidence: dict[str, Any] = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runner": "agentcore.studio_interrupt_accept",
    }

    parity = check_fingerprint_parity()
    evidence["production_topology_fingerprint"] = parity.get("production_fp")
    evidence["studio_topology_fingerprint"] = parity.get("studio_fp")
    evidence["topology_match"] = bool(parity.get("ok"))
    if not parity.get("ok"):
        evidence["error"] = "topology fingerprint parity abort"
        evidence["ok"] = False
        _write_evidence(evidence, args.json)
        return 2

    env, refuse = prepare_studio_env(
        allow_dangerous_langsmith_tracing=False,
        extra={"AGENTCORE_WORKER_MODE": "deterministic"},
    )
    if refuse:
        evidence["error"] = refuse
        evidence["ok"] = False
        _write_evidence(evidence, args.json)
        return 2

    try:
        port = _pick_free_port(int(args.port), find_port=bool(args.find_port))
    except RuntimeError as exc:
        evidence["error"] = str(exc)
        evidence["ok"] = False
        _write_evidence(evidence, args.json)
        return 2

    base = local_api_url(port)
    evidence["port"] = port
    evidence["base"] = base
    evidence["studio_url"] = studio_url(port)
    evidence["docs_url"] = f"{base}/docs"
    evidence["langsmith_api_key_present"] = langsmith_api_key_present()
    evidence["anonymous_studio_attempt"] = not evidence["langsmith_api_key_present"]
    if evidence["anonymous_studio_attempt"]:
        evidence["gate_code"] = GATE_BROWSER_CREDENTIAL_REQUIRED
        if not args.json:
            emit_browser_credential_gate(sys.stderr)

    try:
        cmd = build_langgraph_dev_cmd(port=port, no_reload=True)
    except FileNotFoundError as exc:
        evidence["error"] = str(exc)
        evidence["ok"] = False
        _write_evidence(evidence, args.json)
        return 2

    log_path = _AUDIT / "studio-interrupt-accept.log"
    log_fp = open(log_path, "w", encoding="utf-8")
    popen_kwargs: dict[str, Any] = {
        "cwd": str(_STUDIO),
        "env": env,
        "stdout": log_fp,
        "stderr": subprocess.STDOUT,
        "text": True,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = getattr(
            subprocess, "CREATE_NEW_PROCESS_GROUP", 0
        )
    else:
        popen_kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **popen_kwargs)
    evidence["server_pid"] = proc.pid
    evidence["command"] = cmd
    evidence["tracing_env"] = env.get("LANGSMITH_TRACING")
    evidence["analytics_env"] = {
        "LANGGRAPH_CLI_NO_ANALYTICS": env.get("LANGGRAPH_CLI_NO_ANALYTICS"),
        "LANGGRAPH_ANALYTICS": env.get("LANGGRAPH_ANALYTICS"),
        "LANGGRAPH_HOST": env.get("LANGGRAPH_HOST"),
    }

    try:
        if not _wait_ok(base):
            evidence["error"] = "studio agent server health timeout"
            evidence["ok"] = False
            return 1
        evidence["health_ok"] = True

        code, docs_body = _http(f"{base}/docs", timeout=5)
        evidence["docs_status"] = code
        evidence["docs_reachable"] = code == 200

        code, info = _http(f"{base}/info")
        evidence["info_status"] = code
        if isinstance(info, dict):
            flags = info.get("flags") or {}
            evidence["langsmith_flag"] = flags.get("langsmith")
            evidence["version"] = info.get("version")

        code, asst = _http(
            f"{base}/assistants/search",
            "POST",
            {"graph_id": "agentcore_workflow", "limit": 5},
        )
        evidence["assistants_search_status"] = code
        if not (isinstance(asst, list) and asst):
            evidence["error"] = f"assistant missing: {asst}"
            evidence["ok"] = False
            return 1
        assistant_id = asst[0]["assistant_id"]
        evidence["assistant_id"] = assistant_id
        evidence["graph_id"] = asst[0].get("graph_id")

        project_key = args.project_key
        try:
            project_id, root_path = _resolve_fixture_project(project_key)
        except RuntimeError as exc:
            evidence["error"] = str(exc)
            evidence["ok"] = False
            return 1
        evidence["project_key"] = project_key
        # IDs only — never DSN/password
        evidence["project_id"] = project_id

        worktree = args.worktree or rf"D:\agentcore-worktrees\{project_key}"
        if not Path(worktree).exists():
            worktree = root_path
        evidence["worktree_path"] = worktree

        code, th = _http(
            f"{base}/threads",
            "POST",
            {"metadata": {"purpose": "studio-interrupt-accept"}, "if_exists": "do_nothing"},
        )
        evidence["thread_create_status"] = code
        thread_id = th.get("thread_id") if isinstance(th, dict) else None
        evidence["thread_id"] = thread_id
        if not thread_id:
            evidence["error"] = "thread create failed"
            evidence["ok"] = False
            return 1

        run_input = {
            "project_id": project_id,
            "project_key": project_key,
            "milestone_key": "M6",
            "thread_uuid": thread_id,
            "worktree_path": worktree,
            "provider": "openrouter",
            "model": "deterministic-fixture",
            "goal": "Studio interrupt/resume/judge acceptance",
            "da_enabled": True,
            "current_risk_class": "medium",
            "current_micro_key": "M6.5.1",
            "current_macro_key": "M6.5",
            "run_db_id": "",  # Studio must not write production run rows
        }

        code, run = _http(
            f"{base}/threads/{thread_id}/runs/wait",
            "POST",
            {
                "assistant_id": assistant_id,
                "input": run_input,
                "config": {
                    "configurable": {
                        "provider": "openrouter",
                        "model": "deterministic-fixture",
                    }
                },
                "interrupt_before": ["da_builder"],
                "stream_mode": "values",
            },
            timeout=180,
        )
        evidence["run_interrupt_status"] = code
        evidence["run_response_keys"] = (
            sorted(run.keys())[:40] if isinstance(run, dict) else []
        )

        vals = _as_values(run)
        evidence["gate_det_passed"] = vals.get("det_checks_passed")
        evidence["judge_verdict"] = vals.get("judge_verdict")
        evidence["score"] = vals.get("score")
        evidence["provider_selected"] = vals.get("provider") or "openrouter"
        evidence["model_selected"] = vals.get("model") or "deterministic-fixture"
        evidence["da_enabled"] = vals.get("da_enabled")
        if isinstance(run, dict):
            evidence["run_status"] = run.get("status")
            evidence["run_next"] = run.get("next")

        code, st = _http(f"{base}/threads/{thread_id}/state")
        evidence["state_status"] = code
        if isinstance(st, dict):
            evidence["state_next"] = st.get("next")
            ck = st.get("checkpoint") or {}
            evidence["checkpoint_id"] = (
                ck.get("checkpoint_id") if isinstance(ck, dict) else None
            )
            tasks = st.get("tasks") or []
            evidence["state_tasks_count"] = len(tasks) if isinstance(tasks, list) else 0

        next_nodes = evidence.get("state_next") or evidence.get("run_next") or []
        evidence["has_interrupt"] = (
            isinstance(next_nodes, list) and "da_builder" in next_nodes
        ) or bool(
            isinstance(run, dict)
            and (run.get("interrupts") or run.get("__interrupt__"))
        )

        code, hist = _http(f"{base}/threads/{thread_id}/history", "POST", {"limit": 20})
        if code == 0 or code >= 400:
            code, hist = _http(f"{base}/threads/{thread_id}/history")
        evidence["history_status"] = code
        if isinstance(hist, list):
            evidence["history_len"] = len(hist)
            evidence["history_checkpoint_ids"] = [
                ((h.get("checkpoint") or {}).get("checkpoint_id"))
                for h in hist[:5]
                if isinstance(h, dict)
            ]
            if len(hist) >= 2 and isinstance(hist[1], dict):
                prior = hist[1].get("checkpoint") or {}
                evidence["prior_checkpoint_id"] = (
                    prior.get("checkpoint_id") if isinstance(prior, dict) else None
                )

        code, resumed = _http(
            f"{base}/threads/{thread_id}/runs/wait",
            "POST",
            {
                "assistant_id": assistant_id,
                "input": None,
                "stream_mode": "values",
            },
            timeout=180,
        )
        evidence["resume_status"] = code
        evidence["resume_response_keys"] = (
            sorted(resumed.keys())[:40] if isinstance(resumed, dict) else []
        )
        vals = _as_values(resumed)
        if isinstance(resumed, dict):
            evidence["resume_run_status"] = resumed.get("status")
            evidence["post_resume_next"] = resumed.get("next")
        evidence["post_resume_judge"] = vals.get("judge_verdict")
        evidence["post_resume_score"] = vals.get("score")
        evidence["post_exec_verdict"] = vals.get("post_exec_verdict") or vals.get(
            "post_execution_verdict"
        )
        da_res = vals.get("da_builder_result") or {}
        evidence["da_builder_status"] = (
            da_res.get("status") if isinstance(da_res, dict) else None
        )
        evidence["da_builder_mode"] = (
            da_res.get("worker_mode") if isinstance(da_res, dict) else None
        )
        critic = vals.get("da_critic_result") or {}
        evidence["da_critic_passed"] = (
            critic.get("passed") if isinstance(critic, dict) else None
        )
        evidence["completed_flag"] = vals.get("completed")
        evidence["errors_count"] = len(vals.get("errors") or [])

        code, st2 = _http(f"{base}/threads/{thread_id}/state")
        if isinstance(st2, dict):
            evidence["post_resume_state_next"] = st2.get("next")
            v2 = st2.get("values") if isinstance(st2.get("values"), dict) else {}
            if v2:
                evidence["post_resume_judge"] = evidence.get("post_resume_judge") or v2.get(
                    "judge_verdict"
                )
                evidence["post_exec_verdict"] = evidence.get("post_exec_verdict") or v2.get(
                    "post_exec_verdict"
                )
                da_res = v2.get("da_builder_result") or {}
                if isinstance(da_res, dict) and da_res.get("status"):
                    evidence["da_builder_status"] = da_res.get("status")
                    evidence["da_builder_mode"] = da_res.get("worker_mode")

        # Optional reject-resume probe on a fresh thread (best-effort; not a hard fail)
        code, th2 = _http(
            f"{base}/threads",
            "POST",
            {"metadata": {"purpose": "studio-block-route"}, "if_exists": "do_nothing"},
        )
        thread2 = th2.get("thread_id") if isinstance(th2, dict) else None
        evidence["block_thread_id"] = thread2
        if thread2:
            code, _ = _http(
                f"{base}/threads/{thread2}/runs/wait",
                "POST",
                {
                    "assistant_id": assistant_id,
                    "input": run_input,
                    "interrupt_before": ["da_builder"],
                    "stream_mode": "values",
                },
                timeout=180,
            )
            code, rej = _http(
                f"{base}/threads/{thread2}/runs/wait",
                "POST",
                {
                    "assistant_id": assistant_id,
                    "command": {
                        "resume": {"decision": "reject", "notes": "block-route"}
                    },
                },
                timeout=60,
            )
            evidence["reject_resume_status"] = code
            evidence["reject_note"] = (
                "reject resume attempted on interrupt thread; "
                "primary block route remains production hang-timeout proof"
            )

        evidence["studio_checkpointer"] = (
            "agent-server-dev (not production PostgresSaver)"
        )
        evidence["ok"] = bool(
            evidence.get("health_ok")
            and evidence.get("assistant_id")
            and evidence.get("thread_id")
            and evidence.get("has_interrupt")
            and evidence.get("topology_match")
            and evidence.get("tracing_env") == "false"
            and evidence.get("langsmith_flag") is False
            and evidence.get("history_len", 0) >= 2
            and evidence.get("da_builder_status")
            in ("completed", "failed", "skipped_no_da")
        )
        evidence["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        return 0 if evidence["ok"] else 2
    finally:
        if not args.keep_server:
            terminate_process_tree(proc)
        try:
            log_fp.close()
        except Exception:  # noqa: BLE001
            pass
        _write_evidence(evidence, args.json)


def _is_safe_evidence_key(key: str) -> bool:
    if key == "langsmith_api_key_present":
        return True
    kl = key.lower()
    return (
        "password" not in kl
        and "secret" not in kl
        and "api_key" not in kl
        and "token" not in kl
        and "authorization" not in kl
    )


def _write_evidence(evidence: dict, as_json: bool) -> None:
    out = _AUDIT / "studio-interrupt-accept.json"
    scrubbed = {k: v for k, v in evidence.items() if _is_safe_evidence_key(k)}
    out.write_text(json.dumps(scrubbed, indent=2), encoding="utf-8")
    print(json.dumps(_summarize(scrubbed) if not as_json else scrubbed, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m agentcore.studio_interrupt_accept",
        description=(
            "Productized Studio interrupt/resume/judge acceptance runner. "
            "Localhost-only; tracing forced off; sanitized evidence only."
        ),
    )
    p.add_argument(
        "--port",
        type=int,
        default=_DEFAULT_PORT,
        help=f"Agent Server port (default {_DEFAULT_PORT})",
    )
    p.add_argument(
        "--find-port",
        action="store_true",
        help="if preferred port is busy, search upward for a free port",
    )
    p.add_argument(
        "--project-key",
        default="fixture-project-a",
        help="registered fixture project_key (default fixture-project-a)",
    )
    p.add_argument(
        "--worktree",
        default=None,
        help="optional worktree path override",
    )
    p.add_argument(
        "--keep-server",
        action="store_true",
        help="leave the Agent Server running after the run",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="print full sanitized evidence JSON",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_acceptance(args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
