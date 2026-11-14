"""Manually bounded, allowlisted telemetry. Never records exception text."""

import json
import os
import re
import threading
from contextlib import contextmanager

from opentelemetry.context import Context
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

ALLOWED = {
    "run_id",
    "request_id",
    "attempt",
    "attempt_id",
    "corpus_digest",
    "model_bundle_digest",
    "payload_digest",
    "source_revision",
    "mode",
    "outcome",
}
TRACEPARENT = re.compile(r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


def incoming(value):
    if not value or len(value) > 55:
        return Context(), "absent" if not value else "malformed"
    match = TRACEPARENT.fullmatch(value)
    if not match or int(match[1], 16) == 0 or int(match[2], 16) == 0:
        return Context(), "malformed"
    return TraceContextTextMapPropagator().extract({"traceparent": value}), "valid"


class MeasuredExporter(SpanExporter):
    def __init__(self, endpoint, evidence_path):
        self.delegate = OTLPSpanExporter(endpoint=endpoint, timeout=0.5)
        self.path = evidence_path
        self.drop_requests = set()
        self.lock = threading.Lock()

    def export(self, spans):
        selected = [
            s
            for s in spans
            if not (s.name == "encoding" and s.attributes.get("request_id") in self.drop_requests)
        ]
        result = self.delegate.export(selected) if selected else SpanExportResult.SUCCESS
        record = {
            "received": len(spans),
            "dropped_at_boundary": len(spans) - len(selected),
            "exported": len(selected) if result == SpanExportResult.SUCCESS else 0,
            "unknown": len(selected) if result != SpanExportResult.SUCCESS else 0,
            "request_ids": sorted({s.attributes.get("request_id", "") for s in spans}),
            "pid": os.getpid(),
        }
        if self.path:
            with self.lock:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, sort_keys=True) + "\n")
        return result

    def shutdown(self):
        self.delegate.shutdown()


class Telemetry:
    def __init__(self, service, revision, endpoint, evidence_path=None):
        self.provider = TracerProvider(
            resource=Resource.create(
                {"service.name": service, "process.pid": os.getpid(), "service.version": revision}
            )
        )
        self.exporter = MeasuredExporter(endpoint, evidence_path)
        self.provider.add_span_processor(
            BatchSpanProcessor(
                self.exporter,
                max_queue_size=256,
                max_export_batch_size=64,
                schedule_delay_millis=50,
                export_timeout_millis=1000,
            )
        )
        self.tracer = self.provider.get_tracer("tracepath", "1")

    @contextmanager
    def span(self, name, attributes, enabled=True, context=None):
        if not enabled:
            yield None
            return
        safe = {key: value for key, value in attributes.items() if key in ALLOWED}
        with self.tracer.start_as_current_span(
            name,
            context=context,
            attributes=safe,
            record_exception=False,
            set_status_on_exception=False,
        ) as span:
            yield span

    def headers(self):
        carrier = {}
        TraceContextTextMapPropagator().inject(carrier)
        return carrier

    def flush(self):
        return self.provider.force_flush(timeout_millis=5000)

    def close(self):
        self.flush()
        self.provider.shutdown()
