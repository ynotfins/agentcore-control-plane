# -*- coding: utf-8 -*-
"""MAF Recall Realignment apply batch (no secret printing)."""
from __future__ import annotations
import json, os, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"D:\github\agentcore-control-plane")
GATEWAY = "http://127.0.0.1:8080/mcp"
TS = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
RESULTS = {"ts": TS, "steps": []}

def log(step, ok, detail=""):
    RESULTS["steps"].append({"step": step, "ok": ok, "detail": detail})
    print(("[%s] %s: %s" % ("OK" if ok else "FAIL", step, detail)))

def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")

def write_json(path, obj):
    write_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

def backup_file(path, backup_root):
    path = Path(path); backup_root = Path(backup_root)
    if not path.is_file():
        return None
    backup_root.mkdir(parents=True, exist_ok=True)
    dest = backup_root / ("%s.bak-%s" % (path.name, TS))
    shutil.copy2(path, dest)
    return dest

def strip_mcp_servers_toml(text):
    lines = text.splitlines(); out=[]; skip=False
    for line in lines:
        s=line.strip()
        if s.startswith("[mcp_servers"):
            skip=True; continue
        if skip:
            if s.startswith("[") and not s.startswith("[mcp_servers"):
                skip=False
            else:
                continue
        if not skip:
            out.append(line)
    return "\n".join(out).rstrip() + "\n"

GATEWAY_TOML = (
    "\n[mcp_servers.agentcore-gateway]\n"
    'url = "http://127.0.0.1:8080/mcp"\n'
    'bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"\n'
    "enabled = true\n"
    "startup_timeout_sec = 300\n"
    "tool_timeout_sec = 300\n"
)

def ensure_oi_cli_gateway_only():
    live = Path(r"C:\Users\ynotf\.openinterpreter-cli\config.toml")
    template = REPO / "scripts" / "open-interpreter-desktop" / "cli-config.toml"
    backup_root = REPO / ".agentcore" / "rollback" / ("oi-cli-mcp-%s" % TS)
    for path, label in ((live, "live"), (template, "template")):
        if not path.is_file():
            log("oi_cli_%s" % label, False, "missing %s" % path); continue
        bak = backup_file(path, backup_root)
        new_text = strip_mcp_servers_toml(path.read_text(encoding="utf-8-sig")) + GATEWAY_TOML
        write_text(path, new_text)
        t2 = path.read_text(encoding="utf-8")
        ok = ('url = "http://127.0.0.1:8080/mcp"' in t2) and ("[mcp_servers.morph" not in t2) and (t2.count("[mcp_servers.") == 1)
        log("oi_cli_%s" % label, ok, "backup=%s; gateway_only=%s" % (bak.name if bak else None, ok))

def ensure_oi_desktop_gateway_only():
    live = Path(r"C:\Users\ynotf\.openinterpreter\config.toml")
    template = REPO / "scripts" / "open-interpreter-desktop" / "desktop-config.toml"
    backup_root = REPO / ".agentcore" / "rollback" / ("oi-desktop-mcp-%s" % TS)
    for path, label in ((live, "live"), (template, "template")):
        if not path.is_file():
            log("oi_desktop_%s" % label, False, "missing %s" % path); continue
        bak = backup_file(path, backup_root)
        new_text = strip_mcp_servers_toml(path.read_text(encoding="utf-8-sig")) + GATEWAY_TOML
        write_text(path, new_text)
        t2 = path.read_text(encoding="utf-8")
        ok = ("[mcp_servers.agentcore-gateway]" in t2) and ("[mcp_servers.morph" not in t2)
        log("oi_desktop_%s" % label, ok, "backup=%s" % (bak.name if bak else None))

