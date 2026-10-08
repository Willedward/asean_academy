# Grounded multi-turn AI teacher design

## Product answer

Yes. A student should be able to ask for help on any attempted question, receive
an explanation tailored to that question and approved lesson, say that they still
do not understand, and continue the same conversation. The tutor should remember
the explanation it already tried and change approach instead of repeating itself.

This is a P1/Stage 8 feature. It is deliberately disabled in Milestone 1 because
the grounding source must be reviewed lesson material, and current lesson bodies
are blank drafts. Practice, hints, deterministic marking, Give up, and approved
solutions remain fully usable without an LLM.

## Foundation status (2026-10-03)

The provider-neutral backend foundation is implemented behind
`ASEAN_ACADEMY_TUTOR_ENABLED=false`. It includes:

- learner-owned sessions pinned to exact lesson and assigned-question revisions;
- server-derived answer and solution locks refreshed from practice state;
- structured provider requests and responses with a deterministic test provider;
- an output leakage guard that replaces suspected locked-answer disclosures;
- atomic per-turn reservations, reconciliation and release records;
- daily learner message/token limits, a monthly S$7 learner cost boundary, one
  concurrent generation per learner, and an academy monthly circuit breaker;
- append-only tutor messages and usage events with provider credentials and raw
  prompts excluded from operational logs; and
- a kill switch that leaves lessons, marking, authored hints and solutions usable.

The synthetic provider is accepted only in the test environment. A Gemini REST adapter
is implemented but remains disabled. It accepts only structured responses, uses bounded
timeouts and retries, and records a configurable micro-SGD shadow cost from provider token
usage. The API key is read only from the server environment. No key is stored in content,
reports, logs or browser configuration.

The fixed provider evaluation begins with 14 synthetic cases covering all seven tutor
modes, locked and unlocked solutions, repeated confusion and prompt injection. The runner
exports a machine-readable JSON report and a reviewer-friendly Markdown rubric. Automated
PASS means only that the response was structurally valid, bounded and did not contain the
case's prohibited phrases. It never grants production approval.

Run the local no-cost contract evaluation from the repository root:

```bash
uv run --project services/learning_api --locked \
  python services/learning_api/scripts/evaluate_tutor.py --provider synthetic
```

A live Gemini run is deliberately explicit and reads the private key from the shell:

```bash
GEMINI_API_KEY=... \
  uv run --project services/learning_api --locked \
  python services/learning_api/scripts/evaluate_tutor.py --provider gemini --live
```

Reports are written under the git-ignored `build/tutor-evaluation/` directory unless an
output directory is supplied. Before student access is enabled, replace or extend the
synthetic suite with reviewed published Lesson 1 questions, hints, solutions and lesson
explanations, then obtain Mathematics and editorial approval for every output.

The first real calibration slice now uses 20 questions from the Mathematics- and
editorial-approved N2 B002 batch. It covers all five difficulty levels, outcomes 2.1–2.3,
all seven tutor modes, locked-answer conversations and one unlocked-solution explanation.
Its draft lesson grounding is intentionally marked `draft_for_review`; the review packet is
in `docs/plan/N2_TUTOR_GROUNDING_REVIEW.md` and its decisions are recorded through the
protected `/admin/content` workflow. A synthetic run passes all 20 structural and
leakage checks, but a live provider run remains blocked on grounding approval and a local
API key.

Frontend engineers should use
`docs/plan/AI_TUTOR_FRONTEND_BACKEND_HANDOFF.md` for the typed API integration boundary.
That handoff deliberately excludes visual chat design.

## Administrator conversation evaluation milestone (2026-10-08)

The protected Tutor evaluation panel includes a durable multi-turn conversation lab. An
administrator can start a synthetic or live Gemini conversation from any approved N2
calibration case, send realistic learner follow-ups, and inspect the selected tutor mode,
structured response, automated checks, latency, token usage and shadow cost for every
turn. The latest conversation for each administrator and case is restored after refresh.

Conversation records pin the exact suite, case snapshot, model and prompt version used at
creation. Each turn retains only the bounded recent history sent to the provider, while
the complete evaluation transcript remains append-only in the database. Provider failures
are also recorded so reliability problems are distinguishable from content-review
failures. This tool is the permanent pre-release quality-control path for repeated prompts
such as “Why is my answer wrong?” and “I still don't understand.” It does not enable the
student-facing feature flag or consume a learner's quota.

## Learner interaction

The question screen should offer **Ask teacher** alongside the two authored hints.
The first request creates a tutor session pinned to:

- student;
- course, unit, and lesson revisions;
- practice session and question revision;
- current attempt number and safe correctness feedback;
- hints already opened;
- whether the canonical answer and solution are locked.

A useful progression is:

