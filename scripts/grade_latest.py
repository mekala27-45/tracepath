"""Grade the newest completed run; reject stale runs from another source head."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    candidates = []
    for directory in (ROOT / 'artifacts/raw').glob('study-*'):
        if not (directory / 'window.json').exists():
            continue
        environment = json.loads((directory / 'environment.json').read_text())
        if environment['source_revision'] == revision:
            window = json.loads((directory / 'window.json').read_text())
            candidates.append((window['finished_at'], directory.name))
    if not candidates:
        raise SystemExit('No completed study from the current source revision.')
    subprocess.run([sys.executable, '-m', 'evaluation.independent_grader.study', max(candidates)[1]], check=True)
