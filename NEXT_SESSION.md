# Continue from the actual branch

Read AGENTS.md, PROJECT_STATE.md, RESULTS.md and docs/DEPLOYMENT.md. Fetch current heads and PR checks before editing. Preserve concurrent changes. The implementation branch is build/tracepath and the review is pull request 1.

The next external action needs explicit approval: configure the dedicated tracepath_app database credential in Vercel and remove SSO protection only for the new tracepath-api demo. Automatic review rejected that access reduction. Do not retry through another transport without authorization. If the ephemeral credential is unavailable, rotate only the dedicated application role through the owner connection and put the new value directly in the authorized secret store. Never print it.

After approval, set DATABASE_URL as sensitive and ALLOWED_ORIGIN for the final Pages origin. Use the deployed Git SHA for source identity. Redeploy the final reviewed commit and record ordinary browser, second-client replay and independent database readback. Keep the lab profile disabled.

Resume browser verification when Computer Use can establish the active URL. Test actual 200 percent zoom, reduced motion, loading/error/recovery, full ID copy and the latest frontend across required widths and themes. Earlier responsive checks do not close these missing checks.

Enable GitHub Pages with Actions as its source. Set TRACEPATH_API_URL and TRACEPATH_LIVE_ENABLED=true only after public API verification. Verify the published revision after the final change.

Run python -m scripts.verify_evidence, python -m scripts.render_claims, python -m scripts.scan_artifacts, pytest with disposable database credentials, and the frontend build. The Linux workflow runs actual inference and all scenarios. A skipped integration is not a pass.

Update evaluation/checklist.json with exact source and run identities, then regenerate RESULTS.md and README.md. Only after all eighteen gates are done should the PR be marked ready, merged, tagged and released. Prepare a short recorded demo after the final live check. Leave unrelated projects and schedules unchanged.
