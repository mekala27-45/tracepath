import json
import shutil
from pathlib import Path

from evaluation.independent_grader.study import derive

ROOT = Path(__file__).resolve().parents[2]


def test_missing_and_changed_client_evidence_preserves_denominator(tmp_path):
    accepted = json.loads((ROOT / "artifacts/accepted/study.json").read_text())
    raw = ROOT / "artifacts/raw" / accepted["run_id"]
    target = tmp_path / accepted["run_id"]
    shutil.copytree(raw, target)
    inventory = json.loads((ROOT / "evaluation/inventory.json").read_text())
    assert derive(target, inventory)["acceptance"] == "accepted"
    clients = [json.loads(line) for line in (target / "clients.jsonl").read_text().splitlines()]
    missing_id = inventory["primary"][0]["planned_id"]
    changed_id = inventory["primary"][1]["planned_id"]
    clients = [row for row in clients if row["planned_id"] != missing_id]
    for row in clients:
        if row["planned_id"] == changed_id:
            row["output_digest"] = "0" * 64
    (target / "clients.jsonl").write_text("\n".join(json.dumps(row) for row in clients) + "\n")
    refused = derive(target, inventory)
    assert refused["acceptance"] == "rejected"
    assert len(refused["primary"]) == 24
    assert len(refused["overhead"]) == 72
    assert refused["primary"][0]["business"] == "unavailable"
    assert refused["primary"][0]["client_duration_ms"] is None
    assert not refused["primary"][1]["independent_readback"]
