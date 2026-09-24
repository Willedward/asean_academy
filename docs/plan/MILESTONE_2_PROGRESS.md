# Milestone 2 — Local learner progress and next action

**Branch:** `feature/milestone-2-progress`

**Parent:** `feature/milestone-2-answer-practice`

**Plan mapping:** PLAN V2 M2-03 and the progress portion of Stage 3.

## Goal

Make the answer-only practice flow resumable and meaningful to a learner without
requiring reviewed lesson media, production authentication or PostgreSQL. The
local adapter must establish the behaviour that later authenticated adapters
preserve.

## Implemented

- A `ProgressRepository` boundary and `SQLiteProgressRepository` local adapter.
- A development learner enabled only in development and test environments.
- Idempotent lesson start.
- Practice-session ownership and automatic progress synchronization.
- Existing active sessions resume instead of creating duplicates.
- Course-map states:
  - `not_started`
  - `in_progress`
  - `practice_completed`
  - `proficient`
  - `mastered`
- Configured 70% proficiency threshold read from the course policy.
- Give up prevents proficiency for that completed practice run.
- A later successful retry can promote the lesson to proficient.
- Mastery remains unavailable until the required unit checkpoint passes.
- Server-generated recommended next actions for start, resume, retry, next
  content and pending checkpoint states.
- Course-map progress overlay, learning-home recommendation and `/progress`
  dashboard.
- A blank lesson records its start, and practice completion links directly to
  the progress screen.
- Learner progress fails closed when no development or authenticated learner
  identity exists.

## API

```text
POST /api/v1/lessons/{lessonKey}/start
GET  /api/v1/progress
GET  /api/v1/learning-home
```

Existing practice endpoints now synchronize the progress repository after
question assignment, answer submission, Give up and session completion.

## Persistence

The local practice and progress data share the configured SQLite file:

```text
ASEAN_ACADEMY_PRACTICE_DATABASE=.local/practice.sqlite3
```

New local tables:

- `learner_lesson_progress`
- `learner_practice_sessions`

The tables are an adapter detail. Callers depend on the repository interface so
a PostgreSQL implementation can replace SQLite without moving progression rules
into the frontend.

## Behaviour rules

- Opening a lesson records `in_progress`.
- Starting practice also starts the lesson and links the session.
- An active practice session is the recommended next action.
- A completed run meeting the configured percentage with no Give up result is
  `proficient`.
- A completed run below policy or containing Give up is
  `practice_completed`, with retry recommended.
- Proficiency does not equal mastery. The course policy requires the unit
  checkpoint, which is not yet published.

## Local use

Terminal 1:

```bash
cd /home/william/asean_academy
corepack pnpm dev:api
```

Terminal 2:

```bash
cd /home/william/asean_academy
corepack pnpm dev:web
```

Open `http://localhost:3000/learn`. The dashboard shows the server-recommended
next action. Open Lesson 1, complete or Give up its practice, then inspect
`http://localhost:3000/progress`.

Delete the local SQLite file only when intentionally resetting development
progress. It is ignored by Git.

## Next technical milestone

Implement Supabase identity and a PostgreSQL repository adapter with Row Level
Security. Run the same behavioural suite against both SQLite and PostgreSQL, then
deploy an authenticated preview. A provider-neutral tutor scaffold can proceed
after answer-lock context is exposed, but a live tutor remains disabled until its
lesson and solution grounding has been reviewed.
