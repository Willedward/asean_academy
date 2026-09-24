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

    database_url = os.environ.get("ASEAN_ACADEMY_DATABASE_URL") or os.environ.get(
        "DATABASE_URL"
    )
    if not database_url:
        raise SystemExit("Set ASEAN_ACADEMY_DATABASE_URL or DATABASE_URL.")

    with psycopg.connect(database_url, row_factory=dict_row) as connection:
        user = connection.execute(
            """
            select id, email, raw_user_meta_data
            from auth.users
            where lower(email) = %s
            """,
            (email,),
        ).fetchone()
        if user is None:
            raise SystemExit(
                "No matching Supabase user exists. Ask the administrator to sign in with "
                "Google once, then run this command again."
            )

        raw_metadata = user["raw_user_meta_data"]
        metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
        name_value = metadata.get("full_name") or metadata.get("name")
        display_name = (
            name_value.strip()[:80]
            if isinstance(name_value, str) and name_value.strip()
            else None
        )
        profile = connection.execute(
            """
            insert into profiles (id, role, display_name)
            values (%s, %s, %s)
            on conflict (id) do update
            set role = excluded.role,
                display_name = coalesce(profiles.display_name, excluded.display_name),
                updated_at = now()
            returning id, role::text as role
            """,
            (user["id"], args.role, display_name),
        ).fetchone()

    assert profile is not None
    print(f"Granted {profile['role']} to {email} ({profile['id']}).")


if __name__ == "__main__":
    main()
