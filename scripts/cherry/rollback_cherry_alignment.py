"""Rollback Cherry Studio to a protected pre-alignment backup.

Restores AppData CherryStudio tree from E:\\AgentCore-Backups.
Does not modify Bifrost, PostgreSQL, other IDEs, or Swarm.
Does not delete canonical AgentCore memory.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CHERRY_ROOT = Path(os.environ.get("APPDATA", "")) / "CherryStudio"
BACKUP_ROOT = Path(r"E:\AgentCore-Backups")
LOCKFILE = CHERRY_ROOT / "lockfile"


def cherry_running() -> bool:
    if LOCKFILE.exists():
        return True
    if os.name == "nt":
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq Cherry Studio.exe"],
            text=True,
            errors="replace",
        )
        return "Cherry Studio.exe" in out
    return False


def list_backups() -> list[Path]:
    if not BACKUP_ROOT.is_dir():
        return []
    cands = []
    for p in BACKUP_ROOT.iterdir():
        if not p.is_dir():
            continue
        if p.name.startswith("cherry-pre-alignment-") or p.name.startswith("cherry-enroll-"):
            cands.append(p)
    return sorted(cands, key=lambda x: x.name)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backup", help="Explicit backup directory")
    parser.add_argument("--latest-pre-alignment", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--prove-only", action="store_true", help="Validate backup exists; do not restore")
    args = parser.parse_args()

    if args.backup:
        src = Path(args.backup)
    elif args.latest_pre_alignment:
        pres = [p for p in list_backups() if p.name.startswith("cherry-pre-alignment-")]
        if not pres:
            print("ERROR: no cherry-pre-alignment-* backups")
            return 2
        src = pres[-1]
    else:
        cands = list_backups()
        if not cands:
            print("ERROR: no backups found")
            return 2
        src = cands[-1]

    if not src.is_dir():
        print("ERROR: backup missing", src)
        return 2

    manifest = src / "SHA256MANIFEST.json"
    report = {
        "backup": str(src),
        "manifest_present": manifest.is_file(),
        "has_leveldb": (src / "leveldb").is_dir() or (src / "Local Storage" / "leveldb").is_dir(),
        "has_agents_db": (src / "agents.db").is_file()
        or (src / "Data" / "agents.db").is_file(),
        "has_config": (src / "config.json").is_file(),
    }
    print(json.dumps(report, indent=2))

    if args.prove_only or not args.apply:
        print("ROLLBACK_PROVE=OK (no restore performed)")
        return 0

    if cherry_running():
        print("ERROR: quit Cherry Studio before rollback")
        return 3

    # Safety copy of current state before restore
    safety = BACKUP_ROOT / f"cherry-pre-rollback-{time.strftime('%Y%m%d-%H%M%S')}"
    shutil.copytree(
        CHERRY_ROOT,
        safety,
        ignore=shutil.ignore_patterns("Cache", "Code Cache", "GPUCache", "Dawn*", "Crashpad", "blob_storage"),
    )
    print(f"safety_backup={safety}")

    # Prefer full-tree backups (pre-alignment); enroll backups are partial.
    if (src / "Local Storage").is_dir() or (src / "Data").is_dir():
        # Full tree style
        for name in ("Local Storage", "Data", "config.json", "Preferences", "Local State"):
            s = src / name
            d = CHERRY_ROOT / name
            if not s.exists():
                continue
            if d.exists():
                if d.is_dir():
                    shutil.rmtree(d)
                else:
                    d.unlink()
            if s.is_dir():
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
    else:
        # Partial enroll backup
        if (src / "leveldb").is_dir():
            dest = CHERRY_ROOT / "Local Storage" / "leveldb"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src / "leveldb", dest)
        for name in ("agents.db", "config.json", "Preferences", "Local State"):
            s = src / name
            if not s.is_file():
                continue
            if name == "agents.db":
                shutil.copy2(s, CHERRY_ROOT / "Data" / "agents.db")
            else:
                shutil.copy2(s, CHERRY_ROOT / name)

    print("ROLLBACK_APPLY=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
