# Secondary 2 S2 lesson-authoring stage

This directory contains the two expanded Probability lesson drafts for outcomes 2.1 and
2.2. They are intentionally staged outside the deployable `g3-sec2-math` snapshot while
the four S2 question batches remain planned.

The lessons may receive Mathematics and editorial feedback now. They must not be marked
reviewed or added to the learner course until the 104-question S2 bank, lesson-practice
pools, checkpoint pool and adaptive reserve pass their deterministic validation gates.

Planned integration target:

- course: `backend_resources/courses/g3_math/secondary_2/g2/v1/course.json`;
- lessons: move the reviewed JSON and SVG files into that snapshot's `lessons/` and
  `assets/` directories;
- pool manifest: add `question_pools/s2.json` after all four S2 batches are complete; and
- registry: retain S2 as `planned` until the complete deployable snapshot validates.

