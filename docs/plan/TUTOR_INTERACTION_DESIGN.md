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
- Per-student rate limits, timeouts, logs, and a feature flag.
- A useful fallback when the model is unavailable.
