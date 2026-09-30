# Full Secondary 1–2 Mathematics course registry

## Purpose

The course registry is the canonical structural map for the complete Singapore Secondary 1 and Secondary 2 G3 Mathematics scope. It lets engineering, content generation, review tooling, and the frontend use stable course, unit, and lesson identifiers before every lesson and question bank has been authored.

The registry is separate from a deployable course snapshot. A deployable snapshot requires lesson files, reviewed notes, a learning question bank, practice pools, checkpoint capacity, and immutable database imports. A `planned` registry entry does not make unfinished content available to learners.

## Canonical source

- Registry: `backend_resources/courses/g3_math/v1/registry.json`
- JSON Schema: `backend_resources/courses/schema/course-registry-v1.schema.json`
- Syllabus source: `backend_resources/syllabi/g3_math/v1/catalogue.json`

Run:

```bash
uv run --project question_bank question-bank course-registry-validate
uv run --project question_bank question-bank course-schema
```

Validation compares the registry with the syllabus rather than trusting duplicated counts. It rejects missing or extra topic groups, changed topic ordering, incorrect unit metadata, omitted or duplicated outcomes, invalid parent keys, and duplicate lesson identifiers.

## Registered coverage

| Course | Topic groups | Outcome-linked lesson slots | Current state |
| --- | ---: | ---: | --- |
| `g3-sec1-math` | 10 | 52 | Draft: N1 authored; remaining units planned |
| `g3-sec2-math` | 9 | 35 | Planned |
| **Total** | **19** | **87** | Structurally registered |

Secondary 1 contains N1, N2, N3, N4, N5, N6, N7, G1, G5, and S1. Secondary 2 contains N2, N5, N6, N7, G2, G4, G5, S1, and S2.

Each syllabus outcome currently maps to one registry lesson slot. This keeps coverage auditable and gives the content team a deterministic starting structure. Outcomes may later be combined into a lesson only through a reviewed registry revision that continues to cover every outcome exactly once.

## Stable identifiers

- Courses: `g3-sec1-math`, `g3-sec2-math`
- Units: `g3-sec1-n1`, `g3-sec2-g4`, and equivalent level/topic combinations
- Lessons: `<topic>-lesson-<outcome suffix>`, such as `n2-lesson-04`

Topics taught at both levels retain unique lesson IDs because their outcome suffixes continue across the syllabus. Existing N1 identifiers and titles are preserved exactly.

## API behavior

Authenticated clients can read `GET /api/v1/courses`. The response reports both courses and all registered units, with `content_status`, `available`, and nullable links. Planned content has no link and cannot be opened. Draft content becomes available only when the API explicitly enables development previews; production continues to require published content.

The existing `GET /api/v1/courses/{course_key}/map` endpoint still serves only the validated authored N1 snapshot. As each topic bank and lesson set is completed, its registry status and deployable snapshot advance together.

## Next content slice

Use the registry to create one complete non-N1 calibration unit before bulk generation. N2 Secondary 1 is the recommended slice because it is small, exercises shared-topic identifiers across both school levels, and can validate the complete workflow: blueprint, five difficulty levels, lesson notes, practice pools, checkpoint allocation, review, import, and API delivery.
