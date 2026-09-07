# ASEAN Scholar Preparation Platform — Product and Delivery Plan

**Document status:** Working product plan  
**Last updated:** 7 September 2026  
**Target beta:** December 2026  
**Initial market:** Indonesian students applying for the Singapore ASEAN Scholarship  
**Founding team:** Two former ASEAN Scholarship holders, including Sec 3-entry experience

## 1. Purpose of this document

This file is the source of truth for what the team is building, why it is being built, which features belong in the December 2026 beta, how the learning experience should work, and what should be postponed. Technical implementation details belong in `ARCHI.md`.

## 2. Product vision

Build a focused preparation platform that helps Indonesian students prepare for the academic and interview stages of the Singapore ASEAN Scholarship. The product should combine structured Mathematics and English preparation with guidance from people who have personally completed the scholarship journey.

The long-term product can combine:

- Structured Sec 1-entry and Sec 3-entry preparation paths.
- Mathematics and English practice.
- Automated marking and explanations.
- Live lessons and workshops.
- One-to-one mentoring with former ASEAN scholars.
- Interview preparation.
- Progress tracking and motivational systems.

The December beta is intended to validate the academic-learning product before introducing payments, credits, mentor scheduling, or complex gamification.

## 3. Product principles

1. **Reliability before quantity.** A smaller verified question bank is better than a large unreliable one.
2. **Structured learning before open-ended chat.** Students should follow a clear preparation path rather than depend on a general chatbot.
3. **Source-grounded explanations.** Where official marking schemes exist, generated explanations should be grounded in them.
4. **Productive struggle.** Students should be allowed to retry before seeing a solution.
5. **Low marginal AI cost.** Generate Mathematics solutions once and reuse them.
6. **Founders' experience is the differentiator.** Technology supports the curriculum and mentorship proposition; it is not the entire product.
7. **Build for evidence.** The beta must measure learning, retention, trust, and completion—not merely registrations.

## 4. Confirmed decisions

### 4.1 Audience and tracks

- Support both Sec 1-entry and Sec 3-entry applicants.
- Store the target scholarship track separately from the source-paper level.
- For Sec 3-entry preparation, Singapore Secondary 2 Express papers are valid source material.
- Source papers are clearly labelled by school level.

Example classification:

```text
target_track: sec3_entry
source_level: singapore_secondary_2_express
```

### 4.2 December beta constraints

- Target availability: December 2026.
- Access: free, invitation-only beta.
- Expected cohort: 10–30 students.
- Team capacity: approximately 10–25 combined hours per week.
- Team technical experience: comfortable with Python and JavaScript/TypeScript.
- Starting point: greenfield project.

### 4.3 Mathematics scope

- Both Sec 1-entry and Sec 3-entry Mathematics.
- Practice is organised by topic.
- Students follow a fixed chapter path.
- Chapters unlock sequentially.
- Students submit final answers only.
- Low-confidence extracted questions are hidden automatically.
- The normal wrong-answer response is only: “Incorrect, try again.”
- The complete solution is not displayed automatically after an incorrect attempt.
- The Give up action becomes available after at least two incorrect attempts.
- After two incorrect attempts, a student may continue trying indefinitely.
- The solution is shown only when the student explicitly gives up.
- Mathematics explanations are pre-generated and cached.

### 4.4 English scope

- Grammar and vocabulary.
- Situational writing.
- Continuous writing.
- Essays are typed directly in the browser.
- AI feedback is available only after submission.
- Available marking material includes rubrics and model essays.

### 4.5 Content quality

- Automated verification is the normal publication gate.
- Any extraction or solution that fails confidence thresholds remains hidden.
- The original question crop is displayed to the student in the beta.
- Extracted text is supporting metadata and must not replace the source image when mathematical OCR is uncertain.

## 5. Users and roles

### 5.1 Student

The student selects an entry track, follows the curriculum, practises Mathematics and English, submits essays, receives post-submission feedback, and views progress.

### 5.2 Content administrator

Initially this is a founder. The administrator uploads papers, monitors extraction, sees why questions failed, manages topic assignments, controls publication, creates English prompts, manages rubrics, and invites beta students.

### 5.3 Academic administrator

This role can adjust chapter order, topic coverage, marking rubrics, checkpoint rules, and model answers. It can initially be combined with the content-administrator role.

### 5.4 Mentor — post-beta

