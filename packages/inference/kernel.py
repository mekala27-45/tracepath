"""Small audited GroundedRAG contract adaptation. See REUSE.md and NOTICE."""
import json
import re
from pathlib import Path
from typing import Protocol
import numpy as np
from rank_bm25 import BM25Okapi
from packages.contracts.identity import digest, file_digest

TOKEN = re.compile(r"[a-z0-9]+")
ROOT = Path(__file__).resolve().parents[2]


class Embedder(Protocol):
    dim: int
    bundle_digest: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


def corpus():
    return json.loads((ROOT / "fixtures/corpus/operations-v1.json").read_text(encoding="utf-8"))


def document_text(document):
    return document["title"] + ". " + document["text"]


class BM25Index:
    def __init__(self, documents):
        self.ids = [d["document_id"] for d in documents]
        self.model = BM25Okapi([TOKEN.findall(document_text(d).lower()) for d in documents])

    def search(self, query):
        values = self.model.get_scores(TOKEN.findall(query.lower()))
        return sorted(zip(self.ids, map(float, values), strict=True), key=lambda v: (-v[1], v[0]))


def fuse(rankings, k=60):
    scores = {}
    for ranking in rankings:
        for rank, (doc_id, _) in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda v: (-v[1], v[0]))


class PinnedEmbedder:
    dim = 384

    def __init__(self, model_path: Path, lock_path: Path):
        from fastembed import TextEmbedding
        self.lock = json.loads(lock_path.read_text(encoding="utf-8"))
        self.bundle_digest = digest(self.lock)
        self.model_path = model_path.resolve()
        if not self.lock.get("files") or self.lock.get("provider") != "CPUExecutionProvider":
            raise ValueError("Model unavailable: complete CPU bundle manifest required.")
        for entry in self.lock["files"]:
            target = (self.model_path / entry["path"]).resolve()
            if not target.is_relative_to(self.model_path) or not target.is_file():
                raise ValueError("Model unavailable: required artifact is absent.")
            if file_digest(target) != entry["sha256"]:
                raise ValueError("Model unavailable: artifact identity changed.")
        self.model = TextEmbedding(self.lock["model"], specific_model_path=str(self.model_path),
            local_files_only=True, providers=["CPUExecutionProvider"], threads=1)
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        vectors = np.asarray(list(self.model.embed(texts, batch_size=32)), dtype=np.float32)
        if vectors.shape != (len(texts), self.dim) or not np.isfinite(vectors).all():
            raise ValueError("Model output refused: invalid shape or nonfinite values.")
        if not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5):
            raise ValueError("Model output refused: vectors are not unit normalized.")
        return vectors


def lexical_search(query):
    return [{"document_id": doc_id, "lexical_score": score, "dense_cosine": None,
             "fusion_score": None} for doc_id, score in BM25Index(corpus()).search(query)[:5]]


class HybridKernel:
    def __init__(self, encoder: Embedder):
        self.encoder = encoder
        self.documents = corpus()
        self.corpus_digest = digest(self.documents)
        self.ids = [d["document_id"] for d in self.documents]
        self.lexical = BM25Index(self.documents)
        self.vectors = encoder.embed([document_text(d) for d in self.documents])

    def dense(self, vector):
        return sorted(zip(self.ids, map(float, self.vectors @ vector), strict=True),
                      key=lambda v: (-v[1], v[0]))

    @staticmethod
    def results(dense, lexical):
        d, l = dict(dense), dict(lexical)
        return [{"document_id": key, "dense_cosine": d[key], "lexical_score": l[key],
                 "fusion_score": score} for key, score in fuse([dense, lexical])[:5]]
