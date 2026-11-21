from __future__ import annotations
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MSG = REPO / '.agentcore' / 'rollback' / '20260914-001500-bifrost-context-opt-phase-a' / 'COMMIT_MSG_BC.txt'
FILES = [
    'audits/bifrost/BIFROST_FULL_FEATURE_OPTIMIZATION_AUDIT_2026-09-13.md',
    'audits/bifrost/BIFROST_HASH_CACHE_PROOF_2026-09-14.json',
    '.cursor/rules/vibe-prompt-protection.mdc',
    'scripts/bifrost/_phase_b_cache_proof_20260914.py',
    'scripts/bifrost/sync_code_mode_live_clients.py',
    'ops/bifrost/Test-AgentCoreBifrostGateway.ps1',
]

def run(cmd):
    return subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)

def main() -> int:
    MSG.write_text(
        'Prove Bifrost hash-cache hits and harden Code Mode live sync plus vibe-prompt guard.\n\n'
        'Adds full feature optimization audit, cache proof evidence, live is_code_mode_client sync helper, '
        'and Test assertion that Code Mode clients stay off eager tools/list.\n',
        encoding='utf-8',
    )
    run(['git', 'add', '--', *FILES])
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
