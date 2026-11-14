import pytest
from pydantic import ValidationError
from packages.contracts.models import SearchRequest


def test_query_bound_and_normalization():
    assert SearchRequest(query="  sensor   age ", operation_key="abcdefgh").query == "sensor age"
    for query in ("", " ", "a" * 1025, "\u20ac" * 342):
        with pytest.raises(ValidationError):
            SearchRequest(query=query, operation_key="abcdefgh")


def test_unknown_fields_and_coercion_refused():
    with pytest.raises(ValidationError):
        SearchRequest(query=42, operation_key="abcdefgh")
    with pytest.raises(ValidationError):
        SearchRequest(query="sensor", operation_key="abcdefgh", url="https://example.com")
