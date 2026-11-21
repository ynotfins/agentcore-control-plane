import os
import sys
import tempfile
import time
from pathlib import Path

_TEST_BASE = Path(os.environ.get("AGENTCORE_DISPATCH_TEST_BASE", r"I:\LocalApps\AgentDispatch\test-tmp"))
_TEST_BASE.mkdir(parents=True, exist_ok=True)
_TMP = tempfile.mkdtemp(prefix="run-", dir=_TEST_BASE)
os.environ["AGENTCORE_DISPATCH_ROOT"] = _TMP
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from agent_dispatch import backends, jobs, paperclip, policy, server  # noqa: E402
from bifrost.session_identity import EnrollmentRegistry  # noqa: E402


@pytest.fixture()
def registry():
    tmp_path = Path(tempfile.mkdtemp(prefix="case-", dir=_TEST_BASE))
    proj = tmp_path / "proj"
    (proj / "sub").mkdir(parents=True)
    contract = {
        "projects": [{"project_key": "proj", "paths": [str(proj)]},
                     {"project_key": "other", "paths": [str(tmp_path / "other")]}],
        "foreign_roots": [str(tmp_path / "swarmroot")],
        "foreign_markers": ["swarmvault"],
    }
    (tmp_path / "other").mkdir()
    return EnrollmentRegistry(contract=contract), proj, tmp_path


def test_scratch_default(registry):
    reg, _, _ = registry
    wd, key = policy.resolve_workdir(reg, None, "t", "job1")
    assert wd.is_dir() and key is None and str(wd).startswith(str(Path(_TMP).resolve()))


def test_enrolled_and_subdir(registry):
    reg, proj, _ = registry
    assert policy.resolve_workdir(reg, str(proj / "sub"), "t", "j")[1] == "proj"


@pytest.mark.parametrize("bad,err", [
    ("swarmvault-x", "swarm_project_refused"),
    ("notenrolled", "workdir_not_enrolled"),
    ("nfa-thing", "nfa_workdir_requires_explicit_task_mention"),
])
def test_denials(registry, bad, err):
    reg, _, tmp = registry
    (tmp / bad).mkdir()
    with pytest.raises(policy.WorkdirError, match=err):
        policy.resolve_workdir(reg, str(tmp / bad), "do it", "j")


def test_forbidden_roots(registry):
    reg, _, _ = registry
    for p in (r"H:\SwarmData", r"F:\AgentCore\runtime", r"F:\PostgreSQL18\data"):
        with pytest.raises(policy.WorkdirError):
            policy.resolve_workdir(reg, p, "x", "j")


def test_tool_surface_is_six():
    names = [t["name"] for t in server.TOOLS]
    assert names == ["agents_list", "agent_run", "agents_parallel", "job_status", "job_result", "job_cancel"]
    assert all(len(t["description"]) <= 120 for t in server.TOOLS)


def _fake(name, code="print('hello from fake agent ' * 3)"):
    return backends.Backend(
        name, "fake", 1, 1,
        build=lambda task, wd, model, jd: backends.Launch(argv=[sys.executable, "-c", code]),
        parse=backends._plain)


