# ADR 003: Bound the public lexical service

Status: implementation accepted; public deployment verification pending. Decision date: 2026-11-14.

The workbench distinguishes a fresh deterministic lexical request from a recorded actual CPU experiment. Hosting the encoder would add a different runtime and cost envelope to the public demo. Keep actual model execution in the owned Linux or native process environment. Host only the narrow lexical API on Vercel and its dedicated scoped receipt store on Neon Free.

Sessions last one hour, permit twenty new operations, and have a global active-session ceiling. Identical operation-key replays return the original receipt; different payloads conflict. The public API has no ingestion, arbitrary URL, export-destination, administrative or fault-injection route. Session bearer tokens remain in browser memory and never enter the repository.

The public trace records completed internal operations. Commit completion and response delivery are not independently observed in that trace, so it remains incomplete. The separately read database receipt establishes business persistence.

The database runtime role has only CONNECT, schema USAGE and SELECT, INSERT, UPDATE. Schema migrations and expired-row cleanup use the owner separately. Read expiry is automatic; physical cleanup is an owner operation, not a currently scheduled job.

Vercel deployment protection remains enabled. Automatic review rejected removing SSO because explicit permission for that access change was missing. The failed environment-variable setup left no configured values. Deployment readiness and ordinary public-client verification remain open gates; no release is claimed.

Sources inspected 2026-11-14: [Vercel Python runtime](https://vercel.com/docs/functions/runtimes/python), [Neon documentation](https://neon.com/docs/introduction), [PostgreSQL transactions](https://www.postgresql.org/docs/18/tutorial-transactions.html).
