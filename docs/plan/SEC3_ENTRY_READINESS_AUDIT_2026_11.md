# Sec 3-entry readiness audit (November 2026)

**Date:** 2 November 2026
**Audited commit:** `4645796` (`origin/feature/bulk-question-authoring-pipeline`)
**Product focus:** the Sec 3-entry scholarship track. One learner studies Secondary 1 and
Secondary 2 Mathematics together, using `g3-sec1-math` and `g3-sec2-math`.
**Plans compared:** `ROADMAP_BETA_V2_V3.md`, `BETA_V2_V3_TECHNICAL_EXECUTION.md`,
`B5_CONTENT_RELEASE_CONTROLLED_PILOT.md` and `FULL_SEC1_SEC2_COURSE_REGISTRY.md`.

**Evidence boundary.** This audit uses only the repository: source, migrations, tests,
Git-authored content, and commands run locally against that content. No hosted environment,
database or provider was contacted. Review decisions stored in a hosted database are not
visible to this audit. Nothing is marked complete without repository evidence. Older plans
assume a Sec 1-only Beta. This audit treats that as an assumption to check, not a
requirement.

No product code, content or migration was changed.

## 1. Verdict

The two courses are **authored**, but they are **not yet one learnable product**.

- Content and structure exist. The registry validates 2 courses, 19 topic groups and
  87 lessons. Both course snapshots validate. Together they hold 1,976 learning questions
  and 76 diagnostic items.
- The learner runtime is still built around one course. Lesson start, practice, checkpoints,
  progress and the learning home all read a single "legacy" course: `g3-sec1-math`. They
  return `404` or `422` for Secondary 2 lessons and units. Lesson-start and section endpoints
  also reject 45 of the 52 Secondary 1 lessons, because their path pattern allows only N1
  keys.
- Deployment imports only `g3-sec1-math` into PostgreSQL. A Secondary 2 invitation therefore
  cannot be created on a hosted database built by the current workflows.
- `beta_release_gate.py` evaluates only `g3-sec1-math`. It cannot pass for either course
  alone, and as written it also cannot pass for the pair.
- No Mathematics content is published. Apart from Secondary 1 N2, nothing has recorded
  human approval in the repository.

## 2. Answers to the audit questions

### 2.1 Can one learner enrol in and progress through both courses?

**Enrolment: partly.** The schema allows several enrolments per learner, but each
invitation assigns exactly one course.

| Aspect | Evidence | Finding |
| --- | --- | --- |
| Enrolment table | `supabase/migrations/202609240004_identity_progress_rls.sql:37-47`: `course_enrolments` primary key `(student_id, course_id)` | A learner can hold one enrolment per course, so two courses are possible |
| Invitation shape | Same migration `:23-35`: `beta_invitations.course_version_id` is a single non-null column | One invitation equals one course revision |
| Acceptance | `services/learning_api/src/learning_api/identity_repository.py:136-199` | Accepting adds an enrolment for the invitation's course only. A second invitation for the other course would add a second enrolment |
| Admin creation | `admin_contracts.py:19` defaults `course_key` to `g3-sec1-math`. `apps/web/src/components/admin-invitations-panel.tsx:157` sends `"g3-sec1-math"` with no course selector. `scripts/create_invitation.py:18` has the same default | Operators can invite to Secondary 1 only through the UI. The API and CLI accept another `course_key`, but only if that course is imported (see 2.3) |
| Second invitation in the UI | `apps/web/src/app/onboarding/page.tsx:177` redirects any learner with an active enrolment to `/learn` | A learner who already has one course cannot accept a second invitation through the web app |
| Track | `identity_repository.py:172-184` stores the first invitation's course key as `profiles.target_track`. `coalesce` keeps the first value. The track picker exists only in design-kit previews (`apps/web/src/beta-kit/preview/entry.tsx:12-22`). `AcceptInvitationRequest` has no track field (`beta-kit/screens/entry.tsx:263`) | "Sec 3 entry" is not modelled. The track is whichever course was invited first |
| Web course choice | `apps/web/src/app/(learner)/learn/page.tsx:24` falls back to a hard-coded `g3-sec1-math` map. Learner pages pick the **first** active enrolment (`learn/page.tsx:37`, plus the same pattern in `lessons`, `practice`, `progress`, `checkpoints`, `diagnostics` and `english` pages) | A learner with two enrolments sees only one course |