def _wait(m, jid, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        st = m.status(jid)
        if st["status"] in jobs.TERMINAL or st["status"] == "completed_with_failures":
            return st
        time.sleep(0.2)
    raise AssertionError(f"job {jid} did not finish: {m.status(jid)}")


@pytest.fixture()
def manager(registry, monkeypatch):
    reg, _, _ = registry
    monkeypatch.setitem(backends.BACKENDS, "fake", _fake("fake"))
    monkeypatch.setitem(backends.BACKENDS, "sleepy", _fake("sleepy", "import time; time.sleep(120)"))
    monkeypatch.setitem(backends.BACKENDS, "boom", _fake("boom", "import sys; sys.exit(3)"))
    return jobs.JobManager(registry=reg)


def test_run_and_summary(manager):
    job = manager.submit("fake", "say hi")
    st = _wait(manager, job["job_id"])
    assert st["status"] == "succeeded" and st["exit_code"] == 0
    res = manager.result(job["job_id"])
    assert "hello from fake agent" in res["summary"]
    full = manager.result(job["job_id"], "full")
    assert Path(full["stdout_log"]).exists()


def test_failure_and_cancel(manager):
    assert _wait(manager, manager.submit("boom", "x")["job_id"])["status"] == "failed"
    jid = manager.submit("sleepy", "x")["job_id"]
    time.sleep(1.5)
    manager.cancel(jid)
    assert _wait(manager, jid)["status"] == "cancelled"


def test_identity_mismatch(manager, registry):
    _, proj, _ = registry
    with pytest.raises(policy.WorkdirError, match="project_identity_mismatch"):
        manager.submit("fake", "x", str(proj), caller_project="other")


def test_parallel(manager):
    p = manager.submit_parallel([{"agent": "fake", "task": "a"}, {"agent": "fake", "task": "b"},
                                 {"agent": "nope", "task": "c"}])
    assert len(p["children"]) == 2 and p["rejected"][0]["agent"] == "nope"
    assert _wait(manager, p["job_id"])["status"] == "succeeded"
    assert len(manager.result(p["job_id"])["results"]) == 2


def test_unknown_and_bad_ids(manager):
    with pytest.raises(ValueError):
        manager.submit("nope", "x")
    with pytest.raises(KeyError):
        manager.status("..\\..\\etc")


def test_summary_word_cap():
    assert len(jobs._words("w " * 1000, 300).split()) <= 306


@pytest.mark.parametrize("agent,ok,why", [
    ({"status": "idle", "adapterType": "process", "adapterConfig": {}}, True, ""),
    ({"status": "idle", "adapterType": "opencode_local", "adapterConfig": {"model": "omniroute/deepseek-v4-pro"}}, True, ""),
    ({"status": "idle", "adapterType": "opencode_local", "adapterConfig": {"model": "openrouter/x"}}, False, "routing_not_omniroute"),
    ({"status": "paused", "adapterType": "process", "adapterConfig": {}}, False, "agent_paused"),
])
def test_paperclip_gate(agent, ok, why):
    assert paperclip.runnable(agent) == (ok, why)


def test_paperclip_omniroute_connection_binding(monkeypatch):
    agent = {"status": "idle", "adapterType": "opencode_local",
             "adapterConfig": {"model": "paperclip/deepseek-v4-pro"},
             "runtimeConfig": {"aiConnection": {"mode": "shared", "provider": "openai",
                                                "connectionId": "conn-omni", "grantId": "g"}}}
    monkeypatch.setattr(paperclip, "company_id", lambda: "cid")
    monkeypatch.setattr(paperclip, "_omniroute_connection_ids", lambda cid: frozenset({"conn-omni"}))
    assert paperclip.routing(agent) == "omniroute"
    assert paperclip.runnable(agent) == (True, "")


def test_paperclip_non_omniroute_connection_binding(monkeypatch):
    agent = {"status": "idle", "adapterType": "opencode_local",
             "adapterConfig": {"model": "openrouter/deepseek/deepseek-v4-pro"},
             "runtimeConfig": {"aiConnection": {"mode": "shared", "provider": "openrouter",
                                                "connectionId": "conn-or", "grantId": "g"}}}
    monkeypatch.setattr(paperclip, "company_id", lambda: "cid")
    monkeypatch.setattr(paperclip, "_omniroute_connection_ids", lambda cid: frozenset({"conn-omni"}))
    assert paperclip.routing(agent) == "direct_provider"
    assert paperclip.runnable(agent) == (False, "routing_not_omniroute")


def test_mcp_roundtrip(manager):
    server.MANAGER = manager
    init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}, {})
    assert init["result"]["serverInfo"]["name"] == "agent-dispatch"
    assert server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}, {}) is None
    r = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                       "params": {"name": "agent_run", "arguments": {"agent": "fake", "task": "x"}}}, {})
    assert r["result"]["isError"] is False and r["result"]["structuredContent"]["job_id"]
    bad = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                         "params": {"name": "job_status", "arguments": {"job_id": "missing"}}}, {})
    assert bad["result"]["isError"] is True


def test_preflight_fails_loudly_when_omniroute_down(monkeypatch):
    import urllib.request

    def _boom(*_a, **_k):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(SystemExit) as exc:
        server.preflight_inference(timeout=1)
    assert "OmniRoute unreachable" in str(exc.value)


def test_preflight_accepts_auth_protected_endpoint(monkeypatch):
    import urllib.error
    import urllib.request

    def _unauth(*_a, **_k):
        raise urllib.error.HTTPError("http://x", 401, "auth", {}, None)

    monkeypatch.setattr(urllib.request, "urlopen", _unauth)
    assert "auth required" in server.preflight_inference(timeout=1)


def test_paperclip_guard_only_touches_zero_cent_events(monkeypatch):
    calls = []

    def fake_call(method, path, body=None, timeout=15):
        calls.append((method, path, body))
        if path.endswith("/accounting/health"):
            return {"items": [{"costEventId": "evt-zero"}, {"costEventId": "evt-real"}]}
        if path.endswith("/evt-real/adjustments"):
            raise paperclip.PaperclipError("expectedCents mismatch")
        return {"ok": True}

    monkeypatch.setattr(paperclip, "_call", fake_call)
    monkeypatch.setattr(paperclip, "company_id", lambda: "cid")
    out = paperclip.clear_zero_cost_unpriced()
    assert out["cleared"] == ["evt-zero"] and out["skipped"] == ["evt-real"]
    assert out["resumed"] is True
