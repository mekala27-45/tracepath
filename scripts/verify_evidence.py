"""Clean rederivation reads raw artifacts and refuses altered report provenance."""
import json
from pathlib import Path
from packages.contracts.identity import digest
from packages.evidence.claims import load_accepted
from evaluation.independent_grader.study import derive

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = json.loads((ROOT/"artifacts/accepted/study.json").read_text())
    manifest = load_accepted(ROOT, ROOT/f"artifacts/manifests/{report['run_id']}.json")
    recomputed = derive(ROOT/"artifacts/raw"/report["run_id"],
                        json.loads((ROOT/"evaluation/inventory.json").read_text()))
    if digest(recomputed) != digest(report) or digest(report) != manifest["report_digest"]:
        raise ValueError("Accepted report does not match independent raw rederivation.")
    print("Raw evidence identities and independent report rederivation passed.")


if __name__ == "__main__":
    main()