1. Ask what step or term is confusing.
2. Give a short Socratic prompt based on the student's submitted work.
3. Explain the concept in a different representation or simpler language.
4. Demonstrate an analogous example with different numbers.
5. Ask the student to apply one small step to the original question.
6. After the ordinary Give up rule unlocks the solution, explain the approved
   worked solution and answer follow-up questions about its steps.

The student can continue with free text such as “I still don't get why that is a
prime number.” Each message stays in the same server-owned conversation until the
question changes or the session is closed.

## Tutor modes

- `clarify_question`: rephrase what the question asks without solving it.
- `diagnose_misconception`: use safe attempt evidence to identify a likely gap.
- `socratic_prompt`: ask one focused next-step question.
- `alternative_explanation`: explain the approved concept another way.
- `analogous_example`: work a similar example with different values.
- `solution_explanation`: available only after the server unlocks the solution.
- `lesson_recommendation`: link an approved lesson section for review.

The API, never the browser or model, selects the allowed modes from the current
answer-lock state.

The runtime now loads the latest immutable practice attempt on the server and sends only
the learner's submitted values and deterministic checker result to the provider. Canonical
answers, accepted-answer lists and locked solution steps are excluded. This supports
questions such as “Why is my answer wrong?” while keeping marking authoritative and
deterministic.

## Grounding and answer protection

Every model request receives only:

- the published lesson revision and approved worked examples;
- the student-safe form of the current question;
- approved hints and feedback already unlocked;
- the minimum relevant messages in this tutor session;
- explicit `answer_locked` and `solution_locked` flags.

Before Give up is allowed, the model must not receive the canonical answer or
worked solution. Output is parsed into a structured response, checked for schema
validity and likely answer leakage, then returned. The tutor never marks an
answer, changes mastery, unlocks content, or becomes evidence of correctness.

## Planned persistence

```text
tutor_sessions
  id, student_id, lesson_version_id, session_question_id,
  status, answer_lock_state, model_policy_version, created_at, closed_at

tutor_messages
  id, tutor_session_id, role, mode, content,
  grounding_revision_ids, model_name, prompt_version,
  safety_outcome, latency_ms, token_usage, created_at
```

Messages should be retained under the product's eventual privacy policy. Logs
must avoid full prompt/answer contents unless explicitly needed and protected.

## API boundary

```text
POST /api/v1/tutor/sessions
POST /api/v1/tutor/sessions/{sessionId}/messages
GET  /api/v1/tutor/sessions/{sessionId}
POST /api/v1/tutor/sessions/{sessionId}/close
```

The message response should contain a response type, safe rendered blocks,
suggested learner replies, recommended next action, and request ID. It should not
expose raw provider output.

## Per-learner quota and cost boundary

Tutor quotas are enforced by the Learning API, not by the browser and not solely by the
model provider. Ordinary HTTP rate limits protect request bursts. A separate durable
usage ledger protects model cost and fair access.

For each learner and UTC day, the server tracks reserved and actual request count, input
tokens, output tokens, and total tokens. Before calling a provider, it atomically reserves
the maximum permitted cost for the turn. After the response it reconciles the reservation
with provider-reported usage. A failed provider call releases the unused reservation while
retaining a small failed-call counter for abuse detection.

The pilot configuration includes:

- daily messages per learner;
- daily total model tokens per learner;
- maximum context and output tokens per turn;
- one concurrent generation per learner;
- academy-wide daily/monthly circuit breakers;
- per-learner administrative override with an audit record; and
- a reset timestamp in the standard `tutor_quota_exceeded` response.

Suggested starting values are configuration, not schema constants. Begin with 10 tutor
turns per learner per day and a 20,000 total-token daily ceiling during the Lesson 1 beta,
then reduce or increase them using real prompt size, answer quality, and cost measurements.
Students never receive the provider API key. Quota exhaustion affects only live tutor
messages; lessons, deterministic marking, authored hints, and worked solutions remain
available.

Planned accounting tables are `tutor_usage_daily` for one atomic learner/day balance and
`tutor_usage_events` for append-only reservation/reconciliation records. Stored tutor
messages reference sanitized model usage metadata. Operational logs exclude raw prompts,
student answers, tokens, and provider credentials.

## Provider strategy

Use a provider interface so the implementation can run against a local model, a
hosted model, or a disabled fallback. A local model avoids API token charges but
still needs evaluation for Mathematics accuracy, latency, RAM/VRAM, answer
leakage, and concurrency. Provider choice should follow a fixed Lesson 1
evaluation rather than price alone.

## Required before enabling

- Reviewed and published Lesson 1 material and worked examples.
- Reviewed questions, authored hints, and worked solutions.
- Server-enforced answer/solution lock state.
- Fixed evaluation conversations, including repeated “I don't understand” turns.
- Leakage, curriculum-correctness, latency, and inappropriate-output checks.
- Per-student request and model-token quotas, timeouts, logs, and a feature flag.
- A useful fallback when the model is unavailable.
