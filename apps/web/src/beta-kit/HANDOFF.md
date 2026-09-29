# Beta frontend handoff: what each screen needs from the backend

**Exists** = the learning API already returns it (endpoint or field named).
**NEW** = backend work still to do. The screens already render it from sample data.

**Integration audit (29 September 2026):** This kit was checked against B3. Core spaced retry, checkpoint, question-report, diagnostic and academic-admin deletion APIs now exist. The corrections below distinguish missing API work from the remaining job of wiring these components to existing APIs.

Preview any screen at `/beta-kit/<key>`. Props for every screen are typed in its file under
`screens/`, with `// API:` and `// NEW` comments on each field.

---

## 1. New backend pieces, in suggested build order

| # | Piece | Needed by | Minimum shape |
|---|---|---|---|
| 1 | **Player / XP ledger** | Every tab screen (top bar chips, desktop sidebar card), dashboard, progress, me | `Player` in `types.ts`: level, rank title, XP total, XP this week, XP into level, XP for level, streak days, best streak, freezes, league rank, equipped outfit. Back it with an append-only `xp_events` table (learner, amount, reason, source id, created_at) so totals can be recomputed. |
| 2 | **XP rules** (server side, never trust the client) | Practice, lesson, review, checkpoint, English | Right first try +10, right after a hint or retry +6, lesson section +10, check yourself +5, video watched +10, review question cleared +20 (double), 3 daily quests +15 each and +30 all-three bonus, unit mastered +100, recheck passed +50, essay submitted +30, essay improved +20, confirmed problem report +25, weekly check-in +20. Mistakes never cost XP. No XP for speed. |
| 3 | **Streaks and freezes** | Streak chip, `streak`, dashboard week dots, offline and signed-out screens | Per learner per day: done / freeze / missed, in the learner's time zone. A freeze is earned for hitting the weekly goal (5 days), max 2, never sold. Milestones at 3, 7, 14, 30, 60 days. |
| 4 | **Daily quests** | Dashboard, `quests`, practice correct toast, English home | 3 quests a day (`Quest`: id, title, icon, progress, target, xp), reset time, all-three bonus. Weekly goal (days done of 5) and a monthly challenge. |
| 5 | **Try again list (spaced repetition)** | `review`, `dashboard-review`, give-up and solution screens | **Core exists in B2:** server-owned `due_at`, review stage, 2/4/7/14-day transitions, five-item cap, reserve variants, aggregate scheduled count and next due date. Remaining: wire the kit and add a grouped ready/later/cleared read model if that exact screen remains in Beta. |
| 6 | **Stars per lesson** | Lesson rows, unit, course map, practice done | Derived: 1 star for any right answer, 2 at proficient, 3 at mastered. `adapters.ts` `starsFor()` already does this from `LessonProgressResponse`. Only needs `stars` added if you want it stored. |
| 7 | **Badges and wardrobe** | `me`, `badges`, progress badge shelf, badge-unlocked, level-up | `Badge` (id, name, description, icon, tier, earned, progress). `OutfitItem` (outfit, unlocked, equipped, requirement). Equip endpoint (form field `outfit`). Rarity count for "only 4 of 18 have it". |
| 8 | **Weekly league** | `league`, dashboard league card, sidebar chip | One league for the whole beta. Rows: rank, name, initials, weekly XP, is you, note ("+60 today"). Ends-in label, top 3 crown, "XP behind the next person". Respect the "Show me in the Beta League" setting. |
| 9 | **Checkpoint** | `checkpoint-*`, `unit-mastered`, `checkpoint-resume` | **Core exists in B2:** checkpoint-mode practice supports start, answer, resume, submit, pass/fail, retake and mastery, and `/checkpoints/{sessionId}` already uses it. Remaining: map the kit screens; async marking, richer per-outcome presentation, XP, badge and level data are still NEW. |
| 10 | **Recheck quiz** | `recheck-*`, `unit-recheck`, `dashboard-unit-done` | 5 questions from proficient lessons 2 weeks later, right or wrong after each, pass 4 of 5 moves lessons to mastered (3rd star), +50 XP. |
| 11 | **English** | All `english`, `grammar-*`, `vocab-question`, `essay-*` screens | Nothing exists yet: grammar units and questions with choices and a one-line reason, vocab typed answers, writing tasks, drafts with cross-device autosave and word count, submit and lock a version, async AI marking job, feedback (score, criteria, quotes, fixes, strengths), essay quota, version history, usefulness rating. |
| 12 | **Lesson extras** | `lesson`, `lesson-video` | Per-section done state (for +10 XP each), video asset, captions and transcript lines, "check yourself" answer. |
| 13 | **Small endpoints** | Various | **Question reporting exists in B2** and **academic-admin deletion exists in B3**. Sign-out also exists. Remaining: learner self-service deletion if desired, weekly check-in, game settings and explicit practice-expiry status. |