**Progression: Secondary 1 only, and only partly within Secondary 1.** This was checked
locally with the test application from `services/learning_api/tests/test_practice.py`
(SQLite, drafts enabled):

| Request | Result |
| --- | --- |
| `POST /api/v1/practice-sessions` for `n1-lesson-01`, `n2-lesson-01`, `s1-lesson-01` | `201` |
| `POST /api/v1/practice-sessions` for `g2-lesson-01`, `n2-lesson-04` (Secondary 2) | `404 lesson_not_found` |
| Checkpoint session for unit `g3-sec2-g2` | `404 unit_not_found` |
| Checkpoint session for unit `g3-sec1-n2` | `409 checkpoint_locked`. This is the expected policy response |
| `POST /api/v1/lessons/{key}/start` for `n2-lesson-01`, `s1-lesson-01`, `g2-lesson-01` | `422 validation_error` |
| `GET /api/v1/courses/g3-sec2-math/map` | `200`, but no progress is applied |
| `GET /api/v1/progress` | Always reports `course_key: g3-sec1-math` |

Causes:

- `course_catalogue.py:85-95`: `CourseCatalogue.report` returns only
  `reports["g3-sec1-math"]`. `catalogue.questions` contains only that course's 1,040
  questions.
- `progress_service.py:26, 33, 46-90, 132, 416, 569` and `practice_service.py:26, 79, 115,
  225-226, 272, 307-308` resolve lessons, units, pools, mastery policy and session
  `course_key` from that single report.
- `progress_service.py:569`: `apply_to_course_map` returns other courses unchanged, so the
  Secondary 2 map never shows progress or checkpoint availability. It keeps the catalogue
  default `checkpoint_available=False` (`course_catalogue.py:352`).
- `routers/progress.py:46, 60, 74, 96` restrict lesson start, section progress, section
  completion and active recall to `^n1-lesson-[0-9]{2}$`. The practice contract already
  accepts `^[ngs][0-9]+-lesson-[0-9]{2,3}$` (`practice_contracts.py:17`). The web lesson panel
  calls lesson start on every lesson open and shows a progress warning when it fails
  (`apps/web/src/components/lesson-panel.tsx:60-75`).
- `postgres_practice.py:300-308` checks that the learner is enrolled in the session's
  `course_key`. That key is always `g3-sec1-math`, so a learner enrolled only in
  Secondary 2 cannot practise anything.
- No test covers Secondary 2 practice, lesson progress, checkpoints or progress. Secondary 2
  is tested only through the read-only map, lessons and assets
  (`tests/test_courses.py:200-335`). Authenticated E2E seeds only `g3-sec1-math`
  (`scripts/seed_e2e.py:63`, `apps/web/e2e/beta-journeys.spec.ts`).

### 2.2 Do the diagnostics cover both years? How many published forms exist?

**Authored coverage: yes, both years.** `backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json`
defines `g3-sec1-2-math-readiness-v1` (status `draft`) with two forms:

| Form | Items | Secondary 1 items | Secondary 2 items | Topic groups | Items per group |
| --- | ---: | ---: | ---: | ---: | ---: |
| `g3-sec1-2-math-baseline-v1` r1 | 38 | 20 | 18 | 19 | 2 |
| `g3-sec1-2-math-endline-v1` r1 | 38 | 20 | 18 | 19 | 2 |

`question-bank diagnostic-plan-validate` passes: 2 forms, 76 questions, 0 errors.
The 76 items sit in 19 `v2` diagnostic banks: 40 for Secondary 1 and 36 for Secondary 2.
All are `draft`. All 19 diagnostic batch manifests are `ready_for_review`, with Mathematics
and editorial review `pending`.

**Published forms: 0 for Secondary 1 and 0 for Secondary 2.** The repository has no path
to publish them:

- No importer writes `diagnostic_forms` or `diagnostic_form_items`. These tables are
  populated only in `tests/test_diagnostics_postgres.py:146, 166, 284, 300`. The
  `question-bank` CLI can create and validate the plan, but cannot import it
  (`question_bank/src/question_bank/cli.py:302-330, 747-764`).
