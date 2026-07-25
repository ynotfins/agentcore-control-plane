"""Isolated fixture rollback proof test for AgentCore Stage B."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = Path(r"D:\agentcore-fixture\rollback-test")


def remove_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def safe_rmtree(path: Path):
    if path.exists():
        shutil.rmtree(path, onerror=remove_readonly)


def main():
    print(f"=== Stage B Rollback Proof Test ===")
    print(f"Fixture Root: {FIXTURE_ROOT}")

    # 1. Prepare isolated disposable fixture
    safe_rmtree(FIXTURE_ROOT)
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)

    # Copy .cursor and scripts/agentcore_cursor to fixture
    shutil.copytree(REPO_ROOT / ".cursor", FIXTURE_ROOT / ".cursor")
    shutil.copytree(REPO_ROOT / "scripts" / "agentcore_cursor", FIXTURE_ROOT / "scripts" / "agentcore_cursor")

    # 2. Write Stage B hooks.json to fixture
    stage_b_hooks = {
        "version": 1,
        "hooks": {
            "sessionStart": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event sessionStart", "timeout": 90}],
            "beforeSubmitPrompt": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event beforeSubmitPrompt", "timeout": 90}],
            "preToolUse": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event preToolUse", "timeout": 90}],
            "beforeShellExecution": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event beforeShellExecution", "timeout": 90}],
            "afterFileEdit": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event afterFileEdit", "timeout": 90}],
            "postToolUse": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event postToolUse", "timeout": 90}],
            "stop": [{"command": "powershell -File .cursor/hooks/agentcore-hook.ps1 -Event stop", "timeout": 90}]
        }
    }
    fixture_hooks_json = FIXTURE_ROOT / ".cursor" / "hooks.json"
    fixture_hooks_json.write_text(json.dumps(stage_b_hooks, indent=2) + "\n", encoding="utf-8")

    # Verify Stage B active in fixture
    b_data = json.loads(fixture_hooks_json.read_text(encoding="utf-8"))
    b_events = list(b_data["hooks"].keys())
    print(f"Fixture Stage B Registered Hooks: {b_events}")
    assert "preToolUse" in b_events, "Stage B preToolUse not registered in fixture"
    assert "beforeShellExecution" in b_events, "Stage B beforeShellExecution not registered in fixture"
    assert "stop" in b_events, "Stage B stop not registered in fixture"

    # 3. Import and execute rollback script targeting fixture
    sys.path.insert(0, str(FIXTURE_ROOT / "scripts"))
    from agentcore_cursor.rollback_stage_b import restore_stage_a

    restore_stage_a(FIXTURE_ROOT)

    # 4. Verify Stage A restored in fixture
    a_data = json.loads(fixture_hooks_json.read_text(encoding="utf-8"))
    a_events = list(a_data["hooks"].keys())
    print(f"Fixture Restored Stage A Registered Hooks: {a_events}")
    assert a_events == ["sessionStart", "beforeSubmitPrompt"], f"Rollback failed: expected ['sessionStart', 'beforeSubmitPrompt'], got {a_events}"

    # Cleanup disposable fixture
    safe_rmtree(FIXTURE_ROOT)
    print("=== Rollback Proof Test PASSED ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
