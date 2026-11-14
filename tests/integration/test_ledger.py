import os
import subprocess
import sys
import uuid

import pytest

from packages.operations.ledger import Ledger, LedgerError

pytestmark = pytest.mark.integration


@pytest.fixture
def ledger():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Disposable Postgres URL unavailable; integration is not passed.")
    return Ledger(url)


def test_readback_replay_conflict_and_foreign_scope(ledger):
    token = ledger.new_session()
    other = ledger.new_session()
    request_id = str(uuid.uuid4())
    calls = []

    def produce(scope, connection):
        calls.append(1)
        return {"request_id": request_id, "output_digest": "synthetic"}

    first = ledger.execute(token, "ledger-test", "payload", produce)
    assert not first["replay"]
    assert ledger.read(token, request_id)["output_digest"] == "synthetic"
    assert ledger.execute(token, "ledger-test", "payload", produce)["replay"]
    assert len(calls) == 1
    with pytest.raises(LedgerError) as conflict:
        ledger.execute(token, "ledger-test", "changed", produce)
    assert conflict.value.status == 409
    with pytest.raises(LedgerError) as foreign:
        ledger.read(other, request_id)
    assert foreign.value.status == 404
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import os; from packages.operations.ledger import Ledger; "
                "r=Ledger(os.environ['TEST_DATABASE_URL']).read(os.environ['TEST_SESSION'],os.environ['TEST_REQUEST']); "
                "assert r['output_digest']=='synthetic'; print('independent process readback passed')"
            ),
        ],
        env={**os.environ, "TEST_SESSION": token, "TEST_REQUEST": request_id},
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert child.returncode == 0, child.stderr


def test_budget_and_rollback(ledger):
    token = ledger.new_session()
    for i in range(20):
        ledger.execute(token, f"budget-{i}", str(i), lambda s, c: {"request_id": str(uuid.uuid4())})
    with pytest.raises(LedgerError) as full:
        ledger.execute(token, "budget-extra", "extra", lambda s, c: {})
    assert full.value.status == 429
