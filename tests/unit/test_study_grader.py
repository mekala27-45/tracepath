from evaluation.independent_grader.study import percentile, same_hits


def test_rank_identity_and_registered_tolerance():
    a = [
        {
            "document_id": "note-001",
            "dense_cosine": -0.2,
            "lexical_score": 2.0,
            "fusion_score": 0.03,
        }
    ]
    assert same_hits(a, [dict(a[0], dense_cosine=-0.200001)])
    assert not same_hits(a, [dict(a[0], document_id="note-002")])
    assert not same_hits(a, [])
    assert not same_hits([], [])


def test_percentiles_have_explicit_small_sample_behavior():
    assert percentile([], 0.95) is None
    assert percentile([3, 1, 2], 0.95) == 3
