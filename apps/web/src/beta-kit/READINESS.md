# Readiness check (diagnostic) screens

Roadmap B-04 (diagnostic at onboarding) and B-05 (score report for a parent). Design canvas page:
"Readiness check (diagnostic)". Preview: `/beta-kit` → "Readiness check" group.

William already built the backend and his own screens (`live/live-diagnostic-view.tsx`,
`/diagnostics`). These kit screens are the designed version on the same API, plus the pieces that
were missing. Nothing of his was changed; whether to switch his pages over is his call.

## What is new compared with today

| Gap | Kit piece |
|---|---|
| No route into the check after onboarding | `ReadinessIntroScreen` straight after onboarding, before Lesson 1 ("Do it later" allowed) |
| Dashboard never asks for it | `ReadinessCard`: start, resume (5 of 12 answered), end of beta. `readinessCardKind()` picks it from `GET /diagnostics/next` |
| Results read like a test score | `ReadinessResultScreen`: strengths first, then "your next 3 topics", band shown as a 3-step scale, never "weak" |
| No way to show a parent | `ReadinessShareSheet` (private link, WhatsApp, PDF) and `ParentReportScreen` (no sign-in, scores only) |
| No start vs end view | `ReadinessCompareScreen`: both scores, band change, topic bars start → now |
| Questions not ready | `ReadinessPendingScreen` for status `content_pending` |

Mapping helpers: `readiness-adapters.ts` (`readinessFromResult`, `compareOutcomes`, `readinessCardKind`), tested.

## Backend asks

1. **Finish reward.** +50 XP and the "Starting line" badge for finishing (never for the score). End of beta: badge for the biggest improvement.
2. **Share link.** `POST /diagnostics/sessions/{id}/share` → private URL valid 30 days, revocable in Settings; a public, no-login `GET` for the parent page; a PDF of the same content. Scores only, never answers.
3. **Start and end together.** The comparison screen needs the baseline result while showing the endline one (for example `GET /diagnostics/results?purpose=baseline`, or the baseline session id on the endline result).
4. **Recommended first lesson** on the result (today the screen says "Lesson 1").
5. **Outcome titles.** Results only carry outcome codes; the screen takes titles from the course map.
6. Open roadmap decisions: English in the check (roadmap 10.6), and parent contact at onboarding (10.7).
