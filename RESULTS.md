# Tracepath results

Portfolio observability experiment around a small retrieval service. The corpus and fault cases are authored synthetic fixtures. Actual CPU embedding, live lexical requests and recorded traces are separate. Missing telemetry remains unknown. Results apply to the declared workload, artifacts and environment, not production reliability or general RAG quality.

Source 1193110a8e3f91a944d5137d704b367c9776051a; run study-459aa21b5ffe; recorded 2026-11-14T02:38:01.443506+00:00.

## Accepted measurements

Committed primary requests: 24.000 requests; denominator 24. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

Matched business outputs: 12.000 pairs; denominator 12. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

Median paired tracing overhead: 4.233 ms; denominator 36. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

P95 paired tracing overhead: 17.277 ms; denominator 36. Source artifacts/raw/study-459aa21b5ffe; window 2026-11-14T02:37:47.330382+00:00 to 2026-11-14T02:38:01.443506+00:00; mode actual_cpu_inference.

## Scenario observations

| Family | Lane | Business | Trace | Requests |
| --- | --- | --- | --- | ---: |
| collector_outage | traced | committed | unavailable | 2 |
| collector_outage | untraced | committed | unavailable | 2 |
| dropped_child | traced | committed | incomplete | 2 |
| dropped_child | untraced | committed | unavailable | 2 |
| malformed_context | traced | committed | complete | 2 |
| malformed_context | untraced | committed | unavailable | 2 |
| normal | traced | committed | complete | 2 |
| normal | untraced | committed | unavailable | 2 |
| transient_failure | traced | committed | complete | 2 |
| transient_failure | untraced | committed | unavailable | 2 |
| worker_delay | traced | committed | complete | 2 |
| worker_delay | untraced | committed | unavailable | 2 |

## Export boundary

Counts below include warmup. Exported means exporter acknowledgement, not independent Collector persistence.

| Service | Received | Exported | Deliberately dropped | Unknown |
| --- | ---: | ---: | ---: | ---: |
| gateway | 252 | 242 | 0 | 10 |
| worker | 252 | 240 | 2 | 10 |

## Resource observations

RSS sampled after each request plus OS high water: Windows peak_wset or Linux VmHWM; maximum across observed process generations.

```json
{
  "cpu_seconds": {
    "gateway": 4.1899999999999995,
    "worker": 2.7
  },
  "method": "RSS sampled after each request plus OS high water: Windows peak_wset or Linux VmHWM; maximum across observed process generations",
  "os_high_water_rss_bytes": {
    "collector": 375992320,
    "gateway": 106262528,
    "worker": 329437184
  },
  "sampled_peak_rss_bytes": {
    "collector": 375992320,
    "gateway": 106262528,
    "worker": 329437184
  }
}
```

## Definition of done