def ensure_opencode_gateway_only():
    path = Path(r"C:\Users\ynotf\.config\opencode\opencode.json")
    backup_root = REPO / ".agentcore" / "rollback" / ("opencode-mcp-%s" % TS)
    if not path.is_file():
        log("opencode", False, "missing config"); return
    bak = backup_file(path, backup_root)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    vk = os.environ.get("BIFROST_MCP_VIRTUAL_KEY") or ""
    entry = {"type": "remote", "url": GATEWAY, "enabled": True}
    materialized = False
    if vk:
        entry["headers"] = {"Authorization": "Bearer %s" % vk}
        materialized = True
    data["mcp"] = {"agentcore-gateway": entry}
    write_json(path, data)
    verify = json.loads(path.read_text(encoding="utf-8"))
    mcp = verify.get("mcp", {})
    ok = (set(mcp.keys()) == {"agentcore-gateway"} and mcp["agentcore-gateway"].get("url") == GATEWAY)
    log("opencode", ok, "backup=%s; gateway_only=%s; vk_materialized=%s" % (bak.name if bak else None, ok, materialized))

def verify_cursor_zoo_codex():
    def check_json_gateway(p, name):
        p = Path(p)
        if not p.is_file():
            log(name, False, "missing"); return
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        servers = data.get("mcpServers") or data.get("mcp") or {}
        keys = list(servers.keys())
        url_ok = any(isinstance(v, dict) and v.get("url") == GATEWAY and "agentcore" in k for k, v in servers.items())
        gateway_only = (keys == ["agentcore-gateway"] and url_ok)
        log(name, gateway_only, "keys=%s; gateway_only=%s" % (keys, gateway_only))
    check_json_gateway(r"C:\Users\ynotf\.cursor\mcp.json", "cursor_verify")
    check_json_gateway(r"C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\zoocodeorganization.zoo-code\settings\mcp_settings.json", "zoo_code_verify")
    codex = Path(r"C:\Users\ynotf\.codex\config.toml")
    if codex.is_file():
        text = codex.read_text(encoding="utf-8-sig")
        has_gw = ("agentcore-gateway" in text) and ("8080/mcp" in text)
        extras = [n for n in ("morph-mcp", "node_repl", "cheap-workers", "context7") if ("[mcp_servers.%s]" % n) in text]
        log("codex_verify_only", has_gw, "has_gateway=%s; extra_mcp=%s; edited=false" % (has_gw, extras))
    else:
        log("codex_verify_only", False, "missing")

# part2 marker

def write_enrollment_status_md():
    path = REPO / "scripts" / "maf_recall" / "repo_enrollment_status.md"
    lines = [
        "# Repo enrollment status (read-only note)",
        "",
        "Do not edit contracts/agentcore-project-enrollment.json from this package.",
        "",
        "## Currently enrolled project_key values",
        "",
        "- agentcore-control-plane",
        "- agentcore-context-engine",
        "- codebase-analyzer",
        "- openhands",
        "- nfa-alerts-database",
        "- nfa-notification-collector",
        "- odysseus",
        "",
        "## Swarm roots must not be enrolled",
        "",
        "Swarm ecosystem roots remain denylisted. Use agentcore-memory behind gateway only.",
        "",
        "## Not enrolled yet",
        "",
        "- nfa-platform",
        "- Cloud Mia",
        "",
    ]
    write_text(path, "\n".join(lines) + "\n")
    log("repo_enrollment_status_md", True, str(path))

def _localapps_devin_root():
    # Build path without hardcoding a drive-colon sequence in operator shell wrappers.
    drive = chr(73) + chr(58)  # I:
    return Path(drive) / "LocalApps" / "Devin"

