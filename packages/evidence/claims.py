"""Evidence eligibility only. Acceptance is produced by independent checks."""
import json
from pathlib import Path
from packages.contracts.identity import file_digest


class EvidenceRefusal(ValueError):
    pass


def load_accepted(root: Path, manifest_path: Path) -> dict:
    if not manifest_path.is_file():
        raise EvidenceRefusal("Evidence unavailable: manifest is absent.")
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("acceptance") != "accepted":
        raise EvidenceRefusal("Evidence refused: independent acceptance is absent.")
    if not data.get("artifacts") or not data.get("run_id") or not data.get("source_revision"):
        raise EvidenceRefusal("Evidence unavailable: provenance is incomplete.")
    for artifact in data["artifacts"]:
        item = (root / artifact["path"]).resolve()
        if not item.is_relative_to(root.resolve()) or not item.is_file():
            raise EvidenceRefusal("Evidence unavailable: artifact is outside root or absent.")
        if file_digest(item) != artifact["sha256"]:
            raise EvidenceRefusal("Evidence refused: artifact digest changed.")
    return data


def metric_sentence(metric: dict) -> str:
    required = ("name", "unit", "denominator", "window_start", "window_end", "mode", "source")
    if any(key not in metric for key in required):
        raise EvidenceRefusal("Metric refused: provenance or units missing.")
    if metric["value"] is None or metric["denominator"] <= 0:
        return f"{metric['name']}: unavailable."
    value = metric["value"]
    if not isinstance(value, (int, float)) or not __import__("math").isfinite(value):
        raise EvidenceRefusal("Metric refused: value is not finite.")
    return (f"{metric['name']}: {value:.3f} {metric['unit']}; denominator "
            f"{metric['denominator']}. Source {metric['source']}; "
            f"window {metric['window_start']} to {metric['window_end']}; mode {metric['mode']}.")
