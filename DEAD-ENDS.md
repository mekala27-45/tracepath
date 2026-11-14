# Rejected approaches and observed failures

The Windows default Python alias could not execute. A bundled Python 3.12.14
runtime successfully created an isolated environment and ran the actual model.

Docker did not expose its Linux engine. The app startup approval timed out.
Native Windows process checks are recorded separately; they cannot pass Linux
Compose acceptance. The Linux workflow remains a separate required check.

The initial database probe used a startup statement_timeout option with a
pooled connection returned by the provider. The pooler rejected that parameter.
The driver now sets a transaction-local timeout after connecting, and migration
uses the direct endpoint. This failure is retained instead of hidden by a retry.

GitHub runner container initialization rejected single-quoted health command arguments. No test had run. Changed the job option to double quotes and retained run 43546446504 as failed evidence.