A verified former scholar who can offer interview practice or academic guidance. Mentor profiles, scheduling, credits, payouts, and Zoom integration are not required for the December beta.

### 5.5 Parent — post-beta

A parent-facing role may eventually view progress, payments, and schedules. It is not required for the beta.

## 6. December beta experience

### 6.1 Onboarding

1. Student receives an invitation code or invitation link.
2. Student creates an account.
3. Student selects Sec 1-entry or Sec 3-entry.
4. The platform enrols the student in the corresponding curriculum version.
5. The first chapter becomes available.
6. Later chapters are visibly locked.

### 6.2 Mathematics chapter flow

1. Student opens the currently available chapter.
2. Student selects or is directed to a topic within that chapter.
3. The platform chooses an eligible published question.
4. The student sees the original question crop and final-answer field.
5. The student submits an answer.
6. The server normalises and verifies the submission deterministically.
7. Correct answers complete the question.
8. Incorrect answers increment the attempt counter and display only “Incorrect, try again.”
9. Give up remains unavailable until two incorrect attempts have occurred.
10. After two incorrect attempts, the student can keep trying or select Give up.
11. Give up reveals the cached complete solution and records the event.
12. Progress and first-attempt accuracy update independently.

### 6.3 Chapter unlocking

The platform must make the unlock rule configurable rather than hard-coded. The final rule remains a product decision.

Recommended initial default:

- Complete a required practice set.
- Then pass a short chapter checkpoint.
- Preserve first-attempt accuracy separately from eventual completion.
- Put gave-up questions into a future retry queue without permanently trapping a student.

Alternative supported policies:

- Complete every required question.
- Complete a minimum number of questions.
- Reach a mastery percentage.
- Pass a checkpoint score.

### 6.4 Grammar and vocabulary flow

1. Student opens the current English unit.
2. Student answers objective questions.
3. The system marks them deterministically.
4. Attempts and component accuracy are recorded.
5. Explanations may be cached per question.

### 6.5 Essay flow

1. Student opens a situational-writing or continuous-writing prompt.
2. The editor autosaves the draft.
3. The interface displays word count and submission requirements.
4. AI assistance is unavailable while drafting.
5. Student confirms final submission.
6. The submitted version becomes immutable.
7. A background marking job evaluates the essay against the relevant rubric.
8. The student sees processing status.
9. Structured feedback appears after completion.
10. The student can revisit feedback and earlier submissions.

## 7. Required beta features

Priority meanings:

- **P0:** Beta cannot operate safely or meaningfully without it.
- **P1:** Strongly desirable for the December cohort.
- **P2:** Post-beta enhancement.

### 7.1 Student product requirements

| ID | Priority | Feature | Description and acceptance condition |
|---|---:|---|---|
| STU-001 | P0 | Invitation onboarding | Only invited beta users can register. Invalid or expired invitations are rejected. |
| STU-002 | P0 | Authentication | Students can register, sign in, sign out, and reset access securely. |
| STU-003 | P0 | Track selection | Student selects Sec 1-entry or Sec 3-entry and receives the correct curriculum. |
| STU-004 | P0 | Learning dashboard | Shows current chapter, next action, completion, first-attempt accuracy, and locked chapters. |
| STU-005 | P0 | Sequential chapters | Only chapters allowed by the configured progression rule can be opened. |
| STU-006 | P0 | Topic practice | Student can practise Mathematics within the current curriculum topic. |
| STU-007 | P0 | Question display | Original high-quality question crop and diagrams render clearly on desktop and mobile. |
| STU-008 | P0 | Mathematics input | Accepts supported final-answer formats without requiring handwritten working. |
| STU-009 | P0 | Deterministic marking | Supported answers are marked without an LLM call. Equivalent valid formats are accepted. |
| STU-010 | P0 | Attempt history | Every submission is stored immutably with attempt number and timestamp. |
| STU-011 | P0 | Give-up rule | Give up is unavailable before two errors and optional thereafter. |
| STU-012 | P0 | Cached solution | A complete solution appears only after Give up and does not require a fresh model call. |
| STU-013 | P0 | Progress tracking | Chapter and topic progress update after completed or gave-up questions. |
| STU-014 | P0 | Grammar/vocabulary | Students can complete deterministic English objective exercises. |
| STU-015 | P0 | Essay editor | Supports prompt display, word count, autosave, recovery, and submission confirmation. |
| STU-016 | P0 | Post-submission marking | Essay feedback begins only after the final submission event. |
| STU-017 | P0 | Feedback page | Shows criterion scores, evidence, strengths, and priority improvements. |
| STU-018 | P1 | Submission history | Students can revisit previous essays and feedback. |
| STU-019 | P1 | Retry queue | Previously gave-up questions can reappear later. |
| STU-020 | P1 | Mobile optimisation | All essential flows work on common mobile viewport sizes. |

