# AI tutor frontend-to-backend integration handoff

## Scope

This handoff covers only the frontend code that integrates the AI tutor backend:

- generated TypeScript API contracts;
- authenticated API calls;
- tutor-session lifecycle and client state;
- rendering the backend's structured response blocks;
- quota, safety and failure states; and
- contract-level tests.

It does not prescribe the chat layout, colours, typography, mascot treatment,
animations, responsive composition or other visual design. Those decisions belong to
the frontend design branch.

The backend is already implemented behind `ASEAN_ACADEMY_TUTOR_ENABLED=false`. The UI
must treat a disabled tutor as a normal product state while evaluation is incomplete.

## Source of truth

Do not hand-write duplicate API types. After rebasing onto the backend branch, regenerate
the checked-in OpenAPI artifacts from the repository root:

```bash
uv run --project services/learning_api --locked \
  python services/learning_api/scripts/export_openapi.py
corepack pnpm --filter @asean-academy/web openapi:generate
```

The generated frontend types live in `apps/web/src/lib/api/schema.d.ts`. The backend
contracts live in:

- `services/learning_api/src/learning_api/tutor_contracts.py`;
- `services/learning_api/src/learning_api/routers/tutor.py`; and
- `services/learning_api/openapi.json`.

Never edit `schema.d.ts` manually.

## Frontend API module

Add one integration module, suggested path `apps/web/src/lib/api/tutor.ts`. It should use
the existing `createApiClient` and `apiRequestError` helpers and export generated types,
not locally invented response shapes.

Suggested public functions:

```ts
createTutorSession(input, accessToken?)
getTutorSession(sessionId, accessToken?)
sendTutorMessage(sessionId, message, accessToken?)
closeTutorSession(sessionId, accessToken?)
```

The module should reject fixture mode with the same pattern used by interactive practice.
The AI tutor requires the real Learning API and must never silently return fake student
conversations in a hosted build.

## API operations

### Create a session

```http
POST /api/v1/tutor/sessions
Content-Type: application/json

{
  "practice_session_id": "UUID",
  "question_key": "n2-l2-008",
  "question_revision": 1
}
```

Create at most one active client-side session for the current practice question. The
backend verifies learner ownership and pins the exact question and lesson revisions.

### Restore a session

```http
GET /api/v1/tutor/sessions/{session_id}
```

Use this operation to restore the server-owned message history after a page refresh. Do
not treat browser storage as the authoritative conversation record.

### Send a message

```http
POST /api/v1/tutor/sessions/{session_id}/messages
Content-Type: application/json

{
  "message": "I do not understand why the ratio is simplified this way."
}
```

Messages contain 1 to 1,200 non-whitespace characters. Disable duplicate submission while
the request is pending. The endpoint currently has no message idempotency key, so the
frontend must not automatically replay a timed-out request. Present an explicit retry
action to the learner instead.

For follow-ups such as “Why is my answer wrong?”, send only the learner's chat message.
The Learning API retrieves the latest submitted practice answer and deterministic marking
result from the server-owned attempt record. The frontend must not attach an answer,
correctness flag, canonical answer or worked solution to the tutor request.

The successful response includes:

- one structured assistant message;
- `suggested_replies`, with at most four items;
- `recommended_next_action`;
- server-derived `answer_lock_state`; and
- remaining daily message, token and monthly-cost quota.

### Close a session

```http
POST /api/v1/tutor/sessions/{session_id}/close
```

Close the tutor session when the learner explicitly ends it or leaves the associated
practice question. A closed session rejects further messages.

## Structured response rendering

Render only the `message.blocks` returned by the Learning API. Supported block types are:

| Type | Frontend responsibility |
| --- | --- |
| `text` | Render as ordinary escaped text. |
| `display_math` | Render through the existing KaTeX path as display mathematics. |
| `bullets` | Render the backend-provided content as a list without executing HTML. |

Never render raw provider output or use `dangerouslySetInnerHTML` for tutor content. The
backend validates the structure and may replace a response when it detects answer leakage.

The UI may display the returned `suggested_replies` as convenience controls. Clicking one
must use the same `sendTutorMessage` path as typed input. The frontend must not invent a
tutor mode or send a mode to the backend.

## Client state

Keep the integration state small and derived from server responses:

