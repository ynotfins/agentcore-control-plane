from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROLLBACK = REPO / '.agentcore' / 'rollback' / '20260914-001500-bifrost-context-opt-phase-a'
REGISTRY = REPO / 'contracts' / 'bifrost-upstream-mcp-registry.json'
TEST_CONTRACTS = REPO / 'scripts' / 'bifrost' / 'test_contracts.py'
TOOL_DISCOVERY = REPO / '.agents' / 'skills' / 'agentcore-tool-discovery' / 'SKILL.md'
TOOL_ROUTING = REPO / '.agents' / 'skills' / 'agentcore-project-lifecycle' / 'references' / 'TOOL_ROUTING.md'
NOTE = '2026-09-14: Code Mode enabled (is_code_mode_client=true) with global code_mode_binding_level=tool. Discovery path: listToolFiles -> readToolFile -> executeToolCode; missing tools/list prefixes for Code Mode clients are discovery failures, not missing admissions.'
TARGETS = ('nia', 'cursor-agent-mcp', 'skills-hub')

def backup(src: Path, name: str) -> None:
    ROLLBACK.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, ROLLBACK / name)

def patch_registry() -> None:
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    servers = data['servers']
    for sid in TARGETS:
        server = servers[sid]
        notes = []
        for n in list(server.get('notes') or []):
            if 'Kept classic mode so subagent controls remain directly discoverable' in n:
                notes.append('2026-08-05: wildcard replaced with live named inventory.')
            else:
                notes.append(n)
        if NOTE not in notes:
            notes.append(NOTE)
        server['notes'] = notes
        server['is_code_mode_client'] = True
    if (servers.get('arabold-docs') or {}).get('is_code_mode_client') is True:
        raise SystemExit('refuse: arabold-docs unexpectedly Code Mode')
    REGISTRY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('registry_patched', TARGETS)

def patch_test_contracts() -> None:
    text = TEST_CONTRACTS.read_text(encoding='utf-8')
    if 'registry:nia Code Mode' in text:
        print('test_contracts_already_patched')
        return
    marker = 'check(\n        "registry:nia all-IDE profiles only",'
    injection = 'check(\n        "registry:nia Code Mode",\n        nia.get("is_code_mode_client") is True,\n        f"nia is_code_mode_client={nia.get(\'is_code_mode_client\')}",\n    )\n    cursor_agent = registry["servers"].get("cursor-agent-mcp") or {}\n    check(\n        "registry:cursor-agent-mcp Code Mode",\n        cursor_agent.get("is_code_mode_client") is True,\n        f"cursor-agent-mcp is_code_mode_client={cursor_agent.get(\'is_code_mode_client\')}",\n    )\n    skills_hub = registry["servers"].get("skills-hub") or {}\n    check(\n        "registry:skills-hub Code Mode",\n        skills_hub.get("is_code_mode_client") is True,\n        f"skills-hub is_code_mode_client={skills_hub.get(\'is_code_mode_client\')}",\n    )\n    '
    if marker not in text:
        raise SystemExit('test_contracts.py marker not found')
    TEST_CONTRACTS.write_text(text.replace(marker, injection + marker, 1), encoding='utf-8')
    print('test_contracts_patched')

def patch_tool_discovery() -> None:
    text = TOOL_DISCOVERY.read_text(encoding='utf-8')
    block = '\n\n## Code Mode discovery failure vs missing admission\n\nAbsence of `serena-*`, `nia-*`, `cursor_agent_mcp-*`, or `skills_hub-*` on the first `tools/list` is a **discovery failure**, not a missing Bifrost admission, when those servers are Code Mode clients.\n\nRequired sequence for Code Mode servers (including Serena):\n\n1. `listToolFiles`\n2. `readToolFile` for `servers/<server>/<tool>.pyi`\n3. optional `getToolDocs`\n4. `executeToolCode` (e.g. `serena.find_symbol(...)`)\n\nDo not paste Serena, Nia, cursor-agent-mcp, or skills-hub into IDE `mcp.json` to fix visibility.\n'
    if 'Code Mode discovery failure vs missing admission' not in text:
        TOOL_DISCOVERY.write_text(text.rstrip() + '\n' + block, encoding='utf-8')
        print('tool_discovery_patched')
    else:
        print('tool_discovery_already_patched')

def patch_tool_routing() -> None:
    text = TOOL_ROUTING.read_text(encoding='utf-8')
    new_seq = '## Serena sequence\n\nWhen gateway Code Mode Serena is live (HTTP session shim), use the Bifrost discovery path:\n\n1. `listToolFiles` and confirm `servers/serena/`\n2. `readToolFile` for the needed `servers/serena/<tool>.pyi`\n3. `executeToolCode` (e.g. `serena.find_symbol(...)`, `serena.get_symbols_overview(...)`)\n4. Read `D:/github/agentcore-control-plane/SERENA.md` for enrollment/shim constraints\n5. Run semantic diagnostics and Depwire post-change verification when structural edits land\n\nDo not treat missing `serena-*` on `tools/list` as a missing admission. Do not require a separate host-local Serena process for builder gateway work when Code Mode Serena is live. Do not require Serena for trivial prose edits or when host-native semantic tools already provide sufficient evidence.\n'
    start = text.find('## Serena sequence')
    if start < 0:
        raise SystemExit('TOOL_ROUTING.md Serena sequence missing')
    end = text.find('\n## ', start + 1)
    if end < 0:
        end = len(text)
    TOOL_ROUTING.write_text(text[:start] + new_seq + text[end:], encoding='utf-8')
    print('tool_routing_patched')

def run(cmd):
    print('+', ' '.join(cmd))
    subprocess.check_call(cmd, cwd=str(REPO))

def main() -> int:
    backup(REGISTRY, 'contracts__bifrost-upstream-mcp-registry.json')
    backup(TEST_CONTRACTS, 'scripts__bifrost__test_contracts.py')
    backup(TOOL_DISCOVERY, 'agents__skills__agentcore-tool-discovery__SKILL.md')
    backup(TOOL_ROUTING, 'agents__skills__TOOL_ROUTING.md')
    patch_registry()
    patch_test_contracts()
    patch_tool_discovery()
    patch_tool_routing()
    py = str(REPO / 'scripts' / '.venv' / 'Scripts' / 'python.exe')
    run([py, str(REPO / 'scripts' / 'bifrost' / 'render_bifrost_config.py')])
    run([py, str(REPO / 'scripts' / 'bifrost' / 'validate_contracts.py')])
    run([py, str(TEST_CONTRACTS)])
    print('PHASE_A_APPLY_OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
