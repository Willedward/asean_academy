# Content synchronization and administrator dashboard

**Branch:** `feature/content-sync-admin-dashboard`
**Required migration:** `202609270009_course_revision_audit.sql`
**Current authored catalogue:** `g3-sec1-math` revision 2; 40 N1 draft questions.

## Delivered

1. Startup and readiness validation compare course, lesson and question revision
   hashes/statuses against imported PostgreSQL content. Missing imports no longer
   wait for the first learner lesson request to fail.
2. Repeatable development bootstrap previews and applies pending migrations and
   question/course imports using the saved API connection.
3. Academic administrators can preview and confirm safe forward course-pin changes.
   Active sessions and incompatible lesson evidence block changes; accepted changes
   preserve learner records and append an audit event.
4. A protected admin interface connects the existing analytics, invitations, role,
   audit and operational APIs.
5. CI and release verification now import content into disposable PostgreSQL and run
   database tests instead of silently skipping them for lack of TEST_DATABASE_URL.
6. [Architecture diagrams](BETA_ARCHITECTURE.md) explain current services, workflows,
   data relationships, release sequencing and future integrations.

## Run locally

From `/home/william/asean_academy`:

```bash
corepack pnpm bootstrap:api
corepack pnpm bootstrap:api --apply
```

The first command previews pending migrations. If the schema is already current,
it also rehearses imports inside a rolled-back transaction. If migrations remain,
it validates local content and lists the plan; import rehearsal follows schema
application. The second applies migrations and imports. A repeat run is safe.

Bootstrap:
- loads `services/learning_api/.env.local` through the existing dev configuration;
- refuses non-development environments;
- rejects migration gaps, unknown newer migrations and unreviewed destructive SQL;
- uses transaction-scoped advisory locks compatible with transaction pooling;
- commits each migration together with its migration-ledger row;
- commits question/course imports together after validation;
- accepts identical immutable revisions and rejects conflicting content;
- leaves passwords, student attempts, invitations, roles and enrolment pins alone.

If connection settings are absent, run `corepack pnpm setup:api` once. Do not keep
resetting a password to resolve a missing migration or content import. Authentication,
network connectivity, schema version and content synchronization are separate checks.

Restart the existing API terminal with Ctrl+C, then:

```bash
corepack pnpm dev:api
```

In the web terminal:

```bash
corepack pnpm dev:web
```

Reuse an already running web server on port 3000 rather than launching a second one.

- Student course: <http://localhost:3000/learn>
- Admin dashboard: <http://localhost:3000/admin>
- Users and course updates: <http://localhost:3000/admin/users>
- Database/content status: <http://localhost:3000/admin/operations>
- Readiness: <http://localhost:8000/api/v1/ready>

Sign in with the existing academic-administrator Google account. No separate shared
admin password or hard-coded admin credential is introduced.

## Dashboard behavior

Overview shows aggregate counts, students supports search and pagination, student
details show progress evidence, and questions supports outcome/difficulty filters.
Users includes all roles, so an administrator with an enrolment remains discoverable.
Invitations preserve the existing one-time-code creation flow. Audit lists the latest
100 events. Operations displays live database/release status and content-sync status
independently, with request IDs on errors.

Role changes require selection, review and confirmation. Backend rules still reject
self-role changes and removal of the last academic administrator. A database advisory
lock serializes concurrent role changes.

The UI is deliberately a replaceable application surface. The friend's design can
replace it using the generated OpenAPI types and existing API helpers.

## Course revision changes

1. Open Users and roles, search the account and inspect its enrolment.
2. Select **Preview course update**.
3. Read the source/target revisions, active-session count and blockers.
4. When allowed, enter the reason and select **Confirm course update**.

The request includes the preview's expected source revision and target content hash.
The backend acquires the learner lock and repeats all checks. A stale preview returns
409 and requires a fresh preview. It updates the enrolment and writes the audit event
in one transaction.

This operation never discards a session, resets progress or rewrites an attempt.
If an active session exists, finish it before trying again. If progress belongs to
a changed/removed lesson revision, the update is refused; that evidence needs an
explicit migration policy. There is intentionally no bypass checkbox.

The API serves one bundled catalogue. This is not a complete historical-catalogue
implementation. Resuming sessions across question-revision changes still needs
compatibility validation; keep required question versions available.

## Endpoint access

All endpoints are under `/api/v1/admin`.

| Endpoint | Method | Required role |
| --- | --- | --- |
| `/analytics/overview`, `/analytics/questions` | GET | content_admin or academic_admin |
| `/students`, `/students/{id}` | GET | content_admin or academic_admin |
| `/invitations`, `/audit-events` | GET | content_admin or academic_admin |
| `/invitations`, `/invitations/{id}/revoke` | POST | content_admin or academic_admin |
| `/users` | GET | academic_admin |
| `/users/{id}/role` | PATCH | academic_admin |
| `/users/{id}/curriculum-preview` | GET | academic_admin |
| `/users/{id}/curriculum-migration` | POST | academic_admin |
| `/operations/status`, `/operations/content` | GET | academic_admin |

Student accounts cannot access these APIs. Backend authorization remains authoritative
even if a user manually enters an admin URL.

## Verification

Run against a disposable database, never a live student database:

```bash
# DATABASE_URL and TEST_DATABASE_URL must point to the disposable instance.
bash scripts/validate_migrations.sh
uv run --project services/learning_api --locked question-bank import-db
uv run --project services/learning_api --locked question-bank course-import-db
uv run --project services/learning_api --locked pytest services/learning_api/tests
corepack pnpm ci:web
```

The bootstrap integration test needs CREATE DATABASE permission and creates/drops a
separate uniquely named test database. Tests cover preview without schema writes,
fresh migrations/imports, repeat runs, unknown migration refusal, content mismatches,
role restrictions, stale course previews, active-session blockers and preservation
of incompatible progress. UI tests cover confirmation, blocked migration display,
query filters and independent operational errors.

## Remaining boundaries

- N1 mathematical/editorial review and videos are still pending.
- Only Lesson 1 currently has the new draft notes; the other lesson bodies are placeholders.
- Conversational AI tutoring, content editing/uploading, historical metric storage,
  full audit browsing/export and historical catalogue serving are separate work.
- Actual hosted rollout/Google browser sign-in requires checking the real deployment
  and user session. Local test success does not prove externally configured hosting.
- This milestone does not move existing users to a new course revision automatically.

## Verification record — 27 September 2026

- Learning API: 59 tests passed with disposable PostgreSQL enabled.
- Question-bank domain: 28 tests passed.
- Web: 23 tests passed; lint, TypeScript, contract generation and production build passed.
- Migration safety, repository whitespace and documentation links passed.
- The configured hosted development database received migration 009 and replay-safe
  content imports. A second preview reported no pending migrations.
- Running local API readiness returned database ready, schema current and content current.
- Existing academic administrator role verified. Its revision-1 enrolment has one
  active practice session; migration remains blocked until it is resolved. Enrolment,
  attempts and credentials were not changed by bootstrap.
- Browser OAuth login and the actual production rollout were not independently tested
  in this milestone; external configuration still needs a hosted smoke check.
