# ADR 001: Reuse a small retrieval contract

Status: accepted. Decision date: 2026-11-14.

Tracepath needs real retrieval work but its question concerns observability. Rebuilding a full RAG application would obscure that question. Inspect and adapt the Embedder protocol, BM25 ranking and reciprocal rank fusion from GroundedRAG commit b3273286b3a8f3f48cdb4f540d65c297ad096ccc. Preserve the MIT notice in NOTICE and the boundaries in REUSE.md.

The adapter searches every authored note, retains separate cosine, lexical and fusion scores, and orders equal scores by document ID. Cosine scores can be negative. Fusion uses rank origin one and constant sixty. No score is a calibrated probability.

FastEmbed loads only a local bundle whose files match model.lock.json. The bundle includes model weights and tokenizer files at a pinned Hugging Face revision. CPUExecutionProvider is explicit. A separate tokenizer and ONNX Runtime path verifies two fresh adapter calls. Missing or corrupt artifacts are refused, never replaced with a hash embedding.

The smaller interface is easier to inspect and test. It gives up general document ingestion, vector storage and model selection. Those are outside this experiment.

Sources inspected 2026-11-14: [GroundedRAG source](https://github.com/mekala27-45/grounded-rag/tree/b3273286b3a8f3f48cdb4f540d65c297ad096ccc), [FastEmbed](https://github.com/qdrant/fastembed), [pinned model bundle](https://huggingface.co/Qdrant/bge-small-en-v1.5-onnx-Q/tree/aa8f8b060edb00e03bfdd08813a2949946c8ba55).
