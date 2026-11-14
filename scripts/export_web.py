import json
import shutil
from pathlib import Path

from scripts.verify_evidence import main as verify

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "artifacts/accepted/study.json"
target = ROOT / "web/public/study.json"
if source.is_file():
    verify()
    shutil.copyfile(source, target)
else:
    target.write_text(json.dumps({"acceptance": "unavailable"}) + "\n")
