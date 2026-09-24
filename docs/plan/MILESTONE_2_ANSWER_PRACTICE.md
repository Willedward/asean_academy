# Milestone 2 — Answer-only practice vertical slice

**Branch:** `feature/milestone-2-answer-practice`

**Plan mapping:** PLAN V2 M2-02 and the practice portion of Stage 3.

## Product decision

The MVP collects only final typed answers. Numeric, algebraic-expression and
multipart responses are marked by the deterministic Python assessment engine.
Handwriting recognition and an LLM are not part of answer submission or marking.

After an incorrect attempt, the learner can retry and open two authored hints.
After two incorrect attempts, Give up unlocks the authored worked solution. A
future tutor can explain the same reviewed solution conversationally, but it must
not decide marks or receive a locked answer before the server authorises it.

## Implemented

- FastAPI practice-session creation, resume, next-question, attempt, hint and
  Give-up endpoints.
- Required idempotency keys for session creation and attempt submission.
- Selection restricted to the configured lesson pool in guided, independent and
  challenge order.
- Revision-pinned questions and SQLite persistence across browser refreshes.
- Learner-safe question responses without canonical answers or solutions.
- Numeric, algebraic and multipart answer forms; each part is marked on the
  backend.
- Two-stage hint ordering and two-incorrect-attempt solution lock.
- Development-only access to draft questions. Draft practice fails closed when
  `ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT=false`.
- A Next.js `/practice/[sessionId]` player with KaTeX rendering.
- A draft-practice entry from the blank Lesson 1 shell.
- Generated OpenAPI types used by the frontend.
- Local database configuration through
  `ASEAN_ACADEMY_PRACTICE_DATABASE`.

## Local verification

Terminal 1:

```bash
cd /home/william/asean_academy
ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT=true \
ASEAN_ACADEMY_PRACTICE_DATABASE=/home/william/asean_academy/.local/practice.sqlite3 \
corepack pnpm dev:api
```

Terminal 2:

```bash
cd /home/william/asean_academy
corepack pnpm dev:web
```

Open `http://localhost:3000/lessons/n1-lesson-01`, then select **Start draft
practice**.

The draft label is intentional. The current questions and lesson content have not
passed academic review and cannot be exposed when draft preview is disabled.

## Verification completed

- Learning API: 19 tests.
- Question bank: 28 tests.
- Frontend: 5 tests.
- Python lint, ESLint and strict TypeScript passed.
- Next.js production build passed.
- Live Next.js proxy smoke test passed for lesson load, practice page, session
  creation, question resume, Hint 1, two incorrect attempts and solution unlock.
- The smoke response contained no private answer before unlock.

## Next technical milestone

Add a learner-progress repository interface and local SQLite adapter for lesson
start, practice completion, proficiency and recommended next action. This remains
independent of video production and question review. PostgreSQL and Supabase Auth
can later implement the same repository contract.