- A form belongs to exactly one course revision.
  `supabase/migrations/202609290012_n1_diagnostics.sql:11` sets
  `course_version_id not null`, and `:31-33` allows one current published form per purpose
  per course version. Sessions use the same key (`:46-71`).
- `diagnostic_repository.py:128-140` uses the learner's **most recently** enrolled active
  course. `:150-163` looks for forms on that course revision. `:185-198` unlocks the endline
  only after every lesson in **that one course** is mastered. A learner enrolled in both
  courses would get diagnostics for whichever course was enrolled last. Enrolling in the
  second course later would open a second, separate baseline.
- Scoring and recommendations already work across both years.
  `diagnostic_repository.py:66-118` maps each outcome to the course of the same school level.
  `tests/test_diagnostics.py:119-128` shows a Secondary 2 lesson (`g2-lesson-01`) being
  recommended. Because of 2.1, that lesson cannot be practised yet.

### 2.3 Can `beta_release_gate.py` and the content-release checks validate both courses as one candidate?

**No.** Running `source_checks` locally against the current catalogue gives:

| Check | Result | Measured |
| --- | --- | --- |
| `source.full_syllabus` | BLOCK | 10 topic codes, 19 required |
| `source.question_volume` | BLOCK | 1,040 questions, 1,900 required |
| `source.publication_status` | BLOCK | course `draft`; 0/52 lessons and 0/1,040 questions published |
| `source.lesson_materials` | PASS | 52/52 lessons meet the note-depth gate |
| `source.pool_inventory` | PASS | 622 practice, 196 checkpoint, 222 reserve |
| `source.checkpoint_reserve_capacity` | PASS | |

Structural reasons:

1. `beta_release.py:67-73, 183-190` reads only `catalogue.report`, which is Secondary 1.
   The evidence snapshot records one `course_key`, one revision and one content hash.
2. `beta_release.py:74` counts unique `topic_code` values. If both courses were included,
   N2, N5, N6, N7, G5 and S1 would each be counted once. The maximum would be **13**, so the
   19-topic-group floor could never pass. The level-specific unit key (`g3-sec1-n2`,
   `g3-sec2-n2`) is the correct identity.
3. `beta_release.py:281` expects approvals for `1 + 52 + 1,040` items. However,
   `verify_release_workflow` (`content_review.py:1142-1170`) counts every non-draft item in
   **all** reports, plus English and tutor-grounding items (`content_review.py:188-237`).
   Once any Secondary 2, diagnostic or English item becomes non-draft, the counts no longer
   match.
4. `beta_release.py:294-345` looks for diagnostic forms and pool overlap only on
   `g3-sec1-math`. Secondary 2 pools are never checked for overlap with the diagnostics.
5. `content_sync.check_content` (`content_sync.py:16-26, 93-101`) compares only Secondary 1
   course, lesson and question hashes with PostgreSQL.
6. Import paths cover one course:
   - `question-bank course-import-db` defaults to the Secondary 1 snapshot
     (`question_bank/cli.py:58-61, 150`).
   - CI runs it without a path (`.github/workflows/ci.yml:180, 234`), and so do staging
     (`deploy-staging.yml:150`) and production (`deploy-production.yml:121`).
   - `bootstrap_local.py:53, 83, 110` imports only `catalogue.report`.

`verify_content_release.py` (production deploy) already covers both courses, because it
iterates every catalogue item. It **skips `draft` items** (`content_review.py:1147`), so
today it passes without checking anything.

### 2.4 Hard-coded course keys and Sec 1-only assumptions

