"""Strict boundaries shared by the public and experimental lanes."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Mode = Literal[
    "actual_cpu_inference",
    "deterministic_live",
    "recorded_experiment",
    "synthetic_fault",
    "unavailable",
    "planned",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class SearchRequest(Strict):
    query: str = Field(min_length=1, max_length=1024)
    corpus_version: Literal["operations-v1"] = "operations-v1"
    operation_key: str = Field(min_length=8, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")

    @field_validator("query")
    @classmethod
    def query_bound(cls, text: str) -> str:
        if len(text.encode("utf-8")) > 1024:
            raise ValueError("Query must contain at most 1024 UTF-8 bytes.")
        text = " ".join(text.split())
        if not text:
            raise ValueError("Enter a query with at least one visible character.")
        return text


class Envelope(Strict):
    run_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    request_id: str
    session_scope: Hash
    attempt: int = Field(ge=1, le=2)
    attempt_id: str
    corpus_digest: Hash
    model_bundle_digest: Hash
    payload_digest: Hash
    source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    query: str
    telemetry: bool

    @field_validator("request_id", "attempt_id")
    @classmethod
    def opaque_id(cls, value: str) -> str:
        UUID(value)
        return value

    @field_validator("query")
    @classmethod
    def query_bound(cls, value: str) -> str:
        return SearchRequest.query_bound(value)


class Hit(Strict):
    document_id: str = Field(pattern=r"^note-\d{3}$")
    lexical_score: float
    dense_cosine: float | None = None
    fusion_score: float | None = None


class Gate(Strict):
    schema_version: Literal[1] = 1
    name: str
    run_id: str
    source_revision: str = Field(pattern=r"^[0-9a-f]{40}$")
    verdict: Literal["pass", "fail", "unavailable"]
    evidence: list[str]
    observation: str


class Metric(Strict):
    name: str
    value: float | None
    unit: str
    denominator: int = Field(ge=0)
    window_start: str
    window_end: str
    mode: Mode
    source: str
