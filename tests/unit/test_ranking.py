import numpy as np
import pytest
from packages.inference.kernel import BM25Index, fuse, HybridKernel


def test_rrf_independent_tiny_ranking():
    result = fuse([[('b', 7), ('a', 2)], [('a', 11), ('b', 3)]])
    assert result == [('a', 1/61 + 1/62), ('b', 1/61 + 1/62)]


def test_dense_keeps_negative_cosine():
    kernel = object.__new__(HybridKernel)
    kernel.ids = ['b', 'a', 'c']
    kernel.vectors = np.array([[-1, 0], [-1, 0], [1, 0]])
    assert kernel.dense(np.array([1, 0])) == [('c', 1.0), ('a', -1.0), ('b', -1.0)]


def test_lexical_stable_zero_ties():
    docs = [{"document_id": d, "title": "same", "text": "same token"} for d in ['c','a','b']]
    assert BM25Index(docs).search("absent") == [('a', 0), ('b', 0), ('c', 0)]
