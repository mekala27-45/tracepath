"""Download and verify the immutable official Linux Collector release."""
import hashlib
import io
import os
import tarfile
import urllib.request
from pathlib import Path

URL = 'https://github.com/open-telemetry/opentelemetry-collector-releases/releases/download/v0.165.0/otelcol-contrib_0.165.0_linux_amd64.tar.gz'
EXPECTED = 'bd6e73d94bf3359ad6fac25529a8ee308adb9b0b8a0e8af034ed3891fbe5aa33'
if __name__ == '__main__':
    destination = Path(os.environ['COLLECTOR_BINARY'])
    data = urllib.request.urlopen(URL, timeout=90).read()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise SystemExit('Collector release digest mismatch.')
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        member = next(m for m in archive.getmembers() if m.isfile() and Path(m.name).name == 'otelcol-contrib')
        binary = archive.extractfile(member).read()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(binary)
    destination.chmod(0o755)
    print('Verified Collector 0.165.0 ready.')
