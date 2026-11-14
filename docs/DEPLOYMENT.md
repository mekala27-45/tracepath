# Deployment handoff

The isolated public repository and review branch exist. The Python preview built successfully on Vercel at source 1193110a8e3f91a944d5137d704b367c9776051a. This proves buildability only. The project has no configured environment variables and still has SSO protection, so ordinary public persistence is not verified.

Prepared API preview: https://tracepath-d3u20t03q-mekala27-45s-projects.vercel.app

Configure DATABASE_URL with the dedicated tracepath_app connection as a sensitive runtime variable, ALLOWED_ORIGIN with the final GitHub Pages origin, and SOURCE_REVISION with the deployed SHA or use VERCEL_GIT_COMMIT_SHA. Do not enable TRACEPATH_PROFILE=lab. No owner credential belongs in Vercel. The user must explicitly approve publishing the new API before SSO removal is retried.

After authorized publication, test a fresh session and query from an ordinary client. Replay from a second client, compare the request ID and output digest, then read the receipt through an independent database connection. Record the exact deployment and source SHA. Also test foreign-session refusal and payload conflict with small synthetic requests. Do not run fault or load scenarios publicly.

The Pages workflow is prepared for main. Enable GitHub Pages with GitHub Actions as its source, then publish from the reviewed commit. Until the API passes ordinary public verification, the default production frontend disables live search and accurately says it is unavailable. Set repository variables TRACEPATH_API_URL and TRACEPATH_LIVE_ENABLED=true only after verification. A working recorded workbench does not substitute for the required live API gate.

The prepared preview is not a release. Keep the PR as draft, leave the tag absent, and retain the open checklist items until they pass.
