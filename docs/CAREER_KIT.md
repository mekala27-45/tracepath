# Tracepath technical walkthrough and unsent drafts

Portfolio observability experiment around a small retrieval service. The corpus and fault cases are authored synthetic fixtures. Actual CPU embedding, live lexical requests and recorded traces are separate. Missing telemetry remains unknown. Results apply to the declared workload, artifacts and environment, not production reliability or general RAG quality.

## Walkthrough

Start with a receipt that committed while its encoding span was intentionally dropped. Show the request identity in the independent database export, then show the missing observation in Collector evidence. Compare a complete case with a collector-outage case. Finish with the separate-process crash replay: the same receipt returns without another physical attempt.

## Interview card A

I built Tracepath to distinguish retrieval completion from telemetry completeness. I adapted the GroundedRAG retrieval contract at b3273286b3a8f3f48cdb4f540d65c297ad096ccc and added a scoped receipt ledger, W3C process propagation and an independent topology checker. The registered Linux study produced the accepted values below. They do not establish production reliability or semantic accuracy.

## Interview card B

The initial recovery harness expected one HTTP transport exception. Windows reported a connection reset as another transport exception after the deliberate process exit. I accepted both transport-loss types and verified a new process returned the existing receipt with one physical attempt. The failed run remains in the repository. Public hosted verification is still open.

## Resume draft

Built and independently checked a Python retrieval tracing service with pinned CPU embeddings, PostgreSQL receipts, cross-process OpenTelemetry and deterministic replay; verified the registered synthetic workload and process-death recovery on a Linux runner. Attach only the measured values and source identity below.

## LinkedIn option A: result

Day 29: Tracepath. I separated committed retrieval results from observed trace coverage. The registered synthetic study matched every traced/untraced output pair, while deliberate missing spans remained incomplete. The exact denominators and timing measurements are below. Code and evidence: https://github.com/mekala27-45/tracepath/pull/1

## LinkedIn option B: decision

For Tracepath, I kept the business ledger outside the telemetry path. The deciding evidence was a committed result whose child observation was deliberately omitted after real encoding. The independent checker refused to call that trace complete. This is a bounded synthetic experiment, with no production uptime claim.

## LinkedIn option C: failure

A retrieval response can survive a Collector outage. Tracepath retains the committed receipt and marks the missing trace unavailable. A separate recovery test kills the gateway after commit and checks replay from a fresh process. The evidence applies to the declared workload and environment. Public hosting remains pending.

## Accepted values for these drafts


Committed primary requests: 24.000 requests; denominator 24. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

Matched business outputs: 12.000 pairs; denominator 12. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

Median paired tracing overhead: 4.233 ms; denominator 36. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

P95 paired tracing overhead: 17.277 ms; denominator 36. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

Source 1193110a8e3f91a944d5137d704b367c9776051a; run study-459aa21b5ffe; recorded 2026-11-14T02:38:01.443506+00:00.

All drafts are unsent. No demo GIF has been claimed or published.
