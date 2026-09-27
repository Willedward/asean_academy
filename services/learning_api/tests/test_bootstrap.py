"""Exercise the real bootstrap against a separate, disposable PostgreSQL database."""
import importlib.util
import os
import sys
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services/learning_api/scripts"))
spec = importlib.util.spec_from_file_location("bootstrap_local", ROOT / "services/learning_api/scripts/bootstrap_local.py")
bootstrap_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap_module)


@pytest.mark.postgres
def test_bootstrap_preview_apply_and_repeat_are_safe():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable PostgreSQL with CREATE DATABASE permission")
    name = "bootstrap_test_" + uuid4().hex
    with psycopg.connect(url, autocommit=True) as admin:
        admin.execute(sql.SQL("create database {}").format(sql.Identifier(name)))
    target = make_conninfo(url, dbname=name)
    try:
        # The same minimal Supabase Auth stand-in used by migration CI.
        helper = (ROOT / "scripts/validate_migrations.sh").read_text().split("<<'SQL'\n", 1)[1].split("\nSQL", 1)[0]
        with psycopg.connect(target) as c:
            c.execute(helper)
        preview = bootstrap_module.bootstrap(target, apply=False)
        assert preview["pending_migrations"] == len(list((ROOT / "supabase/migrations").glob("*.sql")))
        with psycopg.connect(target) as c:
            assert c.execute("select to_regclass('public.profiles')").fetchone()[0] is None
        result = bootstrap_module.bootstrap(target, apply=True)
        assert result["questions"] == 40
        assert result["status"] == "current"
        assert bootstrap_module.bootstrap(target, apply=False)["pending_migrations"] == 0
        assert bootstrap_module.bootstrap(target, apply=True) == result
        with psycopg.connect(target) as c:
            assert c.execute("select count(*) from profiles").fetchone()[0] == 0
            assert c.execute("select count(*) from math_question_versions").fetchone()[0] == 40
            assert c.execute("select count(*) from course_enrolments").fetchone()[0] == 0
            c.execute("insert into supabase_migrations.schema_migrations(version) values ('299999999999')")
        with pytest.raises(ValueError, match="absent from this branch"):
            bootstrap_module.bootstrap(target, apply=True)
    finally:
        with psycopg.connect(url, autocommit=True) as admin:
            admin.execute(sql.SQL("drop database {} with (force)").format(sql.Identifier(name)))
