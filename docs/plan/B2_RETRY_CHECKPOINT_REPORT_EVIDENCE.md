# B2 spaced retry, checkpoint and question-report evidence

**Status:** Technical implementation complete on `feature/b2-spaced-retry-reports-checkpoint`.

## Spaced retry

Migration `202609290013_spaced_retry_reports.sql` adds server-owned `due_at`, interval, review-stage, streak and resolution evidence to `question_progress`. The pure retry policy implements:

| Trigger | Next state |
| --- | --- |
| Give up or incorrect checkpoint answer | due in 2 days |
| Correct after help in initial practice | due in 4 days |
| First clean review | due in 7 days |
| Second clean review | due in 14 days |
| Third clean review | leaves the retry queue |
| Assisted review | repeats the current interval and clears the clean streak |

Only due items can enter retry practice. Selection is ordered by overdue time and capped at five questions per learner request. Starting with the second review, PostgreSQL selects a different adaptive-reserve question when the bank contains the same outcome and difficulty. `session_questions.retry_origin_question_id` preserves the original learning record so a correct variant advances the right schedule. Selection falls back to the original item when no safe variant exists.

The progress response exposes total scheduled reviews and the next server-owned due timestamp. The browser formats that timestamp in the learner's local timezone.

## Checkpoint learner flow

The existing 6-of-8 checkpoint policy now has start, resume, completion, result and retake states in the learner web application. The checkpoint player hides hints, solutions and Give up. A completed failing attempt returns to an available retake state; a passing attempt records mastery. The course map no longer labels an available checkpoint as permanently pending.

## Question reports

The same migration adds a learner-owned `question_reports` inbox pinned to the exact practice session and immutable rendered question revision. Supported categories are possible error, unclear wording, display problem and other.

The API provides:

```text
POST  /api/v1/question-reports
GET   /api/v1/question-reports
GET   /api/v1/question-reports/{report_id}
GET   /api/v1/admin/question-reports
GET   /api/v1/admin/question-reports/{report_id}
PATCH /api/v1/admin/question-reports/{report_id}
```

Learners can report the current question from practice and see only their reports. Academic administrators get a paginated/status-filtered inbox and can move reports to in-review, resolved or dismissed. Audit events record the report identifier and status transition without copying submitted answers.

## Verification evidence

- The full migration chain applies cleanly to disposable PostgreSQL, then imports and verifies the 40-question pilot bank.
- Pure policy tests cover 2/4/7/14-day transitions, assisted retries and queue completion.
- PostgreSQL integration coverage proves the five-item cap, same-outcome/level variant selection, original-question provenance, 14-day advancement, report ownership, admin resolution and answer-free audit metadata.
- Generated OpenAPI and TypeScript contracts include retry evidence and all report routes.
- Web lint/typechecking and all component tests cover the checkpoint and progress states.

## Remaining release gates

B2 code is complete. Release still depends on reviewed pool capacity, final frontend/accessibility acceptance, hosted authenticated journeys and the generalized 19-topic content platform. Reserve fallback is deliberately safe when the current 40-question pilot lacks a same-skill alternative.
