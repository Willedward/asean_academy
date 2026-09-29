# NextScholar Feature Roadmap: Beta, V2 and V3

**Document status:** Proposed. Builds on the existing plans; does not replace them.

**Technical companion:** [BETA_V2_V3_TECHNICAL_EXECUTION.md](BETA_V2_V3_TECHNICAL_EXECUTION.md) audits current implementation, feasibility, release gates and execution order. Where the roadmap status column is stale, the audited technical companion governs delivery planning.

**Created:** 29 September 2026

**Builds on:** `plan.md` (December beta product plan), `PLAN_V2.md` (course platform plan), `STAGES.md`, `TUTOR_INTERACTION_DESIGN.md`, `LESSON_VIDEO_HANDOFF.md` and `BETA_OPERATIONS.md`. The design canvas ("NextScholar screens") holds the matching screens.

**Purpose:** One list of every feature discussed so far, sorted into three releases:

| Release | When | Who it is for | Money |
|---|---|---|---|
| **Beta** | December 2026 | 10 to 30 invited students | Free, no payments |
| **V2 website** | Public launch, January 2027, in time for the application window | Any Indonesian family preparing for Sec 1 or Sec 3 entry | Free plan plus paid plans |
| **V3 website** | After the first full application cycle (from mid 2027) | Larger cohort, more subjects and countries | Adds mentors, parents and larger paid bundles |

Rules and priorities in `plan.md` and `PLAN_V2.md` still apply unless this document says otherwise. Section 9 lists every place where this roadmap changes an earlier decision, so those can be confirmed before building.

---

## 1. How to read this document

- Each feature has an ID: `B-` for beta, `V2-` for V2, `V3-` for V3.
- **Source** shows where the feature was first described: an existing ID (for example `STU-019` in `plan.md`) or **New** if it came from the September 2026 product discussions.
- **Status** is one of: *Built* (exists on `feature/beta-operations`), *Partly built*, *Designed* (screens exist on the design canvas), or *Not started*.
- A feature only moves to an earlier release if something is dropped to make room. The beta must stay small.

---

## 2. Beta (December 2026)

**Goal:** Prove that students learn from the course, come back, and trust the content. No payments, no mentors, no gamification.

**Exit criteria:** everything in the December definition of done in `plan.md` section 16, plus: each beta student has a diagnostic score at the start and at the end of the beta, so improvement can be measured.

### 2.1 Getting started

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| B-01 | Invitation onboarding | Only invited Google accounts can join. Invites expire and can be revoked. | STU-001, ADM-008 | Built |
| B-02 | Sign in and sign out | Google sign-in through Supabase. | STU-002 | Built |
| B-03 | Track choice | Student picks Sec 1 or Sec 3 entry if the invite does not decide it. | STU-003 | Built (Sec 1 content only) |
| B-04 | **Diagnostic test at onboarding** | A short placement test that shows where the student starts. See section 5.1. | New | Not started |
| B-05 | **Diagnostic score report** | A clear results page the student can share with a parent. Beta version: a results page plus a shareable link or PDF. See section 5.2. | New | Not started |

### 2.2 Learning

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| B-06 | Course map and unit roadmap | N1 course with 7 lessons, lesson status, recommended next step. | STU-004, STU-005 | Built (needs final design) |
| B-07 | **Lecture notes for every lesson** | Short sections, worked examples, "check yourself" questions and a summary. See section 5.5. | PLAN_V2 4, 7.4 | Partly built (lesson shell only, content blank) |
| B-08 | **Lesson videos** | A short video per lesson with captions and a transcript. Needs a video host decision. See section 5.5. | LESSON_VIDEO_HANDOFF | Not started |
| B-09 | Guided practice | Typed answers, deterministic marking, 2 hints, Give up after 2 wrong tries, worked solution. | STU-006 to STU-012 | Built (needs final design) |
| B-10 | **Spaced "Try again" list** | Questions the student got wrong, gave up on, or needed hints for come back after 2, 4, 7 and 14 days. See section 5.6. | STU-019, New timing rule | Partly built (retry exists, no delay) |
| B-11 | Unit checkpoint | 8 unseen questions, no hints, pass with 6 of 8 to master the unit. | PLAN_V2 7.7 | Designed |
| B-12 | Progress page | Lessons proficient, right first try, outcome view, Try again list. | STU-013 | Built (needs final design) |
| B-13 | Report a problem with a question | Student flags a wrong or unclear question; admin sees it in the reports inbox. | New (audit) | Designed |

