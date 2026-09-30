# B4 frontend kit integration audit

**Source:** `origin/feature/beta-frontend-kit` commit `e04a142` by `alvarovw`  
**Integrated onto:** B3 commit `2707d44` on `integration/b3-beta-frontend`  
**Audit date:** 29 September 2026

## Result

The frontend kit is valid React/Next.js code and can be used as the visual implementation for B4. It was additive: no existing page, API client, authentication flow or backend file was overwritten. The actual frontend commit was cherry-picked onto B3 because the source branch was based on older history containing a duplicate roadmap commit.

The kit supplies 69 responsive, props-driven review states under `/beta-kit`. B4.1 through B4.5 now connect the public entry, authentication, onboarding, learning home, course map, lesson, practice, retry, checkpoint, progress and diagnostic journeys to live authenticated APIs. These routes deliberately omit sample-only XP, league, quests, streaks and rewards. The administrator routes still use the earlier technical UI until their B4 integration step is completed.

## Verified behavior

- ESLint and TypeScript pass against the B3 generated API contract.
- All 37 web tests pass, including the kit adapters and production route gate.
- The production Next.js build succeeds and prerenders 69 screen routes plus comparison routes.
- Development HTTP smoke checks returned `200` for the kit index, dashboard, lesson, practice, checkpoint and loading screens.
- In an unflagged production build, `/beta-kit` returns a true non-cacheable `404` and `/` remains available.
- The current API-contract drift in the adapter test was repaired by adding B2's required `unlocked` and `retry_question_count` fields to its fixture.

## B4.1 live integration (30 September 2026)

- `/learn` uses the authenticated learner's active enrolment instead of a hard-coded course.
- `/courses/[courseKey]` displays API-owned lesson locks, progress and checkpoint state.
- Both pages fetch through the server-side Learning API using the verified Supabase access token; they do not query learning tables directly.
- Known API failures render a safe retry state with the request ID retained for support.
- `ASEAN_ACADEMY_BETA_LEARNING_UI=true` enables these screens in production. Development defaults on; `false` immediately restores the established technical pages.
- Route loading states, mobile navigation and desktop navigation are included. Unsupported gamification remains absent.
- The next B4 slice is lesson and guided-practice visual integration while preserving their existing server-owned state machines.

## B4.2 lesson and guided-practice integration (30 September 2026)

- `/lessons/[lessonKey]` now uses the final responsive shell and component tokens while preserving lesson-start recording, section completion and deterministic active-recall checks.
- Real lesson notes, KaTeX content, objectives, development status and empty video/material placeholders are shown without invented teaching content.
- Starting guided practice still creates the server-owned session with the reviewed question count and follows the returned session ID.
- `/practice/[sessionId]` retains the existing API state machine for selection, multipart typed answers, marking, Hint 1/Hint 2 sequencing, retry, Give up, worked solution, completion and question reporting.
- Checkpoint mode suppresses hints and solutions in the shared live view; the dedicated checkpoint route remains on the technical shell until the next route-integration slice.
- The live views do not display sample XP, stars, streak, quest or league values.
- The same server-only B4 rollout flag restores the established lesson and practice screens immediately.
- Validation now passes 45 web tests, ESLint, TypeScript and the production Next.js build.
- The public `/` route now uses an honest NextScholar landing page with supported beta features only; sample reward claims were removed.
- The next B4 slice is checkpoint/retry/progress visual integration, followed by authentication/onboarding and administrator surfaces.

## B4.3 checkpoint, retry and progress integration (30 September 2026)

- `/progress` now renders real proficiency, question outcomes, unresolved retry counts, scheduled-review timing and checkpoint states through the final responsive component system.
- A learner can start a server-owned `retry_review` session from a lesson with unresolved questions and continue it through the shared practice state machine.
- Checkpoint actions preserve their distinct semantics: an active attempt resumes its existing session, while a failed completed attempt creates a fresh retake session.
- `/checkpoints/[sessionId]` now uses the final focused practice presentation. Checkpoint mode continues to suppress hints, Give up and worked solutions.
- Retry selection, the five-question daily cap, checkpoint availability, scoring and mastery remain enforced by the Learning API.
- Browser extensions such as Grammarly can inject attributes into the document body before React starts; the root body now suppresses that expected attribute-only hydration warning.
- The rollout flag continues to restore the established progress and checkpoint screens without changing API state.
- Validation passes 49 web tests, ESLint, TypeScript and the production Next.js build.
- The next B4 slice is authentication/onboarding visual integration, then diagnostic and administrator surfaces.

## B4.4 Google sign-in and invitation onboarding integration (30 September 2026)

- `/login` now uses the final responsive NextScholar presentation while continuing to invoke the existing server-only Google OAuth action.
- Login errors remain mapped to safe messages, and the validated destination is preserved through OAuth-start and callback failures so invitation links can be retried without losing their code.
- `/onboarding?code=...` now preserves the invitation code when an unauthenticated visitor is sent through Google sign-in.
- The onboarding form still calls the same invitation-acceptance API, displays backend errors with request IDs, creates no client-owned enrolment state and proceeds to the readiness check only after acceptance.
- Existing redirects remain authoritative: academic/content administrators enter `/admin`, already-enrolled students enter `/learn`, and unverified sessions return to `/login`.
- Account switching uses the existing POST sign-out route. The live screens expose no unsupported track picker, XP, streak, league, badge or starter-pack claims.
- Missing Supabase configuration has a dedicated unavailable state instead of an active sign-in control.
- The rollout flag restores the established login and onboarding views without changing cookies, identities or enrolments.
- Validation passes 54 web tests, ESLint, TypeScript and the production Next.js build. Authenticated Playwright remains environment-gated by `E2E_DATABASE_URL`.
- The next B4 slice is diagnostic visual integration, followed by administrator surfaces and final responsive/accessibility acceptance.

