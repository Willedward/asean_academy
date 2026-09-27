# Deployment automation and production observability

## Status

This milestone is implemented on `feature/deployment-observability`. It does
not depend on lesson videos, reviewed questions, or the final frontend design.

The first hosted academic administrator is `willsugiharto@gmail.com`. The
promotion is persisted in `profiles.role`; sign out and back in if an existing
browser session does not immediately expose administrator features.

## What is automated

The manual **Production release** GitHub Actions workflow performs one serialized
release:

1. require the workflow to run from `main`;
2. run migration safety checks;
3. rebuild a disposable PostgreSQL database from every migration;
4. lint and test the learning API and question-bank packages;
5. regenerate and verify API contracts and frontend fixtures;
6. lint, type-check, test, and build the web application;
7. apply pending Supabase migrations;
8. stamp the release with the Git commit SHA;
9. deploy the API through a Railway project token;
10. wait until API liveness, database readiness, and release identity pass;
11. deploy the web service; and
12. verify the complete public application.

The workflow uses a GitHub `production` environment. Configure that environment
with one or more required reviewers so production changes require a final human
approval after all verification has passed. The workflow concurrency group does
not cancel a running release, preventing two migration/deployment sequences from
overlapping.

The **Production availability** workflow runs every 15 minutes and checks the
public API health, API database readiness, and web root. GitHub schedules are a
useful beta safety net, but they are not a guaranteed paging system. Add a
dedicated external uptime service before a public launch.

## GitHub configuration required once

Create a GitHub environment named `production`, enable required reviewers, and
add these environment secrets:

| Secret | Source | Scope |
| --- | --- | --- |
| `RAILWAY_TOKEN` | Railway project settings | Project token for the production environment |
| `SUPABASE_ACCESS_TOKEN` | Supabase account access tokens | Token permitted to link the production project |
| `SUPABASE_DB_PASSWORD` | Supabase database settings | Production database password |

Add these repository or production-environment variables:

| Variable | Example/meaning |
| --- | --- |
| `SUPABASE_PROJECT_ID` | Supabase project reference |
| `RAILWAY_API_SERVICE` | Exact Railway service name for the FastAPI backend |
| `RAILWAY_WEB_SERVICE` | Exact Railway service name for Next.js |
| `PRODUCTION_API_URL` | Public API origin, with no credentials or query string |
| `PRODUCTION_WEB_URL` | Public web origin, with no credentials or query string |

Never paste any of those secrets into source files, issues, chat, or variables
whose names start with `NEXT_PUBLIC_`.

## Railway service settings required once

Keep the existing services and import their current configuration before
adopting Railway Infrastructure as Code:

```bash
railway link
railway config pull
railway config plan
```

Do not create a new `.railway/railway.ts` from guesses. An incomplete
project-level specification can plan removal of existing resources. Commit the
file produced by `railway config pull` in a separate reviewed change.

Configure the API service with:

- build command:
  `uv sync --project services/learning_api --locked --no-dev`
- start command:
  `uv run --project services/learning_api --locked uvicorn learning_api.main:app --host 0.0.0.0 --port $PORT`
- healthcheck path: `/api/v1/ready`
- healthcheck timeout: 300 seconds
- `ASEAN_ACADEMY_ENV=production`
- `ASEAN_ACADEMY_LOG_FORMAT=json`
- `ASEAN_ACADEMY_SLOW_REQUEST_MS=1000`
- deployment overlap: 30 seconds
- deployment draining: 20 seconds
- restart policy: always

Configure the web service with its existing build/start settings and ensure
`LEARNING_API_URL` points to the API service. If both services are in one
Railway project, use Railway private networking for server-to-server API calls.

If Railway's GitHub autodeploy is currently enabled, disable it after the
GitHub Actions production workflow is configured. Leaving both enabled can
create duplicate deployments from one commit.

## Release identity and health

`GET /api/v1/health` proves that the process can answer. It now includes:

- package version;
- environment;
- Git release SHA;
- Railway deployment ID when available; and
- the minimum database schema revision expected by the application.

It also sends `X-Release-SHA`. The deployment smoke test requires the response
header and JSON body to agree.

`GET /api/v1/ready` additionally opens a PostgreSQL connection and checks the
schema landmark introduced by the current required migration. Configure Railway
to use this path before routing traffic to a new API instance.

Railway uses deployment health checks while switching deployments; it does not
continuously poll that endpoint after promotion. The scheduled availability
workflow covers that gap during beta.

## Administrator operational status

An authenticated `academic_admin` can call:

```text
GET /api/v1/admin/operations/status
```

The response reports the active release, process uptime, database round-trip
latency, database server time, and privacy-safe counts for registered users,
students, active enrolments, current course revisions, and current question
revisions. It never returns submitted answers, tokens, invitation codes,
database addresses, or credentials.

The existing administrator endpoints still provide invitation operations,
audit events, student progress, aggregate analytics, question analytics, and
role management. A later frontend can consume these contracts without changing
the backend permissions.

## Logs and incident investigation

Preview and production default to single-line JSON logs. Railway can filter
fields such as:

```text
@message:slow_request
@http_status:>=500
@request_id:<reported-request-id>
@release_sha:<commit-sha>
```

Each request log includes method, path, status, duration, request ID, release,
and deployment ID. Request bodies, authorization headers, database URLs, and
submitted answers are excluded.

For beta, use Railway's CPU, memory, network, logs, and optional automatic
tracing. Railway resource metrics do not replace application-level monitoring.
Before public launch, add an error tracker or OpenTelemetry backend if longer
retention and alerting are required.

## Migration safety

`scripts/check_migration_safety.py` rejects unreviewed:

- dropped tables, columns, constraints, indexes, functions, types, or schemas;
- truncation;
- table/column renames;
- column type changes; and
- unbounded deletes.

Two historical constraint/type changes are recorded with reasons in
`scripts/migration_safety_allowlist.json`. A new risky migration must be
explicitly reviewed and justified. Migration validation then applies the entire
history to a fresh PostgreSQL 16 database.

Use expand-and-contract changes:

1. add backward-compatible schema;
2. deploy code that understands old and new shapes;
3. backfill in bounded jobs;
4. stop all old reads/writes; and
5. remove obsolete schema in a later release.

## Running smoke checks manually

```bash
python3 scripts/smoke_deployment.py \
  --api-url https://api.example.com \
  --web-url https://academy.example.com \
  --expected-release <git-sha>
```

URLs containing embedded credentials, query parameters, or fragments are
rejected so secrets cannot accidentally be written to CI logs.

## Rollback

If the new API never passes `/api/v1/ready`, Railway keeps the previous healthy
deployment serving traffic. If a post-deployment smoke test fails after traffic
switches:

1. stop the workflow before deploying any later service;
2. select the previous known-good deployment in Railway and redeploy it;
3. leave additive database migrations in place;
4. run `scripts/smoke_deployment.py` against production;
5. inspect JSON logs using the failed release SHA and request IDs; and
6. repair forward on a new branch.

A database rollback is appropriate only when it has been designed and tested
before release. Rolling application code back over an additive migration is
usually safer.