### 2.3 English

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| B-14 | Grammar and vocabulary practice | Objective questions with instant marking and a reason for each answer. | STU-014 | Designed |
| B-15 | Essay writing and AI feedback | Autosaved editor, submit, feedback against the rubric, labelled as an AI estimate. | STU-015 to STU-018 | Designed |

If English is not ready by December, move B-14 and B-15 to the first V2 release rather than delaying the beta.

### 2.4 Admin and operations

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| B-16 | Admin home and navigation | One sidebar linking every admin page. | Audit | Designed |
| B-17 | Invitations | Create, copy, revoke, audit. | ADM-008 | Built |
| B-18 | Content review queue and question review | Preview as a student, checks, 3 reviews, publish. | ADM-004, ADM-005 | Designed |
| B-19 | Lesson editor and lesson review | Edit notes, alt text, video metadata; review and publish. | PLAN_V2 7.10 | Designed |
| B-20 | Course editor and question pools | Lesson order, unlock rule, practice, checkpoint and reserve pools. | ADM-006, PLAN_V2 4.1 | Designed |
| B-21 | Reports inbox | Handle student question reports and reply. | New (audit) | Designed |
| B-22 | Audit log | Every publish, retire, hide and review decision. | BETA_OPERATIONS | Partly built (invites only) |
| B-23 | Beta student progress | Per-student activity so founders can check in. | ADM-011 | Designed |
| B-24 | Monitoring, backups, rate limits, account deletion | As listed in `plan.md` 7.3. | OPS-001 to OPS-009 | Partly built |

### 2.5 Brand and front end

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| B-25 | Rename ASEAN Academy to NextScholar | Header, sign-in, onboarding, page titles, logo label. | Audit | Not started |
| B-26 | Brand tokens, favicon, app icons, link preview | Replace the generic teal theme with the NextScholar tokens. | Audit | Designed |
| B-27 | Component library and states | Buttons, fields, badges, hint and feedback panels, toasts, dialogs, skeletons, focus rings. | FRONTEND_TECH_STACK_PLAN | Designed |
| B-28 | Phone, tablet and desktop layouts | 390, 768 and 1440 px. | FRONTEND_TECH_STACK_PLAN | Designed |
| B-29 | Invite-only landing page | Replaces the "System readiness" developer panel on `/`. | Audit | Designed |

---

## 3. V2 website (public launch, January 2027)

**Goal:** Open to the public during the application window, turn free sign-ups into paying families, and keep students practising until test day.

**Exit criteria:** a family can find the site, take the diagnostic, see the score report, try the free plan, pay for a season pass with an Indonesian payment method, and use the whole paid product without founder help.

### 3.1 Marketing and sign-up

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V2-01 | Public marketing website | Full landing page: hero, how it works, mentors, parents, pricing, FAQ, sign-up. | New | Designed |
| V2-02 | Open sign-up (no invite) | Anyone can create a free account. Invitations stay for promotions. | New | Not started |
| V2-03 | Diagnostic as the front door | "Take the free diagnostic" is the main call to action on the website. | New | Not started |
| V2-04 | **Score report sent to parents** | After the diagnostic, the parent receives the report by WhatsApp or email, with an optional free call with a former scholar. See section 5.2. | New | Not started |
| V2-05 | Sec 3 entry course content | Second track content (beta is Sec 1 N1 only). | plan.md 4.1 | Not started |

