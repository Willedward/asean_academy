# Full-syllabus Mathematics diagnostic source plan

**Status (18 October 2026):** all 76 dedicated questions are authored across 19 four-question diagnostic banks. Aggregate validation reports zero errors, warnings or duplicate matches, and the deterministic 38+38 plan validates. Topic scoring, deterministic lesson recommendations and the learner result interface are implemented. Mathematics and editorial approvals remain outstanding, so learner activation remains fail-closed.

## What is now fixed

The tracked source at `backend_resources/diagnostics/g3_math/secondary_1_2/v1/plan.json` defines the production-sized diagnostic inventory without reusing any learning question:

- one 38-item baseline form and one 38-item endline form;
- exactly two items for each of the 19 level-specific Mathematics topic groups on each form;
- 76 globally distinct reserved question keys;
- separate version-2 diagnostic bank keys for every topic group;
- syllabus-validated outcome assignments;
- matched difficulty pairs for each topic group across the two forms; and
- the new `asean-scholarship-math-readiness-v1` policy identity, separate from the N1 pilot.

The plan is generated from the canonical syllabus rather than typed by hand. Re-running the generator produces the same JSON byte-for-byte, so syllabus drift, missing groups and accidental overlap can be detected in CI.

```bash
uv run --project question_bank question-bank diagnostic-plan-create
uv run --project question_bank question-bank diagnostic-plan-validate
```

This milestone used no paid model API. Codex authored the reserved questions through the repository workflow. Every question passes deterministic answer checking and duplicate detection, but Mathematics review and editorial review are still required before either form can be published.

The command below materialises or verifies one isolated version-2 bank and one four-question
manifest for every topic group. It is idempotent and refuses drift from the tracked form plan:

```bash
uv run --project question_bank question-bank diagnostic-authoring-plan
uv run --project question_bank question-bank authoring-next \
  --owner YOUR_GITHUB_USERNAME --bank-role diagnostic
```

## How the diagnostic will drive a study plan

The submitted assessment is marked by the existing deterministic checker. The result service aggregates the two items for each `topic_group_key`, ranks topic groups by percentage, and selects the lesson attached to the weakest tested outcome inside each of the three lowest-scoring topics. Repeated outcome codes remain separate because school level and topic identity are part of the score key. The ordered recommendations are stored with the immutable diagnostic result under policy `topic-readiness-v1` and shown in the learner result interface. Lesson completion, practice evidence and checkpoint results can later move or remove recommendations.

This recommendation path is ordinary application logic. It does not need an LLM call. A language model may later explain a recommendation in friendlier prose, but it must not select the official priority, change the score or unlock content.

## Remaining activation order

1. ~~Author the 76 reserved questions in the 19 version-2 diagnostic banks.~~ Completed 18 October 2026.
2. ~~Add topic-group aggregation, deterministic lesson recommendations and the themed result interface.~~ Completed 18 October 2026.
3. Complete Mathematics and editorial approval for every item and both forms.
4. Import and publish the two immutable forms only when their questions are reviewed and isolated from all learning pools.
5. Run authenticated hosted baseline, resume, submit, recommendation and endline-comparison journeys.

Until step 5, `/diagnostics` continues returning `content_pending`; the new source plan alone cannot expose draft questions to learners.