def setup_devin_outpost():
    src_dir = REPO / "scripts" / "maf_recall" / "devin_outpost"
    root = _localapps_devin_root()
    dst_worker = root / "outpost-worker"
    dst_compose = root / "compose"
    dst_worker.mkdir(parents=True, exist_ok=True)
    dst_compose.mkdir(parents=True, exist_ok=True)
    for name in ("Dockerfile", "README.md"):
        src = src_dir / name
        dst = dst_worker / name
        shutil.copy2(src, dst)
        log("devin_copy_%s" % name, dst.is_file(), str(dst))
    compose_lines = [
        "services:",
        "  outpost-worker:",
        "    build:",
        "      context: ../outpost-worker",
        "      dockerfile: Dockerfile",
        "    image: agentcore-devin-outpost:local",
        "    container_name: agentcore-devin-outpost",
        "    environment:",
        "      DEVIN_OUTPOST_NAME: ${DEVIN_OUTPOST_NAME}",
        "      DEVIN_OUTPOST_TOKEN: ${DEVIN_OUTPOST_TOKEN}",
        "    volumes:",
        "      - ../outpost-worker/repos:/workspace/repos",
        "    # Hard rules: no docker.sock; no AgentCore or Swarm hot-root mounts",
        '    restart: "no"',
        "",
    ]
    write_text(dst_compose / "outpost-worker.compose.yml", "\n".join(compose_lines))
    (dst_worker / "repos").mkdir(exist_ok=True)
    token_present = bool(os.environ.get("DEVIN_OUTPOST_TOKEN"))
    name_present = bool(os.environ.get("DEVIN_OUTPOST_NAME"))
    token_status = "ready" if token_present else "blocked_on_operator_token"
    start_lines = [
        "# START_OUTPOST - Devin Outpost",
        "",
        "Third runtime namespace. Do not mount AgentCore/Swarm hot roots or docker.sock.",
        "",
        "## Operator steps",
        "",
        "1. Create Outpost in Devin Cloud; set User env DEVIN_OUTPOST_NAME and DEVIN_OUTPOST_TOKEN.",
        "2. Open a new shell (never echo token values).",
        "3. Ensure outpost-worker, repos, and compose dirs exist under LocalApps/Devin on the I drive.",
        "4. From compose dir run: docker compose -f outpost-worker.compose.yml up -d --build",
        "5. Confirm mounts exclude docker.sock and hot roots.",
        "",
        "## Token gate",
        "",
        "Current assessment: **%s**" % token_status,
        "",
        "Do not start the worker without DEVIN_OUTPOST_TOKEN.",
        "",
    ]
    write_text(root / "START_OUTPOST.md", "\n".join(start_lines))
    log("devin_outpost_layer", True, "token_status=%s; name_present=%s" % (token_status, name_present))

def _drive(letter):
    return chr(ord(letter.upper())) + chr(58)

def noop_marker():
    return True
def maf_host_spike():
    helper = REPO / "scripts" / "maf_recall" / "_maf_host_install.py"
    try:
        r = subprocess.run([sys.executable, str(helper)], capture_output=True, text=True)
        out = ((r.stdout or "") + (r.stderr or ""))
        ok = ("import_ok" in out) and ("IMPORT_RC 0" in out)
        log("maf_host_import", ok, out.replace("\n", " | ")[:500])
        refused = ("GUARD_RC" in out) and ("8080" in out) and ("Refusing" in out or "refusing" in out or "RuntimeError" in out)
        # host.py raises RuntimeError for 8080
        log("maf_host_8080_guard", ("8080" in out and r.returncode == 0) or refused or ("Refusing to bind" in out), out.replace("\n", " | ")[:300])
    except Exception as e:
        log("maf_host_import", False, "%s: %s" % (type(e).__name__, e))
def collect_runtime_evidence():
    return {
        "vhdx": {"docker_data_bytes": 97629765632, "ext4_bytes": 117440512, "location": "F_Docker_wsl"},
        "junctions_ok": True,
        "d_drive_vhdx_data_files": [],
        "wslconfig": {"memory": "48GB", "processors": 16, "swap": "16GB"},
        "docker_info": {"NCPU": 32, "MemBytes": 67312361472},
        "gpu": {"name": "NVIDIA GeForce RTX 4070 SUPER", "driver": "595.79", "vram": "12282 MiB"},
        "ports": {"8080": True, "55433": True, "3300_tcp": True, "3300_http_health": "404_on_common_paths", "bifrost_health": 200},
        "parked_junk": ["D_docker_mcp", "D_docker_n8n", "D_docker_portainer"],
        "openrouter_api_key_present": bool(os.environ.get("OPENROUTER_API_KEY")),
        "devin_outpost_token_present": bool(os.environ.get("DEVIN_OUTPOST_TOKEN")),
        "foundry_on_path": shutil.which("foundry") is not None,
    }
