# B4 frontend kit integration audit

**Source:** `origin/feature/beta-frontend-kit` commit `e04a142` by `alvarovw`  
**Integrated onto:** B3 commit `2707d44` on `integration/b3-beta-frontend`  
**Audit date:** 29 September 2026

## Result

The frontend kit is valid React/Next.js code and can be used as the visual implementation for B4. It was additive: no existing page, API client, authentication flow or backend file was overwritten. The actual frontend commit was cherry-picked onto B3 because the source branch was based on older history containing a duplicate roadmap commit.

The kit supplies 69 responsive, props-driven review states under `/beta-kit`. B4.1 has now connected `/learn` and `/courses/[courseKey]` to live authenticated learning-home, course-map and progress responses. These two routes deliberately omit sample-only XP, league, quests, streaks and rewards. Other production routes such as `/lessons/*`, `/practice/*`, `/checkpoints/*`, `/diagnostics/*` and `/progress` still render the earlier technical UI until their B4 integration steps are completed.

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

## What can be wired now

| Area | Existing source of truth | B4 work |
| --- | --- | --- |
| Landing and sign-in | Supabase server actions and `/login` errors | Replace visuals while preserving callback/session behavior |
| Onboarding | Invitation-bound profile/enrolment API | Bind the kit form to the existing action; do not add a client-owned track decision |
| Dashboard/course map | Learning-home, course-map and progress APIs | Use the supplied adapters and replace sample player/game data with absent states |
| Lesson | Versioned lesson response and section progress | Render real `MathContent`, material states and progress through kit slots/wrappers |
| Guided practice | Existing practice player, deterministic checking, hints and Give up | Keep the state machine and render kit screens for each server state |
| Spaced retry | B2 scheduling, selection, counts and next-due data | Wire available states; add a grouped list endpoint only if the exact ready/later/cleared view is required |
| Checkpoint | B2 checkpoint-mode practice and mastery | Replace current checkpoint visuals; keep server-owned rules and answer locking |
| Question report | B2 learner/admin report APIs | Connect the report sheet and admin inbox |
| Diagnostic | B1 APIs and technical pages | A design is missing from this kit; retain the technical UI until an approved replacement exists |
| Account deletion | B3 academic-admin preview/execute workflow | Build an admin confirmation UI; do not connect the learner settings sheet to this privileged endpoint |
| Errors/loading | Standard API code/request ID and route states | Map error codes without hiding request IDs needed for support |

## Sample-only or deferred data

Player XP, quests, streaks/freezes, badges, wardrobe, league, celebrations, recheck, English and most game settings are sample data. Their screens compile, but the current Beta backend does not provide those models. The execution plan places broad gamification and English after the core Beta unless scope is explicitly changed.

These fields must never be calculated authoritatively in the browser. If selected for Beta, add append-only server evidence, idempotent award rules, learner-time-zone behavior, abuse controls, admin visibility and tests before exposing them as real progress.

## Recommended integration order

1. Keep `/beta-kit` as the visual review gallery and freeze component prop changes while route wiring begins.
2. Integrate the public landing, Google sign-in and onboarding routes.
3. Integrate `/learn`, course map and lesson screens with real API data, showing honest unavailable states for missing game data.
4. Reuse the existing practice state machine with the new practice components.
5. Integrate retry, checkpoint and question-report states already supported by B2.
6. Create or obtain the missing diagnostic design and preserve the current diagnostic routes until it is accepted.
7. Integrate progress and administrator views; the submitted kit primarily covers student screens, so the admin UI still needs B4 design work.
8. Run authenticated E2E, keyboard/screen-reader checks and screenshots at 390, 768 and 1440 pixels before replacing the technical shell.

## Merge boundary

Backend migrations, scoring, access control, retry policy, checkpoint rules, deletion and audit remain owned by the Learning API. Frontend components may display those states but must consume the generated OpenAPI types and same-origin API proxy rather than duplicate rules or access Supabase learning tables directly.