### 7.2 Administrator requirements

| ID | Priority | Feature | Description and acceptance condition |
|---|---:|---|---|
| ADM-001 | P0 | Administrator access | Admin pages require server-verified administrator permissions. |
| ADM-002 | P0 | PDF upload | Admin can upload a paper and supply school, year, source level, paper type, and target track. |
| ADM-003 | P0 | Ingestion status | Admin can see job stage, progress, errors, timestamps, and retry state. |
| ADM-004 | P0 | Extracted-question viewer | Shows question crop, solution crop, extracted metadata, answer, and confidence. |
| ADM-005 | P0 | Publication control | Admin can publish, unpublish, or permanently reject a question. |
| ADM-006 | P0 | Curriculum editor | Admin can create chapters/topics and change their ordering. |
| ADM-007 | P0 | English content editor | Admin can create prompts and manage rubrics and model essays. |
| ADM-008 | P0 | Invitation manager | Admin can issue, expire, and monitor beta invitation codes. |
| ADM-009 | P1 | Verification diagnostics | Shows which automatic checks passed or failed. |
| ADM-010 | P1 | Regeneration | Admin can rerun extraction, classification, verification, or explanation generation. |
| ADM-011 | P1 | Student progress viewer | Shows engagement, completion and problem areas for the beta cohort. |
| ADM-012 | P1 | AI usage dashboard | Shows calls, models, tokens, failures, latency and estimated cost. |

### 7.3 Operational requirements

| ID | Priority | Requirement | Acceptance condition |
|---|---:|---|---|
| OPS-001 | P0 | Error monitoring | Unhandled web and worker errors are captured with sufficient context. |
| OPS-002 | P0 | Job idempotency | Retrying an ingestion or essay job does not duplicate questions or feedback. |
| OPS-003 | P0 | Access control | Students can only access their own private records. |
| OPS-004 | P0 | Secret management | Service and model keys never reach browser code. |
| OPS-005 | P0 | Automated tests | Critical learning, permission and answer-checking paths run in CI. |
| OPS-006 | P0 | Backups | Production data has a documented backup and recovery procedure. |
| OPS-007 | P1 | Product analytics | Core activation, completion and retention events are recorded. |
| OPS-008 | P1 | Rate limiting | Login, answer submission, essay submission and expensive operations are limited. |
| OPS-009 | P1 | Account deletion | A student account and associated private data can be removed safely. |

## 8. Content strategy

### 8.1 Representative material inspected

Two Sec 2 Express papers were inspected as representative Sec 3-entry preparation sources:

- Canberra Secondary 2022 EOY: 32 pages, two papers, approximately 27 main questions, answers and detailed marking schemes.
- Zhonghua Secondary 2023 SA2: 46 pages, approximately 20 main questions, followed by worked solution pages.

The PDFs have selectable OCR text but are effectively scanned-image pages. Ordinary words are often readable, while mathematical symbols, fractions, inequalities, exponents, coordinates, variables, and diagrams can be corrupted. Consequently:

- The source image is the visual truth shown to students.
- OCR is used primarily for anchors, search, rough segmentation and metadata.
- A vision-capable model performs structured mathematical extraction.
- Official answer and solution pages are paired with questions where available.
- Failed or uncertain content is hidden.

### 8.2 Publishing policy

A question may be published only when:

- Its source and target track are known.
- Its question boundaries are complete.
- Required diagrams are present.
- Its final answer has a supported answer type.
- Automatic extraction checks pass.
- The solution agrees with the source answer.
- Deterministic verification passes where applicable.
- Its confidence meets the configured threshold.

### 8.3 Content status lifecycle

```text
uploaded
→ rendering
→ segmented
→ extracted
→ classified
→ verifying
→ verified
→ published
```

Failure paths:

```text
any processing state
→ needs_review or rejected
→ hidden from students
```

Because the current policy is automatic-only verification, `needs_review` behaves as hidden until a founder deliberately inspects or reprocesses it.

## 9. Learning analytics and beta metrics

### 9.1 Activation

