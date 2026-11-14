import json
from pathlib import Path

import pytest

from packages.inference.kernel import PinnedEmbedder

pytestmark = pytest.mark.model
ROOT = Path(__file__).resolve().parents[2]


def test_absent_model_is_unavailable(tmp_path):
    with pytest.raises(ValueError, match="absent"):
        PinnedEmbedder(tmp_path, ROOT / "model.lock.json")


def test_corrupt_model_is_refused(tmp_path):
    lock = json.loads((ROOT / "model.lock.json").read_text())
    for item in lock["files"]:
        (tmp_path / item["path"]).write_bytes(b"not-the-model")
    with pytest.raises(ValueError, match="identity changed"):
        PinnedEmbedder(tmp_path, ROOT / "model.lock.json")
