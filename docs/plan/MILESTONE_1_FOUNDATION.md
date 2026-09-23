# Milestone 1 — Contracts and repository foundation

**Status:** Implemented locally on `feature/milestone-1-foundation`

**Scope source:** PLAN V2 Stage 1 and the frontend plan's Phase 1

## Outcome

Milestone 1 creates the replaceable application boundary used by later course,
practice, authentication, progress, and tutor work. It does not publish lesson
content or enable students yet.

The implementation contains:

- `apps/web`: Next.js App Router, React, strict TypeScript, Tailwind CSS, a
  shadcn-compatible UI setup, accessible loading/error states, and Vitest.
- `services/learning_api`: FastAPI with `/api/v1`, standard error envelopes,
  request IDs, CORS configuration, idempotency-key validation, and pytest.
- A committed OpenAPI document and generated frontend TypeScript types.
- A same-origin web rewrite from `/api/v1/*` to the configured learning API.
- Fixture mode for frontend work when the API is unavailable.
- Reproducible pnpm and uv lockfiles.
- GitHub Actions for web checks, API/question-domain checks, and clean-database
  migration validation.
- Supabase CLI configuration without secrets or learner data.

## Blank lesson material is supported

All seven N1 lesson files remain `draft` with empty `sections` and `assets`.
This is valid under the course authoring schema and lets application development
continue while videos are recorded.

These safeguards remain in force:

1. An empty draft lesson can be validated, imported, and previewed by authors.
2. Strict publication validation rejects it until sections and review provenance
   exist.
3. Student course queries must select only published course and lesson versions.
4. A video is an optional lesson asset; its absence cannot silently create a
   published empty lesson.

When lesson material is ready, add versioned content blocks and asset metadata,
increment the lesson revision when learner-visible content changes, preview it,
complete Mathematics/editorial/accessibility review, and only then publish it.

## Local setup

Prerequisites are Node 24, Corepack, Python 3.12, and uv.

```bash
cd /home/william/asean_academy
corepack pnpm install
uv sync --project services/learning_api --locked
```

Start the API:

```bash
corepack pnpm dev:api
```

In a second terminal, start the web client:

```bash
corepack pnpm dev:web
```

Open <http://localhost:3000>. API documentation is at
<http://127.0.0.1:8000/docs> in local development.

To work on frontend visuals without the API, copy `apps/web/.env.example` to
`apps/web/.env.local` and set:

```text
NEXT_PUBLIC_USE_API_FIXTURES=true
```

## Verification

Regenerate the API contract whenever a response or endpoint changes:

```bash
corepack pnpm openapi:generate
```

Run local gates:

```bash
corepack pnpm ci:web
corepack pnpm test:python
```

Migration validation requires a disposable empty PostgreSQL database:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/asean_academy_test \
  bash scripts/validate_migrations.sh
```

Never point that script at a shared or production database.

## Exit criteria

| Criterion | Status | Evidence |
|---|---|---|
| Web can call a configured health endpoint | Complete | Same-origin rewrite and typed health panel |
| `/api/v1` conventions exist | Complete | Request ID, errors, idempotency, auth fail-closed boundary |
| OpenAPI client compiles | Complete | Generated `schema.d.ts` passes strict typecheck/build |
| Existing question/practice tests are in CI | Complete in configuration | Python CI job runs `question_bank/tests` |
| Frontend quality checks are in CI | Complete in configuration | Lint, typecheck, Vitest, and Next production build |
| Migration validation is in CI | Complete in configuration | Empty PostgreSQL service applies all migrations |
| Remote CI has passed | Pending push | GitHub cannot run the workflow before the branch is pushed |
| Preview URL exists | Pending hosting choice | No Vercel/Railway/Supabase preview credentials are configured |

Milestone 1 implementation is complete locally. Its two external proofs are
intentionally marked pending rather than claimed: push the branch to execute
GitHub Actions, then connect the web/API preview deployments after choosing their
hosts.

## Inputs still needed from the founders

- The Git hosting/preview deployment choice for the web and API.
- The people responsible for Mathematics review and language/editorial review.
- Confirmation of the current recommended progression defaults: soft lesson
  order, checkpoint prerequisites, and the thresholds stored in `course.json`.
- Video hosting choice and export specification before lesson videos are linked.
- Figma file or design handoff when the temporary health screen is replaced.

None of these inputs block the local Milestone 1 code or continued video work.