| Location | Assumption | Effect on Sec 3-entry |
| --- | --- | --- |
| `services/learning_api/src/learning_api/course_catalogue.py:28, 85-95` | `COURSE_ROOT` and `report` fixed to `g3-sec1-math` | Every legacy consumer sees one course |
| `progress_service.py` (see 2.1) | Single-course progress, units, retries and mastery policy | No Secondary 2 progress |
| `practice_service.py` (see 2.1) | Single-course pools and session `course_key` | No Secondary 2 practice or checkpoints |
| `routers/progress.py:46, 60, 74, 96` | `^n1-lesson-[0-9]{2}$` | Lesson start and sections fail for 45 Secondary 1 and all 35 Secondary 2 lessons |
| `beta_release.py:67-74, 281, 294-345` | One course; topic identity by code | Gate cannot pass for the pair |
| `content_sync.py:17` | One course | DB hash check ignores Secondary 2 |
| `scripts/bootstrap_local.py:53, 83, 110`; `question_bank/cli.py:58-61`; CI and deploy workflows | Import the Secondary 1 snapshot only | Secondary 2 never reaches PostgreSQL. Invitations to it fail with "course not found" |
| `admin_contracts.py:19`; `scripts/create_invitation.py:18`; `apps/web/src/components/admin-invitations-panel.tsx:157` | Default or fixed `g3-sec1-math` | Operators cannot choose a course in the UI |
| `routers/admin_analytics.py:165-167` | Curriculum preview compares any `course_key` with the Secondary 1 revision | Secondary 2 migration previews would target the wrong revision (21 instead of 11) |
| `apps/web/src/app/(learner)/learn/page.tsx:24, 37` and sibling learner pages | Fallback `g3-sec1-math`; first active enrolment only | Second course hidden |
| `apps/web/src/app/onboarding/page.tsx:177` | Any enrolment ends onboarding | Second invitation cannot be accepted in the UI |
| `identity_repository.py:172-184` | `target_track` = first course key | No Sec 3-entry track |
| `diagnostic_repository.py:128-198`; migration `202609290012:11, 31-33` | One course revision per form and session | Cross-year forms need an anchor course |
| `postgres_practice.py:50`; `question_bank/practice.py:131` | Default bank `g3-sec1-n1-v1` | Low impact; empty-session fallback only |
| `scripts/seed_e2e.py:63`; `scripts/export_frontend_fixtures.py:21` | Secondary 1 only | E2E and fixtures never exercise Secondary 2 |
| `question_bank/src/question_bank/english_models.py:182`; `backend_resources/english/v1/exam_profiles/asean-english-sec1-id-reported-v1.json`; forms `english-{baseline,endline}-sec1-id-v1` | English exam profile limited to `secondary_1_entry` | English Layer 1 targets the Sec 1-entry test. Whether it fits Sec 3 entry is a product decision outside this audit |

Level-specific patterns such as `^g3-sec[12]-…` in `question_bank` models and the registry
are correct for two courses. They are not problems.

### 2.5 How much content still needs human review before publication?

Production refuses draft content (`config.py:348`), and the gate requires every revision to
be published (`beta_release.py:108-112`). Both courses therefore need Mathematics review,
editorial review and an audited publication request for every item. Repository state:

| Scope | Course record | Lessons | Learning questions | Diagnostic items | Recorded approval in repo |
| --- | ---: | ---: | ---: | ---: | --- |
| `g3-sec1-math` (r21) | 1 draft | 52 (49 draft, 3 `reviewed`) | 1,040 draft | 40 draft | N2: 4 batches (104 questions) `approved` for Mathematics and editorial; `n2-lesson-01`–`03` `reviewed` |
| `g3-sec2-math` (r11) | 1 draft | 35 draft | 936 draft | 36 draft | None |
| **Total** | **2** | **87** | **1,976** | **76** | |

- **Still needing a first human review:** Secondary 1 has 936 questions, 49 lessons,
  1 course record and 40 diagnostic items (**1,026**). Secondary 2 has 936 questions,
  35 lessons, 1 course record and 36 diagnostic items (**1,008**). Together: **2,034**
  Mathematics items.
- **Approved but still unpublished:** 104 Secondary 1 N2 questions and 3 lessons. The
  question files remain `draft`, so these 107 items still need a source status change and
  publication requests.
- 40 of the 104 Secondary 1 N1 questions (`n1-l1-01`… the original pilot) are not in any batch
  manifest. They can be reviewed through a unit session, but not a batch session.
- Technical pre-review audits exist for 9 of the 19 topic groups:
  - Secondary 1: N1, N2, N3, N6, N7.
  - Secondary 2: G4, G5, N2, N5.

  None exists for:
  - Secondary 1: N4, N5, G1, G5, S1.
  - Secondary 2: G2, N6, N7, S1, S2.
  - The 76 diagnostic items. The G5 and N2 audits list the `v2` items as out of scope.