### 3.2 Plans and payments

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V2-06 | Free plan | Diagnostic, Lesson 1 of each unit, limited worked solutions, group Q&A with alumni. See section 4. | New | Not started |
| V2-07 | **Limited worked solutions for free users** | Free users can open X full explanations. After that, only the final answer is shown. Paid users see every explanation. See section 5.4. | New | Not started |
| V2-08 | Season pass | One payment covering access until test day. No automatic renewal. | New | Designed (plans screen) |
| V2-09 | **Countdown pricing** | The season pass price is based on the time left until the test, with a visible countdown. See section 5.3. | New | Not started |
| V2-10 | Monthly option | For families not ready to commit to the season. Priced higher per month. | plan.md 12.2 | Designed |
| V2-11 | Indonesian payments | QRIS, bank transfer (virtual account) and e-wallets through a local gateway such as Xendit. Instalments. | New | Designed (checkout screens) |
| V2-12 | 7-day money-back guarantee | Replaces a free trial. No card needed upfront, nothing to abuse. | New | Not started |
| V2-13 | Upgrade by paying the difference | Move from self-study to the mentor plan mid-season. | New | Not started |
| V2-14 | **Usage display for paid users** | Show only concrete, scarce items (essay reviews, mentor sessions). Do not show an abstract "AI credits" balance. See section 5.7. | New, plan.md 12.3 | Not started |

### 3.3 Learning additions

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V2-15 | AI tutor ("Ask teacher") | Grounded chat on a question, paid feature with fair use. | TUTOR_INTERACTION_DESIGN | Designed |
| V2-16 | Recheck quiz | 5 questions, 2 weeks after a lesson becomes proficient; passing marks it mastered. | PLAN_V2 3, 4 | Designed |
| V2-17 | **Study planner, first version** | Builds a weekly plan from the test date and diagnostic result using simple rules. See section 5.9. | New | Not started |
| V2-18 | **Gamification, light** | XP for daily tasks, streaks and a weekly goal. No leaderboard yet. See section 5.8. | New, plan.md 13 | Designed |
| V2-19 | Interview prep library | Common questions, example answers, recorded tips from former scholars. | Memory, plan.md 2 | Not started |
| V2-20 | Units after N1 | More maths units and English units, following the same lesson format. | PLAN_V2 3 | Not started |

### 3.4 Mentors and parents, simple version

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V2-21 | Mentor sessions, managed by hand | Mentor-plan families book through a simple request form; founders arrange the Zoom call. Tests demand before building a marketplace. | New | Not started |
| V2-22 | Parent weekly email | Sunday summary: time practised, days active, right first try, what is coming up. | New | Designed |
| V2-23 | Group Q&A with alumni | Monthly live session for all users, free and paid. | New | Not started |

### 3.5 Admin and brand

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V2-24 | Paper upload, OCR review and topic confirmation | Production admin for turning past papers into questions. | ADM-002 to ADM-004, ADM-010 | Designed |
| V2-25 | AI usage dashboard | Calls, cost, failures per feature. Needed once AI features are paid. | ADM-012 | Designed |
| V2-26 | Payments admin | See subscriptions, refunds and instalment status. | New | Not started |
| V2-27 | Mascot | Chosen from the mascot drafts; used on the website, empty states and celebrations. | New | Drafts on canvas |

---

## 4. Free plan and paid plans (V2)

| | Free | Season pass (self-study) | Season pass with mentors |
|---|---|---|---|
| Diagnostic test and score report | Yes | Yes | Yes |
| Lecture notes and videos | Lesson 1 of each unit | All lessons | All lessons |
| Practice questions | Free lessons only | All, plus the Try again list | All, plus the Try again list |
| Worked solutions after Give up | X per week, then answer only | Unlimited | Unlimited |
| Hints | Yes (authored hints stay free) | Yes | Yes |
| Checkpoints and rechecks | Locked | Yes | Yes |
| English essay feedback | 1 sample | Monthly allowance | Monthly allowance |
| AI tutor | Locked | Fair use | Fair use |
| Study planner | Preview only | Yes | Yes |
| Parent weekly email | Diagnostic report only | Every week | Every week |
| Group Q&A with alumni | Yes | Yes | Yes |
| 1:1 mentor sessions and mock interview | No | Buy single sessions | Bundle included |

Pricing ranges from the market research (to test with beta parents before launch):

- Season pass, self-study: Rp990k to 1.29M.
- Season pass with mentors: Rp2.9M to 3.9M, including 4 one-to-one sessions and a mock interview.
- Single mentor session: Rp350k to 450k.
- Monthly option: Rp199k to 249k.

Comparison points: Lister charges Rp8.95M for 20 private sessions; Ruangguru's junior high self-study plan is about Rp279k a month.

---

## 5. Feature specifications for the new features

### 5.1 Diagnostic test (B-04)

