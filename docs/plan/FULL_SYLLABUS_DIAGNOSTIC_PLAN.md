# Full-syllabus Mathematics diagnostic source plan

**Status (16 October 2026):** deterministic authoring contract complete; the 76 dedicated questions and both human approvals remain outstanding. Learner activation remains fail-closed.

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

This milestone uses no model or paid API. Codex can author the reserved questions offline in later batches. Every question must still pass deterministic answer checking, duplicate detection, Mathematics review and editorial review before either form can be published.

## How the diagnostic will drive a study plan

The submitted assessment is marked by the existing deterministic checker. The production scoring revision should aggregate the two items for each `topic_group_key`, rank topic groups by percentage, and map the lowest groups to their course units and lessons. That ordered list becomes the learner's initial study plan. Lesson completion, practice evidence and checkpoint results can then move or remove recommendations.

This recommendation path is ordinary application logic. It does not need an LLM call. A language model may later explain a recommendation in friendlier prose, but it must not select the official priority, change the score or unlock content.

## Remaining activation order

1. Extend the 20–30-item authoring pipeline to support four-item diagnostic banks while preserving individual claims and reviewer packets.
2. Author the 76 reserved questions in the version-2 diagnostic banks.
3. Add topic-group aggregation and deterministic lesson recommendations to diagnostic results.
4. Complete Mathematics and editorial approval for every item and both forms.
5. Import and publish the two immutable forms only when their questions are reviewed and isolated from all learning pools.
6. Run authenticated hosted baseline, resume, submit, recommendation and endline-comparison journeys.

Until step 5, `/diagnostics` continues returning `content_pending`; the new source plan alone cannot expose draft questions to learners.