- The completed audits found defects that need rework before review, not just approval.
  - `PRE_REVIEW_AUDIT_secondary_2_g4.md` reports a wrong answer key (`g4-l2-529`),
    56 answer-revealing diagrams and missing sine and cosine coverage.
  - `PRE_REVIEW_AUDIT_secondary_2_n5.md` reports that correct algebraic answers are
    rejected. This audit confirmed the cause: `question_bank/src/question_bank/checking.py:158-161`
    accepts a `symbolic_equivalence` answer only on an exact string match or a listed
    equivalent. This affects 100 Secondary 1 and 88 Secondary 2 question files that use that
    mode.

Review decisions recorded in a hosted database could exceed what the repository shows.
They cannot be counted here and should not be assumed.

## 3. Built, partly built and missing

| Capability | State | Evidence |
| --- | --- | --- |
| Course registry (2 courses, 19 groups, 87 lessons) | **Built** | `backend_resources/courses/g3_math/v1/registry.json`; `question-bank course-registry-validate` passes |
| Both course snapshots, lessons and pools | **Built (draft)** | `secondary_1/n1/v1/course.json` (10 units, 52 lessons), `secondary_2/g2/v1/course.json` (9 units, 35 lessons). Both validate in `CourseCatalogue.reports`. All 87 lessons pass the note-depth gate |
| Read-only course map and lessons for both courses | **Built** | `routers/courses.py`; `tests/test_courses.py:156-335` |
| Multiple enrolments per learner (schema) | **Built** | migration `202609240004:37-47` |
| Invitation assigning a course | **Partly built** | One course per invitation; UI fixed to Secondary 1; no second-invitation UI |
| Sec 3-entry track | **Missing** | `target_track` = course key; picker only in design previews |
| Lesson start and section progress beyond N1 | **Missing** | `routers/progress.py:46-96` |
| Practice, retry and checkpoint for Secondary 2 | **Missing** | Probe results in 2.1 |
| Progress and learning home across both courses | **Missing** | `progress_service.py` single report |
| Two-course learner UI | **Missing** | First-enrolment selection in learner pages |
| Cross-year diagnostic plan (76 items) | **Built (draft)** | `plan.json`; `diagnostic-plan-validate` passes |
| Diagnostic engine (sessions, autosave, scoring, results) | **Built** | migration `202609290012`; `routers/diagnostics.py`; `diagnostic_repository.py` |
| Cross-year scoring and recommendations | **Built** | `diagnostic_repository.py:66-118`; `tests/test_diagnostics.py:119-128` |
| Diagnostic form import and publication | **Missing** | No importer; 0 published forms |
| Diagnostic attachment for a two-course learner | **Partly built** | One course revision per form; most recent enrolment wins |
| PostgreSQL import of Secondary 2 | **Missing** in workflows and bootstrap | See 2.3 item 6 |
| Content review queue across both courses | **Built** | `content_review.py:188-237` |
| Release workflow check across both courses | **Partly built** | Covers all reports, but skips drafts and conflicts with gate counts |
| Beta release gate for a two-course candidate | **Missing** | See 2.3 |
| Human approval and publication | **Partly built** | Secondary 1 N2 only (approval, not publication) |
| E2E for a two-course learner | **Missing** | `seed_e2e.py:63` |

## 4. Stale statuses in the compared plans