```text
availability: unknown | disabled | available
session: absent | creating | active | closing | closed
messageSend: idle | sending | failed
sessionId: UUID or null
messages: TutorMessageResponse[]
answerLockState: server response
quota: server response
lastError: ApiRequestError or null
```

When the practice question changes, discard the previous client state and close the old
session if possible. Never reuse a tutor session across different question keys or
revisions.

## Authentication and network boundary

Browser requests should use the existing same-origin `/api/v1/...` gateway. The gateway
reads the Supabase cookie session and forwards the bearer token to the Learning API.

The frontend must never:

- call Gemini or another model provider directly;
- read, store or transmit `GEMINI_API_KEY`;
- send canonical answers or locked worked solutions;
- decide whether an answer or solution is unlocked;
- select the tutor mode;
- calculate authoritative quota; or
- use tutor text to mark a student's answer or change mastery.

The Learning API owns all of these decisions.

## Required failure states

Use `ApiRequestError.code`, HTTP status and `requestId` rather than parsing message text.

| Status | Typical code | Required behaviour |
| ---: | --- | --- |
| 401 | `authentication_required` | Return to the existing sign-in flow. |
| 403 | `active_enrolment_required` | Explain that an active beta enrolment is required. |
| 404 | `tutor_session_not_found` | Clear the stale session and allow a new session. |
| 409 | `tutor_session_closed` | Mark the conversation closed. |
| 409 | `tutor_grounding_unavailable` | Keep practice usable and disable tutor for this question. |
| 429 | `tutor_quota_exceeded` | Show the returned reset time and keep ordinary learning available. |
| 429 | rate-limit error | Ask the learner to wait before sending again. |
| 503 | `tutor_disabled` | Hide or disable the entry point without breaking practice. |
| 503 | `tutor_provider_unavailable` | Preserve the conversation and offer an explicit retry. |

Always preserve the request ID in an expandable support detail when one is returned.

## Safety outcomes

The assistant message contains one of these server decisions:

- `accepted`: render normally;
- `answer_leakage_blocked`: render the backend replacement response and do not recover the
  discarded model output; or
- `provider_fallback`: render the safe fallback content supplied by the backend.

Do not infer safety from the text itself.

## Quota presentation contract

The backend response reports:

- `daily_messages_remaining`;
- `daily_tokens_remaining`;
- `monthly_cost_remaining_micros_sgd`; and
- `resets_at`.

The UI may turn these values into a simple allowance indicator. It must not estimate
provider cost locally. Treat the backend's micro-SGD balance as authoritative and avoid
showing raw token pricing unless the product team explicitly designs that experience.

## Minimum integration tests

The frontend branch should add contract-level tests for:

1. Creating a tutor session from a real practice-session/question identity.
2. Sending one message and appending the structured assistant response.
3. Rendering `text`, `display_math` and `bullets` safely.
4. Preventing a duplicate send while one request is pending.
5. Restoring an existing session after refresh.
6. Resetting state when the practice question changes.
7. Handling `tutor_disabled` without breaking the question player.
8. Handling quota exhaustion and displaying `resets_at`.
9. Handling `answer_leakage_blocked` as a valid safe response.
10. Confirming that no provider key or direct provider URL appears in the browser bundle.

Use mocked Learning API responses in component tests. End-to-end tests should exercise the
same-origin gateway and test provider; they must not spend live provider tokens.

## Integration sequence

1. Rebase the frontend branch after the tutor OpenAPI artifacts are updated.
2. Regenerate `schema.d.ts`.
3. Add the typed `lib/api/tutor.ts` module and its unit tests.
4. Connect the module to the friend's visual components.
5. Verify disabled, quota, provider-unavailable and locked-answer states.
6. Run frontend lint, typecheck, unit tests and the tutor end-to-end path.
7. Keep the hosted feature flag disabled until the reviewed N2 model evaluation passes.

## Backend assumptions the frontend must not duplicate

- Tutor sessions are learner-owned and pinned to immutable content revisions.
- Give up and attempt state determine solution access.
- The server chooses the teaching mode from the learner message and practice evidence.
- The server performs output schema validation and answer-leakage checks.
- The server reserves and reconciles quota around every provider call.
- Tutor failure never disables authored hints, deterministic marking or worked solutions.

If an integration need conflicts with one of these assumptions, change the backend contract
first and regenerate OpenAPI instead of adding a browser-only workaround.
