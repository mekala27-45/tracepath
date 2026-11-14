"""Verify and promote a downloaded Actions archive with explicit source identity."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from packages.contracts.identity import write_json

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--workflow-run", required=True)
    parser.add_argument("--artifact-id", required=True)
    args = parser.parse_args()
    data = args.archive.read_bytes()
    if hashlib.sha256(data).hexdigest() != args.sha256:
        raise ValueError("Actions archive digest mismatch.")
    with zipfile.ZipFile(args.archive) as archive:
        study = json.loads(archive.read("artifacts/accepted/study.json"))
        recovery = json.loads(archive.read("artifacts/accepted/recovery.json"))
        model = json.loads(archive.read("artifacts/raw/model-smoke.json"))
        for record in (study, recovery, model):
            if record["source_revision"] != args.source:
                raise ValueError("Remote evidence belongs to another source revision.")
        if (
            study["acceptance"] != "accepted"
            or not recovery["accepted"]
            or not model["direct_agreement"]
        ):
            raise ValueError("Remote acceptance is incomplete.")
        prefixes = tuple("artifacts/raw/" + r["run_id"] + "/" for r in (study, recovery))
        names = [n for n in archive.namelist() if n.startswith(prefixes) and not n.endswith("/")]
        names.append("artifacts/manifests/" + study["run_id"] + ".json")
        for name in names:
            destination = (ROOT / name).resolve()
            if not destination.is_relative_to(ROOT) or destination.exists():
                raise ValueError("Unsafe or existing evidence destination: " + name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(name))
        for name, record in [("study", study), ("recovery", recovery)]:
            existing = ROOT / ("artifacts/accepted/" + name + ".json")
            previous = json.loads(existing.read_text())
            write_json(ROOT / ("artifacts/accepted/" + previous["run_id"] + ".json"), previous)
            write_json(existing, record)
        write_json(ROOT / ("artifacts/raw/linux-model-smoke-" + args.source[:12] + ".json"), model)
    write_json(
        ROOT / "artifacts/accepted/linux-promotion.json",
        {
            "source_revision": args.source,
            "workflow_run": args.workflow_run,
            "artifact_id": args.artifact_id,
            "archive_sha256": args.sha256,
            "study_run_id": study["run_id"],
            "recovery_run_id": recovery["run_id"],
            "mode": "reviewed_remote_promotion",
            "review": "Archive digest and all source identities checked before independent local rederivation.",
        },
    )
    print(
        "Remote source identities and archive digest verified. Run verify_evidence before committing."
    )


if __name__ == "__main__":
    main()
