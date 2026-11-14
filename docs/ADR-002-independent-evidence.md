# ADR 002: Keep receipts independent from telemetry

Status: accepted. Decision date: 2026-11-14.

A missing span cannot tell us whether work failed or observation failed. A gateway and a retrieval worker communicate through real HTTP. The gateway transaction commits a result receipt and operation-key binding. A separate database connection records physical attempts. The Collector writes exported spans independently.

W3C trace context connects the process boundary. It grants no authorization. Session scope comes from a random bearer token whose SHA256 digest is stored in the ledger. Request, attempt, corpus, model, payload and source identities travel with the work. The worker rejects inconsistent identities.

The independent grader imports no instrumentation code. It starts from the frozen planned inventory, joins receipts and raw Collector spans, and checks parent relations, duplicate IDs, operation multiplicity, identities, process separation and durations. An omitted child is incomplete. No observed spans is unavailable. An identity or topology violation is invalid. A committed receipt remains a separate finding.

The exporter uses bounded queues and deadlines. Its received, exported, deliberately dropped and unknown counts explain the export boundary. These counts do not prove Collector persistence. The collector outage is a real process stop and the dropped-child fault occurs at the exporter boundary after actual encoding.

Cross-process timestamp containment is not a grading rule because clocks can skew. Client monotonic time measures end-to-end latency. Overlapping spans must not be added to produce it.

Sources inspected 2026-11-14: [OpenTelemetry propagation](https://opentelemetry.io/docs/concepts/context-propagation/), [Collector resiliency](https://opentelemetry.io/docs/collector/resiliency/), [W3C Trace Context](https://www.w3.org/TR/trace-context/).