---

## 2. Screen by screen

### Entry
| Key | Component | Exists | NEW |
|---|---|---|---|
| `landing` | `LandingScreen` (entry.tsx) | Static copy | none |
| `sign-in`, `sign-in-error` | `SignInScreen` | `signInWithGoogle` server action, `/login?error=` codes | none |
| `onboarding`, `onboarding-error` | `OnboardingScreen` | `ProfileResponse.email`; POST `/onboarding/accept-invitation` with `display_name`, `invitation_code` (input names match); `ErrorDetail.message` for the code error | `target_track` in `AcceptInvitationRequest` (today only on `ProfileResponse`); starter pack (+50 XP welcome) |

### Learn
| Key | Component | Exists | NEW |
|---|---|---|---|
| `dashboard` | `DashboardScreen` (dashboard.tsx) | `GET /learning-home`: `next_action` (use `continueFromNextAction()`), `lessons`, `unresolved_retry_count`; course map for the unit card (`unitFromCourseMap()`) | Player, quests, streak week, league, XP on the continue card |
| `dashboard-new` | `DashboardNewScreen` (learn.tsx) | `next_action` for the first lesson, `CourseLessonMap.estimated_minutes` | Welcome XP, XP rules card, next unlock |
| `dashboard-review` | `DashboardReviewScreen` | `next_action` | Review items, minutes, Review master badge progress |
| `dashboard-unit-done` | `DashboardUnitDoneScreen` | `CourseUnitMap.title`, next unit's `content_pending` lessons | Stars, bonus XP, first-try %, badge, recheck offer |
| `course-map` | `CourseMapScreen` | `GET /courses/{course_key}/map` | Stars and XP per unit, unit reward, badge holder count |
| `unit`, `unit-recheck` | `UnitScreen` | Course map + `GET /progress` via `unitFromCourseMap()`; time from `estimated_minutes` | XP available per lesson, recheck offer |
| `review` | `ReviewScreen` | Ready count from `unresolved_retry_count` | Ready, later and cleared lists, badge progress |
| `quests` | `QuestsScreen` | none | Quests, weekly goal, monthly challenge |
| `streak` | `StreakScreen` | none | Month of `StreakDay`, freezes, milestones |

### Lesson
| Key | Component | Exists | NEW |
|---|---|---|---|
| `lesson` | `LessonScreen` (lesson.tsx) | `GET /lessons/{lesson_key}`: title, position, `estimated_minutes`, `objectives`, `sections` (render with `MathContent` into the slots), `practice.question_count`, `practice.available`; state from `LessonProgressResponse.state` | XP per section, section done state, video, check-yourself result |
| `lesson-in-review` | `LessonInReviewScreen` | `learning_material_state: "pending"` / `availability: "content_pending"` | Review items waiting |
| `lesson-video` | `LessonVideoScreen` | none | Video, captions, transcript lines, section steps |

### Practice
One component, `PracticeQuestionScreen` (practice.tsx), draws every state via `state`:
`answering`, `wrong`, `confirm-give-up`, `solution`, `correct`. Keep your state machine in
`practice-player.tsx` and render this per state.

