# Secondary 1 N2 calibration batch

## Status

The first controlled N2 batch, `g3-sec1-n2-b001`, is authored and marked `ready_for_review`. It contains 26 original questions covering the Secondary 1 syllabus outcomes:

- 2.1 ratios involving rational numbers;
- 2.2 writing a ratio in its simplest form; and
- 2.3 problems involving ratio.

The files are under `backend_resources/question_bank/g3_math/secondary_1/n2/v1/`. The batch manifest records the generator and prompt versions, syllabus and house-rule checksums, style references, exact allocation, and reserved question keys.

## Calibration distribution

| Outcome | Level 1 | Level 2 | Level 3 | Level 4 | Level 5 | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2.1 | 2 | 3 | 2 | 2 | 0 | 9 |
| 2.2 | 2 | 2 | 3 | 1 | 1 | 9 |
| 2.3 | 2 | 2 | 3 | 1 | 0 | 8 |
| **Total** | **6** | **7** | **8** | **4** | **1** | **26** |

Each question has two staged hints, a fully marked worked solution, provenance, and a deterministic answer contract. This batch also introduces `exact_ratio`, which accepts equivalent colon or `to` notation and can require simplest positive integer terms.

## Automated evidence

The aggregate validator confirms:

- all 19 blueprints and 75 manifests remain covered;
- all 26 N2 files match the batch allocation and reserved keys;
- canonical and accepted answers execute successfully;
- source checksums and question contracts are valid; and
- there are no exact or near-prompt duplicates across the 66 authored questions.

Generate the reviewer packet from the repository root:

```bash
uv run --project question_bank question-bank authoring-export \
  backend_resources/question_bank/g3_math/secondary_1/n2/v1/batches/g3-sec1-n2-b001.json \
  backend_resources/question_bank/g3_math/secondary_1/n2/v1/review_packets/g3-sec1-n2-b001 \
  --syllabus backend_resources/syllabi/g3_math/v1/catalogue.json
```

Open `backend_resources/question_bank/g3_math/secondary_1/n2/v1/review_packets/g3-sec1-n2-b001/index.html` for the formatted questions, hints, and solutions. Record per-question decisions and comments in `review.md` directly from VS Code; `review.csv` remains available for spreadsheet workflows. Mathematical and editorial reviewers should check correctness, age-appropriate wording, curriculum alignment, difficulty, marks, and whether each hint reveals an appropriate amount.

## When more examination data helps

Additional papers are not required to review this calibration batch or test the pipeline. The existing references are enough for an initial N2 sample. More representative Secondary 1 papers and marking schemes become valuable after the team reviews this batch and before batches B002–B004 are authored. They can help calibrate school-specific phrasing, mark allocation, calculator expectations, multi-step difficulty, and the balance between routine and unfamiliar problems.

The most useful feedback before scaling is the completed Markdown review (or CSV export) plus any notes describing which questions felt easier or harder than their assigned level. That evidence should be used to adjust the remaining N2 blueprint and authoring prompt before producing another 78 N2 questions.
