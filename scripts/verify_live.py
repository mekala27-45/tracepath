"""Small public API verification using independent HTTP clients."""

import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, build_opener

BASE = "https://tracepath-api.vercel.app"
ORIGIN = "https://mekala27-45.github.io"


def call(method, path, payload=None, token=None, origin=ORIGIN):
    headers = {"Origin": origin, "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(BASE + path, data=body, headers=headers, method=method)
    try:
        response = build_opener().open(request, timeout=20)
    except HTTPError as exc:
        return exc.code, None, dict(exc.headers)
    with response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None, dict(response.headers)


def main():
    status, ready, _ = call("GET", "/ready")
    assert status == 200 and ready["mode"] == "deterministic_live"
    status, session, _ = call("POST", "/v1/sessions", {})
    assert status == 200
    token = session["token"]
    payload = {"query": "How is a model identified?", "operation_key": str(uuid.uuid4())}
    status, receipt, headers = call("POST", "/v1/search", payload, token)
    assert status == 200 and len(receipt["hits"]) == 5 and not receipt["replay"]
    assert receipt["source_revision"] == ready["source_revision"]
    assert receipt["mode"] == "deterministic_live"
    request_id = receipt["request_id"]
    status, readback, _ = call("GET", "/v1/requests/" + request_id, token=token)
    assert status == 200 and readback["output_digest"] == receipt["output_digest"]
    status, replay, _ = call("POST", "/v1/search", payload, token)
    assert status == 200 and replay["replay"] and replay["request_id"] == request_id
    assert replay["output_digest"] == receipt["output_digest"]
    conflict, _, _ = call("POST", "/v1/search", {**payload, "query": "different query"}, token)
    assert conflict == 409
    status, foreign, _ = call("POST", "/v1/sessions", {})
    assert status == 200
    denied, _, _ = call("GET", "/v1/requests/" + request_id, token=foreign["token"])
    assert denied == 404
    invalid, _, _ = call("POST", "/v1/search", {**payload, "query": ""}, token)
    assert invalid == 422
    lab, _, _ = call("POST", "/experiment/search", {})
    assert lab == 404
    wrong_origin, _, _ = call("GET", "/ready", origin="https://invalid.example")
    assert wrong_origin == 403
    status, trace, _ = call("GET", "/v1/requests/" + request_id + "/trace", token=token)
    assert status == 200 and trace["verdict"] == "incomplete"
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    assert normalized_headers["access-control-allow-origin"] == ORIGIN
    result = {
        "schema_version": 1, "accepted": True, "observed_at": datetime.now(UTC).isoformat(),
        "api_url": BASE, "api_source_revision": ready["source_revision"],
        "verification_source_revision": os.environ.get("GITHUB_SHA", "unavailable"),
        "request_id": request_id, "output_digest": receipt["output_digest"],
        "corpus_digest": receipt["corpus_digest"], "mode": receipt["mode"],
        "fresh_client_readback": True, "fresh_client_replay": True,
        "conflict_status": conflict, "foreign_session_status": denied,
        "invalid_query_status": invalid, "experimental_route_status": lab,
        "wrong_origin_status": wrong_origin, "trace_verdict": trace["verdict"],
        "credential_scope": "Ephemeral demo sessions only; no database credential used.",
    }
    target = Path("artifacts/accepted/public-client.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
