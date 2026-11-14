# Method and limits

The frozen plan lives in evaluation/plan.json, preregistration.json and inventory.json. Twenty-four authored scenario lineages cover six families. Two per family are development cases and two are reserved. Each reserved case runs traced and untraced, producing twenty-four primary observations. Twelve normal query shapes, three repetitions and two lanes produce seventy-two overhead requests. Four symmetric warmups are outside these denominators.

Both lanes call the same pinned CPU encoder and search the complete corpus. No query-result cache is used. The independent agreement comparison checks document IDs and scores at absolute and relative tolerance 1e-5. The corpus and fault cases are synthetic; actual inference is real execution of those cases.

Each overhead pair uses the same query. The registered lane order alternates. Paired overhead is traced minus untraced client monotonic time. The summary reports the median and nearest-rank p95 over complete pairs. This is descriptive analysis, with no formal hypotheses, p values or multiplicity correction. These requests are not independent hardware replications.

The public lexical service is a distinct execution mode. Its results cannot be substituted for CPU experiment evidence. The workbench loads only an independently accepted, hash-verified study exported at build time.

The Windows recording includes a remote dedicated Postgres connection. The Linux recording uses disposable local Postgres on a GitHub runner. Their latency distributions are separate observations and are not pooled. The promoted study includes its complete OS, runtime, process IDs, source revision and Collector binary digest. Earlier recordings and rejected attempts remain available.

Resources in the first promoted Linux recording are RSS samples after requests, not a continuous peak. Later harness runs also capture the OS memory high water mark. CPU time is sampled before process termination. Collector restarts are separate process generations. These measurements cover only the declared processes and observation method.

Exporter outcomes are distinct from persisted spans. An unknown outcome is not a zero or success. The topology checker tests parentage and identity, not semantic retrieval correctness. A complete trace does not establish a production SLO or model quality.

Run `python -m scripts.verify_evidence` to hash-check raw files and independently regenerate the accepted report. Run `python -m scripts.render_claims` to regenerate the prose and workbench data from that report.
