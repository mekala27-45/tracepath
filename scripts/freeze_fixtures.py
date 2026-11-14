"""One-time authoring of original CC0 operations fixtures and registered workload."""

from pathlib import Path

from packages.contracts.identity import digest, write_json

ROOT = Path(__file__).resolve().parents[1]
NOTES = [
    (
        "sensor_freshness",
        "Tern freshness window",
        "Tern accepts a sensor sample only when its age is at most thirty seconds. An older sample is marked stale and never replaces the last accepted reading.",
    ),
    (
        "sensor_freshness",
        "Gannet clock checks",
        "Gannet compares sensor timestamps with the gateway clock. A sample more than five seconds in the future is quarantined for a clock check.",
    ),
    (
        "sensor_freshness",
        "Ibis heartbeat",
        "Ibis expects a heartbeat every ten seconds. Three missed heartbeats change the sensor status to unknown without inventing a zero reading.",
    ),
    (
        "sensor_freshness",
        "Petrel freshness recovery",
        "Petrel restores fresh status after two consecutive timely samples. It keeps the stale interval in the audit record.",
    ),
    (
        "document_revision",
        "Cairn revision binding",
        "Cairn binds every index to a corpus digest and document version. A changed document creates a new index identity before it can be searched.",
    ),
    (
        "document_revision",
        "Slate revision conflict",
        "Slate rejects a replacement when the submitted previous version differs from the current version. The caller must read the current version before retrying.",
    ),
    (
        "document_revision",
        "Flint immutable snapshots",
        "Flint snapshots are immutable. Corrections create a new snapshot and retain a link to the prior digest.",
    ),
    (
        "document_revision",
        "Mica withdrawal",
        "Mica excludes withdrawn documents from the next published snapshot. Existing receipts retain the version they actually searched.",
    ),
    (
        "request_budgets",
        "Harbor byte budget",
        "Harbor permits at most 1024 UTF-8 bytes in a demo query. Byte length is checked before retrieval and whitespace-only queries are refused.",
    ),
    (
        "request_budgets",
        "Shoal session allowance",
        "Shoal permits twenty search operations per expiring demo session. An identical replay does not consume another operation.",
    ),
    (
        "request_budgets",
        "Reef retry ceiling",
        "Reef retries one transient worker failure at most once. Each physical attempt has a separate identifier under the logical request.",
    ),
    (
        "request_budgets",
        "Cove deadline",
        "Cove uses a five-second worker deadline. A timed-out client does not prove that worker execution stopped.",
    ),
    (
        "model_identity",
        "Lumen artifact binding",
        "Lumen records hashes for model and tokenizer files. A friendly model name alone cannot identify the bytes used for inference.",
    ),
    (
        "model_identity",
        "Prism missing model",
        "Prism refuses learned inference when a required model file is missing. It never silently substitutes lexical or hashing output.",
    ),
    (
        "model_identity",
        "Halo vector checks",
        "Halo checks vector dimension and finite values after encoding. Dense cosine similarity can be negative and is not a calibrated probability.",
    ),
    (
        "model_identity",
        "Beam provider pin",
        "Beam uses the CPU execution provider and a fixed sequence limit. The provider, normalization and pooling policy belong in the model manifest.",
    ),
    (
        "worker_recovery",
        "Anchor committed replay",
        "Anchor reads an existing committed receipt after a lost response. It can return that result without invoking the encoder again.",
    ),
    (
        "worker_recovery",
        "Keel transient failure",
        "Keel returns a controlled transient error before the first encoding attempt. The second worker call gets a distinct attempt identity.",
    ),
    (
        "worker_recovery",
        "Rudder context isolation",
        "Rudder keeps request context isolated during concurrent work. A trace identifier is never a session credential.",
    ),
    (
        "worker_recovery",
        "Moor collector outage",
        "Moor commits business results even when its telemetry collector is offline. Missing spans remain unknown until independent observations arrive.",
    ),
    (
        "artifact_retention",
        "Archive receipt retention",
        "Archive expires demo receipts after one day. Retained study evidence contains synthetic digests and no session tokens.",
    ),
    (
        "artifact_retention",
        "Vault evidence identity",
        "Vault binds accepted reports to hashes of raw observations. Altered raw bytes invalidate the rendered claim.",
    ),
    (
        "artifact_retention",
        "Cache bundle key",
        "Cache keys include the corpus digest and exact model bundle digest. A stale cache cannot be accepted under a new bundle identity.",
    ),
    (
        "artifact_retention",
        "Ledger rejected attempts",
        "Ledger retains failed and missing planned requests in its report. Successful files alone never define the study denominator.",
    ),
]
QUERIES = [
    "When is a Tern sensor sample too old?",
    "How does Gannet handle future timestamps?",
    "What happens after missing Ibis heartbeats?",
    "How does Petrel restore freshness?",
    "How does Cairn identify an index revision?",
    "What should Slate do on a version conflict?",
    "Can Flint replace an immutable snapshot?",
    "What happens to withdrawn Mica documents?",
    "What is the Harbor query byte limit?",
    "Does a Shoal replay consume the session allowance?",
    "How many times can Reef retry?",
    "Does the Cove timeout prove cancellation?",
    "Which files identify the Lumen model?",
    "What happens if a Prism model file is missing?",
    "Can Halo cosine scores be negative?",
    "Which execution provider does Beam use?",
    "Can Anchor recover without another encoder call?",
    "How does Keel identify a retry?",
    "Can a Rudder trace ID authorize a session?",
    "What happens when the Moor collector is offline?",
    "When do Archive demo receipts expire?",
    "What invalidates a Vault report?",
    "What belongs in a Cache bundle key?",
    "Do missing Ledger requests stay in reports?",
]
FAMILIES = [
    "normal",
    "worker_delay",
    "transient_failure",
    "malformed_context",
    "dropped_child",
    "collector_outage",
]


