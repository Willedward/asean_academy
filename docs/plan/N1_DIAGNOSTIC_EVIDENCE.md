# N1 diagnostic technical evidence

**Status:** B1 technical implementation complete on `feature/n1-diagnostic-baseline`.

**Content status:** Production activation is intentionally blocked until 28 separate diagnostic questions have been authored, reviewed and published. The learner sees a safe `content_pending` state meanwhile. Existing practice and checkpoint questions are not reused.

## Delivered behavior

The N1 readiness workflow now supports one baseline and one endline assessment for the learner's invitation-pinned course revision.

- The baseline is offered after onboarding.
- A started assessment resumes with its saved answers after refresh or a later sign-in.
- Each complete question autosaves without returning correctness.
- Submission is rejected until every form item has a saved response.
- Submission creates one immutable result with an overall percentage, versioned band and per-outcome scores.
- The endline stays locked until all N1 lessons are mastered.
- A learner cannot repeat an effective baseline or endline.
- An academic administrator can reset an exceptional attempt only with a reason; the old result and append-only reset evidence remain in history.
- The admin student view shows baseline and endline results for comparison.

## Persistence and integrity

Migration `202609290012_n1_diagnostics.sql` adds:

| Table | Purpose |
| --- | --- |
| `diagnostic_forms` | Immutable form revision, course revision, purpose, review/publication state and band policy |
| `diagnostic_form_items` | Ordered exact question revisions and N1 outcomes |
| `diagnostic_sessions` | Learner-owned baseline/endline state and create idempotency |
| `diagnostic_responses` | Autosaved answer payload and server-only deterministic score |
| `diagnostic_response_idempotency_keys` | Replay-safe response writes |
| `diagnostic_results` | Immutable aggregate and outcome evidence |
| `diagnostic_resets` | Append-only academic-admin reset audit |

Database constraints allow only one current published form per course revision and purpose. Triggers require every diagnostic item to use a reviewed, published question revision. Symmetric isolation triggers prevent a diagnostic question from entering lesson practice, checkpoint or adaptive reserve pools, regardless of which pool is edited first.

The API authenticates every learner operation and checks session ownership. The application computes scoring on the server with the existing deterministic checker. It does not return answer-level correctness while the session is in progress.

## API contract

```text
GET  /api/v1/diagnostics/next
POST /api/v1/diagnostics/sessions
GET  /api/v1/diagnostics/sessions/{session_id}
PUT  /api/v1/diagnostics/sessions/{session_id}/responses/{position}
POST /api/v1/diagnostics/sessions/{session_id}/submit
GET  /api/v1/diagnostics/sessions/{session_id}/result
GET  /api/v1/admin/students/{learner_id}/diagnostics
POST /api/v1/admin/students/{learner_id}/diagnostics/{purpose}/reset
```

Session creation and response saves use `Idempotency-Key`. The generated OpenAPI document and frontend TypeScript contracts include these routes.

## Learner and administrator UI

The learner flow is available at `/diagnostics` and includes start, resume, content-pending, baseline-complete and all-complete states. Assessment pages live under `/diagnostics/{session_id}` and `/diagnostics/{session_id}/result`. Onboarding now routes to the diagnostic landing page. A Readiness link remains available in the learner header.

The technical player supports structured numeric or algebraic text fields, multipart questions, progress, previous/next navigation, debounced autosave, completion checks and submit. The result view uses supportive labels and shows strengths before priorities. The existing admin student panel loads diagnostic history and renders baseline/endline evidence.

Final visual styling remains part of B4 and does not change these API states.

## Versioned score policy

Policy `n1-readiness-v1` uses these inclusive boundaries:

| Percentage | Band |
| ---: | --- |
| below 50 | Getting started |
| 50 to below 80 | On track |
| 80 to 100 | Ahead |

A future boundary change must use a new policy version so old evidence remains reproducible.

## Verification completed

- Web lint and TypeScript checks pass.
- All 30 web component tests pass, including content-pending, autosave/no-correctness and submitted-result states.
- All 79 Learning API tests pass against a fully migrated disposable PostgreSQL database.
- PostgreSQL coverage proves refresh/resume, idempotent create/save, deterministic outcome scoring, immutable results, admin history, audited reset and diagnostic/practice pool isolation.
- Python lint and migration-safety checks pass.

## Content handoff required for activation

B1 deliberately does not invent or publish the assessed content. B5 must supply 28 new questions:

- 14 baseline questions and 14 matched endline questions;
- two questions per N1 outcome on each form;
- comparable coverage and difficulty across forms without duplicated wording or answers;
- calculator-allowed, structured numeric/algebraic response formats supported by the deterministic checker;
- exact marks, full worked solutions and two hints in the authored source even though hints and solutions are hidden during diagnostics;
- mathematics and editorial review before the question revision is published;
- form-level review before `is_current` is enabled.

The diagnostic bank needs its own authored source contract/import command before production content is loaded. This is best added with the first reviewed item batch, because the current 40-question schema intentionally fixes the practice-bank key, naming pattern and distribution. Until that handoff is complete, no learner can accidentally begin an empty or draft assessment.

## Remaining release evidence

B1 code is complete. Beta release readiness still requires:

1. authoring/reviewing the 28 items and importing both form revisions;
2. a hosted Google-authenticated baseline refresh/resume/submit journey;
3. mastering the course and completing the endline comparison in staging;
4. final responsive/accessibility acceptance during B4; and
5. confirming whether an expiring parent share link or PDF remains stretch work.
