import importlib
import os
import uuid
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture
def client(monkeypatch):
    if not os.environ.get("TEST_DATABASE_URL"):
        pytest.skip("Disposable database required; public API integration not passed.")
    monkeypatch.setenv("DATABASE_URL", os.environ["TEST_DATABASE_URL"])
    monkeypatch.setenv("SOURCE_REVISION", "a"*40)
    monkeypatch.setenv("TRACEPATH_PROFILE", "public")
    import packages.api.gateway as gateway
    gateway = importlib.reload(gateway)
    with TestClient(gateway.app) as client:
        yield client


def test_live_flow_and_scoped_conflicts(client):
    session = client.post('/v1/sessions',json={}).json()['token']
    headers = {'Authorization':'Bearer '+session}
    payload={'query':'sensor freshness','operation_key':'contract-'+uuid.uuid4().hex}
    response=client.post('/v1/search',json=payload,headers=headers)
    assert response.status_code==200
    value=response.json()
    assert value['mode']=='deterministic_live' and len(value['hits'])==5
    assert client.get('/v1/requests/'+value['request_id'],headers=headers).json()['output_digest']==value['output_digest']
    assert client.post('/v1/search',json=payload,headers=headers).json()['replay']
    assert client.post('/v1/search',json={**payload,'query':'changed'},headers=headers).status_code==409
    assert client.get('/v1/requests/'+value['request_id']).status_code==401
    assert client.get('/v1/requests/'+value['request_id']+'/trace',headers=headers).json()['verdict']=='incomplete'


def test_host_boundaries_and_no_experimental_routes(client):
    assert client.post('/experiment/search',json={}).status_code==404
    assert client.post('/v1/search',content='a'*9000,headers={'Content-Type':'application/json'}).status_code==413
    assert client.post('/v1/search',content='{}',headers={'Content-Type':'text/plain'}).status_code==415
    assert client.post('/v1/search',json={},headers={'Origin':'https://foreign.example'}).status_code==403
    assert client.post('/v1/search',json={'query':'x'*1025,'operation_key':'abcdefgh'}).status_code==422