| Gate | Status | Evidence and identity | Observation |
| --- | --- | --- | --- |
| 01 Source, package, host and model probes are recorded with current identities. | done | [artifacts/accepted/deployment-preparation.json](artifacts/accepted/deployment-preparation.json); 1193110a8e3f91a944d5137d704b367c9776051a | Pinned model and packages ran; the protected host built with an identified source. |
| 02 Claim renderer and all required gates pass clean, violated and absent cases. | done | [tests/unit/test_claims.py](tests/unit/test_claims.py); 735c800b345b06f318a570ac4ed6e5492aa7ed49 | Claims refuse missing, altered, unaccepted and unregistered-unit evidence; runtime contract and topology fixtures are exercised. |
| 03 Corpus, request lineages, topology fixtures and evaluation plan are frozen. | done | [evaluation/preregistration.json](evaluation/preregistration.json); 1193110a8e3f91a944d5137d704b367c9776051a | The frozen inventory retains twenty-four lineages and all registered primary and overhead IDs. |
| 04 Pinned CPU encoder actually runs and copied kernel contracts pass. | done | [artifacts/raw/linux-model-smoke-1193110a8e3f.json](artifacts/raw/linux-model-smoke-1193110a8e3f.json); 1193110a8e3f91a944d5137d704b367c9776051a | Two actual CPU calls matched the independent ONNX path within the declared tolerance. |
| 05 Two real processes propagate context with valid request isolation. | done | [artifacts/accepted/recovery.json](artifacts/accepted/recovery.json); recovery-f2a5dc74851c / 1193110a8e3f91a944d5137d704b367c9776051a | Separate worker and gateway processes preserved identities during concurrent requests. |
| 06 The ledger and trace checker independently reconcile topology and identity. | done | [artifacts/manifests/study-459aa21b5ffe.json](artifacts/manifests/study-459aa21b5ffe.json); study-459aa21b5ffe / 1193110a8e3f91a944d5137d704b367c9776051a | Independent raw Collector parsing and database exports rederive the accepted report. |
| 07 Retries, missing spans and collector outage preserve honest status. | done | [artifacts/accepted/study.json](artifacts/accepted/study.json); study-459aa21b5ffe / 1193110a8e3f91a944d5137d704b367c9776051a | Transient retries, deliberate child loss and stopped Collector cases retain explicit status. |
| 08 Public API contracts and scoped receipt transactions are implemented. | done | [tests/contract/test_public_api.py](tests/contract/test_public_api.py); 1193110a8e3f91a944d5137d704b367c9776051a | Real database integration covers scoped create, read, replay, conflict and public boundaries. |
| 09 Functional live lexical API passes browser, client and database readback. | done | [artifacts/accepted/public-deployment.json](artifacts/accepted/public-deployment.json); 48753d88cc472947a002c2a8af74eed5d44792ff | Hosted browser create and replay, ordinary-client isolation checks, and independent Neon receipt readback passed. The public profile remains lexical. |
| 10 Every primary scenario and overhead request is accounted for by planned ID. | done | [artifacts/accepted/study.json](artifacts/accepted/study.json); study-459aa21b5ffe / 1193110a8e3f91a944d5137d704b367c9776051a | All twenty-four primary and seventy-two overhead requests remain in the planned denominator. |
| 11 Traced/untraced agreement and overhead are measured without invented claims. | done | [artifacts/accepted/study.json](artifacts/accepted/study.json); study-459aa21b5ffe / 1193110a8e3f91a944d5137d704b367c9776051a | All twelve business-output pairs match; overhead is descriptive over thirty-six pairs. |
| 12 Crash recovery has fresh independent post-action evidence. | done | [artifacts/accepted/recovery.json](artifacts/accepted/recovery.json); recovery-f2a5dc74851c / 1193110a8e3f91a944d5137d704b367c9776051a | Exit code eighty-six was followed by a new gateway PID and one-receipt replay from a fresh process. |
| 13 Telemetry allowlists and synthetic secret-canary checks pass. | done | [artifacts/accepted/recovery.json](artifacts/accepted/recovery.json); recovery-f2a5dc74851c / 1193110a8e3f91a944d5137d704b367c9776051a | The synthetic marker is absent from exported evidence; source and service-log scans are recorded separately. |
| 14 Four views, both themes, palette and browser accessibility checks pass. | not done | [artifacts/accepted/hosted-browser-checks.json](artifacts/accepted/hosted-browser-checks.json); 48753d88cc472947a002c2a8af74eed5d44792ff | All twenty-four hosted responsive cases, full ID copy, keyboard focus and table alternatives passed. Actual 200 percent zoom and reduced-motion verification remain blocked by native browser availability. |
| 15 Reuse notices, ADRs, repository guidance and three local skills exist. | done | [docs/ADR-002-independent-evidence.md](docs/ADR-002-independent-evidence.md); 6ff25160ac66fd2ce5de7dcb609686701a2424c6 | Three ADRs, license notices, runbooks and three repository-local skills are present. |
| 16 CI, actual CPU evidence and retained failure records pass review. | done | [https://github.com/mekala27-45/tracepath/actions/runs/43552642939](https://github.com/mekala27-45/tracepath/actions/runs/43552642939); 48753d88cc472947a002c2a8af74eed5d44792ff | The merged revision passed actual Linux inference, full inventory, independent grading, recovery, scans and the frontend build. Earlier failure records remain retained. |
| 17 A clean worktree rederives metrics and executes fresh smoke inference. | done | [artifacts/accepted/clean-reproduction.json](artifacts/accepted/clean-reproduction.json); smoke-b77d96156882 / d6f6f323dd365b4d2e21ba2b684407a676f106d3 | A detached clean checkout rederived claims, matched direct inference and accepted two fresh HTTP retrievals. |
| 18 Meaningful commit floor, final checklist and authorized tag/release are verified. | not done | [PROJECT_STATE.md](PROJECT_STATE.md); 48753d88cc472947a002c2a8af74eed5d44792ff | Pull request 1 is merged with forty-nine implementation commits. The tag and release remain absent until the two native browser checks close. |

Stretch: not started. The earlier Windows recording is retained separately and is not pooled with the promoted Linux study.
