# Diagnostic engine pilot evidence

**Status:** B1 reusable diagnostic engine and N1 pilot complete on `feature/n1-diagnostic-baseline`.

**Scope correction (29 September 2026):** N1 was used only to prove the technical workflow. The beta diagnostic measures all 19 supplied Secondary 1–2 Mathematics topic groups. Production activation requires two matched 38-question forms, or 76 separate reviewed items. See [QUESTION_BANK_SCALE_PLAN.md](QUESTION_BANK_SCALE_PLAN.md).

## Delivered behavior

The reusable workflow supports one baseline and one endline assessment for the learner's invitation-pinned course revision.

- A started assessment resumes with saved answers after refresh or a later sign-in.
- Each complete response autosaves without returning correctness.
- Submission is rejected until every form item has a saved response.
- Submission creates one immutable result with an overall percentage, versioned band and per-outcome scores.
- Endline eligibility remains server-owned.
- A learner cannot repeat an effective baseline or endline.
- An academic administrator can reset an exceptional attempt with a reason while retaining the old result and append-only audit evidence.
- The administrator student view compares baseline and endline results.

The current learner UI returns a safe `content_pending` state because no production form has been published. Existing practice, checkpoint and adaptive-reserve questions cannot be reused in a diagnostic.

## Persistence and integrity

Migration `202609290012_n1_diagnostics.sql` adds:

| Table | Purpose |
| --- | --- |
| `diagnostic_forms` | Immutable form revision, course revision, purpose, publication state and score policy |
| `diagnostic_form_items` | Ordered exact question revisions and outcomes |
| `diagnostic_sessions` | Learner-owned baseline/endline state and create idempotency |
| `diagnostic_responses` | Autosaved response payload and server-only deterministic score |
| `diagnostic_response_idempotency_keys` | Replay-safe response writes |
| `diagnostic_results` | Immutable aggregate and outcome evidence |
| `diagnostic_resets` | Append-only academic-admin reset audit |

Constraints allow only one current published form per course revision and purpose. Publication triggers require reviewed, published question revisions. Symmetric isolation triggers prevent a diagnostic question from entering lesson-practice, checkpoint or adaptive-reserve pools regardless of edit order.

The API authenticates each operation, checks session ownership, and computes scoring with the deterministic checker. Answer-level correctness remains hidden while a session is active.

## API and UI contract

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

The learner flow is available at `/diagnostics`, with assessment and result routes below it. The player supports numeric and algebraic fields, multipart questions, previous/next navigation, debounced autosave, completeness validation and final submission. Result labels describe Mathematics readiness and show strengths before priorities. Final visual styling remains a B4 task.

## Score-policy versioning

The pilot policy `n1-readiness-v1` proved versioned score boundaries. The production full-syllabus diagnostic must receive a new policy key and calibrated boundaries so N1 pilot evidence is never confused with a Sec 1–2 readiness result.

## Verification evidence

The pilot integration coverage proves refresh/resume, idempotent create/save, deterministic outcome scoring, immutable results, admin history, audited resets and diagnostic/practice pool isolation against disposable PostgreSQL. Web coverage proves content-pending, autosave without correctness disclosure and submitted-result states. Python lint, OpenAPI generation, migration safety, TypeScript and web tests passed when B1 was completed.

## Content and platform handoff

Production activation needs:

1. a versioned catalogue of all 19 level-specific topic groups and outcome codes;
2. a generalized diagnostic bank/import contract rather than the N1-specific pilot naming;
3. 38 baseline and 38 matched endline items, with two items per level-specific topic group on each form;
4. comparable difficulty across forms without duplicated wording, values or solution paths;
5. marks, two authored hint stages and fully worked solutions, even though help stays hidden in diagnostics;
6. mathematics and editorial approval for every item and form;
7. hosted Google-authenticated baseline resume/submit and endline-comparison testing; and
8. final responsive and accessibility acceptance during B4.

Until these gates pass, no learner can accidentally begin an empty, draft or N1-only assessment and receive a misleading full-syllabus result.
