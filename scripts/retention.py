"""Owner-only retention: inspect first, explicitly apply only expired demo rows."""

import argparse
import os

import psycopg


def cleanup(connection, apply=False):
    counts = {
        "receipts": connection.execute(
            "SELECT count(*) FROM tracepath.receipts WHERE expires_at<=now()"
        ).fetchone()[0],
        "sessions": connection.execute(
            "SELECT count(*) FROM tracepath.sessions WHERE expires_at<=now()"
        ).fetchone()[0],
        "attempts": connection.execute(
            "SELECT count(*) FROM tracepath.attempts WHERE updated_at<now()-interval '1 day'"
        ).fetchone()[0],
    }
    if apply:
        connection.execute("DELETE FROM tracepath.receipts WHERE expires_at<=now()")
        connection.execute("DELETE FROM tracepath.attempts WHERE updated_at<now()-interval '1 day'")
        connection.execute(
            "DELETE FROM tracepath.sessions s WHERE expires_at<=now() AND NOT EXISTS (SELECT 1 FROM tracepath.receipts r WHERE r.session_scope=s.session_scope)"
        )
    return counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with psycopg.connect(os.environ["OWNER_DATABASE_URL"], connect_timeout=5) as connection:
        print({"applied": args.apply, "eligible": cleanup(connection, args.apply)})
