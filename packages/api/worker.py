"""Experimental worker. Bind to loopback or a private Compose network only."""
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException
from packages.contracts.identity import digest, write_json
from packages.contracts.models import Envelope
from packages.inference.kernel import HybridKernel, PinnedEmbedder, ROOT
from packages.operations.telemetry import Telemetry, incoming

kernel = None
telemetry = None


@asynccontextmanager
async def lifespan(app):
    global kernel, telemetry
    kernel = HybridKernel(PinnedEmbedder(ROOT / "models/bge-small", ROOT / "model.lock.json"))
    telemetry = Telemetry("tracepath-worker", os.environ["SOURCE_REVISION"],
        os.environ.get("OTEL_ENDPOINT", "http://127.0.0.1:4318/v1/traces"),
        Path(os.environ.get("RAW_DIR", ".local/raw")) / "worker-export.jsonl")
    yield
    telemetry.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


@app.get("/ready")
def ready():
    if kernel is None:
        raise HTTPException(503, "Worker model unavailable.")
    return {"ready": True, "pid": os.getpid(), "model_bundle_digest": kernel.encoder.bundle_digest,
            "corpus_digest": kernel.corpus_digest}


@app.post("/retrieve")
def retrieve(envelope: Envelope, traceparent: str | None = Header(default=None),
             x_lab_fault: str = Header(default="none")):
    if envelope.model_bundle_digest != kernel.encoder.bundle_digest or envelope.corpus_digest != kernel.corpus_digest:
        raise HTTPException(409, "Worker artifact identity mismatch.")
    if digest(envelope.query) != envelope.payload_digest:
        raise HTTPException(409, "Worker payload identity mismatch.")
    if x_lab_fault not in {"none", "worker_delay", "transient_failure", "dropped_child"}:
        raise HTTPException(400, "Unknown local fault.")
    context, context_status = incoming(traceparent)
    attrs = {**envelope.model_dump(exclude={"query", "telemetry", "session_scope"}),
             "mode": "actual_cpu_inference"}
    if x_lab_fault == "dropped_child":
        telemetry.exporter.drop_requests.add(envelope.request_id)
    began = time.perf_counter()
    observed = {**attrs, "pid": os.getpid(), "started_at": datetime.now(timezone.utc).isoformat(),
                "context_status": context_status, "fault": x_lab_fault, "encoder_invocations": 0}
    path = Path(os.environ.get("RAW_DIR", ".local/raw")) / f"worker-{envelope.attempt_id}.json"
    with telemetry.span("worker.request", attrs, envelope.telemetry, context):
        if x_lab_fault == "transient_failure" and envelope.attempt == 1:
            observed.update(status="transient_failure", elapsed_ms=(time.perf_counter()-began)*1000)
            write_json(path, observed)
            raise HTTPException(503, "Controlled transient worker failure.")
        if x_lab_fault == "worker_delay":
            time.sleep(0.15)
        with telemetry.span("encoding", attrs, envelope.telemetry):
            vector = kernel.encoder.embed([envelope.query])[0]
        observed.update(encoder_invocations=1, input_digest=digest(envelope.query),
                        vector_digest=digest(vector.tolist()))
        with telemetry.span("dense.ranking", attrs, envelope.telemetry):
            dense = kernel.dense(vector)
        with telemetry.span("lexical.ranking", attrs, envelope.telemetry):
            lexical = kernel.lexical.search(envelope.query)
        with telemetry.span("fusion", attrs, envelope.telemetry):
            hits = kernel.results(dense, lexical)
        observed.update(status="completed", output_digest=digest(hits),
                        elapsed_ms=(time.perf_counter()-began)*1000)
        write_json(path, observed)
    telemetry.flush()
    return {"hits": hits, "observation": observed}
