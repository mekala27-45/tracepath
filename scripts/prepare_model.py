"""Download only verified public model files at an exact upstream revision."""
import argparse
import json
import urllib.request
from pathlib import Path
from packages.contracts.identity import file_digest, write_json

REVISION = "aa8f8b060edb00e03bfdd08813a2949946c8ba55"
REPOSITORY = "Qdrant/bge-small-en-v1.5-onnx-Q"
FILES = ["model_optimized.onnx", "config.json", "ort_config.json", "special_tokens_map.json",
         "tokenizer.json", "tokenizer_config.json", "vocab.txt"]


def prepare(root):
    folder = root / "models/bge-small"
    folder.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = folder / name
        url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}"
        if not target.exists():
            urllib.request.urlretrieve(url, target)
    lock = {"schema_version": 1, "model": "BAAI/bge-small-en-v1.5", "repository": REPOSITORY,
            "revision": REVISION, "license": "MIT", "provider": "CPUExecutionProvider",
            "dimension": 384, "pooling": "CLS token", "normalization": "L2",
            "sequence_limit": 512, "query_prefix": "", "threads": 1,
            "files": [{"path": name, "sha256": file_digest(folder/name),
                       "bytes": (folder/name).stat().st_size} for name in sorted(FILES)]}
    lockpath = root / "model.lock.json"
    if lockpath.exists() and json.loads(lockpath.read_text()) != lock:
        raise RuntimeError("Refusing to replace an existing model lock with changed bytes.")
    write_json(lockpath, lock)
    return folder


if __name__ == "__main__":
    prepare(Path(__file__).resolve().parents[1])
