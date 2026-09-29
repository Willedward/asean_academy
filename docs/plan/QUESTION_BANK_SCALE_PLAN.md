# Sec 1–2 Mathematics question-bank scale plan

**Decision:** Build a reviewed bank across all 19 Singapore G3/Express Mathematics topic groups for the beta. The existing 40 N1 questions are the first pilot batch, not the complete beta bank.

## Target inventory

The syllabus supplied covers 19 topic groups across Secondary 1 and Secondary 2. At 100–150 questions per group, the target inventory is 1,900–2,850 reviewed questions.

This inventory is separate from the diagnostic forms. Practice, checkpoint, adaptive-reserve and diagnostic questions have different exposure and measurement roles and must use separate pool assignments. Diagnostic questions must never appear in learning pools.

Recommended first complete target:

| Purpose | Per topic | Total across 19 topics |
| --- | ---: | ---: |
| Guided/independent practice | 55 | 1,045 |
| Challenge practice | 15 | 285 |
| Checkpoint candidates | 15 | 285 |
| Adaptive/retry reserve | 15 | 285 |
| Baseline/endline diagnostic | 4 total: 2 per form | 76 |
| **Initial total** | **104** | **1,976** |

Expand strong or high-weight topics toward 150 after the first review and learner-data cycle. Producing 150 immediately for every topic increases duplicate and review risk without evidence that every topic needs the same depth.

## Full-syllabus diagnostic

The diagnostic measures the complete Sec 1–2 scope, not only N1. The recommended beta design is:

- 38 baseline questions: two questions for each of the 19 topic groups;
- 38 matched endline questions with equivalent outcomes and difficulty, but different values, wording and solution paths;
- resumable sections so a learner does not need to finish all 38 in one sitting;
- an overall readiness band plus topic and syllabus-domain evidence;
- no hints, solutions or correctness before submission; and
- strict isolation from practice, checkpoint and reserve pools.

One question per topic would be shorter but too noisy for topic-level claims. If beta testing shows that 38 questions causes excessive drop-off, the next design should be a versioned two-stage adaptive diagnostic rather than silently reducing measurement quality.

## Generation pipeline

Question generation should run as a controlled content pipeline:

1. Freeze a machine-readable syllabus catalogue for all 19 topic groups and their outcomes.
2. Define a blueprint for each topic: difficulty, response type, marks, multipart rate, calculator use, context type, diagram requirement and pool allocation.
3. Ingest sample papers only as style and mark-allocation references. Questions remain original and do not reproduce paper wording.
4. Generate small batches of 20–30 questions per topic.
5. Validate schema, LaTeX, marks, hints, solutions, deterministic answer specs and referenced assets automatically.
6. Run exact and near-duplicate detection within the batch and against the entire bank.
7. Execute every supported canonical/accepted answer through the deterministic checker.
8. Render reviewer previews for KaTeX/MathJax and SVG diagrams.
9. Require mathematics and editorial approval before publication.
10. Import immutable revisions and generate a coverage report before pool assignment.

Generation should stop when a batch has too many review corrections. The prompt/template and validators are then fixed before producing more questions.

## Repository changes required before bulk generation

The current authoring package deliberately hard-codes the N1 pilot bank, N1 outcomes and N1 stable-key formats. Scaling safely requires:

- a versioned Sec 1–2 syllabus catalogue instead of the current `OUTCOMES` constant;
- generic topic, outcome, bank and question identifiers;
- per-topic blueprint files and aggregate coverage validation;
- separate learning and diagnostic bank roles;
- cross-bank duplicate fingerprints;
- diagram generation specifications and asset checksum validation;
- batch manifests recording generator/prompt version and provenance;
- review queues and coverage dashboards that work across all 19 topics; and
- import commands that reject incomplete or unreviewed publication batches.

Do this generalisation once before generating thousands of files. Hand-editing thousands of N1-shaped files and migrating them later would create unnecessary rework.

## Additional papers and information

Ten to fifteen additional Sec 1/Sec 2 papers with answer schemes are useful for style coverage, mark allocation, common multipart structures and difficulty calibration. They do not need OCR for direct question reuse.

Before full production, record:

- the canonical list and ordering of the 19 topic groups and all outcome codes;
- whether the target is exactly 100, a weighted 100–150 range, or 150 for every topic;
- preferred difficulty distribution for practice and checkpoint pools;
- any schools/paper sections that should carry more style weight;
- notation, rounding and unit conventions that reviewers will enforce;
- excluded contexts or culturally sensitive examples;
- named mathematics and editorial reviewers; and
- the maximum review batch size each reviewer can handle weekly.

The screenshots already provide a good syllabus starting point. The extra papers and answer schemes are the most valuable next input.

## Delivery sequence

1. Generalise schemas and write migration-safe importers.
2. Complete one non-N1 topic as an end-to-end calibration batch of 20–30 questions.
3. Review it and update templates/checks from reviewer corrections.
4. Generate all topics in review-sized batches, prioritising diagnostic and checkpoint coverage.
5. Publish only approved batches; draft quantity is never reported as beta readiness.
6. Expand from roughly 100 toward 150 per topic using review capacity and learner evidence.

With Codex handling structured generation, validation, preview tooling and corrections, producing the draft inventory is feasible. Human review throughput will determine the publication schedule.
