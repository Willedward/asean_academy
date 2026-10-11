# Bulk question-authoring recommendations

**Status:** Working recommendations for pipeline design and beta inventory planning. These defaults allow engineering to proceed before the founder confirms final publication policy.

## Scope and initial inventory

Build reviewed banks for all 19 level-specific Secondary 1–2 G3 Mathematics topic groups. The recommended first complete target is 104 questions per topic group, or 1,976 questions in total.

| Purpose | Per topic group | Total across 19 topic groups |
| --- | ---: | ---: |
| Guided and independent practice | 55 | 1,045 |
| Challenge practice | 15 | 285 |
| Checkpoint candidates | 15 | 285 |
| Adaptive and retry reserve | 15 | 285 |
| Baseline and endline diagnostic | 4 | 76 |
| **Initial total** | **104** | **1,976** |

Diagnostic questions remain isolated from learning pools. Topics can expand toward 150 questions after review evidence and learner data show where more depth is useful.

## Five-level difficulty recommendation

Use this as the default planning distribution. Every topic blueprint must explicitly declare Levels 1–5, but individual topics may vary after calibration.

| Difficulty | Recommended share | Meaning |
| --- | ---: | --- |
| Level 1 | 20% | Direct recall or one familiar taught step |
| Level 2 | 30% | Routine application with one or two linked steps |
| Level 3 | 30% | Multi-step application or interpretation requiring method choice |
| Level 4 | 15% | Unfamiliar problems involving constraints, justification, or method selection |
| Level 5 | 5% | Complex non-routine synthesis, sustained reasoning, or proof |

The blueprint converts percentages to exact integer counts that sum to its declared question count. Algebra, geometry, statistics, and short procedural topics may use different distributions when a mathematics reviewer approves the change.

## Review capacity

Author and export questions in batches of 20–30; 25 is the default batch size. Every batch needs separate mathematics and editorial decisions before publication.

The reviewers' weekly capacity is still an open input. Until it is known, generation should not run so far ahead that a large unreviewed backlog accumulates. Reviewer corrections from the first calibration batch must be incorporated into prompts, blueprints, and validators before bulk drafting continues.

The N2 technical pre-review is now incorporated in
house-rules-v2.json and math-question-authoring-v2.md. New work must distinguish the
allocated outcome in the task itself, reject semantic repeats that reuse the same context,
operation pattern and numbers, use S$ consistently, preserve staged hint boundaries and
independently recompute each answer. Human reviewer corrections remain pending and take
precedence over these provisional rules.

## Provisional house rules

The pipeline must make house rules versioned configuration rather than embedding them in prompts. The initial rules should cover:

- Singapore/British English;
- SI and metric units unless an outcome requires otherwise;
- Singapore dollars written consistently when currency is relevant;
- exact answers by default, with decimal places or significant figures stated explicitly when rounding is required;
- consistent mathematical notation, interval and inequality formatting, multiplication signs, and units in final answers;
- calculator permission declared per question;
- culturally neutral, age-appropriate contexts;
- no copied examination wording; sample papers are style and mark-allocation references only; and
- error-carried-forward behavior declared by policy rather than assumed.

Final notation, rounding, excluded-context, and error-carried-forward rules remain subject to founder and reviewer confirmation.

## Generator policy and provenance

The authoring pipeline is model-independent. A batch may be authored by Codex, Gemini, another model, or a human as long as its manifest records at least:

- stable batch identity and topic blueprint version;
- generator provider, model or author identity, and generator version;
- prompt/template version;
- source-reference identifiers and checksums;
- syllabus and house-rule versions;
- generation timestamp and input hash;
- parent or superseded batch, when applicable; and
- validation and review status.

API credentials are local secrets and must never appear in question JSON, manifests, commits, logs, or chat messages.

## Codex production workflow

Codex can author the approximately 2,000 draft questions, but this is a sustained repository workflow rather than a single prompt. Work must remain in batches of 20–30 so validation failures, duplicate patterns, difficulty drift, and reviewer corrections are contained.

Multiple Codex workspaces can contribute safely when each one:

1. claims a unique batch ID and non-overlapping blueprint allocation;
2. works on a separate Git branch;
3. generates only the files assigned by that batch manifest;
4. runs schema, answer, solution, asset, distribution, and cross-bank duplicate checks;
5. exports the reviewer packet; and
6. merges only after conflicts and aggregate coverage are revalidated.

Account credentials should not be shared. Parallel contributors coordinate through batch manifests and Git, not by relying on conversation memory.

## Sample-paper dependency

Additional sample papers are **not a prerequisite for building the pipeline**. The canonical syllabus, existing N1 bank, current paper set, schemas, and five-level rubric are enough to implement:

- the 19 blueprints;
- batch manifests and provenance;
- validators and deterministic answer execution;
- cross-bank exact and near-duplicate detection;
- asset integrity checks; and
- reviewer-friendly HTML/JSON/CSV exports.

They are also enough for one 20–30-question N2 Secondary 1 calibration batch. Ten to fifteen additional Secondary 1 and Secondary 2 paper sets with answer or mark schemes remain strongly recommended before large-scale difficulty calibration and final publication. They improve style coverage and calibration; they do not change the canonical syllabus and are never copied verbatim.

## Recommended delivery order

1. Build and test the model-independent authoring pipeline.
2. Create all 19 versioned blueprints using the recommended defaults.
3. Produce one N2 Secondary 1 calibration batch of 20–30 questions with Codex.
4. Have mathematics and editorial reviewers annotate the batch.
5. Update house rules, prompt versions, difficulty calibration, and validators from those corrections.
6. Generate the remaining inventory in claimed, review-sized batches.
7. Add new paper references as they arrive and recalibrate future batches where useful.
8. Publish only immutable batches that pass automated checks and both human review gates.

The software work can therefore begin immediately. Human review throughput, rather than model generation speed, is expected to determine the schedule for a publishable beta bank.
