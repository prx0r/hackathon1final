#!/usr/bin/env python3
"""Release verifier — deterministic gate."""
import json, hashlib, subprocess, sys, platform
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha256(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def run(argv):
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    return {"argv": argv, "status": "PASS" if p.returncode == 0 else "FAIL"}

def main():
    checks = [
        run([sys.executable, "-m", "compileall", "-q", "patala_research_ci"]),
        run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]
    failed = [c for c in checks if c["status"] == "FAIL"]
    status = "PROVEN" if not failed else "FAIL"

    # Artifact set hash
    files = sorted(p for p in ROOT.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts
                   and ".git" not in p.parts
                   and ".venv" not in p.parts
                   and not p.name.endswith(".pyc"))
    artifacts = [{"path": str(p.relative_to(ROOT)), "sha256": sha256(p)} for p in files]
    artifact_hash = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode()).hexdigest()

    cert = {
        "status": status,
        "python": sys.version,
        "platform": platform.platform(),
        "checks": [{k: v for k, v in c.items() if k != "stdout"} for c in checks],
        "artifact_count": len(artifacts),
        "artifact_set_hash": artifact_hash,
    }
    (ROOT / "BUILD_CERTIFICATE.json").write_text(json.dumps(cert, indent=2))
    print(json.dumps({"status": status, "checks": len(checks), "artifacts": len(artifacts)}, indent=2))

if __name__ == "__main__":
    main()
