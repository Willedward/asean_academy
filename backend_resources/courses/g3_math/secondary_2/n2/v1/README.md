# Secondary 2 N2 lesson-authoring stage

This directory contains the two expanded Ratio and proportion lesson drafts for outcomes
2.4 and 2.5. They are intentionally staged outside the deployable `g3-sec2-math` snapshot
while the four N2 question batches remain planned.

The lessons may receive Mathematics and editorial feedback now. They must not be marked
reviewed or added to the learner course until the 104-question N2 bank, lesson-practice
pools, checkpoint pool and adaptive reserve pass their deterministic validation gates.

Planned integration target:

- course: `backend_resources/courses/g3_math/secondary_2/g2/v1/course.json`;
- lessons: move the reviewed JSON and SVG files into that snapshot's `lessons/` and
  `assets/` directories;
- pool manifest: add `question_pools/n2.json` after all four N2 batches are complete; and
- registry: retain N2 as `planned` until the complete deployable snapshot validates.
