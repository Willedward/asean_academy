# Mathematics lesson-note structure and coverage audit

**Audience:** secondary-school students across Indonesia and Southeast Asia preparing
for ASEAN Scholarship selection tests.

The Singapore Secondary Mathematics syllabus is a calibration and coverage reference.
It does not define the learner's country, school system or classroom vocabulary. Learner
content should use clear international English, explain unfamiliar terminology and use
contexts that work across Southeast Asia.

## Content hierarchy

Each syllabus topic group is a unit, each numbered syllabus outcome is a separate lesson,
and each lesson is divided into short teaching sections:

```text
Mathematics course
└── N1 Numbers and their operations
    ├── N1.1 Primes and prime factorisation
    │   ├── explanations
    │   ├── worked examples
    │   ├── active recall
    │   └── summary
    ├── N1.2 HCF, LCM, squares, cubes and roots
    └── ...
```

Do not combine all outcomes in a topic group into one long lesson. The stable lesson key,
outcome code, progress record, practice pool and review fingerprint remain independent for
each outcome.

## Baseline lesson-note gate

Every non-empty Mathematics lesson must contain:

- at least six substantive sections;
- at least two explanation sections;
- at least two worked examples with explicit steps and a verification note;
- at least one deterministic active-recall check;
- at least one summary or method checklist; and
- at least 2,500 authored characters across its teaching sections.

Geometry retains its stronger subject-specific gate: at least seven sections, two worked
examples, 3,000 authored characters and one referenced deterministic diagram. A lesson may
exceed these minimums when the outcome contains several methods or common misconceptions.

Run the repeatable audit with:

```bash
UV_CACHE_DIR=/tmp/nextscholar-uv-cache \
  uv run --project question_bank question-bank course-validate
```

Draft lessons below the baseline receive `lesson_notes_thin` warnings. The same findings
become errors when a lesson is marked `reviewed` or `published`, or under
`course-validate --publish`. Empty lessons continue to receive `lesson_content_required`.

## Coverage audit — 14 October 2026

| Scope | Lessons | Result |
| --- | ---: | --- |
| N1 | 7 | Meets the baseline after completing N1.2–N1.7 |
| N2 | 3 | Meets the baseline |
| N3 | 6 | Meets the baseline |
| N4 | 3 | Meets the baseline |
| N5 | 8 | **Flagged for expansion** |
| N6 | 5 | Meets the baseline after expansion and graph-diagram additions |
| N7 | 4 | Meets the baseline after equation-model and worked-example expansion |
| G1 | 7 | Meets the expanded geometry standard |
| G5 | 5 | Meets the expanded geometry standard |
| S1 | 4 | Meets the baseline after data-handling and statistical-diagram expansion |
| Secondary 2 G2 | 5 | Meets the expanded geometry standard |

The current audit therefore passes 49 of 57 authored lessons and flags eight thin lessons:
N5.1–N5.8. Those N5 lessons contain all four required section types, but currently have
only one explanation and one worked example and are below the six-section depth target.
They remain valid drafts for review, but cannot pass the strict publication gate until
expanded.

## Review and publication

Completing the structural gate does not approve or publish a lesson. Every new teaching
revision must still receive Mathematics and editorial approval for its exact fingerprint,
followed by an academic-administrator publication request and a successful content release.
