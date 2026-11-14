# Tracepath project state

The Day 29 implementation is merged and the live workbench is published.
Live: https://mekala27-45.github.io/tracepath/
API: https://tracepath-api.vercel.app
Merged review: https://github.com/mekala27-45/tracepath/pull/1

The accepted CPU experiment remains study-459aa21b5ffe at source 1193110a8e3f91a944d5137d704b367c9776051a. All 24 primary and 72 overhead requests are retained. All 12 traced and untraced business-output pairs match. The generated RESULTS.md retains the exact workload, denominators and measured values.

Public deployment at 48753d88cc472947a002c2a8af74eed5d44792ff passed ordinary-client checks, hosted browser creation and replay, full request-ID copy and independent Neon readback. The deployed runtime uses the restricted tracepath_app role and public profile. The user explicitly authorized configuring its credential and public access. No owner credential is deployed. Experimental routes remain disabled.

Both main-branch workflows passed: integration run 43552642939 and Pages run 43552642896. The earlier branch deployment failed because the existing Pages environment only allowed main. The tested PR was merged to use that existing protection; the rule was not weakened. Future non-main builds now skip the deployment job.

The hosted UI passed all 24 combinations of widths 390, 768 and 1440, both themes and four views without horizontal overflow. Full ID copy, visible keyboard focus, loading state, empty-query blocking and the table alternatives passed. See artifacts/accepted/hosted-browser-checks.json.

Gates 14 and 18 remain not done. Native browser input was interrupted by concurrent input, then the browser runtime failed after the workspace permission paths changed. Actual 200 percent browser zoom and reduced-motion emulation are still unverified. No tag or release is claimed. The substantive commit floor is exceeded.

The canonical branch is main. A separate older local build/day-29-tracepath checkout is not the canonical implementation and must not overwrite this history. No social posts, messages, profile edits or schedules were created.