def freeze():
    corpus = [
        {
            "document_id": f"note-{i + 1:03}",
            "version": 1,
            "group": group,
            "title": title,
            "text": text,
        }
        for i, (group, title, text) in enumerate(NOTES)
    ]
    write_json(ROOT / "fixtures/corpus/operations-v1.json", corpus)
    lineages = [
        {
            "lineage_id": f"lineage-{i + 1:02}",
            "family": FAMILIES[i // 4],
            "split": "development" if i % 4 < 2 else "reserved",
            "query": query,
        }
        for i, query in enumerate(QUERIES)
    ]
    for split in ("development", "reserved"):
        write_json(
            ROOT / f"fixtures/{split}/requests.json",
            [row for row in lineages if row["split"] == split],
        )
    scenarios = [
        {
            "planned_id": f"{r['lineage_id']}-{lane}",
            **r,
            "telemetry": lane == "traced",
            "lane": lane,
        }
        for r in lineages
        if r["split"] == "reserved"
        for lane in ("untraced", "traced")
    ]
    overhead = []
    for shape, query in enumerate(QUERIES[::2]):
        for rep in range(3):
            lanes = ("untraced", "traced") if (shape + rep) % 2 == 0 else ("traced", "untraced")
            for order, lane in enumerate(lanes):
                overhead.append(
                    {
                        "planned_id": f"overhead-{shape:02}-{rep}-{lane}",
                        "pair_id": f"pair-{shape:02}-{rep}",
                        "family": "normal",
                        "query": query,
                        "lane": lane,
                        "telemetry": lane == "traced",
                        "order": order,
                    }
                )
    inventory = {
        "schema_version": 1,
        "scenario_lineages": lineages,
        "primary": scenarios,
        "overhead": overhead,
    }
    write_json(ROOT / "evaluation/inventory.json", inventory)
    plan = {
        "schema_version": 1,
        "scope_version": 1,
        "created_at": "2026-11-14",
        "corpus_digest": digest(corpus),
        "inventory_digest": digest(inventory),
        "model": "BAAI/bge-small-en-v1.5",
        "top_k": 5,
        "rrf_k": 60,
        "rank_origin": 1,
        "lexical_tokenizer": "lowercase [a-z0-9]+",
        "worker_timeout_seconds": 5,
        "max_attempts": 2,
        "delay_seconds": 0.15,
        "flush_deadline_seconds": 5,
        "model_tolerance_absolute": 1e-5,
        "model_tolerance_relative": 1e-5,
        "query_result_cache": False,
        "warmup_requests_per_lane": 2,
        "overhead_statistic": "paired traced minus untraced client monotonic milliseconds",
        "primary_invariant": "matching document IDs and scores within registered tolerance",
        "formal_hypotheses": [],
        "inference": "descriptive; one CPU environment",
        "missing_data": "left join inventory; missing stays unavailable",
        "malformed_context_policy": "discard and start a new root",
        "clock_policy": "preserve raw clocks; do not grade cross-process containment",
        "fixture_license": "CC0-1.0",
        "synthetic": True,
    }
    write_json(ROOT / "evaluation/plan.json", plan)
    write_json(
        ROOT / "evaluation/preregistration.json",
        {
            "plan_digest": digest(plan),
            "inventory_digest": digest(inventory),
            "corpus_digest": digest(corpus),
            "reserved_executed_at_freeze": False,
        },
    )


if __name__ == "__main__":
    freeze()
