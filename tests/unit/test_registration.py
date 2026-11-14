import json
from pathlib import Path

from packages.contracts.identity import digest

ROOT = Path(__file__).resolve().parents[2]


def test_frozen_inventory_covers_all_rows():
    inv = json.loads((ROOT / "evaluation/inventory.json").read_text())
    plan = json.loads((ROOT / "evaluation/plan.json").read_text())
    pre = json.loads((ROOT / "evaluation/preregistration.json").read_text())
    corpus = json.loads((ROOT / "fixtures/corpus/operations-v1.json").read_text())
    assert len(corpus) == 24 and len({d["document_id"] for d in corpus}) == 24
    assert len(inv["primary"]) == 24 and len(inv["overhead"]) == 72
    assert len(inv["scenario_lineages"]) == 24
    assert len({r["planned_id"] for r in inv["primary"] + inv["overhead"]}) == 96
    assert digest(inv) == pre["inventory_digest"] == plan["inventory_digest"]
    assert digest(plan) == pre["plan_digest"]
    assert digest(corpus) == pre["corpus_digest"] == plan["corpus_digest"]
    for family in {r["family"] for r in inv["scenario_lineages"]}:
        rows = [r for r in inv["scenario_lineages"] if r["family"] == family]
        assert sum(r["split"] == "development" for r in rows) == 2
        assert sum(r["split"] == "reserved" for r in rows) == 2
