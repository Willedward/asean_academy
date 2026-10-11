# Secondary 1 N2 calibration unit

## Status

Secondary 1 N2 is the first complete non-N1 calibration unit. Its source contains all 104 planned questions across the three syllabus outcomes and all five difficulty levels:

- 2.1 ratios involving rational numbers;
- 2.2 writing a ratio in its simplest form; and
- 2.3 problems involving ratio.

The aggregate authoring validator reports 144 authored questions across N1 and N2 with zero errors, zero warnings and no exact or near-prompt duplicates. N2 batch state is:

| Batch | Questions | State |
| --- | ---: | --- |
| `g3-sec1-n2-b001` | 26 | `approved` |
| `g3-sec1-n2-b002` | 26 | `approved` |
| `g3-sec1-n2-b003` | 26 | `approved` |
| `g3-sec1-n2-b004` | 26 | `approved` |
| **Total** | **104** | All four batches approved |

Every question has two staged hints, a marked worked solution, provenance and a deterministic answer contract. The bank includes `exact_ratio`, which accepts supported ratio notation and can require simplest positive integer terms.

## Deployable course integration

The `g3-sec1-math` course snapshot now includes `g3-sec1-n2` and three fully written, reviewed lessons. Each lesson has explanations, worked examples, active recall and a summary. The N2 pool manifest allocates every question exactly once:

| Pool role | Questions |
| --- | ---: |
| Lesson practice | 60, split evenly across the three outcomes |
| Unit checkpoint | 20 |
| Adaptive reserve | 24 |
| **Total** | **104** |

All four question batches, all three N2 lessons and the N2 additions in course revision 3 have Mathematics and editorial approval. The complete Secondary 1 course cannot be published until the seven N1 lessons pass their independent review and the remaining publication evidence is recorded.

## Validation and review

Run from the repository root:

```bash
uv run --project question_bank question-bank authoring-validate
uv run --project question_bank question-bank catalogue-validate
uv run --project question_bank question-bank course-validate
uv run --project question_bank question-bank course-registry-validate
```

Reviewer packets for all four batches are stored under `backend_resources/question_bank/g3_math/secondary_1/n2/v1/review_packets/`. Open each `index.html` for the formatted questions, hints and solutions, then record Mathematics and editorial decisions through the protected content dashboard or the packet's `review.md` fallback.

The deployment bootstrap imports the complete question catalogue before the course snapshot, so the N2 pool foreign keys resolve in disposable CI databases and hosted staging. The production release workflow still fails closed until all required review and publication evidence exists.

The technical pre-review audit recomputed all 78 pending-question answers and inspected all
three lessons. It corrected B004 outcome alignment, a semantic duplicate and currency
notation, then produced house rules and prompt contract v2 for future batches. See
[N2_CALIBRATION_PRE_REVIEW_AUDIT.md](N2_CALIBRATION_PRE_REVIEW_AUDIT.md). The audit did not
replace human review; those decisions are now recorded as approved for all four batches,
all three N2 lessons and the N2 additions in course revision 3.