**What it is:** a placement test taken right after sign-up that shows how ready the student is, before any lessons.

- **Length:** about 20 to 25 minutes. Maths first (12 questions across the units that exist), then English (8 objective questions). Essay writing is not part of the diagnostic.
- **Rules:** no hints, no Give up, no feedback until the end, no timer. Answers autosave so the student can leave and come back.
- **Scoring:** score per syllabus outcome (for example 1.1 Primes: 2 of 2; 1.5 Ordering: 0 of 2), plus an overall band such as "Getting started", "On track" or "Ahead".
- **Question source:** a separate diagnostic pool so these questions never appear in practice or checkpoints.
- **Retake:** once at the end of the beta (and later, once before the test) so progress can be measured. The two results are shown side by side.
- **Uses the result:** the recommended first lesson, the study planner (V2-17), and the parent score report.
- **Tone:** the report never calls a child weak or failing. It shows strengths first, then "what to work on next".

### 5.2 Score report for parents (B-05, V2-04)

- **Beta:** a results page for the student with a "Share with a parent" button that creates a private link or PDF.
- **V2:**
  - Sent automatically to the parent's WhatsApp or email when the student finishes, if the student added a parent contact during onboarding.
  - Content: overall band, strengths, the three outcomes to work on first, a suggested plan until test day, and an invitation to a free 15-minute call with a former scholar.
  - Available in English and Bahasa Indonesia.
  - Privacy: the report shows scores only, never individual answers. The parent link expires after 30 days.
- This report is also the main sales moment: the call with a former scholar is where families learn about the paid plans.

### 5.3 Countdown pricing (V2-09)

**Idea:** the season pass always ends on the student's test day, and the price depends on how much time is left.

- The student's intake (Sec 1 or Sec 3) sets the expected test date, taken from MOE's published timeline. Admins update it each year.
- Price = weeks remaining × weekly rate, with a minimum price and a maximum price. Families who join early pay more in total but less per week; families who join late pay less.
- An early-bird discount applies before a fixed date (for example before applications open).
- The pricing page and checkout show a real countdown: "112 days until the selection test. Your pass covers all of them."
- **Rules for honesty:** the countdown is always the real test date. No fake timers, no "offer ends in 10 minutes", no crossed-out prices that were never charged.
- **Decision needed:** whether price goes down as the test approaches (fairer) or stays flat with the countdown shown only as urgency. The recommended default is pro-rated pricing with a floor.

### 5.4 Limited worked solutions for free users (V2-07)

**What it is:** free users can see the full step-by-step working for a limited number of questions. After that, Give up shows only the final answer.

- Allowance: **X full solutions per week** (recommended default 5, refilled every Monday, set in admin config). A weekly refill gives free users a reason to come back; a one-time allowance would be simpler but ends their engagement.
- What counts: opening the full worked solution after Give up, or opening the solution after a correct answer (if that is allowed). Hints do not count and stay free.
- When the allowance is used up:
  - Give up shows the correct answer with a short note: "Full working is part of the season pass. You have used your 5 free solutions this week. They refill on Monday."
  - The question still goes into the Try again list as normal.
- Paid users: every explanation is available, with no counter shown.
- The counter is shown to free users before they tap Give up ("3 of 5 free solutions left this week"), so it is never a surprise.
- **Note:** this is a change to `plan.md`, where every student sees the full solution after Give up. It only applies from V2; the beta stays unlimited.

### 5.5 Lecture notes and videos (B-07, B-08)

- Each lesson: objectives, quick recall, 2 to 4 short explanation sections, a worked example, a "check yourself" question, a summary, then guided practice.
- Video: one 5 to 8 minute video per lesson, with English captions and a transcript that follows along. Students can mark a section as done.
- Content is versioned. A lesson edit becomes a new revision that goes through review before students see it.
- Videos follow `LESSON_VIDEO_HANDOFF.md`: master files stay outside Git; the repo holds metadata, captions, transcripts and posters.
- **Blocker:** choose a video host (for example a private video platform or a storage bucket with a player).

### 5.6 Spaced "Try again" list (B-10)

Questions come back on a schedule instead of immediately.

