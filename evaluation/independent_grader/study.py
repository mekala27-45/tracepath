"""Join from the inventory. Never derive coverage from successful artifacts."""
import argparse
import json
import math
import statistics
from pathlib import Path
from packages.contracts.identity import digest, file_digest, write_json
from evaluation.independent_grader.collector import read_collector
from evaluation.independent_grader.topology import grade

ROOT = Path(__file__).resolve().parents[2]


def same_hits(left, right):
    if not left or not right or len(left) != len(right):
        return False
    for a, b in zip(left, right, strict=True):
        if a["document_id"] != b["document_id"]:
            return False
        for field in ("dense_cosine", "lexical_score", "fusion_score"):
            if not math.isclose(a[field], b[field], rel_tol=1e-5, abs_tol=1e-5):
                return False
    return True


def percentile(values, p):
    values = sorted(values)
    if not values:
        return None
    # Nearest-rank; the method and denominator are retained.
    return values[max(0, math.ceil(len(values)*p)-1)]


def derive(directory, inventory):
    raw = [json.loads(line) for line in (directory/"clients.jsonl").read_text().splitlines()]
    by_id = {r["planned_id"]: r for r in raw}
    ledger = json.loads((directory/"ledger.json").read_text())
    receipts = {r["request_id"]:r for r in ledger["receipts"]}
    all_spans = read_collector(directory/"collector.jsonl")
    environment = json.loads((directory/"environment.json").read_text())
    window = json.loads((directory/"window.json").read_text())
    rows = []
    for planned in inventory["primary"] + inventory["overhead"]:
        observed = by_id.get(planned["planned_id"])
        receipt = receipts.get(observed.get("request_id")) if observed else None
        spans = [s for s in all_spans if receipt and s["attributes"].get("request_id") == receipt["request_id"]]
        check = grade(spans, receipt, receipt.get("attempts") if receipt else None)
        known = "unavailable" if not planned["telemetry"] or planned["family"] == "collector_outage" else (
            "incomplete" if planned["family"] == "dropped_child" else "complete")
        row = {"planned_id": planned["planned_id"], "family": planned["family"],
            "lane": planned["lane"], "pair_id": planned.get("pair_id"),
            "request_id": receipt.get("request_id") if receipt else None,
            "business": "committed" if receipt else "unavailable", "trace": check,
            "expected_trace": known, "trace_matches_control": check["verdict"] == known,
            "client_duration_ms": observed.get("client_duration_ms") if observed else None,
            "independent_readback": bool(receipt and observed and observed.get("http_readback") and
                receipt["output_digest"] == observed.get("output_digest")),
            "attempt_count": len(receipt.get("attempts", [])) if receipt else 0,
            "mode": "recorded_experiment", "underlying_mode": "actual_cpu_inference",
            "spans": spans, "hits": receipt.get("hits", []) if receipt else []}
        rows.append(row)
    primary = rows[:len(inventory["primary"])]
    agreement = []
    for i in range(0, len(primary), 2):
        a,b = primary[i:i+2]
        agreement.append({"lineage": inventory["primary"][i]["lineage_id"],
                          "agreement": same_hits(a["hits"],b["hits"])})
    pairs = {}
    for row in rows[len(primary):]:
        pairs.setdefault(row["pair_id"], {})[row["lane"]] = row
    differences = []
    for pair_id, lanes in sorted(pairs.items()):
        a,b = lanes.get("untraced"),lanes.get("traced")
        if a and b and a["independent_readback"] and b["independent_readback"] and same_hits(a["hits"],b["hits"]):
            differences.append({"pair_id": pair_id, "difference_ms": b["client_duration_ms"]-a["client_duration_ms"],
                                "traced_ms": b["client_duration_ms"], "untraced_ms": a["client_duration_ms"]})
    values = [p["difference_ms"] for p in differences]
    accepted = (len(rows) == 96 and all(r["independent_readback"] and r["trace_matches_control"] for r in rows)
                and all(p["agreement"] for p in agreement) and len(differences) == 36)
    common = {"window_start": window["started_at"], "window_end": window["finished_at"],
              "mode": "actual_cpu_inference", "source": f"artifacts/raw/{directory.name}"}
    metrics = [{**common, "name": "Committed primary requests", "value": sum(r["business"]=="committed" for r in primary),
                "unit": "requests", "denominator": len(primary)},
               {**common, "name": "Matched business outputs", "value": sum(p["agreement"] for p in agreement),
                "unit": "pairs", "denominator": len(agreement)},
               {**common, "name": "Median paired tracing overhead", "value": statistics.median(values) if values else None,
                "unit": "ms", "denominator": len(values)},
               {**common, "name": "P95 paired tracing overhead", "value": percentile(values,.95),
                "unit": "ms", "denominator": len(values)}]
    return {"schema_version": 1, "acceptance": "accepted" if accepted else "rejected", "run_id": directory.name,
        "source_revision": environment["source_revision"], "mode": "recorded_experiment",
        "timestamp": window["finished_at"], "environment": environment, "metrics": metrics,
        "primary": primary, "overhead": rows[len(primary):], "business_agreement": agreement,
        "pairs": differences, "percentile_method": "nearest rank", "formal_hypotheses": [],
        "limits": ["One CPU environment and one synthetic workload.",
            "Client time includes database connections, export flush and process scheduling.",
            "Trace completeness is not semantic retrieval correctness.",
            "No production reliability or general model quality claim."],
        "resources": json.loads((directory/"resources.json").read_text())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    args = parser.parse_args()
    if not args.run_id.startswith("study-") or "/" in args.run_id or "\\" in args.run_id:
        raise ValueError("Expected a recorded study ID.")
    directory = ROOT/"artifacts/raw"/args.run_id
    inventory = json.loads((ROOT/"evaluation/inventory.json").read_text())
    report = derive(directory, inventory)
    destination = "accepted" if report["acceptance"] == "accepted" else "rejected"
    write_json(ROOT/f"artifacts/{destination}/study.json", report)
    files = [p for p in sorted(directory.rglob("*")) if p.is_file()]
    manifest = {"schema_version": 1, "run_id": args.run_id, "source_revision": report["source_revision"],
        "acceptance": report["acceptance"], "artifacts": [{"path": p.relative_to(ROOT).as_posix(),
        "sha256": file_digest(p)} for p in files], "report_digest": digest(report), "metrics": report["metrics"]}
    write_json(ROOT/f"artifacts/manifests/{args.run_id}.json", manifest)
    print(json.dumps({"acceptance": report["acceptance"], "metrics": report["metrics"],
        "unexpected": [{"id": r["planned_id"], "trace":r["trace"]} for r in report["primary"]+report["overhead"]
            if not r["trace_matches_control"]]}, indent=2))
    if report["acceptance"] != "accepted":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
