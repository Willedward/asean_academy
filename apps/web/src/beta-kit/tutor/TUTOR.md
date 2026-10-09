# Ask the hornbill: AI tutor frontend (V2-15)

The learner side of William's tutor backend (`feat/tutor-hybrid-model-routing`), built from the
design canvas page "AI tutor (V2)". Product plan: `AI_TUTOR_PLAN.md` in the ASEAN Academy project.
API contract: `docs/plan/AI_TUTOR_FRONTEND_BACKEND_HANDOFF.md`.

Only new files were added. No existing page or component was changed.

## See it

```bash
corepack pnpm dev:web
# open http://localhost:3000/beta-kit/tutor
```

13 screens on sample data, one per canvas board. Each one is responsive: phones get a tall sheet
over the question, desktops a panel on the right. "Phone and desktop" shows both side by side.

## Files

| File | What it is |
|---|---|
| `src/lib/api/tutor.ts` | Typed API calls: `createTutorSession`, `getTutorSession`, `sendTutorMessage`, `closeTutorSession`. Generated types only, same-origin gateway, refuses fixture mode, every failure becomes a `TutorApiError` (status, code, requestId, details). |
| `tutor/use-tutor.ts` | Client state machine from the handoff: one send at a time, explicit retry only, restore after refresh (session id in sessionStorage, history from the server), close the session when the learner leaves the question. |
| `tutor/tutor-dock.tsx` | **The drop-in.** Entry button plus chat window, wired to the API. |
| `tutor/tutor-view.tsx` | The chat window, stateless. Phone sheet / desktop panel. |
| `tutor/parts.tsx` | Bubbles, pinned question, starters, suggestions, next step, composer, quota and error notices. Replies render through the existing `TutorContent` (KaTeX, no raw HTML). |
| `tutor/launcher.tsx` | "Ask the hornbill" button, nudge bubble, desktop side card. |
| `tutor/sheets.tsx` | Report a reply, free-plan Season pass sheet. |
| `tutor/format.ts` | Error code to UI mapping, quota rules, "7:00 tomorrow" reset label. |
| `tutor/preview.tsx`, `tutor/sample.tsx` | Previews and sample data only. |
| `app/beta-kit/tutor/**` | Preview routes (same production gate as `/beta-kit`). |

## Wiring it into practice

`TutorDock` is one component. Put it where the button should appear; the window is fixed to the
screen, so it does not change the page layout. Each question key gets a fresh conversation.

In `live-practice-view.tsx`, next to the Hint buttons:

```tsx
import { TutorDock } from "../tutor/tutor-dock";

{!checkpoint ? (
  <TutorDock
    practiceSessionId={sessionId}
    questionKey={question.stable_key}
    questionRevision={question.revision}
    practiceMode={current.session.mode}
    wrongTries={attempt?.correct ? 0 : Math.max(attempt?.attempt_number ?? 0, current.attempt_count ?? 0)}
    solutionOpen={Boolean(solution)}
    questionLabel={`Question ${position}`}
  />
) : null}
```

Rules it already follows (from the plan, 2026-10-09):

- **Hidden before the first try and in checkpoints.** `wrongTries` 0 or `practiceMode="checkpoint"` renders nothing.
- **Hidden when the tutor is off.** A `503 tutor_disabled` (flag off) removes the button. Practice is untouched.
- **Quota stays out of sight** until 3 or fewer messages are left. At 0, a "back at 7:00 tomorrow" card replaces the input.
- **No XP for chatting.** The XP rule (right after tutor help = +6, like a hint) belongs to the backend: record "tutor used" on the attempt.

Optional props: `launcher="nudge"` (button plus the hornbill's speech bubble, phones), `launcher="card"`
(desktop side card with starter questions), `plan="locked"` (free plan), `onOpenChange` (add
`lg:pr-[456px]` to the page while the desktop panel is open), `onReport`, `onSendToParent`.

## Error handling

Mapped by `code` and status, never by message text (`format.ts`, tested):

| Server says | Learner sees |
|---|---|
| 401 | Sent to sign in |
| 403 `active_enrolment_required` | "The hornbill needs an active course" |
| 404 `tutor_session_not_found` | Session forgotten; "This chat timed out", sending again starts a new one |
| 409 `tutor_session_closed` | "This chat has ended" |
| 409 `tutor_grounding_unavailable` | "Can't help with this question yet", hints and solution still work |
| 429 `tutor_quota_exceeded` | Sleepy hornbill, reset time from `details.resets_at` |
| 429 other | "Wait a moment" with Try again |
| 503 `tutor_disabled` | Button disappears |
| 503 `tutor_provider_unavailable`, 5xx, network | "Can't answer right now", chat kept, Try again, support code |

`answer_leakage_blocked` replies render normally with a small "answer stays hidden" note.

## Backend asks (not built yet)

1. Server rule: a session needs at least one submitted try (`tutor_attempt_required`). The UI already handles the code.
2. `recommended_next_action` as `{type, label, target}`. Today it is text, so the button only goes back to the question.
3. `POST /tutor/sessions/{id}/messages/{message_id}/report` with `{reason, note}`. Reasons: `maths_wrong`, `gave_away_answer`, `confusing`, `other`. Until it exists, leave `onReport` out and the link is hidden.
4. `tutor_plan_required` for free accounts (opens the Season pass sheet).
5. Record "tutor used" on the attempt so a right answer after tutor help earns +6 XP, not +10.
6. Optional: a server greeting. Today the hello and starter buttons are written by the frontend.

## Tests

`src/lib/api/tutor.test.ts`, `tutor/format.test.ts`, `tutor/tutor-dock.test.tsx`. They cover all 10
"minimum integration tests" in the handoff, plus hidden-before-first-try, low quota, explicit retry
and the free plan. Run with `corepack pnpm test:web`.
