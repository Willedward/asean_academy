# Mathematics question bank sources

This directory contains version-controlled source JSON for reviewed mathematics questions. PostgreSQL is the production source of truth after validation and import.

## Layout

```text
schema/question-v1.schema.json
g3_math/secondary_1/n1/v1/blueprint.json
g3_math/secondary_1/n1/v1/questions/*.json
g3_math/secondary_1/n1/v1/assets/*.{svg,png,webp}
```

Each question file follows `question-v1.schema.json`. The blueprint fixes the bank size, difficulty mix, syllabus coverage, and publication checks. Binary or SVG assets are uploaded to object storage during import; their metadata and checksums are stored in PostgreSQL.

Question files must contain original questions. Sample examination papers are style and mark-allocation references and must not be copied verbatim.
