"""Two fresh real HTTP encoder requests and independent receipt readbacks."""

import os
import uuid

import httpx

base = os.environ.get("GATEWAY_URL", "http://127.0.0.1:8765")
with httpx.Client(base_url=base, timeout=20, trust_env=False) as client:
    response = client.post("/v1/sessions", json={})
    response.raise_for_status()
    headers = {"Authorization": "Bearer " + response.json()["token"]}
    identities = []
    for query in [
        "When is a Tern sensor reading stale?",
        "How does Anchor recover a committed receipt?",
    ]:
        response = client.post(
            "/experiment/search",
            headers=headers,
            json={
                "query": query,
                "operation_key": str(uuid.uuid4()),
                "run_id": "smoke-" + uuid.uuid4().hex,
                "telemetry": True,
                "fault": "none",
            },
        )
        response.raise_for_status()
        receipt = response.json()
        assert receipt["mode"] == "actual_cpu_inference"
        assert receipt["attempts"][-1]["status"] == "completed"
        readback = client.get("/v1/requests/" + receipt["request_id"], headers=headers)
        readback.raise_for_status()
        assert readback.json()["output_digest"] == receipt["output_digest"]
        identities.append(receipt["request_id"])
    assert len(set(identities)) == 2
    print(
        {
            "actual_http_requests": len(identities),
            "request_ids": identities,
            "independent_readback": True,
        }
    )
