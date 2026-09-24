# Beta operations: administrator invitations and observability

## Status

This milestone is implemented on `feature/beta-operations`. It adds a protected
administrator workspace at `/admin/invitations`, database-backed administrator
authorization, invitation creation and revocation, privacy-minimal operational
counts, immutable audit events and request telemetry.

Lesson videos and reviewed question content are not required for this milestone.
The dashboard can support controlled technical testers while those materials are
still being prepared.

## What administrators can do

A user with `profiles.role` set to `content_admin` or `academic_admin` can:

- issue an invitation for an exact Google email address;
- choose a 7, 14 or 30 day expiry and a usage limit;
- copy the raw invitation code or onboarding link immediately after creation;
- list recent invitations and see active, expired, exhausted or revoked status;
- revoke an active invitation;
- view student, recent-enrolment and invitation counts; and
- inspect recent invitation and onboarding audit events with request IDs.

The raw invitation code is returned once by the creation endpoint. Only its
SHA-256 digest is stored. It is excluded from list responses, logs and audit
metadata, so it cannot be recovered later.

## Authorization model

FastAPI verifies the Supabase access token first. It then reads `profiles.role`
from PostgreSQL for every admin request. A role claim supplied by the browser or
an old token is not sufficient to gain administrator access.

- `content_admin` and `academic_admin`: access `/admin/invitations` and
  `/api/v1/admin/*`.
- `student`: redirected to `/learn` by the web app and receives `403
  administrator_required` from direct API calls.
- authenticated user without a profile: redirected to onboarding and receives
  the existing `403 onboarding_required` API response.
- anonymous user: redirected to login and receives `401` from direct API calls.

Database credentials remain in the API service. The browser uses the authenticated
same-origin Next.js gateway.

## 1. Apply the database migration

Apply all migrations through the normal Supabase migration workflow, including:

```text
supabase/migrations/202609250005_beta_operations.sql
```

The migration creates `beta_audit_events`, its supporting indexes and an
update/delete rejection trigger. Row-level security is enabled without a direct
browser policy; these records are server-managed.

For a new disposable database, validate the complete migration chain before
using it:

```bash
DATABASE_URL='postgresql://...' bash scripts/validate_migrations.sh
```

Do not run that validation command against an existing shared database because it
is designed for a disposable database.

## 2. Bootstrap the first administrator

The user must sign in with Google once so a row exists in `auth.users`. They do
not need a student invitation. From a trusted terminal with the server database
URL, run:

```bash
ASEAN_ACADEMY_DATABASE_URL='postgresql://...' \
  uv run --project services/learning_api --locked \
  python services/learning_api/scripts/set_admin_role.py admin@example.com
```

To grant the academic administrator role instead:

```bash
ASEAN_ACADEMY_DATABASE_URL='postgresql://...' \
  uv run --project services/learning_api --locked \
  python services/learning_api/scripts/set_admin_role.py \
  admin@example.com --role academic_admin
```

The command locates the exact normalized email in Supabase Auth and upserts the
profile role. It never accepts or prints passwords, OAuth tokens or database
secrets. After the command succeeds, the administrator can open
`https://YOUR_WEB_DOMAIN/admin/invitations`. A generic login flow also redirects
an administrator away from student onboarding to this dashboard.

This command is the one exceptional bootstrap action. Normal invitation work then
uses the dashboard and does not require SQL or a database URL on an administrator's
computer.

## 3. Issue and hand off an invitation

1. Open `/admin/invitations` and sign in with the bootstrapped Google account.
2. Enter the student's exact Google email.
3. Choose the expiry and usage limit, then select **Create invitation**.
4. Select **Copy onboarding link** before leaving or reloading the page.
5. Send the link through a private channel to the intended student.
6. Ask the student to sign in with the same Google email and accept the invitation.

The link has this shape:

```text
https://YOUR_WEB_DOMAIN/onboarding?code=RAW_INVITATION_CODE
```

The code in the URL is sensitive until it expires or is accepted. Email matching,
expiry and usage checks still apply if another person sees it.

The old `create_invitation.py` command remains available as an emergency server
operator fallback. The web dashboard is the normal beta workflow.

## 4. API endpoints

All endpoints below require a verified administrator token:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/admin/invitations` | List invitations with computed status |
| `POST` | `/api/v1/admin/invitations` | Create an invitation and return its raw code once |
| `POST` | `/api/v1/admin/invitations/{id}/revoke` | Revoke an invitation |
| `GET` | `/api/v1/admin/operations/summary` | Return privacy-minimal beta counts |
| `GET` | `/api/v1/admin/audit-events` | Return recent immutable operational events |

The OpenAPI file and generated TypeScript client types include these contracts.
Malformed requests use the standard safe `422 validation_error` envelope.

## 5. Telemetry and incident diagnosis

Every API response includes `X-Request-ID`. The API writes a structured completion
line containing request ID, method, path, status and duration. Query strings and
request bodies are excluded, preventing invitation codes from entering normal
request logs.

Invitation creation, revocation and acceptance create append-only audit rows.
The audit metadata contains operational fields such as course revision and usage
limit; it excludes raw invitation codes, access tokens and student answers.
Onboarding rejection logs contain a safe error code and request ID without the
submitted code or email.

For beta support:

1. Ask the tester for the request ID shown in the UI error.
2. Search the API service logs for that request ID.
3. Compare it with the dashboard audit trail when the action was create, revoke
   or accept.
4. Revoke a suspected invitation and issue a fresh one when required.

A hosted log alerting provider is not configured by this repository. Railway log
retention and alert routing should be chosen before expanding beyond a small
controlled beta.

## 6. Verification checklist

Run locally before deployment:

```bash
uv run --project services/learning_api --locked \
  pytest services/learning_api/tests
uv run --project services/learning_api --locked \
  ruff check services/learning_api/src services/learning_api/tests \
  services/learning_api/scripts/set_admin_role.py
corepack pnpm --filter @asean-academy/web test
corepack pnpm --filter @asean-academy/web typecheck
corepack pnpm --filter @asean-academy/web lint
corepack pnpm --filter @asean-academy/web build
```

With an empty migrated PostgreSQL test database and the course imports loaded:

```bash
TEST_DATABASE_URL='postgresql://...' \
  uv run --project services/learning_api --locked \
  pytest services/learning_api/tests/test_postgres_stage4.py
```

The PostgreSQL test covers role lookup, invitation lifecycle, digest-only storage
and audit immutability. It is intentionally skipped when `TEST_DATABASE_URL` is
not set.

After deployment, verify with separate administrator and student accounts:

1. a student cannot open the admin page or call an admin endpoint;
2. an administrator can create an invitation and sees its code once;
3. a page reload lists the invitation without revealing the code;
4. the intended student can accept the link;
5. the summary and audit trail update;
6. a revoked invitation cannot be accepted; and
7. relevant UI errors can be matched to API logs by request ID.

## Remaining external work

The implementation is complete without lesson materials. Hosted verification
still needs:

- a Supabase project with the new migration applied;
- a real Google sign-in completed by the first administrator;
- a server database URL available when running the one-time role command;
- deployed web and API domains with the variables in
  `HOSTED_AUTH_ONBOARDING.md`; and
- a disposable PostgreSQL URL if the opt-in integration tests are to run in CI.
