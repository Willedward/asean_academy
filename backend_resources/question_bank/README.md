# Mathematics question bank sources

This directory contains version-controlled source JSON for original mathematics questions.
PostgreSQL becomes the production source of truth only after validation, review, and import.

## Layout

```text
authoring/house-rules-v1.json
authoring/batch-claims-v1.json
schema/question-v1.schema.json
schema/question-batch-manifest-v1.schema.json
schema/question-batch-claims-v1.schema.json
schema/question-house-rules-v1.schema.json
g3_math/<school_level>/<topic>/v1/
  blueprint.json
  batches/<batch-id>.json
  questions/<stable-key>.json
  assets/*.{svg,png,webp}
```

Every question follows `question-v1.schema.json`. A blueprint fixes bank size, five-level
difficulty distribution, syllabus coverage, and publication checks. A batch manifest allocates
20–30 questions and records generator, prompt, sources, checksums, and review state.
The claim registry ensures that one named branch owns each active batch while multiple
authors work in parallel.

Binary or SVG assets are uploaded to object storage during import; their metadata and checksums
are stored in PostgreSQL. Questions must be original. Sample examination papers are style,
difficulty, and mark-allocation references and must not be copied verbatim.
