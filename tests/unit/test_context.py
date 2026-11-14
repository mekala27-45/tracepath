from opentelemetry import trace

from packages.operations.telemetry import ALLOWED, incoming


def test_valid_context_and_reject_malformed():
    ctx, status = incoming("00-" + "1" * 32 + "-" + "2" * 16 + "-01")
    assert status == "valid"
    assert trace.get_current_span(ctx).get_span_context().trace_id == int("1" * 32, 16)
    for value in ("broken", "00-" + "0" * 32 + "-" + "2" * 16 + "-01", "x" * 4096):
        ctx, status = incoming(value)
        assert status == "malformed"
        assert not trace.get_current_span(ctx).get_span_context().is_valid
    assert incoming(None)[1] == "absent"


def test_no_sensitive_attribute_names():
    assert not {"query", "document", "token", "database_url", "baggage"} & ALLOWED
