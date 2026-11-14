---
name: prepare-reviewed-release
description: Prepare a reviewable Tracepath release using the eighteen evidence gates and exact source identity.
---

Read AGENTS.md, RESULTS.md, PROJECT_STATE.md and NEXT_SESSION.md. Inputs are the candidate commit, fresh CI result, reviewed remote promotion record and hosted verification receipt.

Create a clean worktree from the candidate. Run `python -m scripts.verify_evidence`, fresh model inference, the main HTTP smoke and the frontend build. Check all eighteen gate entries, substantive commit history and source identity of every deployment. Verify ordinary browser and independent client persistence after the final code change.

Expect exact source and run identifiers, raw evidence, generated claims and explicit limits. Refuse a tag while any mandatory gate is not done, a check is stale, authorization is absent or a deployment is protected from ordinary users. Prepare the final review before requesting any missing access approval. Do not publish social drafts or activate schedules. This skill is repository-local.
