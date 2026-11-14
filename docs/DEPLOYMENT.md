# Public deployment

Workbench: https://mekala27-45.github.io/tracepath/
API: https://tracepath-api.vercel.app

The user approved storing the dedicated tracepath_app connection in Vercel production and preview and removing SSO protection only from tracepath-api. Both changes are complete. DATABASE_URL is sensitive. ALLOWED_ORIGIN is https://mekala27-45.github.io. TRACEPATH_PROFILE is public. No owner credential or experimental lab route is exposed.

Verified production source: 48753d88cc472947a002c2a8af74eed5d44792ff.
Vercel deployment: dpl_7SxuGejSrHgtwiAdDhsQFsW8bAHw.
Pages deployment: https://github.com/mekala27-45/tracepath/actions/runs/43552642896.
Integration: https://github.com/mekala27-45/tracepath/actions/runs/43552642939.

The ordinary-client verifier creates a fresh scoped session, submits a synthetic lexical request, reads the receipt independently and replays it from another client. It also verifies payload conflict, foreign-session refusal, invalid input, disabled experimental routes and origin restrictions. Each Pages build runs this verifier before enabling live search. Tokens and database credentials are never retained in that evidence.

A hosted browser independently created receipt 46e2fe4e-d86f-4906-90cf-81e1171b4cd6, read it back and replayed the identical ID. A separate Neon connection confirmed five results, the exact output digest and the deployed source. See artifacts/accepted/public-deployment.json. This is bounded lexical verification, not hosted embedding inference or a load test.

GitHub Pages uses Actions and the existing main-only environment rule. A branch attempt was correctly rejected; the tested PR was merged to deploy through main. Non-main workflow runs build and verify but skip publication. No environment protection was weakened.

The public product is usable. The formal release remains gated on actual browser 200 percent zoom and reduced-motion verification. Those checks were interrupted by native input contention and then browser runtime startup failure. The recorded responsive checks do not substitute for them.