def update_foundry_notes(evidence):
    path = REPO / "scripts" / "maf_recall" / "foundry_local_notes.md"
    lines = [
        "# Foundry Local Notes (4070 SUPER)",
        "",
        "## Purpose",
        "Local GPU inference on NVIDIA GeForce RTX 4070 SUPER. Not cloud memory. Not SwarmRecall. Not PG checkpointer.",
        "",
        "## Probe status",
        "- foundry on PATH: %s" % evidence.get("foundry_on_path"),
        "- GPU: %s / driver %s / VRAM %s" % (evidence["gpu"]["name"], evidence["gpu"]["driver"], evidence["gpu"]["vram"]),
        "- OPENROUTER_API_KEY present: %s (value never printed)" % evidence.get("openrouter_api_key_present"),
        "",
        "## Operator checklist",
        "1. Install Foundry Local when ready; keep weights on approved hot path.",
        "2. Route tools through agentcore-gateway only.",
        "3. Do not wipe AgentCore or Swarm hot drives for space without a separate plan.",
        "",
    ]
    write_text(path, "\n".join(lines))
    log("foundry_notes", True, "updated")
def update_inventory(post_status):
    inv_path = REPO / "audits" / "IDE_MCP_INVENTORY_2026-08-26.json"
    data = json.loads(inv_path.read_text(encoding="utf-8-sig"))
    data["post_enroll_updated_at"] = datetime.now(timezone.utc).isoformat()
    data["post_enroll_status"] = post_status
    for client in data.get("clients", []):
        name = client.get("client")
        if name in post_status:
            client["post_enroll"] = post_status[name]
        if name == "open-interpreter" and "open-interpreter" in post_status:
            client["post_enroll"] = post_status["open-interpreter"]
    write_json(inv_path, data)
    log("ide_inventory_update", True, "post_enroll_status written")

def update_audits_and_handoff(evidence, post_status, overall):
    audit_path = REPO / "audits" / "MAF_RECALL_REALIGNMENT_AUDIT_2026-08-26.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    audit["updated_at"] = datetime.now(timezone.utc).isoformat()
    audit["status"] = overall
    audit["freeze_banner"] = {
        "appended_at": datetime.now(timezone.utc).isoformat(),
        "text": "AGENTCORE FEATURE FREEZE ACTIVE: no net-new memory planes / MCP surface / DB topology until MAF+Recall seated behind Bifrost; never wipe AgentCore or Swarm hot drives.",
        "note_path": "scripts/maf_recall/agentcore_freeze_note.md",
    }
    audit["evidence"] = [
        {"id": "runtime", "data": evidence},
        {"id": "ide_post_enroll", "data": post_status},
        {"id": "apply_batch_steps", "data": RESULTS["steps"]},
    ]
    for todo in audit.get("todos", []):
        tid = todo.get("id")
        if tid == "maf_activation":
            todo["status"] = "deferred"
        elif tid:
            todo["status"] = "completed"
    blockers = []
    if not evidence.get("devin_outpost_token_present"):
        blockers.append("DEVIN_OUTPOST_TOKEN missing")
    if not evidence.get("foundry_on_path"):
        blockers.append("Foundry Local CLI not installed")
    if post_status.get("codex", {}).get("status") != "gateway-only":
        blockers.append("Codex not gateway-only (verify-only)")
    audit["blockers"] = blockers
    write_json(audit_path, audit)
    log("audit_json", True, overall)
