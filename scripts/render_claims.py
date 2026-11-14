"""Generate every published numerical summary from hash-checked accepted output."""

import json
from collections import Counter
from pathlib import Path

from packages.evidence.claims import metric_sentence
from scripts.verify_evidence import main as verify

ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = (
    "Portfolio observability experiment around a small retrieval service. "
    "The corpus and fault cases are authored synthetic fixtures. Actual CPU embedding, "
    "live lexical requests and recorded traces are separate. Missing telemetry remains unknown. "
    "Results apply to the declared workload, artifacts and environment, not production reliability "
    "or general RAG quality."
)


def main():
    verify()
    report = json.loads((ROOT / "artifacts/accepted/study.json").read_text())
    checklist = json.loads((ROOT / "evaluation/checklist.json").read_text())
    live_verified = any(e["id"] == 9 and e["status"] == "done" for e in checklist)
    release_verified = any(e["id"] == 18 and e["status"] == "done" for e in checklist)
    publication = (
        "The [live workbench](https://mekala27-45.github.io/tracepath/) and lexical API are published and verified. "
        if live_verified else "Public hosted verification remains pending. "
    ) + (
        "All core acceptance gates and the release are verified."
        if release_verified else "Final release remains pending. See the checklist for open gates."
    )
    hosted = (
        "Public lexical requests, replay and independent receipt readback are verified."
        if live_verified else "Public hosted verification remains pending."
    )
    identity = f"Source {report['source_revision']}; run {report['run_id']}; recorded {report['timestamp']}."
    metrics = "\n\n".join(metric_sentence(m) for m in report["metrics"])
    table = "| Gate | Status | Evidence and identity | Observation |\n| --- | --- | --- | --- |\n"
    for entry in checklist:
        table += f"| {entry['id']:02d} {entry['requirement']} | {entry['status']} | [{entry['path']}]({entry['path']}); {entry['identity']} | {entry['observation']} |\n"
    counts = Counter(
        (r["family"], r["lane"], r["business"], r["trace"]["verdict"]) for r in report["primary"]
    )
    outcomes = "| Family | Lane | Business | Trace | Requests |\n| --- | --- | --- | --- | ---: |\n"
    for (family, lane, business, verdict), count in sorted(counts.items()):
        outcomes += f"| {family} | {lane} | {business} | {verdict} | {count} |\n"
    exports = []
    for service in ["gateway", "worker"]:
        file = ROOT / f"artifacts/raw/{report['run_id']}/{service}-export.jsonl"
        records = [json.loads(line) for line in file.read_text().splitlines() if line]
        totals = {
            key: sum(row[key] for row in records)
            for key in ["received", "exported", "dropped_at_boundary", "unknown"]
        }
        exports.append({"service": service, **totals})
    result = f"# Tracepath results\n\n{DISCLAIMER}\n\n{identity}\n\n## Accepted measurements\n\n{metrics}\n\n## Scenario observations\n\n{outcomes}\n## Export boundary\n\nCounts below include warmup. Exported means exporter acknowledgement, not independent Collector persistence.\n\n"
    result += "| Service | Received | Exported | Deliberately dropped | Unknown |\n| --- | ---: | ---: | ---: | ---: |\n"
    for e in exports:
        result += f"| {e['service']} | {e['received']} | {e['exported']} | {e['dropped_at_boundary']} | {e['unknown']} |\n"
    result += "\n## Resource observations\n\n" + report["resources"]["method"] + ".\n\n"
    result += "```json\n" + json.dumps(report["resources"], indent=2) + "\n```\n\n"
    result += (
        "## Definition of done\n\n"
        + table
        + "\nStretch: not started. The earlier Windows recording is retained separately and is not pooled with the promoted Linux study.\n"
    )
    (ROOT / "RESULTS.md").write_text(result, encoding="ascii")
    readme = f"""# Tracepath

Tracepath answers two separate questions: did retrieval commit, and did we observe its path? A PostgreSQL receipt records business completion. An independent checker reconciles actual Collector spans against the planned request inventory.

{DISCLAIMER}

## Status and evidence

{publication} Read the full eighteen-line [checklist](RESULTS.md), [setup and recovery guide](docs/RUNBOOK.md), [method](docs/METHOD.md), and [review branch](https://github.com/mekala27-45/tracepath/pull/1).

{identity}

{metrics}

## Architecture

```mermaid
flowchart TD
    Client[Client] --> Gateway[Gateway process]
    Gateway --> Worker[CPU retrieval worker]
    Gateway --> Ledger[Postgres receipts]
    Worker --> Collector[OpenTelemetry Collector]
    Gateway --> Collector
    Ledger --> Grader[Independent grader]
    Collector --> Grader
    Plan[Frozen inventory] --> Grader
    Grader --> UI[Recorded workbench]
```

The public request view performs lexical ranking. The recorded Trace, Coverage and Method views display actual CPU evidence. Missing telemetry is incomplete or unavailable. A green trace result does not establish semantic retrieval correctness.

## Reproduce

Install requirements.lock in Python 3.12.14, prepare the pinned model, and follow [RUNBOOK.md](docs/RUNBOOK.md). The [Linux workflow](.github/workflows/verify.yml) exercises actual inference, HTTP process boundaries, a disposable database, fault scenarios, crash recovery and the typed frontend. Recompute retained claims with `python -m scripts.verify_evidence` and `python -m scripts.render_claims`.

The small retrieval contract is adapted from GroundedRAG. See [REUSE.md](REUSE.md), [NOTICE](NOTICE), the three [ADRs](docs/ADR-001-retrieval-reuse.md) and [agent operating rules](AGENTS.md). The original synthetic corpus is CC0. No external messages or social posts were sent.
"""
    (ROOT / "README.md").write_text(readme, encoding="ascii")
    values = "\n\n" + metrics + "\n\n" + identity
    career = f"""# Tracepath technical walkthrough and unsent drafts

{DISCLAIMER}

## Walkthrough

Start with a receipt that committed while its encoding span was intentionally dropped. Show the request identity in the independent database export, then show the missing observation in Collector evidence. Compare a complete case with a collector-outage case. Finish with the separate-process crash replay: the same receipt returns without another physical attempt.

## Interview card A

I built Tracepath to distinguish retrieval completion from telemetry completeness. I adapted the GroundedRAG retrieval contract at b3273286b3a8f3f48cdb4f540d65c297ad096ccc and added a scoped receipt ledger, W3C process propagation and an independent topology checker. The registered Linux study produced the accepted values below. They do not establish production reliability or semantic accuracy.

## Interview card B

The initial recovery harness expected one HTTP transport exception. Windows reported a connection reset as another transport exception after the deliberate process exit. I accepted both transport-loss types and verified a new process returned the existing receipt with one physical attempt. The failed run remains in the repository. {hosted}

## Resume draft

Built and independently checked a Python retrieval tracing service with pinned CPU embeddings, PostgreSQL receipts, cross-process OpenTelemetry and deterministic replay; verified the registered synthetic workload and process-death recovery on a Linux runner. Attach only the measured values and source identity below.

## LinkedIn option A: result

Day 29: Tracepath. I separated committed retrieval results from observed trace coverage. The registered synthetic study matched every traced/untraced output pair, while deliberate missing spans remained incomplete. The exact denominators and timing measurements are below. Code and evidence: https://github.com/mekala27-45/tracepath/pull/1

## LinkedIn option B: decision

For Tracepath, I kept the business ledger outside the telemetry path. The deciding evidence was a committed result whose child observation was deliberately omitted after real encoding. The independent checker refused to call that trace complete. This is a bounded synthetic experiment, with no production uptime claim.

## LinkedIn option C: failure

A retrieval response can survive a Collector outage. Tracepath retains the committed receipt and marks the missing trace unavailable. A separate recovery test kills the gateway after commit and checks replay from a fresh process. The evidence applies to the declared workload and environment. {hosted}

## Accepted values for these drafts
{values}

All drafts are unsent. No demo GIF has been claimed or published.
"""
    (ROOT / "docs/CAREER_KIT.md").write_text(career, encoding="ascii")
    print("README, RESULTS and career drafts generated from accepted evidence.")


if __name__ == "__main__":
    main()
