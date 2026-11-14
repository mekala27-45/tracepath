"""Gateway for the bounded live lexical and private experimental flows."""

import json
import os
import re
import time
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import Field

from packages.contracts.identity import digest
from packages.contracts.models import Envelope, SearchRequest
from packages.inference.kernel import ROOT, corpus, lexical_search
from packages.operations.ledger import Ledger, LedgerError
from packages.operations.telemetry import Telemetry, incoming

ledger = None
telemetry = None
LAB = os.environ.get("TRACEPATH_PROFILE") == "lab"
REVISION = os.environ.get("SOURCE_REVISION", "unavailable")
CORPUS_DIGEST = digest(corpus())
LEXICAL_IDENTITY = digest(
    {
        "model": "BM25Okapi",
        "rank_bm25": "0.2.2",
        "tokenizer": "[a-z0-9]+",
        "k1": 1.5,
        "b": 0.75,
        "epsilon": 0.25,
    }
)


@asynccontextmanager
async def lifespan(app):
    global ledger, telemetry
    ledger = Ledger(os.environ["DATABASE_URL"])
    ledger.ready()
    if LAB:
        telemetry = Telemetry(
            "tracepath-gateway",
            REVISION,
            os.environ.get("OTEL_ENDPOINT", "http://127.0.0.1:4318/v1/traces"),
            Path(os.environ.get("RAW_DIR", ".local/raw")) / "gateway-export.jsonl",
        )
    yield
    if telemetry:
        telemetry.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://127.0.0.1:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=False,
)


@app.middleware("http")
async def boundaries(request: Request, call_next):
    if request.headers.get("origin") not in (None, ALLOWED_ORIGIN):
        return JSONResponse({"detail": "Origin not permitted."}, status_code=403)
    if request.method == "POST":
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"detail": "Use application/json."}, status_code=415)
        length = request.headers.get("content-length")
        if length and (not length.isdigit() or int(length) > 8192):
            return JSONResponse({"detail": "Request body exceeds 8192 bytes."}, status_code=413)
        body = await request.body()
        if len(body) > 8192:
            return JSONResponse({"detail": "Request body exceeds 8192 bytes."}, status_code=413)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    # Do not echo query text, tokens, or pydantic input values.
    return JSONResponse(
        {
            "detail": "Invalid request. Use a nonempty query of at most 1024 UTF-8 bytes and a valid operation key."
        },
        status_code=422,
    )


@app.exception_handler(LedgerError)
async def ledger_error(request, exc):
    return JSONResponse({"detail": exc.detail}, status_code=exc.status)


def token(authorization):
    if not authorization or not re.fullmatch(r"Bearer [A-Za-z0-9_-]{43}", authorization):
        raise HTTPException(401, "Start a demo session before searching.")
    return authorization[7:]


def require_revision():
    if not re.fullmatch(r"[0-9a-f]{40}", REVISION):
        raise HTTPException(503, "Source identity unavailable.")


@app.get("/health")
def health():
    return {"alive": True}


@app.get("/ready")
def ready():
    require_revision()
    ledger.ready()
    return {
        "ready": True,
        "mode": "actual_cpu_inference" if LAB else "deterministic_live",
        "source_revision": REVISION,
        "corpus_digest": CORPUS_DIGEST,
        "pid": os.getpid(),
    }


@app.post("/v1/sessions")
def session():
    require_revision()
    return {"token": ledger.new_session(), "expires_in_seconds": 3600, "search_budget": 20}


@app.post("/v1/search")
def search(body: SearchRequest, authorization: str | None = Header(default=None)):
    require_revision()
    session_token = token(authorization)
    payload = digest(body.query)

    def produce(session_scope, connection):
        spans = []

        def timed(name, action):
            start = time.time_ns()
            monotonic_start = time.perf_counter_ns()
            result = action()
            spans.append(
                {
                    "name": name,
                    "start_ns": start,
                    "end_ns": start + time.perf_counter_ns() - monotonic_start,
                    "service": "tracepath-public",
                    "mode": "deterministic_live",
                }
            )
            return result

        timed("admission", lambda: SearchRequest.model_validate(body.model_dump()))
        hits = timed("lexical.ranking", lambda: lexical_search(body.query))
        return {
            "schema_version": 1,
            "run_id": "public",
            "request_id": str(uuid.uuid4()),
            "mode": "deterministic_live",
            "corpus_digest": CORPUS_DIGEST,
            "model_bundle_digest": LEXICAL_IDENTITY,
            "payload_digest": payload,
            "output_digest": digest(hits),
            "source_revision": REVISION,
            "hits": hits,
            "timestamp": datetime.now(UTC).isoformat(),
            "trace": {
                "verdict": "incomplete",
                "spans": spans,
                "missing": ["receipt commit completion", "response send observation"],
                "explanation": "Completed internal operations are persisted before the response. Sending the response is not independently observed.",
            },
        }

    return ledger.execute(session_token, body.operation_key, payload, produce)


