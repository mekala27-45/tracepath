"""One-time scoped role setup on the new owned project."""

import os

import psycopg
from psycopg import sql

with psycopg.connect(os.environ["DATABASE_URL"]) as connection:
    exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname='tracepath_app'").fetchone()
    if exists:
        raise RuntimeError("Existing role preserved; refusing to replace its credential.")
    connection.execute(
        sql.SQL("CREATE ROLE tracepath_app LOGIN PASSWORD {} ").format(
            sql.Literal(os.environ["APP_DB_PASSWORD"])
        )
    )
    connection.execute("GRANT CONNECT ON DATABASE tracepath TO tracepath_app")
    connection.execute("GRANT USAGE ON SCHEMA tracepath TO tracepath_app")
    connection.execute(
        "GRANT SELECT,INSERT,UPDATE ON ALL TABLES IN SCHEMA tracepath TO tracepath_app"
    )
print("Dedicated runtime role created with schema-only application grants.")
