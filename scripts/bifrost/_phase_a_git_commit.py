from __future__ import annotations
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MSG = REPO / '.agentcore' / 'rollback' / '20260914-001500-bifrost-context-opt-phase-a' / 'COMMIT_MSG.txt'

def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)

def main() -> int:
    run(['git', 'restore', '--staged', '.agentcore/rollback/20260914-001500-bifrost-context-opt-phase-a/WRITE_PROBE.txt'])
    commit = run(['git', 'commit', '-F', str(MSG)])
    print(commit.stdout)
    print(commit.stderr)
    if commit.returncode != 0:
        return commit.returncode
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=str(REPO), text=True).strip()
    print('COMMIT_SHA', sha)
    push = run(['git', 'push', 'origin', 'HEAD'])
    print(push.stdout)
    print(push.stderr)
    print('PUSH_CODE', push.returncode)
    return push.returncode

if __name__ == '__main__':
    raise SystemExit(main())
