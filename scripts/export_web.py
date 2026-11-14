import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "artifacts/accepted/study.json"
target = ROOT / "web/public/study.json"
if source.is_file():
    shutil.copyfile(source, target)
else:
    target.write_text(json.dumps({"acceptance": "unavailable"}) + "\n")
