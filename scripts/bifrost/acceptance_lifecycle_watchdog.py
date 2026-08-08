from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = REPO_ROOT / "ops" / "bifrost" / "Invoke-AgentCoreBifrostWatchdog.ps1"


def run(runtime_root: Path, health: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "pwsh", "-NoProfile", "-File", str(WATCHDOG),
            "-RuntimeRoot", str(runtime_root),
            "-TestMode", "-TestHealthResult", health,
            "-GatewayStartedAtUtc", "2000-01-01T00:00:00Z",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bifrost-watchdog-") as temporary:
        runtime_root = Path(temporary) / "runtime"
        results = [run(runtime_root, "Unhealthy") for _ in range(4)]
        expected = (
            "WATCHDOG_FAILURE count=1",
            "WATCHDOG_FAILURE count=2",
            "WATCHDOG_TEST_RECYCLE count=3",
            "WATCHDOG_RECYCLE_SUPPRESSED count=4",
        )
        if any(result.returncode != 0 for result in results):
            raise RuntimeError("watchdog test-mode invocation failed")
        if any(marker not in result.stdout for marker, result in zip(expected, results, strict=True)):
            raise RuntimeError("watchdog debounce/recycle contract failed")
        state = json.loads((runtime_root / "state" / "bifrost-watchdog.json").read_text())
        if state != {"consecutive_failures": 4, "recycle_attempted": True}:
            raise RuntimeError("watchdog persisted state contract failed")
        if run(runtime_root, "Healthy").returncode != 0:
            raise RuntimeError("watchdog healthy reset failed")
    print("BIFROST_WATCHDOG_ACCEPTANCE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
