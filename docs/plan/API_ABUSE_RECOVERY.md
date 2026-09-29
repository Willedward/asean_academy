# API abuse protection, load smoke, and database recovery

**Implementation:** 28 September 2026 on `feature/api-abuse-recovery`.

This milestone protects sensitive API writes, limits oversized request bodies, and proves
that critical PostgreSQL data can be backed up and restored. It is independent of final
lesson videos, question approval, and frontend design.

## Request controls

Rate limits are enforced after token verification so the learner key comes from the
verified identity. Hosted deployments use atomic PostgreSQL counters shared by every API
replica. Local development without PostgreSQL uses an in-memory implementation with the
same response contract.

| Operation | Limit | Window | Key |
| --- | ---: | ---: | --- |
| Accept beta invitation | 5 | 15 minutes | Learner |
| Accept beta invitation | 20 | 15 minutes | Client IP |
| Start/resume practice | 30 | 10 minutes | Learner |
| Submit an answer | 120 | 10 minutes | Learner |
| Open hint or give up | 60 | 10 minutes | Learner |
| Write lesson/progress evidence | 120 | 10 minutes | Learner |
| Administrator mutations | 30 | 10 minutes | Administrator |

A successful protected response carries `RateLimit-Limit`, `RateLimit-Remaining`, and
`RateLimit-Reset`. A rejected request returns HTTP 429, `Retry-After`, a request ID, and
the standard `rate_limit_exceeded` error envelope. If the hosted shared limiter cannot
reach PostgreSQL, a protected write fails closed with HTTP 503 rather than bypassing the
control.

The database stores only an HMAC-SHA256 subject digest. It never stores a raw learner ID,
IP address, access token, answer, or invitation code in rate counters or security events.
Denied requests create append-only `api_security_events` for operational investigation.
The HMAC secret must be at least 32 characters and must remain server-only.

Mutating `/api/v1/` requests with a declared body larger than 64 KiB return HTTP 413
before authentication or JSON parsing. The hosting ingress should also enforce a body
limit so chunked requests or requests without `Content-Length` are bounded before they
reach the application.

## Hosted configuration

Set these API variables:

```text
ASEAN_ACADEMY_RATE_LIMITS_ENABLED=true
ASEAN_ACADEMY_ABUSE_HASH_SECRET=<random server-only value of at least 32 characters>
ASEAN_ACADEMY_TRUST_PROXY_HEADERS=true
ASEAN_ACADEMY_MAX_REQUEST_BODY_BYTES=65536
```

Generate a secret locally and copy it directly into the GitHub environment secret:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Use `STAGING_ABUSE_HASH_SECRET` for staging and `PRODUCTION_ABUSE_HASH_SECRET` for
production. Use different values. `ASEAN_ACADEMY_TRUST_PROXY_HEADERS=true` is appropriate
only when the public ingress overwrites `X-Forwarded-For`; otherwise leave it false so a
client cannot choose its own IP-limit identity.

Migration `202609280011_api_abuse_controls.sql` must be applied before deploying the new
API. `/api/v1/ready` checks both abuse-control tables and schema revision
`202609280011` before a deployment accepts traffic.

## Bounded staging load smoke

Run this only against staging after its normal deployment smoke passes:

```bash
python3 scripts/load_test_api.py \
  --api-url https://staging-api.example.com \
  --requests 100 \
  --concurrency 10 \
  --max-p95-ms 1500
```

The default target is the read-only `/api/v1/health` endpoint. The script is deliberately
capped at 1,000 requests and concurrency 50. It reports status counts, throughput, and
latency percentiles as JSON and exits nonzero if the success ratio or p95 threshold fails.
It does not create learner data.

To smoke an authenticated read endpoint, put a short-lived tester token in the process
environment, never in a command argument:

```bash
read -r -s -p "Short-lived staging access token: " LOAD_TEST_ACCESS_TOKEN
printf '\n'
export LOAD_TEST_ACCESS_TOKEN
python3 scripts/load_test_api.py \
  --api-url https://staging-api.example.com \
  --path /api/v1/learners/me \
  --requests 50 \
  --concurrency 5
unset LOAD_TEST_ACCESS_TOKEN
```

Do not run mutation load tests with a real learner. They create application records and
would intentionally activate rate limits.

## Backup and restore proof

`scripts/backup_restore_drill.py` requires PostgreSQL `pg_dump` and `pg_restore`. It:

1. rejects identical source and target databases;
2. requires an empty disposable restore database;
3. creates a custom-format dump without owner or ACL statements;
4. restores into the disposable target;
5. calculates deterministic row counts and SHA-256 signatures; and
6. fails if any critical table differs.

The verified data includes Auth users, profiles, enrolments, practice sessions, selected
questions, attempts, question and lesson progress, mastery, diagnostics, question reports,
pseudonymous account-deletion evidence, immutable content revisions, review/audit records,
abuse counters/events, and migration history. Connection strings come only from
environment variables and are not printed.

```bash
read -r -s -p "Source database URL: " SOURCE_DATABASE_URL
printf '\n'
read -r -s -p "Empty restore database URL: " RESTORE_DATABASE_URL
printf '\n'
export SOURCE_DATABASE_URL RESTORE_DATABASE_URL
uv run --project services/learning_api --locked \
  python scripts/backup_restore_drill.py
unset SOURCE_DATABASE_URL RESTORE_DATABASE_URL
```

Never point `RESTORE_DATABASE_URL` at staging or production. Use a fresh disposable
PostgreSQL database. CI performs this drill against isolated databases on every change.
For hosted operations, keep Supabase managed backups enabled, record retention and
point-in-time recovery settings, and run this restore drill against a disposable project
before beta launch and after material schema changes. A backup is not operationally
proven until a restore and application-level verification succeed.

## Cleanup and retention

Rate-counter rows are bounded to one row per policy and subject, but inactive rows should
be removed by a scheduled maintenance task after the retention policy is agreed.
Security events are append-only evidence. Define retention before public launch, then archive them or remove them through a reviewed maintenance migration that explicitly
handles the immutability trigger. Browser clients must never receive direct table access.

## AI tutor is the next feature milestone

HTTP abuse limits and AI usage budgets solve different problems. The tutor will retain a
short per-minute request limit, plus a server-side daily quota for each learner. The
planned provider-neutral accounting model reserves an estimated request cost before a
provider call and reconciles the provider's actual input and output tokens afterward.

The tutor pilot will include:

- a configurable daily message allowance and total model-token budget per learner;
- maximum input context and output tokens per turn;
- one in-flight generation per learner;
- an academy-wide monthly spend/call circuit breaker;
- administrator-visible aggregate usage and per-learner quota overrides;
- `tutor_quota_exceeded` with a reset time when the daily budget is exhausted; and
- no provider key, model credentials, or raw internal prompt exposed to the browser.

Start the beta with a small configurable allowance, then set the final number from the
Lesson 1 accuracy, latency, and cost evaluation. The course, deterministic marking,
authored hints, and unlocked worked solutions must continue to work when the tutor is
disabled or its quota is exhausted.

The backend tutor scaffold can be built next while content review continues. Enabling
responses for students remains gated on reviewed Lesson 1 notes, reviewed worked
solutions, answer-leakage tests, and the server-owned solution-lock state described in
[TUTOR_INTERACTION_DESIGN.md](TUTOR_INTERACTION_DESIGN.md).