| Document | Statement | Repository evidence |
| --- | --- | --- |
| `ROADMAP_BETA_V2_V3.md` B-03 | "Built (Sec 1 content only)" | No learner track choice exists. The invitation decides, and only Secondary 1 is runnable. For Sec 3 entry this is **not built** |
| ROADMAP B-04, B-05 | "Not started" | Diagnostic engine, player and result page exist (migration `202609290012`, `app/(learner)/diagnostics/…`). Forms are unpublished |
| ROADMAP B-06 | "N1 course with 7 lessons" | 52 + 35 lessons registered and authored |
| ROADMAP B-07 | "content blank" | All 87 lessons pass the note-depth gate (draft) |
| ROADMAP B-10 | "retry exists, no delay" | `retry_policy.py`; migration `202609290013_spaced_retry_reports.sql` |
| ROADMAP B-11, B-13, B-21 | "Designed" | Checkpoint sessions and pages exist (`app/(learner)/checkpoints`). Question reports are implemented (`routers/question_reports.py`) |
| ROADMAP B-14, B-15 | "domain/content not started" | English migrations `202610190028`–`202611020047` and `routers/english.py` exist. English readiness is not re-audited here |
| ROADMAP V2-05 | "Sec 3 entry course content — Not started (beta is Sec 1 N1 only)" | `g3-sec2-math` is fully authored as a draft. It is now the product focus, not V2 |
| `BETA_V2_V3_TECHNICAL_EXECUTION.md` §1 and §1.1 | Sec 3 content moved to Layer 2/V2 and kept out of the Layer 1 gate | Conflicts with the current focus |
| Tech execution §2 | "seven N1 lesson shells", "40 draft questions" | 87 lessons and 1,976 learning questions |
| Tech execution §3 B-03 | "Keep invitation-assigned Sec 1 for Beta; defer student selection and Sec 3" | Superseded by the Sec 3-entry focus |
| Tech execution §4.1 | "every Beta invitation pins the Sec 1 course" | Superseded. The cross-year diagnostic it also requires cannot be attached to a learner without an anchor-course rule |
| Tech execution §5 B0 exit and B5 status | "reach the current N1 shell"; "current N1 source remains below the threshold… six lesson notes remain empty" | Notes are complete. The gate still blocks, but because it reads only Secondary 1 (10 groups, 1,040 questions) |
| Tech execution §4.2 | Two criteria numbered 9 | Numbering defect |
| `B5_CONTENT_RELEASE_CONTROLLED_PILOT.md` evidence table | Topic groups 19 **Pass**; 1,976 questions **Pass**; 87 lessons **Pass** | The gate measures 10, 1,040 and 52, and blocks the first two |
| B5 evidence table | Pools "1,044 practice, 393 checkpoint, 475 reserve" | Both courses: 1,081 / 408 / 487 (622/196/222 + 459/212/265) |
| B5 "Current evidence" | "Secondary 1 N2 is reviewed" | Batches approved and lessons `reviewed`, but the 104 question files are `draft` and the registry lists N2 lessons as `draft` |
| B5 | "English currently has UI designs but no production domain"; English rows "0 / Blocked" | English domain code and migrations exist. These rows need re-auditing |
| B5 "What is implemented" | "two current published 38-question diagnostic forms" | The check exists, but it is tied to `g3-sec1-math`, and there is no importer to create the forms |
| `FULL_SEC1_SEC2_COURSE_REGISTRY.md` | `g3-sec1-math`: "N2 reviewed" | `registry.json` lists every Secondary 1 lesson as `draft`, while `course.json` lessons are `reviewed` |
| Registry doc, "API behavior" | Registry status and snapshot "advance together" | No validator compares them. `course_registry.py` checks only the syllabus, so they have already drifted |

## 5. What blocks the first invited learners (ordered)

These are ordered by dependency. Items 1–6 are engineering; items 7–9 are content and human
gates; items 10–11 are release evidence.

1. **Import both courses into PostgreSQL.** Bootstrap, CI, staging and production import only
   `g3-sec1-math`. Without this, a Secondary 2 invitation cannot be created.
2. **Resolve lessons and units by course.** Replace single-course `catalogue.report` use in
   `ProgressService` and `PracticeService` with lookups by lesson or unit key, and widen the
   lesson-key pattern in `routers/progress.py`. Until then, Secondary 2 cannot be practised,
   and most Secondary 1 lessons cannot record lesson progress.
3. **Enrol one learner in both courses.** Either let one invitation enrol both courses, or
   let onboarding accept a second invitation. Add a course choice to the admin invitation form.
4. **Show both courses to the learner.** Progress, the learning home and the course map
   overlay must cover all active enrolments. Learner pages must stop using only the first
   enrolment.
5. **Attach the cross-year diagnostic to the learner.** Choose an anchor course revision for
   the forms (recommended: `g3-sec1-math`). Resolve diagnostics through that course rather
   than the latest enrolment, and decide the endline rule across both courses.
6. **Add a diagnostic importer** that publishes `plan.json` forms into `diagnostic_forms`
   and `diagnostic_form_items` from approved item revisions.
7. **Fix known blocking defects before review.** These include the `symbolic_equivalence`
   string matching (`checking.py:158-161`) and the G4 wrong key and answer-revealing
   diagrams. Finish technical pre-review for the 10 unaudited topic groups and the
   76 diagnostic items.
