# Milestone 2 — Lesson 1 pilot shell and content handoff

**Branch:** `feature/milestone-2-pilot-shell`

**Plan mapping:** PLAN V2 Stage 2 is already complete in branch history. This
milestone starts Stage 3 while keeping unfinished lesson material out of Git.

## Goal

Create a safe path from course map to lesson to guided practice. Application work
must continue while the Lesson 1 video and teaching sections are produced, but no
empty or unreviewed content may appear to a real student.

## Implemented setup

- `GET /api/v1/courses/{courseKey}/map` returns the validated N1 course map.
- `GET /api/v1/lessons/{lessonKey}` returns student-safe lesson metadata,
  objectives, sections, assets, and planned practice entry.
- Draft content is available only when `ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT=true`.
- With draft preview disabled, the current draft course returns a safe 404.
- `/learn` and `/courses/[courseKey]` render the seven-lesson course map.
- `/lessons/[lessonKey]` renders objectives and an honest material-pending state.
- Guided practice displays its allocated question count but remains disabled.
- Fixture mode implements the same generated OpenAPI types used by the live API.
- Large video formats are ignored by Git to prevent accidental repository uploads.

## Why practice remains locked

The Lesson 1 shell has no reviewed sections, and its three allocated questions are
still drafts. Opening practice now would undermine the publication rules. The
application therefore exposes the intended practice entry without making it
clickable. Local question checking can still be exercised through the existing
question-bank development practice tool.

## Remaining work, in order

### M2-01 — Decide video delivery and add the neutral video contract

**Can start:** after the hosting choice below

Define lesson-video metadata, caption tracks, transcript, poster image, duration,
and provider playback reference. Add PostgreSQL storage and the frontend player
boundary. Do not put video binaries in Git.

**Acceptance**

- One metadata shape works for local/preview and the selected managed host.
- Captions and transcript are required before publication.
- The browser never receives a private storage credential.

### M2-02 — Complete the production practice API boundary

**Can start immediately; independent of videos**

- Move existing tested practice behaviour behind FastAPI.
- Accept `lesson_key`, `mode`, `question_count`, and an idempotency key.
- Restrict selection to the configured lesson pool.
- Keep answers and solutions private until server-authorised.
- Preserve refresh/resume, two-error Give up, hints, and deterministic marking.
- Use a local SQLite learner adapter first; PostgreSQL/auth remains Stage 4.

**Acceptance**

- A development learner starts Lesson 1 practice and receives only its three
  allocated questions.
- Refresh resumes the assigned revision and question order.
- OpenAPI-generated frontend types compile.

### M2-03 — Add local lesson progress and next action

**Can start after M2-02**

Record lesson start, section completion, practice result, proficiency and the next
recommended action through a repository interface. SQLite is the local adapter;
the later PostgreSQL adapter must pass the same behavioural tests.

### M2-04 — Deliver Lesson 1 material

**Depends on the founder's material and reviewers**

Add the approved video metadata, accessible transcript, explanations, worked
examples, active-recall check, and summary. Increment the lesson revision when
learner-visible content changes.

### M2-05 — Review Outcome 1.1 questions

**Depends on Mathematics/editorial reviewers**

Review the six Outcome 1.1 questions. Lesson practice uses three; two are reserved
for the checkpoint and one for adaptive practice. Check Mathematics, language,
marks, difficulty, hints, solution agreement and rendering.

### M2-06 — Publish and exercise the local vertical slice

After M2-02 through M2-05, publish only the approved Lesson 1 and question
revisions, then verify lesson → practice → proficiency → next action. The course
can remain a limited pilot until Lessons 2–7 are ready.

## Inputs needed

1. **Video host:** managed streaming service, unlisted external video, or private
   object storage. Managed streaming is recommended for adaptive playback and
   simpler browser support.
2. **Video access:** public/unlisted for the pilot, or authenticated students only.
3. **Accessibility:** confirm English captions and a text transcript for every
   lesson video. This is the recommended default.
4. **Review ownership:** name the Mathematics reviewer and editorial reviewer.
5. **Progression:** confirm the existing 70% lesson/checkpoint thresholds and the
   recommended soft lesson order.

Only the video contract and publication are blocked by these answers. Practice API
and local progress work can continue independently.
