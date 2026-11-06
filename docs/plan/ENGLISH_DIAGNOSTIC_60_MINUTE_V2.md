# English diagnostic v2: 60-minute objective form

**Decision date:** 6 November 2026  
**Status:** approved for implementation by the product owner

## Purpose

Replace each short 20-part English baseline, matched endline and reserve form with a
protected 60-minute form that samples vocabulary more reliably and tests reading across
both narrative and factual writing. This is a placement and progress diagnostic, not the
90-minute Section 1 full mock.

## Fixed form contract

Every baseline, endline and reserve form contains 43 scored parts:

| Part | Scored parts | Time budget |
| --- | ---: | ---: |
| Vocabulary in context | 15 | 15 minutes |
| Banked cloze | 8 | 10 minutes |
| Open cloze | 8 | 10 minutes |
| Narrative reading comprehension | 6 | 12 minutes |
| Factual/informational reading comprehension | 6 | 13 minutes |
| **Total** | **43** | **60 minutes** |

Vocabulary items are designed for roughly one minute each. Each form uses one narrative
and one informational reading passage. Reading passages target 300–450 words; cloze
passages target 150–250 words. Baseline, endline and reserve content remain mutually
disjoint and also remain separate from full-mock, lesson, practice and checkpoint pools.

## Equivalence requirements

- Vocabulary targets use approximately 60–70% B2, 20–30% C1 and no more than 10% C2,
  with no more than one C2 item per form.
- Correct-option positions and option lengths must not reveal answers.
- Each banked cloze uses eleven choices for eight gaps.
- Each open cloze includes lexical or collocational gaps as well as function-word gaps.
- Each reading pair samples literal retrieval, reference, vocabulary in context,
  inference, purpose/structure and main idea.
- The three forms use the same part counts, timing and skill mix. Human English and
  editorial review remain mandatory before publication.

## Runtime behaviour

The learner sees a 60-minute countdown based on the server-recorded session start time.
Expiry is a soft limit, matching the existing full-mock safety behaviour: the interface
states that time is up but preserves saved work and allows the learner to finish the
current protected form. This avoids losing answers through connectivity or accessibility
delays while still producing timing evidence for the pilot.

## Acceptance checks

- Foundation and authoring validators report zero new errors and zero duplicate matches.
- Each diagnostic form resolves to exactly 43 parts with distribution 15/8/8/12.
- Each form contains two reading groups: one `narrative`, one `informational`.
- Protected-form question keys are disjoint across baseline, endline and reserve.
- API landing metadata reports 43 parts and 60 minutes.
- The learner card and player show the form metadata and 60-minute countdown.
- Regression tests cover start, resume, expiry messaging, scoring and result routing.

