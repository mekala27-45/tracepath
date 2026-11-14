"""Fresh two-process HTTP inference smoke with independent ledger and trace checks."""

import json
import uuid

from evaluation.independent_grader.collector import read_collector
from evaluation.independent_grader.topology import grade
from packages.contracts.identity import write_json
from scripts.run_study import ROOT, Lab


def main():
    lab = Lab("smoke-" + uuid.uuid4().hex[:12])
    rows = []
    try:
        lab.start()
        session = lab.session()
        for i, query in enumerate(
            ["When is a Tern sensor reading stale?", "How does Anchor recover a committed receipt?"]
        ):
            rows.append(
                lab.execute(
                    {
                        "planned_id": f"fresh-smoke-{i}",
                        "query": query,
                        "family": "normal",
                        "lane": "traced",
                        "telemetry": True,
                    },
                    session,
                    "fresh_smoke",
                )
            )
    finally:
        lab.close()
    spans = read_collector(lab.directory / "collector.jsonl")
    ledger = json.loads((lab.directory / "ledger.json").read_text())
    verdicts = []
    readbacks = []
    for row in rows:
        receipt = next(
            (r for r in ledger["receipts"] if r["request_id"] == row.get("request_id")), None
        )
        readbacks.append(
            bool(
                receipt
                and row.get("http_readback")
                and receipt["output_digest"] == row.get("output_digest")
            )
        )
        verdicts.append(
            grade(
                [s for s in spans if s["attributes"].get("request_id") == row.get("request_id")],
                receipt,
                receipt["attempts"] if receipt else None,
            )
        )
    accepted = (
        len(rows) == 2 and all(readbacks) and all(g["verdict"] == "complete" for g in verdicts)
    )
    report = {
        "accepted": accepted,
        "run_id": lab.run_id,
        "source_revision": lab.revision,
        "actual_http_requests": len(rows),
        "grades": verdicts,
    }
    write_json(ROOT / "artifacts/accepted/fresh-smoke.json", report)
    print(json.dumps(report))
    if not accepted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