8. **Run human review** of 2,034 Mathematics items, and publish those 2,034 plus the 107
   already-approved Secondary 1 N2 items. That is 2 courses, 87 lessons, 1,976 questions and
   76 diagnostic items.
9. **Publish two current baseline and endline forms** on the anchor course revision.
10. **Make the release gate two-course aware.** See section 6, then run it strictly against
    staging.
11. **Collect the hosted evidence** the gate already requires: OAuth, authenticated E2E for a
    two-course learner, accessibility, restore, load and rate limits, owners, freeze and
    founder sign-off. Then run the founder-alpha phase.

The English Layer 1 gate (B5 doc) also applies if English remains in the first cohort. Its
exam profile is currently Sec 1-entry only.

## 6. Smallest change that supports both courses

Keep the two existing courses and their stable keys. Do not merge them into one course: the
course model has one `school_level` per course, and cross-year diagnostic scoring depends on
that. Make the runtime and gate course-aware instead. **No migration is required.**

1. **Catalogue lookups.** Add `report_for_lesson(lesson_key)`, `report_for_unit(unit_key)` and
   an all-courses question index to `CourseCatalogue`. Lesson and unit keys are already
   unique across both courses. Keep `report` only as a deprecated alias.
2. **Progress and practice.**
   - In `ProgressService` and `PracticeService`, use the owning report for lesson, unit, pool,
     mastery policy and the session's `course_key` and `course_revision`.
   - In `routers/progress.py`, change the four path patterns to the one already used by
     `practice_contracts.py:17`.
   - Return progress per active enrolment, or for a `course_key` parameter.
3. **Import.**
   - Loop over `catalogue.reports` in `bootstrap_local.py` and `content_sync.check_content`.
   - Either let `course-import-db` accept several snapshots or run it once per course in the
     three workflows.
4. **Enrolment.**
   - Add a course select to `admin-invitations-panel.tsx`; the API already accepts
     `course_key`.
   - Let `/onboarding` accept an invitation code even when the learner is already enrolled.
     The repository already supports a second enrolment for a different course.
   - A later improvement is a "track" invitation that enrols both courses in one
     transaction.
5. **Diagnostics.**
   - Pin the cross-year forms to the `g3-sec1-math` revision.
   - Make `DiagnosticRepository._enrolment` select the enrolment that has current published
     forms.
   - Evaluate endline eligibility across the learner's active enrolments.
   - Add a `diagnostic-import-db` command for `plan.json`.
6. **Gate.**
   - In `source_checks`, aggregate over all reports. Count topic groups by unit `stable_key`,
     giving 19.
   - Record each course's key, revision and hash in the snapshot.
   - Compare approvals with the items `verify_release_workflow` actually checks.
   - Run the diagnostic and pool-overlap queries over both course revisions.
7. **Tests.**
   - Secondary 2 practice, lesson start, checkpoint and progress tests.
   - A PostgreSQL test for a learner with two enrolments.
   - A gate test with a two-course fake catalogue.
   - An E2E seed for both courses.

Items 1–3 and 6 are backend-only changes, mostly to `course_catalogue.py`,
`progress_service.py`, `practice_service.py`, `routers/progress.py`, `content_sync.py`,
`bootstrap_local.py`, `beta_release.py` and three workflow files. Items 4–5 add one admin
field, one onboarding condition and three diagnostic query changes.

## 7. How to reproduce

```bash
uv run --project question_bank question-bank course-registry-validate
uv run --project question_bank question-bank diagnostic-plan-validate
uv run --project services/learning_api python -m pytest \
  services/learning_api/tests/test_courses.py services/learning_api/tests/test_beta_release.py \
  services/learning_api/tests/test_diagnostics.py services/learning_api/tests/test_identity.py \
  services/learning_api/tests/test_practice.py services/learning_api/tests/test_progress.py -q
```

All three commands passed on the audited commit (41 tests). The source-gate figures in 2.3
come from calling `learning_api.beta_release.source_checks` on
`CourseCatalogue(repository_root, allow_drafts=True)`. The status codes in 2.1 come from the
in-process test application used by `tests/test_practice.py`. Neither needs a database or
network access.