- Percentage of invitees who register.
- Percentage who select a track and begin the first chapter.
- Percentage who complete their first five questions.

### 9.2 Engagement

- Weekly active students.
- Questions attempted per active student.
- Essays submitted per active student.
- Number of active days per week.
- Chapter completion rate.

### 9.3 Learning behaviour

- First-attempt accuracy.
- Eventual accuracy.
- Give-up rate.
- Average attempts before success.
- Accuracy when a gave-up question reappears.
- Performance by topic and difficulty.
- Checkpoint score improvement.

### 9.4 Trust and quality

- Percentage of students reporting an incorrect answer key.
- Percentage of published questions later unpublished.
- Essay-feedback usefulness rating.
- Solution clarity rating.
- Automated ingestion acceptance rate.

### 9.5 Beta success criteria

Suggested initial targets:

- At least 70% of registered students complete a first practice session.
- At least 50% return in a following week.
- At least 60% complete one chapter or a defined equivalent.
- Fewer than 1% of student-served Mathematics questions are reported as technically incorrect.
- Median essay-feedback usefulness is at least 4 out of 5.
- The team can add a new paper without changing application code.

These are learning targets, not promises; revise them after the first five students.

## 10. Delivery roadmap

The schedule assumes roughly 12–14 weeks from early September to December 2026 and 10–25 combined team hours weekly.

### Phase 0 — product freeze and setup

**Goal:** Prevent scope drift before implementation.

- Finalise Sec 1-entry and Sec 3-entry chapter outlines.
- Decide the exact chapter-unlocking rule.
- Define supported Mathematics answer formats.
- Define the topic taxonomy.
- Create the repository, issue tracker, environments and coding conventions.
- Establish a small golden dataset of representative Mathematics questions and essays.

**Exit condition:** Both founders agree on the beta definition of done.

### Phase 1 — platform foundation

**Goal:** A secured empty learning application.

- Create the Next.js application.
- Create Supabase development and production projects.
- Add database migrations and generated types.
- Implement authentication, invitations, profiles, roles and track selection.
- Apply Row-Level Security.
- Build administrator and student shells.
- Add error monitoring and CI.

**Exit condition:** Invited users can register, select a track and see an empty chapter dashboard without accessing another user’s records.

### Phase 2 — Mathematics vertical slice

**Goal:** One complete topic works end to end.

- Upload one PDF.
- Run the ingestion worker.
- Produce question and solution crops.
- Extract structured question data.
- Verify and publish a small set.
- Render questions in the student UI.
- Accept and verify final answers.
- Store attempts.
- Implement two-error Give up logic.
- Reveal cached solutions.
- Update progress.

**Exit condition:** A student can complete a real topic from an uploaded source paper.

### Phase 3 — Mathematics breadth

**Goal:** Enough reliable content for both tracks.

- Expand answer types.
- Add question selection and retry rules.
- Add chapters and checkpoints.
- Process additional papers.
- Build ingestion diagnostics and regeneration.
- Run automated regression tests on all published questions.

**Exit condition:** Both tracks have a usable fixed path with no known critical marking failures.

### Phase 4 — English vertical slice

**Goal:** Objective English and one essay component work end to end.

- Build grammar/vocabulary question types.
- Build the essay editor and autosave.
- Implement immutable submission.
- Configure rubrics and model essays.
- Run asynchronous structured marking.
- Display criterion-level feedback.
- Add submission history.

**Exit condition:** A student can submit an essay and receive persisted post-submission feedback.

### Phase 5 — beta hardening

**Goal:** Make the product safe enough for real invited students.

- Mobile and cross-browser testing.
- Load and failure testing for job retries.
- Rate limits and abuse controls.
- Backup and recovery rehearsal.
- Analytics dashboards.
- AI cost logging and budget alerts.
- Founder pilot using fresh accounts.
- Resolve all P0 issues.

**Exit condition:** A complete founder-run test passes from invitation through Mathematics and English feedback.

### Phase 6 — invited rollout

**Goal:** Learn from 10–30 students.

- Invite a small first group.
- Observe onboarding and first-session completion.
- Fix blockers before inviting the remainder.
- Conduct weekly student feedback collection.
- Review incorrect-question reports immediately.
- Produce a beta outcome report.

## 11. Testing plan

### 11.1 Mathematics golden set

Maintain representative examples for every supported answer type and failure mode:

