# Core learning API

This FastAPI service owns the versioned `/api/v1` boundary. Mathematics checking and course rules remain in `question_bank`; HTTP handlers do not duplicate them.

## Local SQLite development

From the repository root:

```bash
uv sync --project services/learning_api --locked
uv run --project services/learning_api uvicorn learning_api.main:app --reload
```

The default development environment uses `development-learner` and `.local/practice.sqlite3`, so the placeholder frontend works without an identity provider. Open <http://127.0.0.1:8000/docs> or call `http://127.0.0.1:8000/api/v1/health`.

## Supabase/PostgreSQL mode

Apply migrations, import the validated authored records, and configure the server-only database connection:

```bash
DATABASE_URL=postgresql://... bash scripts/validate_migrations.sh
DATABASE_URL=postgresql://... uv run --project question_bank --extra postgres question-bank import-db
DATABASE_URL=postgresql://... uv run --project question_bank --extra postgres question-bank course-import-db
```

`validate_migrations.sh` is for an empty disposable database. Apply `supabase/migrations` through the normal Supabase migration workflow for an existing project.

Set:

```bash
ASEAN_ACADEMY_ENV=preview
ASEAN_ACADEMY_DATABASE_URL=postgresql://...
SUPABASE_URL=https://PROJECT_REF.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated
ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT=false
```

Asymmetric Supabase access tokens are verified from the project JWKS. A legacy HS256 project must also provide `SUPABASE_ANON_KEY`; those tokens are validated through Supabase Auth. In the hosted web app, the browser keeps a Supabase cookie session and calls the same-origin Next.js gateway. That server forwards the access token as `Authorization: Bearer ...`; this API verifies it independently. Database and service-role credentials stay server-only.

After an intended administrator has signed in with Google once, bootstrap their database-backed role:

```bash
ASEAN_ACADEMY_DATABASE_URL=postgresql://... \
  uv run --project services/learning_api --locked \
  python services/learning_api/scripts/set_admin_role.py admin@example.com
```

The administrator can then open `/admin/invitations` to create and revoke student invitations. Raw invitation codes are returned once and the database stores only their SHA-256 digests. The `create_invitation.py` script remains an emergency operator fallback. After a Supabase user accepts a matching invitation, the API creates the student profile and pins the enrolment to the current N1 course revision.

## Verification

Fast tests:

```bash
uv run --project services/learning_api --locked pytest services/learning_api/tests
```

The real PostgreSQL test requires an empty migrated database with the question bank and course already imported:

```bash
TEST_DATABASE_URL=postgresql://... \
  uv run --project services/learning_api --locked \
  pytest services/learning_api/tests/test_postgres_stage4.py
```

It checks invitation onboarding, per-learner idempotency, cross-learner session isolation, immutable attempts, and concurrent duplicate session creation.

The Google OAuth and hosted environment runbook is in `docs/plan/HOSTED_AUTH_ONBOARDING.md`. Administrator invitation operations and observability are documented in `docs/plan/BETA_OPERATIONS.md`.
