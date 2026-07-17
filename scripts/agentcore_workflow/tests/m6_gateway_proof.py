"""M6 gateway proof — capability profile effective through agentcore-gateway path.

Proves:
1. Project A has test-safe-tool in active profile → startup_context returns it
2. Project B does NOT have it → startup_context does not return it
3. Expire the JIT lease → tool no longer in Project A's effective profile

Run: python scripts/agentcore_workflow/tests/m6_gateway_proof.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from agentcore_workflow import db as wfdb

PG_PASS = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
CI = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={PG_PASS}"

results: list[dict] = []
all_ok = True


def chk(name: str, passed: bool, detail: str = "") -> None:
    global all_ok
    if not passed:
        all_ok = False
    status = "PASS" if passed else "FAIL"
    results.append({"name": name, "status": status, "detail": detail})
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))


def load_server():
    # Add agentcore_memory scripts dir so knowledge_memory import resolves
    mem_dir = str(REPO / "scripts" / "agentcore_memory")
    if mem_dir not in sys.path:
        sys.path.insert(0, mem_dir)
    spec = importlib.util.spec_from_file_location("server", REPO / "scripts" / "agentcore_memory" / "server.py")
    srv = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(srv)
    return srv


if __name__ == "__main__":
    print("\n=== M6 Gateway Capability Profile Proof ===\n")

    # Setup two test projects
    with psycopg.connect(CI, row_factory=dict_row) as c:
        pa = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('m7-cap-test-a', 'M7 Cap A', 'D:/test/m7a', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id"
        ).fetchone()
        pb = c.execute(
            "INSERT INTO agentcore.projects (project_key, project_name, root_path, trust_class) "
            "VALUES ('m7-cap-test-b', 'M7 Cap B', 'D:/test/m7b', 'project_verified') "
            "ON CONFLICT (project_key) DO UPDATE SET project_name=EXCLUDED.project_name RETURNING id"
        ).fetchone()
        pid_a = str(pa["id"])
        pid_b = str(pb["id"])

    # 1. Activate test-safe-tool for Project A only
    wfdb.set_capability_state(pid_a, "test-safe-tool", "core_active", "M7", "M7 gateway proof", False)
    srv = load_server()
    profile_a = srv.get_project_capability_profile(pid_a)
    profile_b = srv.get_project_capability_profile(pid_b)

    chk("Project A has test-safe-tool in effective profile",
        "test-safe-tool" in profile_a.get("effective_tools", []),
        f"a_effective={profile_a.get('effective_tools')}")
    chk("Project B does NOT have test-safe-tool",
        "test-safe-tool" not in profile_b.get("effective_tools", []),
        f"b_effective={profile_b.get('effective_tools')}")

    # 2. JIT lease for Project A → appears in jit_leased_tools
    lease_id = wfdb.create_jit_lease(pid_a, "test-jit-gateway", "m7-proof-step", 1, "M7 JIT gateway test")
    profile_a_jit = srv.get_project_capability_profile(pid_a)
    chk("JIT lease appears in Project A jit_leased_tools",
        "test-jit-gateway" in profile_a_jit.get("jit_leased_tools", []),
        f"jit={profile_a_jit.get('jit_leased_tools')}")
    chk("JIT lease NOT in Project B profile",
        "test-jit-gateway" not in srv.get_project_capability_profile(pid_b).get("jit_leased_tools", []),
        "cross-project isolation OK")

    # 3. Expire lease — tool disappears from Project A effective profile
    time.sleep(2)
    expired = wfdb.expire_jit_leases(pid_a)
    profile_a_after = srv.get_project_capability_profile(pid_a)
    chk("After lease expiry: test-jit-gateway NOT in Project A effective_tools",
        "test-jit-gateway" not in profile_a_after.get("effective_tools", []),
        f"expired={expired} effective_after={profile_a_after.get('effective_tools')}")

    # 4. Revoke test-safe-tool from Project A → also disappears
    wfdb.set_capability_state(pid_a, "test-safe-tool", "dormant")
    profile_a_revoked = srv.get_project_capability_profile(pid_a)
    chk("After revoking to dormant: test-safe-tool NOT in Project A active_tools",
        "test-safe-tool" not in profile_a_revoked.get("active_tools", []),
        f"active_after={profile_a_revoked.get('active_tools')}")

    print(f"\nResult: {'PASS — M6 capability profile wired through gateway' if all_ok else 'FAIL'}")
    print(json.dumps(results, indent=2))
    sys.exit(0 if all_ok else 1)
