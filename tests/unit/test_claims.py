import pytest

from packages.contracts.identity import file_digest, write_json
from packages.evidence.claims import EvidenceRefusal, load_accepted, metric_sentence


def test_claim_clean_violation_absent(tmp_path):
    raw = tmp_path / "raw.json"
    write_json(raw, {"observed": True})
    manifest = tmp_path / "manifest.json"
    write_json(
        manifest,
        {
            "schema_version": 1,
            "acceptance": "accepted",
            "run_id": "r1",
            "source_revision": "a" * 40,
            "artifacts": [{"path": "raw.json", "sha256": file_digest(raw)}],
        },
    )
    assert load_accepted(tmp_path, manifest)["run_id"] == "r1"
    write_json(raw, {"observed": False})
    with pytest.raises(EvidenceRefusal, match="digest changed"):
        load_accepted(tmp_path, manifest)
    raw.unlink()
    with pytest.raises(EvidenceRefusal, match="absent"):
        load_accepted(tmp_path, manifest)


def test_refuses_missing_acceptance_and_escape(tmp_path):
    manifest = tmp_path / "manifest.json"
    write_json(manifest, {"schema_version": 1, "acceptance": "planned"})
    with pytest.raises(EvidenceRefusal):
        load_accepted(tmp_path, manifest)
    write_json(
        manifest,
        {
            "schema_version": 1,
            "acceptance": "accepted",
            "run_id": "r",
            "source_revision": "a" * 40,
            "artifacts": [{"path": "../escape", "sha256": "a" * 64}],
        },
    )
    with pytest.raises(EvidenceRefusal):
        load_accepted(tmp_path, manifest)


def test_no_observations_never_becomes_zero():
    m = {
        "name": "overhead",
        "value": None,
        "unit": "ms",
        "denominator": 0,
        "window_start": "a",
        "window_end": "b",
        "mode": "unavailable",
        "source": "raw",
    }
    assert metric_sentence(m) == "overhead: unavailable."
    del m["unit"]
    with pytest.raises(EvidenceRefusal):
        metric_sentence(m)
