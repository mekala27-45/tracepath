"""Atomic receipt persistence; connection ownership is explicit."""
import hashlib
import secrets
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path
import psycopg
from psycopg.types.json import Jsonb


class LedgerError(Exception):
    def __init__(self, status, detail):
        self.status, self.detail = status, detail
        super().__init__(detail)


def scope(token):
    return hashlib.sha256(token.encode("ascii")).hexdigest()


class Ledger:
    def __init__(self, url):
        self.url = url

    def connection(self):
        return psycopg.connect(self.url, connect_timeout=5, options="-c statement_timeout=10000")

    def initialize(self):
        with self.connection() as connection:
            connection.execute(Path(__file__).with_name("schema.sql").read_text())

    def ready(self):
        with self.connection() as connection:
            connection.execute("SELECT 1 FROM tracepath.sessions LIMIT 1")

    def new_session(self):
        token = secrets.token_urlsafe(32)
        with self.connection() as connection:
            connection.execute("INSERT INTO tracepath.sessions VALUES (%s,now()+interval '1 hour',20)",
                               (scope(token),))
        return token

    def execute(self, token, key, payload_digest, produce, commit_span=nullcontext):
        session_scope = scope(token)
        with self.connection() as connection:
            session = connection.execute("SELECT expires_at,remaining FROM tracepath.sessions "
                "WHERE session_scope=%s FOR UPDATE", (session_scope,)).fetchone()
            if session is None or session[0] <= datetime.now(timezone.utc):
                raise LedgerError(401, "Session expired or unknown. Start a new demo session.")
            prior = connection.execute("SELECT payload_digest,receipt FROM tracepath.receipts "
                "WHERE session_scope=%s AND operation_key=%s AND expires_at>now()",
                (session_scope, key)).fetchone()
            if prior:
                if prior[0] != payload_digest:
                    raise LedgerError(409, "Operation key already belongs to a different query.")
                return {**prior[1], "replay": True}
            if session[1] <= 0:
                raise LedgerError(429, "Session budget exhausted. Start a new demo session later.")
            receipt = produce(session_scope, connection)
            with commit_span():
                connection.execute("INSERT INTO tracepath.receipts(request_id,session_scope,operation_key,"
                    "payload_digest,receipt) VALUES (%s,%s,%s,%s,%s)",
                    (receipt["request_id"], session_scope, key, payload_digest, Jsonb(receipt)))
                connection.execute("UPDATE tracepath.sessions SET remaining=remaining-1 WHERE session_scope=%s",
                                   (session_scope,))
                connection.commit()
        # The connection context has committed before returning.
        return {**receipt, "replay": False}

    def read(self, token, request_id):
        with self.connection() as connection:
            row = connection.execute("SELECT r.receipt FROM tracepath.receipts r "
                "JOIN tracepath.sessions s USING(session_scope) WHERE r.request_id=%s "
                "AND r.session_scope=%s AND r.expires_at>now() AND s.expires_at>now()",
                (request_id, scope(token))).fetchone()
        if row is None:
            raise LedgerError(404, "Receipt unavailable in this session.")
        return row[0]

    def attempt(self, observation):
        with self.connection() as connection:
            connection.execute("INSERT INTO tracepath.attempts VALUES (%s,%s,%s,%s,%s,now()) "
                "ON CONFLICT(attempt_id) DO UPDATE SET observation=EXCLUDED.observation,updated_at=now()",
                (observation["attempt_id"], observation["request_id"], observation["run_id"],
                 observation["attempt"], Jsonb(observation)))