| What happened | When it comes back |
|---|---|
| Gave up and saw the solution | 2 days |
| Right only after wrong tries or hints | 4 days |
| On a review: right first try, no hints | Next gap: 7 days, then 14 days, then cleared |
| On a review: right with hints or wrong tries | Same gap again |
| On a review: wrong or gave up | Back to 2 days |
| A new question right first try, no hints | Never scheduled |

Extra rules:

- Nothing is scheduled later than 2 days before the student's test date.
- At most 5 review questions a day, most overdue first.
- From the second review, serve a similar question from the reserve pool (same outcome and level) instead of the identical question, so students cannot just remember the answer.

Build notes (fits the current code on `feature/beta-operations`):

- Add `review_box` and `due_at` to `question_progress`.
- Compute the next due date in one small, tested function when an attempt is resolved or the student gives up.
- In practice selection, only treat a retry as due when `due_at <= now()`.
- Because `attempts` can never be edited, all due dates can be recalculated from history if the gaps change later.

### 5.7 Showing AI usage to paid users (V2-14)

**Recommendation: do not show an "AI credits" balance.** Show only concrete, limited things.

- **Maths practice, hints and solutions:** never counted. They are pre-written and cost almost nothing per use (as `plan.md` 12.2 already says).
- **Essay feedback:** show a simple count, for example "5 of 8 essay reviews left this month", because each one has a real cost and families understand it.
- **AI tutor:** fair use with no visible number. A soft notice appears only near the limit: "You have used most of this week's tutor time. It resets on Monday."
- **Mentor sessions:** show a count, for example "2 of 4 mentor sessions left", because they are the scarcest item.
- **Why:** a single token balance makes parents worry about "wasting" credits and makes children avoid asking for help. Counting only the scarce items keeps the product simple and protects margins.
- **Admin side:** the AI usage dashboard (V2-25) tracks real cost per student, so limits can be tuned with data.

### 5.8 Gamification (V2-18, V3-06)

Gamification should reward learning habits, not guessing fast.

- **V2 (light):**
  - XP for completing daily tasks: finish a lesson section, clear the Try again list for the day, complete a practice set.
  - A daily streak with one free "streak freeze" per week, so one missed day does not reset a month of effort.
  - A weekly goal (for example 5 active days).
  - No XP for correct answers alone, so there is no reason to rush or guess.
- **V3:**
  - Leaderboards by intake, weekly, opt-in, showing first names only.
  - Badges for milestones (first unit mastered, 30-day streak).
  - XP-to-credits conversion only if the guardrails are clear: a monthly cap, and credits that only apply to lower-cost items, never to 1:1 mentor time.

### 5.9 AI study planner (V2-17, V3-05)

**V2, rule-based:**

- Inputs: test date, diagnostic result by outcome, how many days a week the student can study, current progress.
- Output: a weekly plan, for example "This week: Lesson 3, 2 practice sets, your Try again list, 1 essay".
- Priorities: weak outcomes from the diagnostic first, then the normal lesson order, with the Try again list every day.
- Replans every Monday and when the student falls behind, without shaming ("Last week was busy. Here is a lighter plan.").
- The same plan appears in the parent weekly email.

**V3, AI-assisted:**

- An AI model adjusts the plan using recent accuracy, time per question and missed days, and explains its choices in plain language.
- Guardrails: the AI can only choose from published content and the fixed rules (test date, daily review limit). It never marks answers or unlocks solutions.

---

## 6. V3 website (from mid 2027)

**Goal:** Scale beyond the first cohort: a real mentor marketplace, parent accounts, and new markets.

