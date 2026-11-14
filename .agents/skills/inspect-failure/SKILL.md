---
name: inspect-failure
description: Diagnose a failed Tracepath request without confusing business completion and missing telemetry.
---

Inputs are the planned ID, run directory and exact source revision. Read AGENTS.md. Inspect the inventory first, then clients.jsonl, ledger.json, worker observations, export boundaries and Collector output. Use the independent grader; do not infer a receipt from HTTP success or a span from expected work.

Run `python -m evaluation.independent_grader.study RUN_ID` for a completed study. Compare immutable request and physical attempt identities. Confirm the failure injector observation and process identity before attributing a fault. Keep missing duration unknown and preserve clock skew.

Expect a specific violated or absent invariant and an evidence path. Refuse cross-run mixing, guessed exporter success or disappearance of failed planned rows. Never inject faults into the public API. Add the observed failure and remedy to DEAD-ENDS.md. This skill is repository-local.
