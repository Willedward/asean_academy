# Stage 4 authentication and PostgreSQL foundation

## Status

The credential-independent Stage 4 backend is implemented on `feature/stage-4-auth-postgres-foundation`. It preserves the SQLite development flow and adds the production Supabase/PostgreSQL path. No reviewed lesson video or lesson body was required.

A real Supabase project is still needed for hosted verification. The implementation can be tested locally with signed fixture tokens and a disposable PostgreSQL 16 database until those project settings are available.

## Delivered behavior

### Authentication

- Private course, lesson, progress and practice routes resolve one request-scoped learner identity.
- Asymmetric Supabase `RS256` and `ES256` access tokens are verified with the project JWKS, including signature, issuer, audience, expiry and required claims.
- Legacy `HS256` tokens are validated through the Supabase Auth `/user` endpoint when `SUPABASE_ANON_KEY` is configured.
- Invalid or expired tokens return `401`; an unavailable identity provider returns `503`.
- Development keeps the credential-free local learner when PostgreSQL is not enabled.
- Preview and production fail at startup if `SUPABASE_URL` or the PostgreSQL URL is missing.

### Invitation onboarding

- `beta_invitations` stores only SHA-256 token digests, expiry, use limits and the pinned course revision.
- `POST /api/v1/onboarding/accept-invitation` checks the authenticated email, creates a student profile, and creates an enrolment pinned to the invitation's exact course revision.
- Acceptance is idempotent; replay does not consume another invitation use.
- `GET /api/v1/me` returns the authenticated profile and pinned enrolments.
- Private learning routes require an active enrolment in PostgreSQL mode.
- `create_invitation.py` issues a raw invitation code once for an imported course.

### PostgreSQL learning persistence

- The PostgreSQL practice adapter implements the existing deterministic behavior for session creation, ordered lesson pools, question assignment, attempts, hints, Give up, completion and question progress.
- Session creation and attempt submission use per-learner idempotency keys.
- Transaction row locks serialize assignment and submission.
- Advisory transaction locks make concurrent duplicate session creation resolve to one session.
- Attempts and mastery events are immutable.
- The PostgreSQL progress adapter implements lesson start, active-session resume, session synchronization, proficiency and next-action reporting.
- Reaching lesson proficiency writes an immutable mastery evidence event. It does not claim mastery; the later checkpoint remains required.

### Isolation and RLS

Owner read policies cover profiles, enrolments, practice sessions, assignments, attempts, question progress, lesson progress, mastery events and session idempotency keys. Browser-authenticated database roles have no write grants on marking, progress or mastery tables; all mutations pass through the deterministic API. API queries also include the authenticated learner ID, providing a second ownership check.

The migration validator's local `auth.uid()` reads the same transaction-local claim used by integration tests. Direct RLS tests confirmed that learner B sees zero of learner A's sessions and progress.

### Frontend integration boundary

The generated OpenAPI types include `/api/v1/me` and invitation acceptance. `createApiClient(accessToken)` adds the bearer token, and all existing API helpers accept an optional access token without changing the placeholder screens. `identity.ts` exposes typed onboarding calls.

The friend building the final visual frontend can add Supabase sign-in and pass `session.access_token` into these helpers. That work does not require changes to marking, progress or onboarding APIs.

## Database migration

`202609240004_identity_progress_rls.sql` adds:

- `profiles`
- `beta_invitations`
- `course_enrolments`
- `learner_lesson_progress`
- `mastery_events`
- `practice_session_idempotency_keys`
- write-side owner policies for existing practice tables
- text idempotency keys for browser/API compatibility
- the existing `configured_lesson_pool` selection reason used by the application

## Local verification completed

The implementation was exercised against PostgreSQL 16 with all migrations and all 40 authored questions plus the N1 course imported.

Verified flows:

1. A learner without onboarding receives `403 onboarding_required`.
2. Invitation acceptance creates a student profile and course-revision enrolment.
3. Replaying acceptance leaves `use_count` at one.
4. An authenticated learner starts Lesson 1, creates practice, receives a safe question, submits a correct deterministic answer, completes the session and reaches `proficient`.
5. Another learner cannot retrieve that session.
6. Direct RLS queries hide the first learner's sessions and progress.
7. Updating an attempt raises `attempts are immutable`.
8. Two concurrent creates with one learner and idempotency key return the same session.

## Inputs needed for hosted Supabase verification

Provide these only when the project is ready to connect:

- Supabase project URL.
- Supabase browser publishable key for the future sign-in UI.
- Confirmation whether the project signs JWTs with `ES256`/`RS256` or legacy `HS256`.
- Server-only pooled PostgreSQL connection string for the API deployment.
- The beta student email addresses to invite.
- The final frontend origin for CORS.

Do not place the PostgreSQL password or a service-role key in `NEXT_PUBLIC_*` variables.

## Remaining Stage 4 deployment work

- Apply the migration to the actual Supabase project.
- Import the reviewed question and course revisions into that project.
- Configure Supabase Auth providers and redirect URLs.
- Wire the final sign-in/invitation screens to the token-aware client helpers.
- Run the opt-in PostgreSQL test and a two-browser hosted smoke test against the real project.

Question and lesson review remains a separate content gate. Production deliberately rejects draft content; local/test environments can continue using the current drafts while review is pending.