@app.get("/v1/requests/{request_id}")
def receipt(request_id: uuid.UUID, authorization: str | None = Header(default=None)):
    return ledger.read(token(authorization), request_id)


@app.get("/v1/requests/{request_id}/trace")
def trace_receipt(request_id: uuid.UUID, authorization: str | None = Header(default=None)):
    result = ledger.read(token(authorization), request_id)
    return {
        "request_id": str(request_id),
        "mode": result["mode"],
        "source_revision": result["source_revision"],
        **result["trace"],
    }


@app.get("/v1/experiments/{experiment_id}")
def experiment(experiment_id: str):
    if experiment_id != "registered-study":
        raise HTTPException(404, "Recorded experiment unavailable.")
    path = ROOT / "artifacts/accepted/study.json"
    if not path.is_file():
        raise HTTPException(
            503, "Recorded experiment unavailable. Actual study has not been accepted."
        )
    return json.loads(path.read_text())


class StudyRequest(SearchRequest):
    run_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    telemetry: bool
    fault: Literal[
        "none",
        "normal",
        "worker_delay",
        "transient_failure",
        "malformed_context",
        "dropped_child",
        "collector_outage",
        "crash_after_commit",
    ] = "none"


if LAB:

    @app.post("/experiment/search")
    def study(
        body: StudyRequest,
        authorization: str | None = Header(default=None),
        traceparent: str | None = Header(default=None),
    ):
        require_revision()
        session_token = token(authorization)
        model = json.loads((ROOT / "model.lock.json").read_text())
        request_id = str(uuid.uuid4())
        attrs = {
            "run_id": body.run_id,
            "request_id": request_id,
            "corpus_digest": CORPUS_DIGEST,
            "model_bundle_digest": digest(model),
            "payload_digest": digest(body.query),
            "source_revision": REVISION,
            "mode": "actual_cpu_inference",
        }
        context, context_status = incoming(traceparent)
        with telemetry.span("request", attrs, body.telemetry, context):
            with telemetry.span("admission", attrs, body.telemetry):
                pass

            def produce(session_scope, connection):
                result = None
                attempts = []
                for attempt in (1, 2):
                    attempt_id = str(uuid.uuid4())
                    attempt_attrs = {**attrs, "attempt": attempt, "attempt_id": attempt_id}
                    envelope = Envelope(
                        **{k: v for k, v in attempt_attrs.items() if k != "mode"},
                        session_scope=session_scope,
                        query=body.query,
                        telemetry=body.telemetry,
                    )
                    observation = {
                        **attempt_attrs,
                        "status": "started",
                        "worker_timeout_seconds": 5,
                    }
                    ledger.attempt(observation)
                    worker_fault = (
                        body.fault
                        if body.fault in {"worker_delay", "transient_failure", "dropped_child"}
                        else "none"
                    )
                    with telemetry.span("worker.http", attempt_attrs, body.telemetry):
                        headers = telemetry.headers() if body.telemetry else {}
                        headers["X-Lab-Fault"] = worker_fault
                        try:
                            response = httpx.post(
                                os.environ["WORKER_URL"] + "/retrieve",
                                json=envelope.model_dump(),
                                headers=headers,
                                timeout=5,
                                trust_env=False,
                            )
                        except httpx.TimeoutException:
                            observation.update(
                                status="timed_out", cancellation="worker outcome unknown"
                            )
                            ledger.attempt(observation)
                            raise HTTPException(
                                504, "Worker deadline exceeded; completion remains unknown."
                            )
                        if response.status_code == 503 and attempt == 1:
                            observation.update(status="transient_failure")
                            ledger.attempt(observation)
                            attempts.append(observation)
                            continue
                        if response.status_code != 200:
                            observation.update(status="failed", status_code=response.status_code)
                            ledger.attempt(observation)
                            raise HTTPException(502, "Worker failed without an accepted result.")
                        result = response.json()
                        observation.update(
                            status="completed",
                            worker_pid=result["observation"]["pid"],
                            input_digest=result["observation"]["input_digest"],
                            vector_digest=result["observation"]["vector_digest"],
                            output_digest=result["observation"]["output_digest"],
                        )
                        ledger.attempt(observation)
                        attempts.append(observation)
                        break
                return {
                    "schema_version": 1,
                    **attrs,
                    "hits": result["hits"],
                    "attempts": attempts,
                    "output_digest": digest(result["hits"]),
                    "timestamp": datetime.now(UTC).isoformat(),
                    "context_status": context_status,
                    "trace": {
                        "verdict": "unavailable",
                        "explanation": "Collector observations are reconciled independently after completion.",
                    },
                }

            result = ledger.execute(
                session_token,
                body.operation_key,
                digest(body.query),
                produce,
                commit_span=lambda: telemetry.span("receipt.commit", attrs, body.telemetry),
            )
            if body.fault == "crash_after_commit":
                os._exit(86)
            with telemetry.span("response", attrs, body.telemetry):
                pass
        telemetry.flush()
        return result
