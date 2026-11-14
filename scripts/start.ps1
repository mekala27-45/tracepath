$ErrorActionPreference = 'Stop'
$env:SOURCE_REVISION = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m scripts.prepare_model
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
New-Item -ItemType Directory -Force -Path .local/evidence | Out-Null
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$deadline = (Get-Date).AddSeconds(90)
do {
    try {
        $ready = Invoke-RestMethod -Uri http://127.0.0.1:8765/ready -TimeoutSec 2
        if ($ready.ready) {
            python -m scripts.smoke_http
            exit $LASTEXITCODE
        }
    } catch { Start-Sleep -Milliseconds 250 }
} while ((Get-Date) -lt $deadline)
Write-Error 'Observed readiness deadline exceeded.'
exit 1
