# Run and recover Tracepath

Use Python 3.12.14, Node 24.19.0, Git and Docker with a Linux engine. Use the repository root for Python commands. Install `requirements.lock` into a fresh virtual environment and run `npm ci --prefix web`. Model preparation downloads the pinned public bundle and verifies each file.

## Compose

Run `powershell -File scripts/start.ps1`. It sets the current source identity, prepares the model, starts disposable Postgres, Collector, worker and gateway, waits for readiness, then runs two fresh HTTP encoder requests with independent readbacks. It preserves the exit status. The local database password in Compose is a disposable fixture; do not reuse it outside this loopback profile.

The Windows environment used during implementation did not provide a working Linux Docker engine. The native process harness ran locally, and GitHub Actions verified the complete Linux process profile with disposable Postgres. Do not describe an unexecuted local Compose check as passed.

## Native process experiment

Set DATABASE_URL to a dedicated initialized database, and COLLECTOR_BINARY to the pinned platform Collector executable. Keep values in the shell environment or authorized secret store. Run `python -m scripts.prepare_model`, then `python -m scripts.run_study --development`. After reviewing development observations, run `python -m scripts.run_study` and `python -m scripts.grade_latest`. Each run gets a new directory. Never delete a failed run to improve a denominator.

The harness owns loopback ports 8765, 8766, 4318 and 13133. It refuses readiness failures. Stop an already running local preview before launching the harness. Run `python -m scripts.check_recovery` for a deliberate gateway exit after commit, fresh-process replay and concurrent request isolation.

## Public lexical development

Set DATABASE_URL, SOURCE_REVISION to the forty-character Git SHA, and ALLOWED_ORIGIN to `http://127.0.0.1:5173`. Start `uvicorn packages.api.gateway:app --host 127.0.0.1 --port 8765 --no-access-log`. Set VITE_API_URL to `http://127.0.0.1:8765` and run `npm run dev --prefix web -- --host 127.0.0.1`.

Create a session, submit a synthetic query, read the returned request ID independently, then replay the same key and payload. Another session must receive 404 for that receipt. The private experimental route exists only when TRACEPATH_PROFILE is lab. Do not enable that profile on a public deployment.

## Retention and refusal

Use OWNER_DATABASE_URL only for `python -m scripts.migrate` with DATABASE_URL set to the dedicated owner connection, or `python -m scripts.retention`. Retention defaults to a count-only inspection. `--apply` removes expired receipts, old attempt observations and unreferenced expired sessions. No schedule has been activated. Public reads refuse expired scope automatically. The runtime role has no DELETE or DDL privilege.

If the Collector is unavailable, keep the receipt result and report trace status unavailable or incomplete. If the model bundle changes, stop inference. If an operation key conflicts, use a new operation only after deciding a new query is intended. Never retry a different payload under the same key.

## Release

Read RESULTS.md and NEXT_SESSION.md. Require successful checks for the exact candidate, an ordinary public-client readback, browser checks and all eighteen gates before tagging. A blocked access change or missing observation remains not done. Do not alter SSO protection or use another transport to bypass approval review.
