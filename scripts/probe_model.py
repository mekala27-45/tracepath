"""Compare the adapter with direct tokenizer and ONNX execution."""
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer
from packages.contracts.identity import digest, write_json
from packages.inference.kernel import PinnedEmbedder

ROOT = Path(__file__).resolve().parents[1]


def probe():
    model_path = ROOT / "models/bge-small"
    encoder = PinnedEmbedder(model_path, ROOT / "model.lock.json")
    queries = ["When is a Tern sensor reading stale?", "How does Anchor recover a committed receipt?"]
    start = time.perf_counter()
    observed = np.vstack([encoder.embed([query])[0] for query in queries])
    tokenizer = Tokenizer.from_file(str(model_path / "tokenizer.json"))
    tokenizer.enable_truncation(max_length=512)
    tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
    inputs = tokenizer.encode_batch(queries)
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    session = ort.InferenceSession(str(model_path / "model_optimized.onnx"),
                                  sess_options=options, providers=["CPUExecutionProvider"])
    arrays = {"input_ids": np.array([x.ids for x in inputs], dtype=np.int64),
              "attention_mask": np.array([x.attention_mask for x in inputs], dtype=np.int64),
              "token_type_ids": np.array([x.type_ids for x in inputs], dtype=np.int64)}
    raw = session.run(None, {i.name: arrays[i.name] for i in session.get_inputs()})[0]
    direct = raw[:, 0] if raw.ndim == 3 else raw
    direct = direct / np.linalg.norm(direct, axis=1, keepdims=True)
    difference = float(np.max(np.abs(observed-direct)))
    accepted = bool(np.allclose(observed, direct, atol=1e-5, rtol=1e-5))
    record = {"schema_version": 1, "mode": "actual_cpu_inference", "run_id": "model-smoke",
        "source_revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                    text=True).strip(),
        "timestamp": datetime.now(timezone.utc).isoformat(), "pid": os.getpid(),
        "runtime": platform.python_version(), "os": platform.platform(),
        "encoder_calls": encoder.calls, "input_digests": [digest(q) for q in queries],
        "output_digest": digest(observed.tolist()), "shape": list(observed.shape),
        "bundle_digest": encoder.bundle_digest, "provider": session.get_providers(),
        "direct_max_absolute_difference": difference, "direct_agreement": accepted,
        "duration_ms": (time.perf_counter()-start)*1000}
    write_json(ROOT / "artifacts/raw/model-smoke.json", record)
    if not accepted:
        raise RuntimeError("Direct inference did not match the adapter.")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    probe()