| Key | State | Exists | NEW |
|---|---|---|---|
| `practice-answer` | answering | `NextQuestionResponse` (`position`, `stage`, `highest_hint_stage`, `question`); `PublicQuestionResponse` (`stable_key`, `difficulty`, `primary_outcome`, `total_marks`, `stem`, `parts`); `QuestionPartResponse` (`label`, `prompt`, `marks`, `input_placeholder`). Inputs are named `answer-<position>`, matching `SubmitAttemptRequest.answers` | XP rules for the question, quest progress, combo |
| `practice-wrong-1`, `practice-wrong-2` | wrong | `AttemptResponse` (`attempt_number`, `parts[].correct`, `solution_available`); `HintResponse` | none beyond the above |
| `practice-give-up` | confirm-give-up | POST give-up | Due date of the review, badge it counts toward |
| `practice-solution` | solution | `GiveUpResponse.solution` (`SolutionResponse`: `canonical_latex`, `steps`) | Review note (from spaced repetition) |
| `practice-correct` | correct | `AttemptResponse.correct` | XP earned, lesson stars, quest toast, combo |
| `practice-done` | `PracticeDoneScreen` | `PracticeSessionSummary` (`question_count`, `correct_count`, `gave_up_count`) | XP tally, level after, streak after, per-question XP, "next star" |
| `practice-keyboard` | `PracticeKeyboardScreen` | Same as answering | Maths key toolbar needs a small client wrapper to insert `data-insert` text |

### Checkpoint and recheck
Checkpoint core is implemented in B2 and needs kit integration; recheck remains NEW (see section 1, items 9 and 10). Components in checkpoint.tsx:
`CheckpointIntroScreen`, `CheckpointActiveScreen`, `CheckpointReviewScreen` (states `reviewing`
and `confirm`), `CheckpointMarkingScreen`, `CheckpointResultScreen`, `RecheckIntroScreen`,
`RecheckActiveScreen` (states `answering`, `wrong`, `right`), `RecheckResultScreen`.
Outcome rows use `CourseLessonMap.outcomes`, `title`, `position` and `LessonProgressResponse.state`.

### English
All NEW (section 1, item 11). Components in english.tsx: `EnglishHomeScreen`,
`GrammarQuestionScreen` (states `answering`, `wrong`, `right`), `VocabQuestionScreen`,
`EssayPromptScreen`, `EssayEditorScreen`, `EssaySubmitScreen`, `EssayMarkingScreen`,
`EssayFeedbackScreen`, `EssayHistoryScreen`. Choice buttons, rating and the textarea need a
small client wrapper.

### Progress, league and me
| Key | Component | Exists | NEW |
|---|---|---|---|
| `progress` | `ProgressScreen` (me.tsx) | `GET /progress`: `resolved_count`, `gave_up_count`, `eventual_correct_percentage`, `state`, `lesson_title`, `position` | First-try % (needs first-answer tracking), level and rank ladder, badge shelf, league cell, recent work with XP |
| `settings` | `SettingsScreen` | `ProfileResponse.display_name`, `email`, `target_track`; `EnrolmentResponse.course_key` | Game settings (fields `sounds`, `celebrations`, `show_in_league`, `streak_reminder`), save profile, sign out, delete account |
| `settings-delete` | `SettingsScreen` with the delete sheet | Academic-admin preview/confirm deletion exists in B3 | Learner self-service deletion is not implemented; do not wire this screen to the administrator endpoint |
| `me` | `ProfileScreen` | `ProfileResponse.display_name` | Wardrobe, badges, equip endpoint |
| `league` | `LeagueScreen` | none | League table, chase, prize |
| `badges` | `BadgesScreen` | none | Badges with progress |

### Celebrations (full screen moments)
`LevelUpScreen`, `StreakMilestoneScreen`, `UnitMasteredScreen`, `BadgeUnlockedScreen`
(celebrations.tsx). All data NEW. Show once per event: the backend should return pending
celebrations (for example on `GET /learning-home`) and mark them seen.

### System states
`LoadingScreen` and skeletons need only the player. `NotFoundScreen` and `ServerErrorScreen`
use `ErrorDetail.code` and `request_id`. `PracticeExpiredScreen` uses
`PracticeSessionSummary.resolved_count` plus a NEW expired status. `ReportProblemScreen` can
use the B2 question-report endpoint and `CheckpointResumeScreen` can use checkpoint-mode
practice; `WeeklyCheckinScreen` still needs a new endpoint.

---

## 3. Not built yet (no design)

- Desktop layouts for phone-only boards were designed sensibly by the kit, not on the canvas.
- A failed checkpoint or recheck result, and a "see my answers" page.
- The "Later" and "Cleared" tabs of the Try again list (only "Ready now" is designed).
- Parent, payment, tutor and study-planner designs remain separate V2/V3 work. Diagnostic is a Beta feature: B1 backend and technical pages exist, but this kit contains no diagnostic design, so B4 still needs an approved diagnostic UI.
