# Authenticated beta end-to-end verification

**Implemented:** 28 September 2026 on branch **feature/authenticated-beta-e2e**.

This milestone gives CI a real browser check across the Next.js web server, FastAPI
Learning API and a fresh PostgreSQL database. It does not call Google or Supabase and
does not use a development learner override. The two local services accept the same
short-lived signed test token only when both explicitly run in the test environment.

## What the suite proves

The serial Chromium suite covers these beta-critical journeys:

1. an unauthenticated learner is redirected to login;
2. an invalid invitation is rejected and a valid email-bound invitation onboards;
3. lesson-section completion persists after a reload;
4. draft guided practice loads through the normal API and database repositories;
5. a wrong answer exposes authored feedback, Hint 1, then Hint 2;
6. the full solution unlocks only after the second wrong submission;
7. give-up and attempt state appear in progress and survive re-authentication;
8. a second learner cannot see the first learner's progress;
9. a content administrator cannot perform mathematics review or open academic-only user management;
10. an academic administrator can open user management and safe student preview;
11. safe preview disables answer entry and does not expose the worked solution;
12. a learner report reaches the administrator inbox and a content administrator records a learner-visible resolution;
13. content and academic administrator navigation and protected controls follow database roles;
14. the administrator shell has no page-level horizontal overflow at 390, 768 and 1440 pixels;
15. mobile navigation is keyboard-operable, moves focus into the menu, closes with Escape and restores focus; and
16. academic deletion is previewed through the signed backend workflow without executing permanent deletion.

The Playwright report attaches administrator screenshots at all three widths and a content-administrator phone-menu screenshot.

These are browser/API/database integration checks. Google account selection, the
Supabase-hosted OAuth callback and provider consent screen remain a small hosted smoke
test because CI must not store or automate a personal Google login.

## Test-only authentication boundary

**apps/web/src/app/auth/e2e-session/route.ts** issues a one-hour, HttpOnly cookie after a
request presents the private E2E secret. The cookie contains an HS256 token with issuer
asean-academy-e2e, audience and role authenticated, UUID subject, email, issue time and
expiry. FastAPI checks its signature and every required claim.

The route and verifier are available only when:

```text
ASEAN_ACADEMY_ENV=test
ASEAN_ACADEMY_E2E_AUTH_SECRET=<at least 32 characters>
```

The API refuses to start with that secret in development, preview or production. The
web route returns 404 outside test mode. No production or preview deployment should
define this variable. The known local/CI secret is test infrastructure, not a user,
database or Supabase credential.

## Disposable data

**services/learning_api/scripts/seed_e2e.py** seeds fixed identities for:

- one academic administrator;
- one content administrator;
- two invitation-only learners.

It refuses remote hosts, requires a database name containing e2e, and refuses to run
again when fixture identities are present. This guard reduces the chance of running it
against shared data. It runs only after migrations and content imports.

The Playwright API process enables the deterministic synthetic tutor. In test mode only,
the tutor repository may ground against the imported draft fixtures when draft content is
explicitly enabled. Preview and production still require published question and lesson
grounding. The student journey submits a wrong answer, starts a tutor session, sends a
message, and checks the grounded reply before continuing through hints and Give up.

## CI execution

The **authenticated-e2e** job in **.github/workflows/ci.yml** starts PostgreSQL 16,
installs locked Python and Node dependencies, applies every migration, imports questions
and the course catalogue, seeds identities, installs Chromium, then runs:

```bash
pnpm test:e2e
```

Playwright starts the API on port 8100 and the web app on port 3100. The web test server uses `.next-e2e`, so it can run alongside a developer server using `.next`. It retains traces, screenshots and video on failure, attaches responsive acceptance screenshots on success, and CI uploads the HTML report for seven days after every run.

## Local execution

Use a disposable local PostgreSQL database whose name contains e2e. Never point these
commands at the hosted beta project.

```bash
export E2E_DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/asean_academy_e2e'

DATABASE_URL="$E2E_DATABASE_URL" bash scripts/validate_migrations.sh
DATABASE_URL="$E2E_DATABASE_URL" uv run --project services/learning_api --locked question-bank import-db
DATABASE_URL="$E2E_DATABASE_URL" uv run --project services/learning_api --locked question-bank course-import-db
uv run --project services/learning_api --locked python services/learning_api/scripts/seed_e2e.py

corepack pnpm --filter @asean-academy/web exec playwright install chromium
corepack pnpm test:e2e
```

The seed is intentionally one-shot. Recreate the disposable database before another
complete run. Linux machines may also require Playwright system packages:

```bash
corepack pnpm --filter @asean-academy/web exec playwright install-deps chromium
```

## Files

- **apps/web/playwright.config.ts**: service orchestration, ports and failure evidence;
- **apps/web/e2e/beta-journeys.spec.ts**: browser journeys and fixed identities;
- **apps/web/src/lib/auth/e2e-config.ts**: fail-closed environment gate;
- **apps/web/src/lib/auth/e2e-session.ts**: signed cookie/token implementation;
- **services/learning_api/src/learning_api/identity.py**: API token verification;
- **services/learning_api/scripts/seed_e2e.py**: guarded disposable fixtures;
- **.github/workflows/ci.yml**: fresh-database CI job.
