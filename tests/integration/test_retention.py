import os
import uuid

import psycopg
import pytest

from scripts.retention import cleanup


@pytest.mark.integration
def test_expired_session_refusal_and_owner_retention():
    url = os.environ.get("OWNER_DATABASE_URL")
    if not url:
        pytest.skip("Owner-only retention requires a disposable owner credential.")
    with psycopg.connect(url) as connection:
        scope = uuid.uuid4().hex + uuid.uuid4().hex
        connection.execute(
            "INSERT INTO tracepath.sessions VALUES (%s,now()-interval '1 day',20)", (scope,)
        )
        before = cleanup(connection)
        assert before["sessions"] >= 1
        cleanup(connection, apply=True)
        assert (
            connection.execute(
                "SELECT count(*) FROM tracepath.sessions WHERE session_scope=%s", (scope,)
            ).fetchone()[0]
            == 0
        )
        assert cleanup(connection)["attempts"] == 0
        connection.rollback()