| ID | Feature | What it does | Source | Status |
|---|---|---|---|---|
| V3-01 | Mentor marketplace | Mentor profiles, availability, booking, Zoom links, notes after each session, ratings. | plan.md 5.4 | Designed |
| V3-02 | Mentor application and verification | Scholarship letter check, intro call, child-safety training, code of conduct. | New | Designed |
| V3-03 | Mentor payouts | Monthly payout to mentors for completed sessions. | plan.md 13 | Not started |
| V3-04 | Parent account and dashboard | Parents log in to see progress, bookings and payments, and approve purchases. | plan.md 5.5 | Designed |
| V3-05 | AI study planner, adaptive | See section 5.9. | New | Not started |
| V3-06 | Leaderboards, badges, XP-to-credits | See section 5.8. | plan.md 13 | Designed |
| V3-07 | Credits for human services | Top-ups and rollover for mentor sessions and mock interviews only. | Memory, plan.md 12.2 | Designed |
| V3-08 | Live group classes and workshops | Scheduled classes by former scholars for the whole cohort. | plan.md 2 | Not started |
| V3-09 | Mock interview simulator | Practice interview with recorded answers and feedback, then a real mock with a mentor. | New | Not started |
| V3-10 | Malaysia expansion | Malaysian intake, local payments, adjusted content. | Memory | Not started |
| V3-11 | Native mobile app | Only if phone-browser use shows a clear need. | PLAN_V2 18 | Not started |
| V3-12 | Other syllabuses | Reuse the platform beyond ASEAN Scholarship prep. The NextScholar name allows it. | Memory | Not started |
| V3-13 | Live voice tutor | Spoken tutoring, only after the text tutor is proven. | PLAN_V2 18 | Not started |

---

## 7. Dependencies between releases

| Before this | You need this |
|---|---|
| Diagnostic test (B-04) | A separate reviewed diagnostic question pool, at least 20 questions |
| Parent score report by WhatsApp (V2-04) | Parent contact at onboarding, a message provider, parent consent wording |
| Free-plan solution limit (V2-07) | Plans and entitlements in the database, which also power V2-06 and V2-14 |
| Countdown pricing (V2-09) | Test dates per intake stored in admin config, payment gateway (V2-11) |
| Study planner (V2-17) | Diagnostic results by outcome (B-04), test date, spaced review (B-10) |
| Recheck quiz (V2-16) | Enough reserve questions per outcome (PLAN_V2 4.1) |
| AI tutor as a paid feature (V2-15) | Tutor evaluation set passing (TUTOR_INTERACTION_DESIGN), AI usage dashboard (V2-25) |
| Mentor marketplace (V3-01) | Demand proven by managed mentor sessions (V2-21) |
| XP-to-credits (V3-06) | Credit guardrails agreed (see section 5.8) |

---

## 8. What each release measures

| Release | Main questions | Signals |
|---|---|---|
| Beta | Do students learn and come back? Is the content trusted? | Diagnostic score change from start to end; weekly active students; lessons proficient; question reports per 100 questions |
| V2 | Will families pay? Does the free plan lead to paid? | Diagnostic completions; share of parents opening the score report; free to paid conversion by week, especially after applications open; refund rate |
| V3 | Can it scale beyond the founders? | Mentor sessions per week; mentor rating; parent dashboard use; cost per active student |

---

## 9. Changes to earlier decisions (confirm before building)

| Earlier document | Earlier decision | This roadmap proposes |
|---|---|---|
| `plan.md` 4.3 | Every student sees the full solution after Give up | From V2, free users see full solutions X times a week, then the answer only. Beta unchanged. |
| `plan.md` 12.1 | No student-facing token balance | Keep this: show counts only for essay reviews and mentor sessions, never an AI credit balance |
| `plan.md` 13 | Leaderboards and XP deferred | XP, streaks and weekly goals in V2; leaderboards in V3 |
| `plan.md` 13 | Parent dashboards deferred | Parent score report and weekly email in V2; full parent dashboard in V3 |
| `plan.md` 6.1 | Onboarding goes straight to the first chapter | Onboarding adds the diagnostic test before the first lesson |
| `STU-019` / `PLAN_V2` retry queue | Gave-up questions reappear later | Retries follow the spaced schedule in section 5.6 |
| `plan.md` 12.3 | Around S$50 a month with credits (hypothesis) | Season pass paid once, pro-rated to test day, with a monthly option |

---

## 10. Open decisions

1. The value of X for free solutions per week (recommended 5).
2. Whether free users can practise every lesson or only Lesson 1 of each unit.
3. Countdown pricing: pro-rated price, or a flat price with the countdown shown only for urgency.
4. Exact prices, to be tested with beta parents.
5. Video host for lesson videos.
6. Whether the diagnostic includes English in the beta, or Maths only.
7. Parent contact: collected at onboarding (with consent) or only when the student shares the report.
8. Which mascot to use (drafts on the design canvas).
9. Whether English (B-14, B-15) is ready for December or moves to V2.
