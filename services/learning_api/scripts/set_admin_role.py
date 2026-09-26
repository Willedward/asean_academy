"""Grant an existing Supabase user an ASEAN Academy administrator role."""

from __future__ import annotations

import argparse
import os

import psycopg
from psycopg.rows import dict_row

ADMIN_ROLES = ("content_admin", "academic_admin")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("email", help="Email of a user who has already signed in once")
    parser.add_argument(
        "--role",
        choices=ADMIN_ROLES,
        default="content_admin",
        help="Administrator role to grant (default: content_admin)",
    )
    args = parser.parse_args()
    email = args.email.strip().casefold()
    if "@" not in email:
        raise SystemExit("Provide a valid email address.")

    database_url = os.environ.get("ASEAN_ACADEMY_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("Set ASEAN_ACADEMY_DATABASE_URL or DATABASE_URL.")

    with psycopg.connect(database_url, prepare_threshold=None, row_factory=dict_row) as connection:
        profile = connection.execute(
            """
            update profiles
            set role = %s, updated_at = now()
            where email = %s
            returning id, role::text as role
            """,
            (args.role, email),
        ).fetchone()
        if profile is None:
            raise SystemExit(
                "No matching learner profile exists. Sign in with Google and accept a beta "
                "invitation once, then run this command again."
            )

    assert profile is not None
    print(f"Granted {profile['role']} to {email} ({profile['id']}).")


if __name__ == "__main__":
    main()
