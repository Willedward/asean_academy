import os

import psycopg
import pytest


@pytest.mark.postgres
def test_diagnostic_responses_are_read_only_through_the_api():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    with psycopg.connect(url) as connection:
        for role in ("anon", "authenticated"):
            for privilege in ("select", "insert", "update", "delete"):
                allowed = connection.execute(
                    "select has_table_privilege(%s, 'diagnostic_responses', %s)",
                    (role, privilege),
                ).fetchone()[0]
                assert allowed is False, (role, privilege)
        connection.execute("set local role authenticated")
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            connection.execute("select score from diagnostic_responses limit 1")
