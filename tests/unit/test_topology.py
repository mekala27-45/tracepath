from copy import deepcopy
import pytest
from evaluation.independent_grader.topology import grade


def fixture():
    receipt = {"run_id": "truth", "request_id": "r1", "corpus_digest": "c",
               "model_bundle_digest": "m", "payload_digest": "p", "source_revision": "s"}
    names = ["request", "admission", "worker.http", "worker.request", "encoding",
             "dense.ranking", "lexical.ranking", "fusion", "receipt.commit", "response"]
    parents = [None, 0, 0, 2, 3, 3, 3, 3, 0, 0]
    spans = [{"name": name, "span_id": f"{i+1:016x}", "trace_id": "1"*32,
        "parent_id": None if parents[i] is None else f"{parents[i]+1:016x}",
        "start_ns": 10, "end_ns": 20, "attributes": {**receipt, "mode": "actual_cpu_inference",
        "attempt_id": "a1"}, "service": "tracepath-worker" if 3 <= i <= 7 else "tracepath-gateway",
        "process_id": 2 if 3 <= i <= 7 else 1} for i,name in enumerate(names)]
    return spans, receipt


def test_known_complete():
    spans, receipt = fixture()
    assert grade(spans, receipt)["verdict"] == "complete"


@pytest.mark.parametrize("mutation,expected", [("missing", "incomplete"), ("parent", "invalid"),
    ("duplicate", "invalid"), ("duration", "invalid"), ("foreign", "invalid")])
def test_known_violations(mutation, expected):
    spans, receipt = fixture()
    if mutation == "missing": spans.pop(4)
    if mutation == "parent": spans[4]["parent_id"] = spans[1]["span_id"]
    if mutation == "duplicate": spans.append(deepcopy(spans[4]))
    if mutation == "duration": spans[4]["end_ns"] = 1
    if mutation == "foreign": spans[4]["attributes"]["request_id"] = "foreign"
    assert grade(spans, receipt)["verdict"] == expected


def test_missing_evidence_refused():
    spans, receipt = fixture()
    assert grade([], receipt)["verdict"] == "unavailable"
    assert grade(spans, None)["verdict"] == "unavailable"


def test_cross_process_clock_skew_preserved():
    spans, receipt = fixture()
    spans[4]["start_ns"], spans[4]["end_ns"] = 100, 110
    assert grade(spans, receipt)["verdict"] == "complete"


def test_same_process_is_not_boundary():
    spans, receipt = fixture()
    for span in spans: span["process_id"] = 1
    assert grade(spans, receipt)["verdict"] == "invalid"
