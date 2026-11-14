"""Independent OTLP projection grading. Does not import instrumentation code."""

import re
from collections import Counter

REQUIRED = {
    "request",
    "admission",
    "worker.http",
    "worker.request",
    "encoding",
    "dense.ranking",
    "lexical.ranking",
    "fusion",
    "receipt.commit",
    "response",
}
PARENTS = {
    "admission": "request",
    "worker.http": "request",
    "worker.request": "worker.http",
    "encoding": "worker.request",
    "dense.ranking": "worker.request",
    "lexical.ranking": "worker.request",
    "fusion": "worker.request",
    "receipt.commit": "request",
    "response": "request",
}
WORKER = {"worker.request", "encoding", "dense.ranking", "lexical.ranking", "fusion"}


def grade(spans, receipt, expected_attempts=None):
    if not receipt:
        return {
            "verdict": "unavailable",
            "reasons": ["receipt unavailable"],
            "missing": sorted(REQUIRED),
        }
    if not spans:
        return {
            "verdict": "unavailable",
            "reasons": ["no observed spans"],
            "missing": sorted(REQUIRED),
        }
    invalid, missing = [], []
    ids = [s.get("span_id") for s in spans]
    if any(count > 1 for count in Counter(ids).values()):
        invalid.append("duplicate span ID")
    by_id = {s.get("span_id"): s for s in spans}
    traces = {s.get("trace_id") for s in spans}
    if len(traces) != 1:
        invalid.append("multiple trace IDs")
    if any(
        not isinstance(t, str) or not re.fullmatch(r"[0-9a-f]{32}", t) or int(t, 16) == 0
        for t in traces
    ):
        invalid.append("invalid trace ID")
    for span in spans:
        attr = span.get("attributes", {})
        for field in (
            "run_id",
            "request_id",
            "corpus_digest",
            "model_bundle_digest",
            "payload_digest",
            "source_revision",
        ):
            if attr.get(field) != receipt.get(field):
                invalid.append(f"identity mismatch: {field}")
        start, end = span.get("start_ns"), span.get("end_ns")
        if not isinstance(start, int) or not isinstance(end, int) or end < start:
            invalid.append("invalid duration")
        if (
            not isinstance(span.get("span_id"), str)
            or not re.fullmatch(r"[0-9a-f]{16}", span["span_id"])
            or int(span["span_id"], 16) == 0
        ):
            invalid.append("invalid span ID")
        name = span.get("name")
        if name not in REQUIRED:
            invalid.append("unknown operation")
        expected_service = "tracepath-worker" if name in WORKER else "tracepath-gateway"
        if span.get("service") != expected_service:
            invalid.append("service identity mismatch")
        if attr.get("mode") != "actual_cpu_inference":
            invalid.append("execution mode mismatch")
        if name in PARENTS:
            parent = by_id.get(span.get("parent_id"))
            if parent is None:
                missing.append(f"parent of {name}")
            elif parent.get("name") != PARENTS[name]:
                invalid.append(f"wrong parent: {name}")
            elif name in WORKER and parent.get("attributes", {}).get("attempt_id") != attr.get(
                "attempt_id"
            ):
                invalid.append(f"attempt mismatch: {name}")
        # Cycle detection does not assume synchronized clocks across services.
        visited, current = set(), span
        while current and current.get("parent_id") in by_id:
            if current["span_id"] in visited:
                invalid.append("parent cycle")
                break
            visited.add(current["span_id"])
            current = by_id[current["parent_id"]]
    names = Counter(s.get("name") for s in spans)
    missing += sorted(REQUIRED - set(names))
    for name in ("request", "admission", "receipt.commit", "response"):
        if names[name] > 1:
            invalid.append(f"duplicate operation: {name}")
    observed_attempts = {
        s.get("attributes", {}).get("attempt_id")
        for s in spans
        if s.get("name") == "worker.request"
    }
    per_attempt = Counter(
        (s.get("attributes", {}).get("attempt_id"), s.get("name"))
        for s in spans
        if s.get("name") in WORKER | {"worker.http"}
    )
    if any(count > 1 for count in per_attempt.values()):
        invalid.append("duplicate physical operation")
    if expected_attempts is not None:
        known = {a["attempt_id"] for a in expected_attempts}
        if observed_attempts - known:
            invalid.append("unknown physical attempt")
        if known - observed_attempts:
            missing.append("physical attempt")
        for attempt in expected_attempts:
            if attempt.get("status") == "completed":
                operations = {
                    s.get("name")
                    for s in spans
                    if s.get("attributes", {}).get("attempt_id") == attempt["attempt_id"]
                }
                missing += [
                    f"{attempt['attempt_id']}:{name}" for name in sorted(WORKER - operations)
                ]
    pids = {
        service: {s.get("process_id") for s in spans if s.get("service") == service}
        for service in ("tracepath-gateway", "tracepath-worker")
    }
    if pids["tracepath-gateway"] & pids["tracepath-worker"] or None in set.union(*pids.values()):
        invalid.append("process boundary not observed")
    return {
        "verdict": "invalid" if invalid else "incomplete" if missing else "complete",
        "reasons": sorted(set(invalid)),
        "missing": sorted(set(missing)),
        "observed_spans": len(spans),
        "observed_attempts": len(observed_attempts),
    }
