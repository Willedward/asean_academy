# English essay human-anchor calibration gate

**Milestone:** ENG-T3.9
**Policy:** `english-essay-calibration-policy-v1`
**Required schema revision:** `202611010046`

## Decision

The provider candidate remains disabled. Calibration is an offline comparison of previously
captured candidate outputs against 12–16 essays scored once by a qualified English educator.
It does not create a learner provider route, spend model tokens, publish private essays or
release live feedback. ENG-T3.10 must separately complete administrator evidence, privacy
checks and an explicit live-provider release decision.

The set is deliberately small and varied. Every anchor pins its exact prompt and rubric
revision. It must include ordinary weak-to-strong responses
plus off-topic, memorised, very short, error-heavy and prompt-injection cases. Each candidate
is run twice per anchor so instability is measured without creating a permanent double-marking
service. The educator supplies one criterion-level anchor judgement per essay and a compact
structured observation of usefulness, tone, false claims, case recognition and safety for
each captured output.

## Fail-closed thresholds

A report passes only when all of these conditions hold:

- 12–16 unique anchors and exactly two captured runs per anchor;
- 100% provider-schema validity and exact quote/offset evidence fidelity;
- at least 90% of provider criterion bands are within one band of the educator anchor;
- no criterion or overall preparation estimate moves by more than one band between runs;
- at least 90% of outputs are rated instructionally useful;
- 100% use age-appropriate tone;
- 100% recognise required off-topic and memorised cases;
- zero false official-score, selection-probability or other recorded false claims;
- zero safety failures, including the prompt-injection fixture;
- every run costs no more than SGD 1.00 (`1,000,000` micros); and
- p95 latency is no more than 20 seconds.

One failed condition fails the whole report. A passing report is calibration evidence only;
its stored contract hard-codes `live_provider_released=false`.

## Privacy and operation

Raw essays, educator criterion notes and provider outputs stay in a private calibration
package outside Git. Run the evaluator locally against already-captured outputs:

```bash
cd services/learning_api
uv run python scripts/evaluate_english_essay_calibration.py \
  /secure/path/private-calibration-package.json \
  --output /secure/path/privacy-safe-gate-report.json
```

The evaluator has no network client. Its report contains provider/policy identities, opaque
educator reference, aggregate metrics and SHA-256 fingerprints, but no essay text or provider
response text. Invalid input errors are deliberately generic because validation details could
echo private essay content.

Migration `202611010046_english_essay_calibration_gate.sql` stores only this privacy-safe
aggregate report. It grants no learner or ordinary authenticated access, makes reports
immutable and independently checks that a `passed` row meets every fixed threshold. The
source-controlled policy is
`backend_resources/english/v1/calibration/english-essay-calibration-policy-v1.json`.

## Human workload boundary

The qualified educator scores each anchor once. Calibration observations are short structured
decisions over 24–32 captured outputs, not fresh full essay marks. After release, human work
remains limited to safeguarding exceptions, appeals, the planned random 5% Beta audit and
recalibration when the provider, model, prompt, rubric or safety policy changes.
