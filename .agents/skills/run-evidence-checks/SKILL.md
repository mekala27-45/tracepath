---
name: run-evidence-checks
description: Verify Tracepath evidence, model identities and derived claims before a code review or release.
---

Read AGENTS.md and the current branch head. Inputs are the accepted study, matching manifest, frozen inventory and raw run directory.

Run `python -m scripts.verify_evidence`, `python -m pytest -q`, `python -m scripts.scan_artifacts` and `python scripts/validators/palette_validator.py palette.json`. Supply disposable test database credentials through environment variables when running integration tests. Treat skipped integrations as unavailable. Run `python -m scripts.render_claims` only after acceptance passes.

Expect unchanged raw hashes, a reproducible report, explicit source identity and no scan findings. Refuse stale, missing, rejected or altered evidence. Preserve failed output. Do not mutate the registered workload or publish anything. This skill is repository-local and must not be installed globally.
