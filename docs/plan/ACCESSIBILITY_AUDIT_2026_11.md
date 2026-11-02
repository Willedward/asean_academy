# Accessibility audit: learner and admin screens (local)

**Date:** 2 November 2026

**Branch base:** `origin/feature/bulk-question-authoring-pipeline` at `fe25859`

**Decision boundary:** report only. This audit changes no product code, content, configuration
or review state. It does **not** complete the hosted acceptance item in
[B5_CONTENT_RELEASE_CONTROLLED_PILOT.md](B5_CONTENT_RELEASE_CONTROLLED_PILOT.md) ("Complete
keyboard, focus, contrast and 390/768/1440-pixel visual checks"). That item still needs a
run against the deployed candidate SHA. This document tells that run what to fix first and
what to re-check.

## Summary

The learner and admin screens are largely in good shape:

- Pages have a single labelled `nav` and `main` and `lang="en"`.
- Answer inputs have labels.
- Right and wrong answers are shown in text, not only by colour.
- KaTeX outputs MathML.
- 25 of 26 screens have no horizontal page scroll at 390, 768 or 1440 px.

Eight problems should be fixed before the hosted keyboard and focus check. Without these fixes
the hosted check would fail:

1. **After "Check final answer", keyboard focus is lost to `<body>`.** This was measured at
   390 and 1440 px. It breaks the core practice loop for keyboard and screen-reader users.
2. **The phone tutor sheet is not modal.** Tab leaves it and moves into the hidden page behind
   it. Escape then stops working, and closing the sheet sends focus to `<body>`.
3. **On phones, the fixed bottom navigation can completely cover the focused control** (WCAG 2.2
   2.4.11).
4. **Every page has the same `<title>` ("NextScholar").** Next.js therefore never announces
   client-side route changes.
5. **The admin invitations page scrolls horizontally at 390 px.** The document is 684 px wide.
6. **The dark diagnostic result card has text at 2.04:1 and 1.45:1 contrast.** This finding is
   from static analysis only, because the screen could not be reached locally.
7. **Lesson and practice math has an `aria-label` of raw LaTeX on a generic `<span>`** (axe:
   serious, 69 nodes). Display equations wider than the screen sit in a scroll area that
   keyboard users cannot reach.
8. **There is no skip link** on any of the 26 screens.

## Method

Everything ran in the session container against `127.0.0.1` only. No hosted staging,
production, Supabase or OAuth endpoint was contacted.

1. **Stack.** I used the same disposable stack as the `authenticated-e2e` CI job:
   - local PostgreSQL 16, with `scripts/validate_migrations.sh` plus catalogue, course and
     English imports;
   - `seed_e2e.py`;
   - `learning_api` on port 8100 (`ASEAN_ACADEMY_ENV=test`, synthetic tutor provider);
   - `next dev` on port 3100 with `ASEAN_ACADEMY_BETA_LEARNING_UI=true`.

   Sign-in used the existing local E2E session route with the seeded `student.a` and
   `academic` identities. The database was deleted afterwards.
2. **Crawl.** Playwright drove the preinstalled Chromium at 390×844, 768×1024 and 1440×900
   across 26 screens.

   **Learner screens:** login, home, onboarding, readiness landing, learn, course map,
   lesson `n1-lesson-01`, practice (before and after a wrong answer, and with the tutor open),
   progress, English home, English lesson `e0-lesson-01` and the English essay editor.

   **Admin screens:** overview, students, student detail, questions, reports, content,
   tutor evaluation, invitations, audit, users, essay feedback and operations.

   For each screen and width the crawl recorded:
   - axe-core 4.10.3 results (WCAG 2.0/2.1/2.2 A and AA, plus best practice);
   - document `scrollWidth`;
   - elements wider than the viewport;
   - text smaller than 12 px;
   - targets smaller than 24 px;
   - KaTeX structure;
   - headings, landmarks and skip links;
   - full-page screenshots.

   At 1440 px it walked 60 Tab stops, and at 390 px 25 Tab stops. At each stop it recorded the
   computed outline or ring and whether `elementFromPoint` showed the focused element covered.
3. **Targeted probes.** I added extra checks for:
   - focus and live regions after checking an answer;
   - tutor dialog semantics, its Tab sequence, Escape and focus return;
   - the admin mobile navigation drawer;
   - reflow at 320 px on four learner screens;
   - KaTeX wrappers, scroll containers and the Chromium accessibility tree;
   - the cause of the invitations-page overflow;
   - the focus style of the essay editor.
4. **Static source review.** I reviewed `src/beta-kit/live/*`, `src/beta-kit/components/*`,
   `src/beta-kit/tutor/*`, `src/components/*`, the theme tokens and layouts. I computed WCAG
   contrast ratios from the tokens in `src/beta-kit/theme.css`.

The **Evidence** column below says how each finding was established:

- **Live** means it was measured in the running app.
- **axe** means axe-core reported it in the running app.
- **Static** means it comes from source review only. Re-check these on the hosted run.

The Next.js dev-tools portal (`<nextjs-portal>`) only exists in `next dev`. It appeared in the
Tab order and was excluded from all results.

## Ranked findings

Priority definitions:

- **P1:** blocks the hosted keyboard, focus, contrast or mobile acceptance item, or blocks a
  core learner task for assistive-technology users.
- **P2:** a WCAG 2.2 AA failure or significant barrier with a workaround.
- **P3:** best practice or polish.

### P1: fix before the hosted acceptance run

#### P1-1. Focus is lost after checking an answer, and feedback is announced unreliably

- **Evidence:** Live at 390 and 1440 px; also static.
- **WCAG:** 2.4.3 Focus Order, 4.1.3 Status Messages.
- **Files:** `apps/web/src/beta-kit/live/live-practice-view.tsx:415-445`; the same pattern is in
  `apps/web/src/components/english-practice-player.tsx:946-954`.
- **What happens:**
  - After a wrong final answer is submitted with "Check final answer",
    `document.activeElement` is `<body>` at both widths.
  - The focused Check button gets `disabled={busy || …}` (line 423) while the request runs, so
    the browser drops focus.
  - The `finished ? <Button>Continue</Button> : <>…Check…</>` swap and the hint buttons that
    become `disabled` after use (lines 432 and 438) do the same.
  - The "Try again" callout (`role="status"`) is inserted together with its text, so a screen
    reader may never announce it.
  - The next Tab starts again from the logo.
- **Proposed fix:**
  - Keep one feedback live region permanently in the DOM and change only its text.
  - After a check or Continue, move focus programmatically to the feedback heading, or to the
    question `H1` with `tabIndex={-1}`.
  - While busy, use `aria-disabled` and ignore clicks instead of `disabled`.
  - Keep used hint buttons focusable with `aria-disabled="true"` plus "(opened)" in the name.

#### P1-2. The phone tutor sheet is not modal: focus escapes, Escape fails, and focus is not returned

- **Evidence:** Live at 390 and 1440 px; also static.
- **WCAG:** 2.4.3, 2.4.11, 4.1.2.
- **Files:**
  - `apps/web/src/beta-kit/tutor/tutor-view.tsx:146-156` (`role="dialog"`, no `aria-modal`)
  - `apps/web/src/beta-kit/tutor/tutor-view.tsx:251` (`fixed inset-0` below `lg`)
  - `apps/web/src/beta-kit/tutor/tutor-dock.tsx:159` (`onClose={() => setOpen(false)}`)
  - `apps/web/src/beta-kit/tutor/launcher.tsx`
- **What happens at 390 px:**
  - Opening the tutor correctly puts focus in the textarea.
  - Five Tabs later, focus moves to "Report a problem", the navigation and the answer input.
    These are behind the full-screen sheet and invisible.
  - Escape is handled by `onKeyDown` on the dialog, so once focus has escaped, Escape does
    nothing. The dialog stayed open.
  - Closing with the close button leaves focus on `<body>`.
- **What happens at 1440 px:** the tutor is a side panel and non-modal behaviour is acceptable.
  Escape closed it, but focus again went to `<body>` and not to "Ask the hornbill".
- **Proposed fix:**
  - Below `lg`, add `aria-modal="true"` and either make the page root `inert` or use a focus
    trap.
  - Handle Escape at document level while the sheet is open.
  - Keep a ref to the launcher and call `.focus()` in `onClose` at every width.
- **Related static finding:** the shared `Sheet` primitive
  (`apps/web/src/beta-kit/components/ui.tsx:582-601`) declares `aria-modal="true"` but has no
  initial focus, Escape handling, focus trap or focus return. In the live product it is used
  by `TutorPlanSheet` when the server returns `planRequired` (`tutor-dock.tsx:109,188`).
  Implement focus management once in `Sheet`, or use a native `<dialog>` with `showModal()`.

#### P1-3. The fixed bottom navigation hides focused controls on phones

- **Evidence:** Live at 390 px.
- **WCAG:** 2.4.11 Focus Not Obscured (Minimum, AA in 2.2).
- **File:** `apps/web/src/beta-kit/live/core-learning-shell.tsx:69` (`fixed inset-x-0 bottom-0 h-[72px]`).
- **What happens:**
  - Tabbing on `/learn` brings "View English" into view at y = 781–825.
  - It sits entirely under the 72 px navigation (y = 772–844), and all three sample points hit
    `nav[aria-label=Main]`.
  - The same happens to "Open lesson" on `/progress` (y = 793–837 and 800–844).
  - The 112 px bottom padding on `main` (`pb-28`, line 200) only stops the *last* content from
    being covered. It does not stop the browser scrolling a focused element to the viewport
    edge.
- **Proposed fix:** set `scroll-padding-bottom: 88px` on `html` while the bottom navigation is
  visible (below `lg` and outside focus mode). For example, add a class on `ns-root` and a rule
  in `theme.css`.

#### P1-4. Every page has the same title, so client-side navigation is never announced

- **Evidence:** Live (26 of 26 screens) and static.
- **WCAG:** 2.4.2 Page Titled, 4.1.3.
- **File:** `apps/web/src/app/layout.tsx:15-19` (`title: "NextScholar"`). No learner or admin
  page exports `metadata` or `generateMetadata`.
- **What happens:**
  - All screens report `document.title === "NextScholar"`.
  - Next's route announcer announces only when `document.title` changes, so screen-reader
    users hear nothing when moving between Learn, a lesson, practice or any admin view.
- **Proposed fix:**
  - Set `title: { default: "NextScholar", template: "%s · NextScholar" }` in the root layout.
  - Export `metadata` from static pages ("Progress", "Admin · Invitations", and so on).
  - Use `generateMetadata` for lesson, practice and essay pages. For example, "Question 1 of 9
    · Primes and prime factorisation" is acceptable. Do not put learner data in titles.

#### P1-5. The admin invitations page scrolls horizontally at 390 px

- **Evidence:** Live.
- **WCAG:** 1.4.10 Reflow.
- **File:** `apps/web/src/components/admin-invitations-panel.tsx:290-292`.
- **What happens:**
  - Document `scrollWidth` is 684 px in a 390 px viewport, so the page scrolls sideways.
  - The table itself is correctly clipped by its `overflow-x-auto` wrapper (wrapper 356 px,
    table 771 px).
  - The cause is the `<span className="sr-only">Actions</span>` inside the last `<th>`.
    `sr-only` is `position:absolute`, and no ancestor is positioned. Its containing block is
    therefore the viewport, so the scroll wrapper does not clip it and it extends the document
    to x ≈ 684.
  - Other admin tables have no `sr-only` header and do not overflow.
- **Proposed fix:** add `relative` to the `overflow-x-auto` wrapper (or to the `<th>`). Add an
  E2E assertion with `expectNoPageOverflow` at 390 px for `/admin/invitations`.

#### P1-6. The diagnostic result card on a dark background fails contrast

- **Evidence:** Static (contrast computed from tokens).
- **WCAG:** 1.4.3.
- **File:** `apps/web/src/beta-kit/live/live-diagnostic-view.tsx:480-501`.
- **What happens:**
  - The card uses `tone="brand"`, with an `ns-ink` (#0f3d40) background.
  - The `Eyebrow` "… MATHEMATICS READINESS" uses `text-ns-amber-text` #94560f, which gives
    **2.04:1**.
  - The `ProgressBar` value uses `text-ns-muted` #4e6667 on `bg-white/10` over ink (about
    #275053), which gives **1.45:1**.
  - The local seed has no published readiness form ("Readiness check is being prepared"), so
    the result screen could not be rendered.
- **Proposed fix:**
  - Add an `onDark` variant to `Eyebrow` that uses `text-ns-gold` (5.49:1 on ink).
  - Give `ProgressBar` an `onDark` option that uses `text-ns-on-dark-muted` (6.04:1) or
    `text-ns-on-brand`.
  - Re-check with a published form.

#### P1-7. KaTeX: a prohibited `aria-label` and display math that keyboard users cannot scroll

- **Evidence:** axe, Live and static.
- **WCAG:** 4.1.2, 1.3.1, 2.1.1, 1.4.10.
- **File:** `apps/web/src/components/math-content.tsx:24-37`.
- **What happens:**
  - `aria-label={latex}` sits on a role-less `<span>`. axe reports `aria-prohibited-attr`
    (serious) on 69 nodes across lesson, practice, feedback and tutor screens at all widths.
  - Chromium ignores it, but other browser and screen-reader pairs may read raw LaTeX
    (`360=2\times180…`) instead of the MathML.
  - Display math uses `overflow-x-auto` on a non-focusable span. At 390 px, the equation
    `360=2\times180=2\times2\times90=2\times2\times2\times45` is 374 px wide inside a 260 px
    scroller, and axe reports `scrollable-region-focusable` (serious).
  - KaTeX output itself is good:
    - all 20 lesson expressions include `.katex-mathml` with `.katex-html[aria-hidden=true]`;
    - there are no `.katex-error` nodes;
    - rendered sizes are 19.4 px inline and 21.8 px display;
    - there is no page-level overflow at 320 px.
- **Proposed fix:**
  - Remove `aria-label` and let the MathML be read.
  - For display mode, use the kit pattern already in `src/beta-kit/screens/lesson.tsx:157-176`
    (`ScrollMath`: `role="region" tabIndex={0} aria-label="Equation, scroll horizontally"`)
    with a visible focus ring.
  - Where an authored spoken form exists (the lesson already has text such as "2 cubed times 3
    squared times 5 equals 360"), put it in an adjacent `sr-only` span and keep the MathML.

#### P1-8. No skip link on any screen

- **Evidence:** Live (0 of 26) and static.
- **WCAG:** 2.4.1 Bypass Blocks. Landmarks technically satisfy this criterion, but keyboard
  users still need a skip link.
- **Files:** `apps/web/src/beta-kit/live/core-learning-shell.tsx:175-210` and
  `apps/web/src/beta-kit/live/admin-shell.tsx:220-320`.
- **What happens:** at 1440 px, admin pages put up to 11 navigation links plus the account card
  before `<main>`, and learner pages put 6 to 8.
- **Proposed fix:** add a first-focusable "Skip to content" link targeting
  `<main id="main" tabIndex={-1}>`, reusing the pattern in
  `src/components/marketing/marketing-landing.tsx:239-245`.

### P2: fix during the pre-Beta polish pass

| # | Finding | Evidence | File(s) | Proposed fix |
| --- | --- | --- | --- | --- |
| P2-1 | Locked English lesson rows use `opacity-70`, so muted text falls to **3.17:1** (#839495 on #fff). axe `color-contrast` reports 30 nodes per width. | axe | `apps/web/src/beta-kit/live/english-learning-screens.tsx:221` | Drop `opacity-70`. Show the locked state with a lock icon and the text "Locked". Keep `text-ns-muted` (6.14:1). |
| P2-2 | Placeholder `placeholder:text-ns-muted/80` is 3.89:1 on white. | Static | `apps/web/src/beta-kit/live/live-practice-view.tsx:292`, `live-diagnostic-view.tsx:375`, `src/beta-kit/tutor/parts.tsx:522` | Use `placeholder:text-ns-muted` (6.14:1). |
| P2-3 | The kit `focusRing` (`outline-ns-success` #1f6f8b) is **2.10:1** against `ns-ink`. This affects the gold CTA inside brand cards (for example `core-learning-screens.tsx:142`). | Static | `apps/web/src/beta-kit/components/ui.tsx:15-16` | Add `focusRingOnDark` (`outline-ns-gold`) and apply it to controls on `tone="brand"` cards. |
| P2-4 | The token `--color-ns-brand` is not defined. Only `--color-ns-brand-soft` is. As a result, `focus:border-ns-brand`, `focus:ring-ns-brand/20`, `has-[:checked]:border-ns-brand` and `accent-ns-brand` generate no colour. On the essay editor, focus is still visible because the ring falls back to the ink colour (live: a 2 px #0f3d40 box-shadow), but the intended styling is missing. The feedback rating pills hide the radio with `sr-only`, have no focus style on the label, and show the selected state only as `bg-ns-brand-soft` on white (1.20:1). | Live (editor) and static (pills) | `apps/web/src/beta-kit/theme.css:26`; `src/components/english-essay-draft-editor.tsx:349,488`; `english-essay-self-review.tsx:309,333,347,369,377`; `english-essay-feedback-report.tsx:458-466,479` | Define `--color-ns-brand: #0f3d40`, or replace with `ns-ink`. Give the pills `has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-ns-success` and a check icon plus a 2 px `ns-ink` border when selected. |
| P2-5 | Admin table scroll wrappers cannot be reached by keyboard. axe reports `scrollable-region-focusable` at 390 px on questions, audit and student detail. | axe | `apps/web/src/components/admin-dashboard.tsx:101`; `admin-invitations-panel.tsx:290`; `tutor-routing-evidence-panel.tsx:630-631` (`min-w-[78rem]`) | Add `role="region" tabIndex={0} aria-labelledby={tableHeadingId}` and a focus ring to each wrapper. Consider `<caption>`; no admin table has one. |
| P2-6 | Tutor evaluation nests a second `<main>` inside the admin shell's `<main>`. axe reports `landmark-no-duplicate-main`, `landmark-main-is-top-level` and `landmark-unique` at all widths. | axe | `apps/web/src/components/tutor-evaluation-panel.tsx:285,469` | Change the inner element to `<section aria-labelledby=…>`. |
| P2-7 | Answer helper and error text are not linked to the input. Examples are "Enter an algebraic expression using standard keyboard notation." and `result.error`. | Static (helper visible live) | `apps/web/src/beta-kit/live/live-practice-view.tsx:301-310`; `live-diagnostic-view.tsx:379-383`; `src/components/onboarding-form.tsx:88-90` | Give the helper and error text ids and add `aria-describedby` on the input. |
| P2-8 | "Report a problem" replaces the button with a form without moving focus. Cancel and Send unmount the focused control. | Static | `apps/web/src/components/question-report-form.tsx:55-90,138` | Focus the reason select on open. Return focus to the "Report a problem" button on cancel or after a send, and announce the confirmation in a persistent status region. |
| P2-9 | Two selects and one textarea in the review form have no label (the textarea has a placeholder only). They render only after an evaluation run exists, so axe did not see them locally. | Static | `apps/web/src/components/tutor-evaluation-panel.tsx:405,416,450` | Wrap them in `<label>` elements or add `aria-label` ("Review dimension", "Decision", "Review notes"). |
| P2-10 | Focus indicators in the established (fallback) UI are weak. `ring-teal-500` is about 2.4:1 on white, and `outline-none` with `ring-teal-100` is about 1.1:1. These are used when `ASEAN_ACADEMY_BETA_LEARNING_UI` is off and by admin `Button`. | Static | `apps/web/src/components/ui/button.tsx:8`; `src/components/onboarding-form.tsx:102,123` | Use `ring-teal-700` or an outline of at least 3:1, and drop `outline-none`. |
| P2-11 | Some loop animations have no way to pause: the hornbill idle loop, the gold-button glow and the entry float. Reduced motion *is* respected: live, no animations ran on the lesson page under `prefers-reduced-motion: reduce`. | Static | `apps/web/src/beta-kit/components/hornbill.module.css:15-40`; `ui.tsx:32`; `live/live-entry.tsx:62,158` | Stop loops after a few cycles, or extend the existing celebrations toggle to cover them. |
| P2-12 | Onboarding has two `h1` elements ("Welcome to the beta." and "Activate student access"). Home and lesson jump from `h1` to `h3` ("Learn in course order", "By the end you can"); axe reports `heading-order`. | Live and axe | `apps/web/src/beta-kit/live/live-entry.tsx:168,239`; `live-landing.tsx:11`; `live-lesson-view.tsx:120` | Make the second onboarding heading an `h2`. Use `H2` for the first section heading under the page `H1`. |

### P3: best practice and polish

- **The `Callout` component is always `role="status"`** (`src/beta-kit/components/ui.tsx:462`).
  Static information callouts, such as "Development practice", therefore become live regions.
  Some are nested inside `role="alert"` (`live-entry.tsx:83-87`). Make the role opt-in.
- **The tutor message list has nested live regions.** `aria-live="polite"` wraps the starter
  buttons and a nested `role="status"` "Thinking" indicator (`tutor-view.tsx:183`,
  `tutor/parts.tsx:253`), which risks double announcements. Put the live region on the message
  log only, with `role="log"`.
- **`QuestionPin` has `aria-label="Show the question"`, which overrides the visible "Question 1 ·
  2 wrong tries"** (`tutor/parts.tsx:125-133`, WCAG 2.5.3 Label in Name). Use
  `${label}: show the question`.
- **The essay-feedback checkboxes are 13×20 px** (`english-essay-release-panel.tsx`). They pass
  2.5.8 because the wrapping label enlarges the target, but `size-5` would help touch users.
- **`scrollIntoView({behavior:"smooth"})` ignores reduced motion**
  (`english-practice-player.tsx:359`).
- **The amber progress fill on the `brand-soft` track is 2.79:1** (`ui.tsx:366-375`). The value
  is also shown as text, so this is minor.
- **Preview-only kit screens use `aria-pressed` buttons for single-choice answers**
  (`src/beta-kit/screens/lesson.tsx:295-298`, `screens/english.tsx:505-507`). If they are
  ported to live, use native radios in a `fieldset`, as the live English player already does.

## Checks that passed

- **Layout, 390/768/1440:** no horizontal page scroll on 25 of 26 screens (the exception is
  P1-5). There is no text under 12 px on live screens. Apart from the essay-feedback
  checkboxes, every target under 24 px is the 132×21 logo link, which passes 2.5.8 by spacing.
  Reflow at 320 px passed on `/learn`, the lesson, `/progress` and `/english`.
- **Admin mobile navigation drawer:**
  - Focus moves into the drawer when it opens.
  - Escape closes it and returns focus to the toggle.
  - `aria-expanded` and `aria-controls` are correct.
  - Tab can leave the drawer, which is acceptable for a disclosure that is not a modal.
- **Keyboard reachability:** every interactive control on the crawled screens was reachable by
  Tab. There is no `tabIndex > 0` and no clickable `div` or `span`. At 1440 and 390 px every
  Tab stop showed a visible outline or ring, with two exceptions:
  - the stops hidden by the bottom navigation (P1-3);
  - the admin tutor-evaluation `Evidence month` (`type="month"`) input. Under Tab focus it
    showed `outline: none`; under programmatic `.focus()` it showed a 3 px #1f6f8b outline.
    This is inconclusive (Chromium focuses a sub-field), so check it by hand.
- **Screen-reader basics:**
  - `lang="en"` is set.
  - Every axe run found no unlabelled inputs, images without `alt`, or empty buttons or links.
  - The logo image has `alt="NextScholar"`.
  - Icon-only buttons have names, for example "Close the hornbill and go back to the
    question" and "Open administrator navigation".
  - Navigation landmarks are labelled and use `aria-current`.
  - Admin table headers have `scope="col"`.
- **Right/wrong feedback** uses text ("Not yet", "Try again") as well as colour, and the
  input sets `aria-invalid`.
- **Contrast:** apart from the items above, every text pair axe tested passed. These token
  pairs pass:

  | Pair | Ratio |
  | --- | ---: |
  | ink / surface | 11.42 |
  | muted / surface | 5.88 |
  | muted / brand-soft | 5.10 |
  | amber-text / amber-soft | 5.00 |
  | success / success-soft | 4.91 |
  | danger / danger-soft | 5.64 |
  | ink / gold | 5.49 |
  | input border `line-strong` / white | 3.27 |
  | focus ring / surface | 5.43 |

## What I could not run

| Not run | Why | Who closes it |
| --- | --- | --- |
| Any hosted check (staging or production URL, deployed SHA, Google OAuth, hosted authenticated journey) | Out of scope: the brief was local only, and no hosted host was contacted. | The B5 hosted acceptance run |
| Real screen readers (NVDA, JAWS, VoiceOver for macOS and iOS, TalkBack) | None is available in a headless Linux container. Screen-reader findings come from axe, DOM inspection and the Chromium accessibility tree. How screen readers actually *read* KaTeX MathML is unverified. | Manual check on Windows + NVDA/Chrome and iOS VoiceOver/Safari |
| Firefox and Safari/WebKit | Only the preinstalled Chromium was used. Behaviour that differs by engine was not observed: focusability of scroll containers, MathML handling, `aria-label` on generic elements, `<input type="month">`. | Hosted run on at least Safari iOS and Firefox |
| Production build (`next build && next start`) | The audit used `next dev`, as the E2E config does. The container has Node 22.23, but the repo's `engines` field requires Node 24 or later. Production CSS and hydration could differ slightly. | Hosted run against the deployed build |
| Readiness diagnostic in progress and result, checkpoints, English diagnostic and practice players, essay feedback report and self-review, lesson-complete and celebrations, the "report a problem" open state, the tutor plan sheet | The local seed has no published diagnostic forms. Some screens need flows or provider feedback that the crawl did not drive. Findings for these screens (P1-6, P2-4 pills, P2-7, P2-8, P2-9) are static only. | Extend `e2e/beta-journeys.spec.ts`, or check them during the hosted run |
| 200% and 400% browser zoom, the WCAG 1.4.12 text-spacing override, Windows forced-colours or high-contrast mode | Not emulated. Only the 320 px reflow approximation was run. | Manual hosted check |
| Non-text contrast of every component state (hover, disabled, selected) | axe checks text contrast only. Component contrast was computed from tokens for the states listed above. | Manual hosted check |

## Suggested follow-up

1. Fix P1-1 to P1-8 in one focused PR. Each is local to the files listed.
2. Add axe-core to `e2e/beta-journeys.spec.ts`, failing on serious and critical issues.
3. Extend the existing `expectNoPageOverflow` helper to cover 390 px on the admin routes.
4. Add a focus assertion after "Check final answer" and after the tutor closes.
5. Re-run this audit on the hosted candidate, add the real screen-reader and engine checks
   listed above, and then tick the B5 hosted acceptance item.
