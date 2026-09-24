"""Issue a one-time beta invitation and print its raw code exactly once."""

from __future__ import annotations

import argparse
import os
import secrets
from datetime import UTC, datetime, timedelta

import psycopg

from learning_api.identity_repository import invitation_digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email")
    parser.add_argument("--course", default="g3-sec1-math")
    parser.add_argument("--expires-days", type=int, default=14)
    parser.add_argument("--max-uses", type=int, default=1)
    args = parser.parse_args()
    database_url = os.environ.get("ASEAN_ACADEMY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("Set ASEAN_ACADEMY_DATABASE_URL or DATABASE_URL.")
    if args.expires_days < 1 or args.max_uses < 1:
        raise SystemExit("--expires-days and --max-uses must be positive.")
    code = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(days=args.expires_days)
    with psycopg.connect(database_url) as connection:
        row = connection.execute(
            """
            select versions.id
            from course_versions versions
            join courses on courses.id = versions.course_id
            where courses.course_key = %s and versions.is_current
            """,
            (args.course,),
        ).fetchone()
        if row is None:
            raise SystemExit("The requested current course revision is not imported.")
        connection.execute(
            """
            insert into beta_invitations (
                token_sha256, email, course_version_id, max_uses, expires_at
            ) values (%s, %s, %s, %s, %s)
            """,
            (
                invitation_digest(code),
                args.email.strip().casefold(),
                row[0],
                args.max_uses,
                expires_at,
            ),
        )
    print(code)


if __name__ == "__main__":
    main()
