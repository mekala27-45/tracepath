# Reuse audit

GroundedRAG source was inspected at b3273286b3a8f3f48cdb4f540d65c297ad096ccc.
Repository: https://github.com/mekala27-45/grounded-rag
Inspection date: 2026-11-14 UTC.

| Source | Adaptation | Check |
| --- | --- | --- |
| src/grounded_rag/index/embeddings.py | Embedder protocol and FastEmbed wrapper; exact offline bytes, provider and vector validation added | scripts/probe_model.py |
| src/grounded_rag/index/bm25.py | Same lowercase alphanumeric tokenizer; stable ID ties and all-document ranking | tests/unit/test_ranking.py |
| src/grounded_rag/retrieval/retriever.py | One-based reciprocal rank fusion; NumPy exact search replaces Qdrant for this bounded corpus | tests/unit/test_ranking.py |

The upstream score-only tie order is not retained. Raw cosine can be negative.
Lexical, dense and fusion scores remain separate. No earlier retrieval metrics
are reused. The MIT notice is retained in NOTICE. Corpus text is original CC0.