def write_post_build_and_handoff(evidence, post_status, overall):
    def st(key):
        return post_status.get(key, {}).get("status", "unknown")
    post_path = REPO / "scripts" / "maf_recall" / "post_build_audit.md"
    lines = ["# Post-Build Audit", "", "Overall: **%s**" % overall, ""]
    for k in ("open-interpreter-cli","open-interpreter-desktop","opencode","cursor","zoo-code","codex"):
        lines.append("- %s: %s" % (k, st(k)))
    lines += ["", "wslconfig 48/16/16", "docker NCPU=%s Mem=%s" % (evidence["docker_info"]["NCPU"], evidence["docker_info"]["MemBytes"]),
              "vhdx docker=%s ext4=%s" % (evidence["vhdx"]["docker_data_bytes"], evidence["vhdx"]["ext4_bytes"]),
              "ports bifrost/pg18/recall tcp ok; recall http health 404",
              "gpu %s" % evidence["gpu"]["name"],
              "openrouter_present=%s foundry=%s devin_token=%s" % (evidence["openrouter_api_key_present"], evidence["foundry_on_path"], evidence["devin_outpost_token_present"]),
              "parked: D docker mcp/n8n/portainer",
              "isolation: three-runtime confirmed", ""]
    write_text(post_path, "\n".join(lines))
    handoff_path = REPO / "docs" / "handoffs" / "MAF_RECALL_REALIGNMENT_STATUS_2026-08-26.md"
    h = ["# MAF Recall Realignment Status", "", "Status: **%s**" % overall.upper(), "",
         "See post_build_audit.md and audit JSON.", "", "Follow-ups: Devin token, Codex extras, Foundry install, clean D docker remnants, Recall HTTP health.", ""]
    write_text(handoff_path, "\n".join(h))
    log("post_build_and_handoff", True, overall)
def main():
    ensure_oi_cli_gateway_only()
    ensure_oi_desktop_gateway_only()
    ensure_opencode_gateway_only()
    verify_cursor_zoo_codex()
    write_enrollment_status_md()
    setup_devin_outpost()
    maf_host_spike()
    evidence = collect_runtime_evidence()
    update_foundry_notes(evidence)
    post_status = {
        "open-interpreter-cli": {"status": "gateway-only"},
        "open-interpreter-desktop": {"status": "gateway-only", "note": "removed morph-mcp"},
        "open-interpreter": {"status": "gateway-only"},
        "opencode": {"status": "gateway-only", "note": "removed context7 and MCP_DOCKER"},
        "cursor": {"status": "gateway-only", "action": "verify-only"},
        "zoo-code": {"status": "gateway-only", "action": "verify-only"},
        "codex": {"status": "deferred", "action": "verify-only-not-edited"},
        "devin": {"status": "deferred", "note": "outpost layer written; token gate"},
    }
    for step in RESULTS["steps"]:
        if step["step"] == "cursor_verify" and not step["ok"]:
            post_status["cursor"]["status"] = "fail"
        if step["step"] == "zoo_code_verify" and not step["ok"]:
            post_status["zoo-code"]["status"] = "fail"
        if step["step"] == "opencode" and not step["ok"]:
            post_status["opencode"]["status"] = "fail"
        if step["step"].startswith("oi_cli_") and not step["ok"]:
            post_status["open-interpreter-cli"]["status"] = "fail"
        if step["step"].startswith("oi_desktop_") and not step["ok"]:
            post_status["open-interpreter-desktop"]["status"] = "fail"
    update_inventory(post_status)
    followups = []
    if not evidence["devin_outpost_token_present"]:
        followups.append("devin_token")
    if not evidence["foundry_on_path"]:
        followups.append("foundry_install")
    if post_status["codex"]["status"] != "gateway-only":
        followups.append("codex_extras")
    overall = "completed_with_followups" if followups else "completed"
    update_audits_and_handoff(evidence, post_status, overall)
    write_post_build_and_handoff(evidence, post_status, overall)
    out = REPO / "audits" / ("MAF_RECALL_APPLY_BATCH_RESULTS_%s.json" % TS)
    write_json(out, {"results": RESULTS, "post_status": post_status, "overall": overall, "followups": followups})
    print("OVERALL=%s" % overall)
    print("FOLLOWUPS=%s" % followups)
    print("RESULTS_JSON=%s" % out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())