## B4.5 readiness diagnostic integration (30 September 2026)

- `/diagnostics`, `/diagnostics/[sessionId]` and `/diagnostics/[sessionId]/result` now use the responsive NextScholar learner shell and component system.
- The presentation reuses the B1 diagnostic controller and generated OpenAPI types. Form choice, session state, immutable question revisions, autosave, deterministic scoring, bands and outcome evidence remain owned by the Learning API.
- The player restores saved answers, supports numeric and algebraic multipart fields, autosaves only after every part of the current question is complete, blocks incomplete final submission and withholds correctness until submission.
- Start, resume, completed-result and `content_pending` states come directly from `GET /api/v1/diagnostics/next`. The interface does not claim that the planned 19-topic, 76-item production forms are published.
- Results show API-owned weighted marks, percentages, bands, strengths and priorities as learning evidence. No client-computed mastery, XP, streak, league or reward data was added.
- Loading and failure states, keyboard focus, semantic labels, KaTeX content and mobile/desktop navigation use the shared B4 patterns.
- `ASEAN_ACADEMY_BETA_LEARNING_UI=false` immediately restores all three established diagnostic pages without changing session data.
- Regression coverage includes content-pending fallback, API-selected start, multipart completeness, delayed autosave, submission routing and supportive results. Validation passes 56 web tests, ESLint, TypeScript and the production Next.js build.
- Authenticated Playwright remains environment-gated by `E2E_DATABASE_URL`. The next B4 slice is administrator visual integration, followed by the final responsive/accessibility and authenticated-journey acceptance pass.

## What can be wired now

| Area                 | Existing source of truth                                            | B4 work                                                                                                   |
| -------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Landing and sign-in  | Supabase server actions and `/login` errors                         | Integrated in B4.4 with safe error and destination handling                                               |
| Onboarding           | Invitation-bound profile/enrolment API                              | Integrated in B4.4 without a client-owned track decision                                                  |
| Dashboard/course map | Learning-home, course-map and progress APIs                         | Use the supplied adapters and replace sample player/game data with absent states                          |
| Lesson               | Versioned lesson response and section progress                      | Render real `MathContent`, material states and progress through kit slots/wrappers                        |
| Guided practice      | Existing practice player, deterministic checking, hints and Give up | Keep the state machine and render kit screens for each server state                                       |
| Spaced retry         | B2 scheduling, selection, counts and next-due data                  | Wire available states; add a grouped list endpoint only if the exact ready/later/cleared view is required |
| Checkpoint           | B2 checkpoint-mode practice and mastery                             | Replace current checkpoint visuals; keep server-owned rules and answer locking                            |
| Question report      | B2 learner/admin report APIs                                        | Connect the report sheet and admin inbox                                                                  |
| Diagnostic           | B1 APIs and technical pages                                         | Integrated in B4.5 across next/start/resume/player/result states; production forms remain a content gate  |
| Account deletion     | B3 academic-admin preview/execute workflow                          | Build an admin confirmation UI; do not connect the learner settings sheet to this privileged endpoint     |
| Errors/loading       | Standard API code/request ID and route states                       | Map error codes without hiding request IDs needed for support                                             |

## Sample-only or deferred data

Player XP, quests, streaks/freezes, badges, wardrobe, league, celebrations, recheck, English and most game settings are sample data. Their screens compile, but the current Beta backend does not provide those models. The execution plan places broad gamification and English after the core Beta unless scope is explicitly changed.

These fields must never be calculated authoritatively in the browser. If selected for Beta, add append-only server evidence, idempotent award rules, learner-time-zone behavior, abuse controls, admin visibility and tests before exposing them as real progress.

## Recommended integration order

1. Keep `/beta-kit` as the visual review gallery and freeze component prop changes while route wiring begins.
2. Integrate the public landing, Google sign-in and onboarding routes.
3. Integrate `/learn`, course map and lesson screens with real API data, showing honest unavailable states for missing game data.
4. Reuse the existing practice state machine with the new practice components.
5. Integrate retry, checkpoint and question-report states already supported by B2.
6. Integrate the diagnostic journey with the shared component system while keeping B1 session and scoring rules server-owned. Completed in B4.5.
7. Integrate progress and administrator views; the submitted kit primarily covers student screens, so the admin UI still needs B4 design work.
8. Run authenticated E2E, keyboard/screen-reader checks and screenshots at 390, 768 and 1440 pixels before replacing the technical shell.

## Merge boundary

Backend migrations, scoring, access control, retry policy, checkpoint rules, deletion and audit remain owned by the Learning API. Frontend components may display those states but must consume the generated OpenAPI types and same-origin API proxy rather than duplicate rules or access Supabase learning tables directly.
