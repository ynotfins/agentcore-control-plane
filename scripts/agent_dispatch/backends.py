"""CLI worker backends. Every argv is a direct executable (no cmd.exe), so task text
is never shell-parsed. Model traffic goes to OmniRoute except Codex (subscription)."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .policy import RUNTIME_ROOT

HOME = Path(os.environ.get("USERPROFILE", str(Path.home())))
NODE = os.environ.get("AGENTCORE_DISPATCH_NODE", r"C:\Program Files\nodejs\node.exe")
OMNIROUTE_V1 = os.environ.get("AGENTCORE_DISPATCH_OMNIROUTE", "http://127.0.0.1:20128/v1")
DEFAULT_MODEL = os.environ.get("AGENTCORE_DISPATCH_DEFAULT_MODEL", "deepseek-v4-pro")
LANGGRAPH_MODEL = os.environ.get("AGENTCORE_DISPATCH_LANGGRAPH_MODEL", "deepseek-v4.1-flash")
CODEX_MODEL = os.environ.get("AGENTCORE_DISPATCH_CODEX_MODEL", "gpt-5.6-terra")
PI_AGENT_DIR = RUNTIME_ROOT / "pi-agent"
WORKFLOW_PY = Path(r"D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe")
WORKFLOW_CWD = Path(r"D:\github\agentcore-control-plane\scripts")

# Backends whose model traffic bypasses OmniRoute stay off unless the operator opts in.
ALLOW_DIRECT_OPENROUTER = os.environ.get("AGENTCORE_DISPATCH_ALLOW_DIRECT_OPENROUTER") == "1"

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


@dataclass
class Launch:
    argv: list[str]
    env: dict[str, str] = field(default_factory=dict)
    stdin: Optional[str] = None
    cwd: Optional[Path] = None


@dataclass
class Parsed:
    text: str = ""
    tokens: Optional[int] = None
    cost_usd: Optional[float] = None


@dataclass
class Backend:
    name: str
    summary: str
    default_minutes: int
    max_minutes: int
    build: Callable[[str, Path, str, Path], Launch]
    parse: Callable[[Path], Parsed]
    model_label: Callable[[str], str] = lambda m: f"omniroute/{m}"
    available: Callable[[], bool] = lambda: True
    default_model: str = ""


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _jsonl(p: Path):
    for line in _read(p).splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _plain(p: Path) -> Parsed:
    return Parsed(text=ANSI.sub("", _read(p)).strip())


# --- Pi -------------------------------------------------------------------
def _pi_build(task, workdir, model, jobdir):
    launcher = HOME / ".pi" / "agent" / "bin" / "pi-launcher.js"
    return Launch(
        argv=[NODE, str(launcher), "-p", "--no-session", "--provider", "omniroute", "--model", model, task],
        env={"PI_CODING_AGENT_DIR": str(PI_AGENT_DIR)},
    )


# --- OpenHands --------------------------------------------------------------
def _oh_build(task, workdir, model, jobdir):
    exe = HOME / ".local" / "bin" / "openhands.exe"
    return Launch(
        argv=[str(exe), "--headless", "--json", "--override-with-envs", "--exit-without-confirmation", "-t", task],
        env={
            "LLM_BASE_URL": OMNIROUTE_V1,
            "LLM_MODEL": f"openai/{model}",
            "LLM_API_KEY": os.environ.get("OMNIROUTE_API_KEY", "omniroute-loopback"),
            "PYTHONIOENCODING": "utf-8",
        },
    )


def _oh_parse(stdout: Path) -> Parsed:
    text = ""
    for ev in _jsonl(stdout):
        if ev.get("kind") == "MessageEvent" and ev.get("source") == "agent":
            parts = (ev.get("llm_message") or {}).get("content") or []
            text = "\n".join(p.get("text", "") for p in parts if isinstance(p, dict)) or text
    return Parsed(text=text or _plain(stdout).text[-4000:])


# --- OpenCode ---------------------------------------------------------------
def _oc_build(task, workdir, model, jobdir):
    exe = HOME / ".local" / "bin" / "opencode"
    if not exe.exists():
        exe = exe.with_suffix(".exe")
    return Launch(argv=[str(exe), "run", "-m", f"omniroute/{model}", "--format", "json", "--dir", str(workdir), task])


def _oc_parse(stdout: Path) -> Parsed:
    texts, tokens, cost = [], 0, 0.0
    for ev in _jsonl(stdout):
        part = ev.get("part") or {}
        if ev.get("type") == "text" and part.get("text"):
            texts.append(part["text"])
        if ev.get("type") == "step_finish":
            tokens += int((part.get("tokens") or {}).get("total") or 0)
            cost += float(part.get("cost") or 0)
    return Parsed(text="\n".join(texts) or _plain(stdout).text[-4000:], tokens=tokens or None, cost_usd=cost or None)


# --- Codex (subscription; never OmniRoute) ---------------------------------
def _codex_build(task, workdir, model, jobdir):
    js = Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    m = model if model and model != DEFAULT_MODEL else CODEX_MODEL
    return Launch(
        argv=[NODE, str(js), "exec", "--skip-git-repo-check", "--ephemeral", "--sandbox", "workspace-write",
              "-C", str(workdir), "-m", m, "-o", str(jobdir / "last_message.txt"), "-"],
        stdin=task,
    )


def _codex_parse(stdout: Path) -> Parsed:
    raw = _read(stdout)
    m = re.search(r"tokens used\s*\n\s*([\d,]+)", raw + "\n" + _read(stdout.parent / "stderr.log"))
    last = _read(stdout.parent / "last_message.txt").strip()
    return Parsed(text=last or ANSI.sub("", raw)[-4000:], tokens=int(m.group(1).replace(",", "")) if m else None)


# --- LangGraph M6 governed workflow (PostgresSaver on PG18) ---------------
def _lg_build(task, workdir, model, jobdir):
    from bifrost.session_identity import EnrollmentRegistry

    res = EnrollmentRegistry().resolve(candidate_path=str(workdir))
    project = res.project_key or str(workdir)
    m = model or LANGGRAPH_MODEL
    return Launch(
        argv=[str(WORKFLOW_PY), "-m", "agentcore", "workflow", "start", "--project", project,
              "--goal", task, "--provider", "omniroute", "--model", m, "--json"],
        cwd=WORKFLOW_CWD,
        env={"LANGSMITH_TRACING": "false", "LANGGRAPH_CLI_NO_ANALYTICS": "1"},
    )


def _lg_parse(stdout: Path) -> Parsed:
    raw = _read(stdout)
    start = raw.find("{")
    try:
        p = json.loads(raw[start:]) if start >= 0 else {}
    except json.JSONDecodeError:
        return _plain(stdout)
    text = (f"ok={p.get('ok')} completed={p.get('completed')} verdict={p.get('judge_verdict')} "
            f"score={p.get('score')} thread={p.get('thread_uuid')} run={p.get('run_db_id')} errors={p.get('errors')}")
    return Parsed(text=text)


BACKENDS: dict[str, Backend] = {
    b.name: b
    for b in [
        Backend("pi", "Fast, light coding/file edits and quick scripted tasks.", 10, 30, _pi_build, _plain),
        Backend("openhands", "Long autonomous multi-step coding with self-verification.", 30, 90, _oh_build, _oh_parse),
        Backend("opencode", "General coding tasks; good tool use, reports tokens/cost.", 20, 60, _oc_build, _oc_parse),
        Backend("codex", "Hard coding/debugging on the Codex subscription (not OmniRoute).", 30, 90,
                _codex_build, _codex_parse, model_label=lambda m: f"codex/{m if m and m != DEFAULT_MODEL else CODEX_MODEL}"),
        Backend("langgraph", "Governed M6 milestone workflow on an enrolled repo; OmniRoute deepseek-v4.1-flash default. Slow.",
                60, 180, _lg_build, _lg_parse,
                model_label=lambda m: f"omniroute/{m or LANGGRAPH_MODEL}",
                available=lambda: WORKFLOW_PY.exists(), default_model=LANGGRAPH_MODEL),
    ]
}