- Integer and negative integer.
- Decimal tolerance.
- Fraction equivalence.
- Percentage.
- Algebraic equivalence.
- Multiple roots.
- Coordinates.
- Units.
- Geometry with diagram.
- Graph question.
- Multi-page question.
- Bad OCR.
- Missing solution.

No answer-checker change may ship if it causes a golden-set regression.

### 11.2 English evaluation set

Create a small internal benchmark containing:

- Prompt.
- Essay.
- Applicable rubric.
- Expected strengths and weaknesses.
- Founder-estimated score range.

The purpose is not to promise perfect machine grading; it is to detect prompt or model changes that make feedback less consistent.

### 11.3 Permission tests

Automated tests must confirm:

- Student A cannot read Student B’s essays, attempts or progress.
- A student cannot access administrator endpoints.
- Unpublished questions cannot be served.
- Private source PDFs cannot be listed publicly.
- Service credentials never appear in client bundles.

## 12. Business model plan

### 12.1 Beta

- Free, invitation-only.
- No payment integration.
- No student-facing token balance.
- Measure real usage before determining included limits.

### 12.2 Recommended post-beta model

- Monthly subscription for the core academic platform.
- Mathematics practice should not consume visible credits.
- Include a fair-use allowance for essay marking.
- Use separate credits or direct purchase for scarce human services such as mentor calls and interview practice.
- Allow top-ups for human services if the market validates them.

### 12.3 Pricing hypothesis

The earlier idea of approximately S$50 per month with credits is a hypothesis, not a confirmed price. Before charging, interview Indonesian parents and test multiple packages. The first paid offer should remain easy to understand; avoid mixing learning access, AI tokens, interview slots, XP conversion and rollover into one complicated balance.

## 13. Deferred features

The following should not delay the December beta:

- Paid subscriptions and payment gateways.
- Credit rollover and top-ups.
- XP-to-credit conversion.
- Leaderboards.
- Zoom integration.
- Mentor profiles and marketplace.
- Mentor availability and payouts.
- Interview booking.
- Parent dashboards.
- Handwriting recognition.
- Live conversational AI tutoring.
- Native Android or iOS applications.
- Full re-typesetting of every scanned question.
- Vector search or recommendation machine learning.

## 14. Key risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Mathematical OCR corruption | Wrong question or solution | Image-first display, vision extraction, independent verification and automatic hiding |
| Diagram omitted by cropper | Question becomes unsolvable | Asset-completeness checks and original-page metadata |
| Answer format too broad | False incorrect results | Explicit supported answer types and golden tests |
| Unlimited retries inflate mastery | Misleading progress | Store first-attempt accuracy separately |
| AI essay score inconsistency | Loss of trust | Rubric-level structured output, benchmark set, prompt/model versioning and “AI estimate” labelling |
| Scope expansion | Missed December beta | Enforce P0/P1/P2 priorities and deferred-feature list |
| Background job duplication | Duplicate questions or feedback | Checksums, idempotency keys and database uniqueness constraints |
| Minor-user privacy exposure | Serious trust and safety issue | Minimal data, private storage and Row-Level Security |
| Founder workload | Content pipeline becomes bottleneck | Reusable ingestion pipeline, clear failure states and batch processing |

## 15. Remaining product decisions

1. Exact chapter-unlocking rule.
2. Whether gave-up questions enter a retry queue automatically.
3. Minimum question count per chapter and topic.
4. Checkpoint length and passing score.
5. Whether students may revisit earlier unlocked chapters freely.
6. Whether a correct answer should ever allow optional viewing of the solution.
7. Exact Sec 1-entry and Sec 3-entry topic taxonomies.
8. English score scale and wording of the AI-estimate disclaimer.
9. Quantity of essay submissions allowed during the free beta.
10. What evidence will justify a paid launch after the beta.

## 16. December definition of done

The beta is ready when:

- An invited student can register and select the correct track.
- The student sees a sequential learning path.
- Published questions are source-grounded and automatically verified.
- Mathematics final answers are checked deterministically.
- Attempt and Give up behaviour matches the confirmed rules.
- Cached solutions display without fresh AI generation.
- Grammar/vocabulary practice functions.
- Situational and continuous-writing submissions autosave and submit correctly.
- Essay feedback is generated asynchronously and stored.
- Administrators can upload papers and understand processing failures.
- Permission, answer-checking and critical browser tests pass.
- Errors and AI usage are observable.
- The product works on desktop and mobile for a 10–30-student invited cohort.

