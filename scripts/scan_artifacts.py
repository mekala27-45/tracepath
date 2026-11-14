"""Scan published evidence and local service logs with an explicit small rule set."""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANARY = "TRACEPATH_SYNTHETIC_SECRET_4d271b"
RULES = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "neon_credential": re.compile(r"postgres(?:ql)?://[^\s]+@[^\s]*neon\.tech"),
}


def main():
    files = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()
    candidates = [ROOT / name for name in files]
    candidates += list((ROOT / ".local/logs").rglob("*.log"))
    candidates += [p for p in (ROOT / "web/dist").rglob("*") if p.is_file()]
    failures = []
    for item in candidates:
        data = item.read_text(encoding="utf-8", errors="replace")
        for name, pattern in RULES.items():
            if pattern.search(data):
                failures.append({"path": item.relative_to(ROOT).as_posix(), "rule": name})
        public = (
            item.is_relative_to(ROOT / "artifacts")
            or item.is_relative_to(ROOT / "web/public")
            or item.is_relative_to(ROOT / "web/dist")
        )
        log = item.suffix == ".log"
        if (public or log) and CANARY in data:
            failures.append({"path": item.relative_to(ROOT).as_posix(), "rule": "synthetic_canary"})
    result = {
        "schema_version": 1,
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "files_checked": len(candidates),
        "rules": list(RULES) + ["synthetic_canary"],
        "failures": failures,
        "scope": "Tracked source and artifacts plus local service logs; not a security certificate.",
    }
    (ROOT / "artifacts/accepted/source-scan.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"files_checked": len(candidates), "failures": len(failures)}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
