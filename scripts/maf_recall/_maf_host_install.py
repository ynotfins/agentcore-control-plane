from pathlib import Path
import subprocess, sys, os
REPO = Path(r"D:\github\agentcore-control-plane")
venv = REPO / "scripts" / "maf_recall" / "maf_host" / ".venv"
req = REPO / "scripts" / "maf_recall" / "maf_host" / "requirements.txt"
py = sys.executable
venv.parent.mkdir(parents=True, exist_ok=True)
if not (venv / "Scripts" / "python.exe").is_file():
    subprocess.run([py, "-m", "venv", str(venv)], check=True)
pip = str(venv / "Scripts" / "pip.exe")
print("PIP_INSTALL_START")
subprocess.run([pip, "install", "-r", str(req)], check=True)
vpy = str(venv / "Scripts" / "python.exe")
r = subprocess.run([vpy, "-c", "import agent_framework; print('import_ok')"], capture_output=True, text=True)
print("IMPORT_RC", r.returncode)
print(r.stdout or "")
print(r.stderr or "")
print("GUARD_SKIPPED")