# Mathematics question-authoring prompt contract v2

Use this contract with g3_math_house_rules_v2_draft. It incorporates the technical
pre-review findings from the complete Secondary 1 N2 calibration unit.

For every allocated stable key:

1. Write an original question whose actual task assesses the allocated syllabus outcome.
   Related topic vocabulary is not enough. In particular, keep direct simplification,
   comparison, equivalence and application outcomes distinct when the syllabus separates
   them.
2. Match the five-level rubric. Levels 4 and 5 need real method selection, constraints,
   justification or synthesis; extra arithmetic alone does not raise difficulty.
3. Search the existing catalogue for the combination of context, operation pattern and
   numerical structure. Replace a question when that semantic combination already exists,
   even if its wording differs.
4. Use Singapore/British English, metric units and S$ for learner-facing
   Singapore-dollar amounts. State the requested response unit explicitly.
5. Provide exactly two ordered hints. The first identifies the concept or decision. The
   second gives an intermediate setup. Neither gives the final answer.
6. Recompute the answer independently, then substitute it into every original condition.
   Ensure the canonical answer, accepted answers, response checker and worked solution agree.
7. Award method and accuracy marks explicitly, keep their sum equal to the part marks, and
   do not assume error-carried-forward credit.
8. Run aggregate validation and inspect the rendered reviewer packet before changing the
   batch to ready_for_review.

Human Mathematics and editorial decisions remain mandatory. Automated validation and this
prompt contract do not approve content.
