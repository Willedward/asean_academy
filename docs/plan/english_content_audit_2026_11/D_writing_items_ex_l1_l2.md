# D_writing1 — findings: ex-l1-001…011, ex-l2-001…013 (E0, E6–E9 objective writing/orientation)

Reviewer note on level: following the audit level-fit basis, level fit is judged against the
`secondary_1_entry` profile, so learners are about 11–12, in their final primary year, with English as a second language.
Evidence status checked against `catalogue.json` (`exam_blueprint`: both sections `evidence_status:
"candidate_reported"`), `exam_profiles/asean-english-sec1-id-reported-v1.json` and `sources.json`
(`candidate-report-2026-english-format` is the only source for the 90/30 minutes, the part list and the
approximately 300 words; the MOE page "does not define detailed English paper parts, counts, marks or wording").
Keyed numbers (90, 30, about 300, 12/17, 15/20 surplus arithmetic) are consistent with the profile.

---

## Slice-wide

### ex-l1-001 … ex-l2-013 (slice-wide) — Keyed option is almost always the longest; key position predictable
- **Location:** all 24 files `backend_resources/english/v1/questions/ex-l1-0*.json`, `ex-l2-0*.json`
- **Severity:** S2 · **Category:** level-fit (test-wise cue)
- **Evidence:** In 86 of the 95 single-choice parts, the keyed option is the longest option. It is typically 1.5–3× the mean distractor length, and up to 5.5× in ex-l2-006 part 3. Single-choice keys are distributed B 40 / C 25 / A 23 / D 7. All 11 multiple-response sets include A. Five sets are exactly A-B-C (ex-l1-002, ex-l1-004, ex-l2-001, ex-l2-002, ex-l2-013) and two are A-B (ex-l2-009, ex-l2-012). The keyed option is also usually the only hedged or qualified one ("…unless official instructions permit transfer", "…and label strictness unconfirmed", "…though another assembly would be needed…"). Distractors are often self-refuting ("Exactly 96.4 per cent of pupils felt calmer, although nobody was surveyed"; "The word ‘deadline’ contains eight letters"; "It is an interview"; "Double the number").
- **Problem:** A learner can reach most keys by choosing the longest or most qualified option, without the target skill. This affects the protected module checkpoints most (ex-l1-008…011, ex-l2-007…012). It also makes difficulty labels of 3–4 unrealistic.
- **Proposed correction:** Balance option lengths so the key is the longest in no more than about 30% of parts. Give at least two distractors the same specificity and hedging as the key, built from plausible near-misses (for example, a correct structure with one wrong element, or an accurate detail serving the wrong paragraph). Rotate key letters, including D and including multiple-response sets that omit A.

---

## E0 orientation (EX0.1 / EX0.2)

### ex-l1-005 part 1 — Candidate-reported timing presented as "evidence-backed"
- **Location:** `backend_resources/english/v1/questions/ex-l1-005.json` (instructions; part 1 correct_explanation; part 2 rationale B…C)
- **Severity:** S2 · **Category:** correctness / validity
- **Evidence:** Instructions: "Make all five decisions using only the current evidence-backed paper profile." Part 1 explanation: "The current evidence supports separate 90- and 30-minute periods." Part 2 why C: "This is the supported surplus-bank format." Part 5: "Approximately 300 words is a practice target, not yet a confirmed strict rule."
- **Problem:** The 90/30 timings, the surplus bank and the about-300-word figure all come from the same single candidate report (`evidence_status: candidate_reported`; `configurable_fields` includes "part timing"). The item presents timing and format as established evidence and only the word count as provisional. This is the exact error the EX0.1 outcome targets ("without treating provisional counts as official facts"). It also contradicts e0-lesson-01, which asks learners to label each statement "official, candidate-reported or uncertain".
- **Proposed correction:** In the instructions, write "using only the current candidate-reported paper profile". Part 1 explanation: "The current candidate report describes separate 90- and 30-minute periods; treat these as the working practice limits until official instructions confirm them." Part 2 why C: "This is the reported surplus-bank format."

### ex-l1-008 part 1 — Distractor rationale undermines the basis of the key
- **Location:** `backend_resources/english/v1/questions/ex-l1-008.json` (part 1, option D rationale and explanation)
- **Severity:** S3 · **Category:** validity
- **Evidence:** D: "Exactly five questions in every part because one candidate remembered that number". Why D: "A remembered count is not an official fixed rule." Explanation: "The safe map records the supported section structure…"
- **Problem:** The keyed map (B) also rests entirely on one candidate's recollection. Rejecting D *because* it comes from a remembered candidate account is therefore inconsistent. D is wrong because counts are listed as configurable and "exactly … every part" over-generalises.
- **Proposed correction:** Why D: "Question counts are not part of the reported profile; they stay configurable, and one remembered number should not be fixed as a rule." Explanation: "…records the reported section structure and keeps uncertain counts configurable."

### ex-l1-008 part 1–3 (with ex-l1-009) — E0 checkpoint forms are trivially easy and not parallel
- **Location:** `ex-l1-008.json`, `ex-l1-009.json` (difficulty 3, `module_checkpoint`); forms `english-checkpoint-e0-orientation-a/b-v1.json`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Distractors include "A 30-minute vocabulary paper followed by a 90-minute interview", "Invent a 500-word official minimum", "Remove composition practice entirely", "Delete them from the total test time", and "A spoken debate with no text". The same decisions appear at difficulty 2 in the exit and retry items (ex-l1-006 part 2 compared with ex-l1-008 part 2; ex-l1-006 part 5 compared with ex-l1-008 part 3; ex-l1-006 part 1 compared with ex-l1-009 part 3). Form A tests overall map, banked cloze and word count. Form B tests open cloze, reading and time transfer.
- **Problem:** Each protected checkpoint part has one serious option and three absurd ones, so the mastery decision carries little information. The difficulty-3 label does not match identical difficulty-2 practice decisions. The paired forms sample different EX0.1 facts, so they are not parallel.
- **Proposed correction:** Write distractors as near-miss profiles. Examples: "90-minute Section 1 including a separate editing part, then a 30-minute composition"; "Section 1 and Section 2 share one 120-minute clock"; "Banked cloze uses every bank word once"; "300 words is a strict penalty limit". Give both forms the same sub-blueprint, for example one timing/structure part, one cloze-format part and one evidence-status part each. Align difficulty labels with ex-l1-006.

### ex-l1-008 part 3 — Asks the learner to make the course's editorial decision (also ex-l1-006 part 5)
- **Location:** `ex-l1-008.json` part 3; `ex-l1-006.json` part 5
- **Severity:** S3 · **Category:** validity
- **Evidence:** "How should the course present this?"; "An unsourced site claims exactly 300 words are compulsory. What should the course do? … A) Publish it as official."
- **Problem:** The stem tests NextScholar's content policy rather than the learner's own preparation decision. It is also abstract for 11–12-year-olds.
- **Proposed correction:** "How should you use this number when you practise?" Options: "As a target of about 300 words, remembering that strictness is unconfirmed" / "As a strict rule: exactly 300 words or you lose marks" / …

### ex-l1-006 part 3 — Ungrammatical stem ("prepares open cloze")
- **Location:** `backend_resources/english/v1/questions/ex-l1-006.json` (part 3 prompt)
- **Severity:** S2 · **Category:** grammar
- **Evidence:** "Which activity best prepares open cloze?"
- **Problem:** Read literally, "prepare open cloze" means to write or construct the test. The stem is learner-visible.
- **Proposed correction:** "Which activity best prepares you for open cloze?"

### ex-l1-006 part 3 — "One word per gap" is not in the reported profile (also ex-l1-009 part 1)
- **Location:** `ex-l1-006.json` part 3 option C; `ex-l1-009.json` part 1 option B
- **Severity:** S3 · **Category:** validity
- **Evidence:** "Supply one word per gap…"; "Write one suitable word for each gap…". The profile says only "Fill passage gaps without a supplied word bank."
- **Problem:** A single-word constraint is presented as part of the reported demand, but the profile does not say it.
- **Proposed correction:** "Write a suitable word for each gap without a word bank, then check…". Alternatively, mark "one word per gap" as the course's practice convention.

### ex-l1-006 part 1 — Distractor D is unclear; telegraphic options throughout
- **Location:** `ex-l1-006.json` part 1 option D; part 2 option C; part 4 option A
- **Severity:** S3 · **Category:** grammar / level-fit
- **Evidence:** "Use all time for composition." (why D: "That abandons Section 1", although Rafi has already finished Section 1); "Write outside synonyms."; "evidence-based MCQ".
- **Problem:** These clipped options are hard for 11–12-year-old ESL readers to parse. "MCQ" is an unexplained abbreviation.
- **Proposed correction:** D: "Move the spare minutes to the composition." C: "Write your own synonyms that are not in the bank." Option A: "…and multiple-choice questions based on evidence."

### ex-l1-009 part 3 — Illogical subject
- **Location:** `ex-l1-009.json` part 3 prompt
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "A practice platform finishes Section 1 with eight minutes unused."
- **Problem:** A learner, not a platform, finishes Section 1.
- **Proposed correction:** "During a practice test, Dani finishes Section 1 with eight minutes unused."

### ex-l2-005 part 5 — A self-rating is also "least affected by answer memory"
- **Location:** `backend_resources/english/v1/questions/ex-l2-005.json` (part 5)
- **Severity:** S2 (borderline S1) · **Category:** ambiguity
- **Evidence:** "Which comparison is least affected by answer memory? … C) A secure matched form with fresh prompts. D) A self-rating." Why D: "That is different evidence."
- **Problem:** Read literally, a self-rating does not depend on remembering answers at all, so D satisfies the stem at least as well as C. The rationale does not refute this; it changes the criterion. The parallel checkpoint ex-l2-008 part 2 correctly adds "best tests improvement while reducing answer-memory effects".
- **Proposed correction:** Stem: "Which comparison best measures real improvement while reducing the effect of remembered answers?"

### ex-l2-004 part 3–4 — Psychometric metalanguage beyond 11–12 ESL (also ex-l2-005 rationales)
- **Location:** `ex-l2-004.json` parts 3–5; `ex-l2-005.json` rationales
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Prompts: "What may the baseline legitimately support?", "Which limitation belongs beside an objective result?" Rationales: "No representative norm exists.", "No finite form does.", "Recall confounds growth.", "Constructs differ.", "Preserve blueprint, change items.", "Blueprint changes.", "Optimise honesty."
- **Problem:** The learner-visible stems and the feedback use assessment-specialist vocabulary (legitimately, objective result, norm, construct, confound, blueprint). Primary-age ESL learners cannot be expected to know these words. "Finite" also clashes with the grammar term "finite verb" taught in E2/E8.
- **Proposed correction:** Part 3: "What can your first test result honestly be used for?" Part 4: "What should you remember about a score from the multiple-choice questions?" Use plain rationales, for example "It does not tell you how well you write a full essay", "If you have seen the same questions before, a higher score may only show that you remember them", and "No test can check every English skill."

### ex-l2-008 part 2 — Asks the learner a test-designer's question (EX0.2 validity; also ex-l2-004 part 5, ex-l2-005 part 5)
- **Location:** `ex-l2-008.json` part 2 (module_checkpoint)
- **Severity:** S2 · **Category:** validity / level-fit
- **Evidence:** "After several weeks of learning, which comparison best tests improvement while reducing answer-memory effects? … C) Use a secure matched form covering the same blueprint with fresh prompts." EX0.2 outcome (catalogue): "Complete an untutored, mixed diagnostic covering vocabulary, grammar/cloze and reading."
- **Problem:** Choosing parallel forms is the platform's job, not a learner skill. The protected checkpoint therefore assesses recall of NextScholar's test-integrity jargon rather than the EX0.2 outcome. The wording ("secure matched form", "blueprint") is far above level.
- **Proposed correction:** Replace this part with a learner-action decision, for example: "You want to check your progress after six weeks. What should you do? A) Take the new progress test without looking at your old answers first…" Alternatively, re-scope EX0.2 checkpoints to the learner's own conduct only.

### ex-l1-005 part 2 — Abstract one-line rationales (also parts 3–4; ex-l1-006)
- **Location:** `ex-l1-005.json`, `ex-l1-006.json` choice_rationales
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "That describes generation." "This is the defining response demand." "That is recognition." "Reproduce its response mode."
- **Problem:** The feedback relies on the lesson's own labels (generation, recognition, response mode) instead of explaining the mistake in plain language.
- **Proposed correction:** For example, why B: "That describes open cloze, where you write your own word with no choices." Why A (ex-l1-006 part 3): "Choosing a title does not practise writing the missing words yourself."

---

## E6 planning (EW6.1 / EW6.2)

### ex-l1-001 part 6 — Key is the lesson's model contract verbatim; hint relies on the T-C-A-S-P acronym
- **Location:** `ex-l1-001.json` part 6 (exit_ticket); `lessons/e6-lesson-01.json` section 5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "‘I will explain to secondary-school readers how one school-learned skill applies in another area of life, using one specific actual or realistic example.’" Key B: "I will explain to secondary-school readers how one school-learned skill or idea applies in another area of life, using a specific actual or realistic example." Hint: "…preserves every T-C-A-S-P feature…"
- **Problem:** The exit ticket uses the same prompt as the lesson, and the key copies the lesson's worked answer. Part 6 therefore measures recall, not task decoding. The same sentence frame reappears as the key of the protected checkpoint ex-l1-010 part 1.
- **Proposed correction:** Give the exit ticket a fresh prompt, for example about a skill learned in a club and an audience of younger pupils, so the contract must be built anew. In the hint, write "topic, command, audience, scope and personal application" instead of the acronym.

### ex-l1-001 part 5 — Key is the only specific, long option; abstract stem at difficulty 2
- **Location:** `ex-l1-001.json` part 5
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** Stem: "What satisfies the prompt’s personal-application requirement?" Key D (83 characters): "A specific actual use or a realistic situation in which the writer could use the skill". The distractors are 33–55 characters.
- **Problem:** The answer can be found from length alone. "Personal-application requirement" is lesson metalanguage that is heavy for 11–12-year-olds at difficulty 2.
- **Proposed correction:** Stem: "The prompt says ‘have used it, or could use it’. Which example is allowed?" Use near-miss distractors, for example "A real use of the skill inside the same school lesson" or "A made-up past event written as if it really happened".

### ex-l1-007 part 1 — Unnatural key wording; title does not match prompt
- **Location:** `ex-l1-007.json` title and part 1 option B
- **Severity:** S3 · **Category:** grammar
- **Evidence:** Title: "Decode a community-change composition prompt". Prompt: "…one change you made after learning something in class…" (no community). Key: "One class lesson that led the writer to change an action".
- **Problem:** "Change an action" is not idiomatic, and the title refers to a community that the prompt does not mention.
- **Proposed correction:** B: "One change the writer made after a lesson in class". Title: "Decode a lesson-to-change composition prompt".

### ex-l1-007 part 5 — Non-parallel option in a model plan
- **Location:** `ex-l1-007.json` part 5 option B
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Describe learning to compare evidence, applying it to a recycling trial, and explaining what changed"
- **Problem:** An imperative verb is followed by two -ing forms, so the list is not parallel.
- **Proposed correction:** "Describe learning to compare evidence, apply it to a recycling trial and explain what changed".

### ex-l1-010 part 1–2 — Protected checkpoint reuses the exit-ticket and lesson template and its key pattern
- **Location:** `ex-l1-010.json` parts 1–2 (module_checkpoint) compared with `ex-l1-001.json` parts 4 and 6 and `e6-lesson-01`
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Key 1B: "I will explain to secondary-school readers how one group-project habit can solve an outside-school problem, using one actual or realistic example." The part 2 options mirror ex-l1-001 part 4 (one X / "comparison of at least three" / outside application / specific example / "Proof that … succeeded perfectly"), with the same key A, C, D.
- **Problem:** A learner who memorised the practice pattern can answer without decoding the new prompt.
- **Proposed correction:** Vary the frame. For example, build a prompt whose audience is younger pupils or the school principal, or one where the example must be past only. Include a distractor that keeps the right frame but gets one feature wrong, for example "…to my teachers…" or "…several habits…".

### ex-l1-011 part 1–3 — Difficulty-4 protected checkpoint answerable by length; "community court" unclear
- **Location:** `ex-l1-011.json` (module_checkpoint, difficulty 4)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** All three keys are the longest options, at about 2× the distractor length. Distractors include "List every scientific idea learned since primary school." and "Compare the difficulty of all school subjects." Key 3A: "…test a booking board for a crowded community court…"
- **Problem:** With no near-miss options, the checkpoint does not discriminate at the stated difficulty. "Community court" may be read as a law court by ESL learners.
- **Proposed correction:** Add near-miss distractors, for example a focus with the right idea but no specific situation, or one specific situation with no school-learned idea. Write "a crowded community basketball court".

### ex-l2-001 part 3 — I-S-A-R jargon in the stem, labelled keys, copied lesson example
- **Location:** `ex-l2-001.json` part 3 (exit_ticket); `lessons/e6-lesson-02.json` "Use the I-S-A-R frame" / "Usable idea"
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Stem: "Which THREE details make the charity-sale idea developable with the I-S-A-R frame?" The keys literally begin "The school-learned idea is…", "The situation is…" and "The action is…". The distractors carry no I/S/A label. The lesson model is "break a multi-step mathematics problem into smaller parts … school charity sale by separating publicity, supplies, prices and staffing". Why B mentions "the original mathematics problem", which the item never states.
- **Problem:** The answer can be found by matching labels, and the scenario is the lesson's worked example. The stem relies on a NextScholar acronym (skill d). The rationale refers to context that is not on screen.
- **Proposed correction:** Use a new scenario. Remove the "The idea/situation/action is" lead-ins, or add them to the distractors too, for example "The result is that everyone loved it". Write "with the Idea–Situation–Action–Result frame" in full, and state the mathematics origin in the stem if the rationale needs it.

### ex-l2-001 part 2 — Incongruous scenario; tests the lesson's taxonomy
- **Location:** `ex-l2-001.json` part 2
- **Severity:** S3 · **Category:** validity
- **Evidence:** "A learner notices an older sibling use a study timetable to prepare for a sports tournament." Why D: "The observation can supply relevant evidence when it is connected to the selected learning." (This does not say why D is wrong.)
- **Problem:** A "study timetable" for a sports tournament is odd. The part tests recall of the lesson's category names rather than idea generation. The D rationale explains B instead of D.
- **Proposed correction:** "…use a training timetable to prepare for a badminton tournament." Why D: "It is not an opinion; it is something the learner saw another person do."

---

## E7 paragraphs (EW7.1 / EW7.2)

### ex-l1-002 part 1 — Instructions (and lesson) state the keyed paragraph promises (also part 4)
- **Location:** `ex-l1-002.json` instructions, parts 1 and 4; `lessons/e7-lesson-01.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Instructions: "Body paragraph one explains how dividing the event into tasks created a manageable initial plan. Body paragraph two shows how the same method supported adaptation…" Key 1B: "…turned a confusing workload into a manageable initial plan." Key 4B: "…the same step-by-step method helped us identify urgent tasks and adapt calmly." The lesson gives the same two promises word for word.
- **Problem:** The learner-visible instructions contain the answer for parts 1 and 4. Each key is the only option that echoes them, and the other options are throwaways ("I will now write my second paragraph about another topic").
- **Proposed correction:** Remove the paragraph-job sentences from the instructions and give only the event notes. Alternatively, keep them and change the parts so learners must judge between two on-topic but differently scoped promises.

### ex-l1-002 part 1, 4–6 — Writing-theory metalanguage beyond 11–12 ESL
- **Location:** `ex-l1-002.json` prompts
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Which paragraph promise gives body paragraph one the clearest controlling purpose?"; "…best establishes body paragraph two's dominant function?"; "A paragraph is reverse-outlined as…"; "Which reverse outline shows the clearest progression…". Rationales: "functionally relevant context", "task route".
- **Problem:** The stems require knowing terms such as controlling purpose, dominant function and reverse outline before the skill can be shown.
- **Proposed correction:** For example, "Which sentence best tells the reader what body paragraph one will be about?"; "Which sentence would be the best first sentence for body paragraph two?"; "A student wrote one-line notes for each paragraph: ‘…’. What should she change?"

### ex-l1-002 part 2 — "Exposed that" in a model sentence (also ex-l2-002 part 2)
- **Location:** `ex-l1-002.json` part 2 option B; `ex-l2-002.json` part 2 option C
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Giving each area a deadline exposed that nobody had confirmed the drinks order." / "The checklist exposed that the drinks order had not been confirmed."
- **Problem:** "Expose" followed by a that-clause is unidiomatic. These are keyed model sentences.
- **Proposed correction:** "…showed that nobody had confirmed the drinks order." / "The checklist revealed that the drinks order had not been confirmed."

### ex-l2-002 part 1 — Key and distractors copied from the lesson (also part 4)
- **Location:** `ex-l2-002.json` parts 1 and 4 (exit_ticket); `lessons/e7-lesson-02.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "Compare ‘The plan helped us’ with ‘Assigning a deadline to publicity, supplies, prices and staffing exposed the unconfirmed drinks order before the sale.’" Key 1C: "Assigning deadlines to publicity, supplies, prices and staffing exposed the unconfirmed drinks order while there was still time to act." Lesson: "water nearing an extension lead … Describing every cloud, shoe and wall colour". Part 4 key: "Water was spreading towards an extension lead…"; the distractors are clouds, shoes and the hall paint.
- **Problem:** The exit ticket reproduces the lesson's worked contrast, so it measures recall.
- **Proposed correction:** Use a different event, such as the library or seed-exchange contexts, or at least a different weak/strong pair and different irrelevant details.

### ex-l2-002 part 5 — Self-refuting distractors (also part 2 E, ex-l2-009 part 2 E, ex-l2-011 part 3 D)
- **Location:** `ex-l2-002.json` parts 2E and 5C; `ex-l2-009.json` part 2E; `ex-l2-011.json` part 3D; `ex-l2-006.json` part 4B
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "All 1,347 visitors became exactly 82 per cent calmer because of our method, although we collected no attendance or survey data." "Exactly 88.6 per cent of all confusion disappeared, although no count was made."
- **Problem:** Each distractor states its own flaw. No student would write this, so the part does not test whether learners can spot false precision in realistic writing. In the checkpoints, this reduces the real option count.
- **Proposed correction:** Use realistic false precision without the self-refuting clause, for example "About 200 visitors came, and most of them said the hall felt calmer." Learners must then check this against the notes.

### ex-l2-006 part 3 — Keyed "cautious interpretation" invents a finding absent from the verified notes
- **Location:** `backend_resources/english/v1/questions/ex-l2-006.json` (instructions; part 3 option A; part 1 option B)
- **Severity:** S2 · **Category:** validity / correctness
- **Evidence:** Notes: "Hana tested separate return and borrowing lines for one lunch period, recorded where delays occurred, and recommended a second trial before permanent change." Key 3A: "The pauses showed that book scanning, not returns, caused most observed delay, so changing every counter at once would have been premature." Why A: "This interprets the observation cautiously." Part 5 rejects "Scanning became 43.7% faster" because "No timed percentage was recorded."
- **Problem:** The notes never say where the delays occurred, so the keyed sentence states an unverified result. This contradicts the item's own rule ("Develop a paragraph from verified notes"). Part 1 key B ("where the borrowing process slowed") also presupposes this result.
- **Proposed correction:** Add to the notes: "…recorded where delays occurred (most pauses were at the scanning desk on the borrowing line)…". Alternatively, change 3A to "The marked pauses showed where the delay began, so changing every counter at once would have been premature."

### ex-l2-009 part 2 — Keyed evidence is not in the notes despite "Use only the stated evidence"
- **Location:** `ex-l2-009.json` instructions and part 2 (module_checkpoint); also part 3A
- **Severity:** S2 · **Category:** validity
- **Evidence:** Notes: "…one mixed queue at two doors caused uncertainty. A student team trialled blue cards for the left door and gold cards for the right door, while one helper redirected anyone in the wrong line. Use only the stated evidence." Keys: "A) The team handed each pupil a card matching one of the two doors. B) Several pupils checked their cards before joining a line." Why E: "The percentage invents evidence that the notes do not contain."
- **Problem:** Option B, the "observation" half of the keyed pair, is not in the notes. A learner applying the instruction strictly could reject it. E is rejected on exactly that ground, so the standard is inconsistent. Part 3A's "before the bottleneck … correct exceptions" also goes beyond the notes.
- **Proposed correction:** Add to the notes: "Pupils received a card before walking to the doors; several pupils checked their cards before joining a line, and the helper redirected only a few pupils."

### ex-l2-010 part 1 — Depends on ex-l2-009 notes and adds facts despite the "no facts beyond notes" instruction
- **Location:** `ex-l2-010.json` instructions, part 1 options A/B, part 2 option A
- **Severity:** S3 · **Category:** validity
- **Evidence:** Instructions: "Continue developing the assembly-entrance paragraph … without adding facts beyond the practice notes." (No notes are shown in this item.) The keyed relevant details are "Several pupils looked down at the card before choosing their line." The key ending is "…a simple signal can move routine choices earlier…".
- **Problem:** The item cannot stand alone: once the learner moves past ex-l2-009, the notes are not visible. The details it treats as relevant are themselves beyond those notes. "Move routine choices earlier" is opaque for 11–12-year-olds.
- **Proposed correction:** Repeat the expanded notes (see the ex-l2-009 fix) in the instructions. Rewrite the ending: "The trial suggests that giving pupils a simple sign before they reach the doors helps them choose the right line, though another assembly would be needed to check that it keeps working."

### ex-l2-011 part 1 — Keyed promise claims an unrecorded result
- **Location:** `ex-l2-011.json` instructions and part 1 option A (module_checkpoint)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Notes: "…Mira trialled large labels showing plant type and sowing month, then watched which questions visitors still asked. Use only the stated evidence." Key: "Clear labels helped visitors sort most packets independently while revealing what guidance was still missing." Why A: "…includes both the observed benefit…"
- **Problem:** The notes record no benefit ("most packets independently"). The keyed promise breaks the instruction that the item is testing.
- **Proposed correction:** Add to the notes: "After the labels went up, most visitors placed familiar packets without asking; questions continued about packets with local names not shown on the labels."

### ex-l2-012 part 1 — Inconsistent "evidence in the notes" standard
- **Location:** `ex-l2-012.json` instructions and part 1 (module_checkpoint)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Instructions: "…preserve the limits of the original notes." Key A: "Visitors began matching familiar packets to the labelled tables without first asking a volunteer." Why E: "The notes contain no evidence about visitors' later gardening success."
- **Problem:** A is not in the original notes either, so the same test that rejects E would reject A.
- **Proposed correction:** Apply the ex-l2-011 note expansion, and repeat the notes in this item's instructions so it can stand alone.

### ex-l2-011 part 3 — "Broad labels" is ambiguous
- **Location:** `ex-l2-011.json` part 3 option A
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "This showed that the broad labels reduced routine uncertainty but needed examples of local names…"
- **Problem:** The notes say "large" labels. "Broad" here could mean wide or general, and "routine uncertainty" is abstract for this level.
- **Proposed correction:** "This showed that the large labels helped with familiar packets but needed examples of local plant names before they could guide every visitor."

---

## E8 editing (EW8.1 / EW8.2)

### ex-l1-003 part 2 — Lesson gives the keyed revisions verbatim (also parts 3–4)
- **Location:** `ex-l1-003.json` parts 2–4 (exit_ticket); `lessons/e8-lesson-01.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "‘Did a new shelf arrangement’ becomes ‘introduced labelled return trays’; ‘got advice’ becomes ‘collected pupil feedback’; ‘a bad system’ becomes ‘returns remained unsorted…’" and "‘Returned books were sorted into labelled trays. Most returns were reshelved that day.’ Replacing ‘returns’ with … ‘literary items’ would blur the meaning". The keys are 2B "introduced labelled return trays and a reshelving rota", 3C "collected pupil feedback on opening hours" and 4A "Returned books went into labelled trays, and most returns were reshelved…". Distractor 4B is "literary commodities".
- **Problem:** The exit ticket asks for the exact edits the lesson performed on the same paragraph, so it measures recall rather than editing for precision.
- **Proposed correction:** Give the exit ticket a fresh draft with notes, or change the lesson to model on a different paragraph.

### ex-l1-003 part 4 — Keyed sentence drops the time limit from the notes
- **Location:** `ex-l1-003.json` part 4 option A
- **Severity:** S3 · **Category:** validity
- **Evidence:** Notes: "by the third weekend, most returns were reshelved on the day they arrived". Key: "Returned books went into labelled trays, and most returns were reshelved on the day they arrived."
- **Problem:** Without "by the third weekend", the result seems to apply from the start. The same item penalises claims wider than the notes.
- **Proposed correction:** "Returned books went into labelled trays, and by the third weekend most returns were reshelved on the day they arrived."

### ex-l1-003 part 6 — Model paragraph shifts its reference term right after a part praising stable reference
- **Location:** `ex-l1-003.json` part 6 option C
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "The volunteers opened… They introduced… After older students requested Sunday afternoon access, the team added a session…"
- **Problem:** The paragraph moves from "volunteers" to "the team", although part 4 has just taught learners to keep the reference term stable. "Requested" is also slightly stronger than the notes' "wanted".
- **Proposed correction:** "…After feedback showed that older students wanted Sunday afternoon hours, the volunteers added a Sunday session that 18 pupils attended."

### ex-l2-003 part 2 — Lesson gives the keyed combined sentences verbatim (also parts 4, 6)
- **Location:** `ex-l2-003.json` parts 2, 4, 6 (exit_ticket); `lessons/e8-lesson-02.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "‘Because the front room faced a bus stop, traffic obscured parts of two recordings.’" (identical to key 2B). Lesson: "‘Each of the interviewers was asked’ is singular…" (part 4). Lesson: "‘The club moved its next session to a back room, where each interviewer tested a microphone before recording. The later recordings were clearer.’" (copied into key paragraph 6B).
- **Problem:** The keyed sentences can be recognised from the lesson rather than built, so the item does not show control of sentence combining.
- **Proposed correction:** Keep the lesson's media-club model and give the exit ticket a parallel but different notes set, such as a different club, cause and agreement trap.

### ex-l2-003 part 5 — Option contains invented fact; "THREE sentences" includes a two-sentence option
- **Location:** `ex-l2-003.json` part 5 options A, F
- **Severity:** S3 · **Category:** validity
- **Evidence:** Instructions: "Use only these verified notes when editing". A: "When the first session ended, the club checked the audio." F: "The team changed its routine. The later recordings were clearer."
- **Problem:** A (keyed) adds an event that is not in the notes. F is two sentences offered as one of "THREE sentences".
- **Proposed correction:** A: "After the first session, the club moved to a back room." Stem: "Which THREE options are complete and use their structure…".

---

## E9 forms (EW9.1 / EW9.2)

### ex-l1-004 part 1–6 — Whole exit ticket replays the lesson's worked analysis
- **Location:** `ex-l1-004.json` (exit_ticket); `lessons/e9-lesson-01.json` "Turn an event into reflection"
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "a group assumed every basil seedling needed the same amount of water … Insight: a familiar rule may need adjustment… Transfer: when organising a book drive, the writer can first test one collection point, record when and what people donate, and revise the wider plan…". Keys: 3C "At first I treated a familiar rule as if it suited every pot…", 4B "…begin with one collection point, record when donations arrive and which categories…".
- **Problem:** The experience, insight and transfer are all supplied in the lesson, so the exit ticket checks memory of the model.
- **Proposed correction:** Use a new experience and transfer pair in the exit ticket, for example a debate-club rehearsal transferred to helping a younger sibling with homework.

### ex-l1-004 part 1, 3, 6 — Stem metalanguage and reading load too high
- **Location:** `ex-l1-004.json` instructions (115 words) and prompts
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Which controlling focus best answers the prompt and gives the response a reflective route?"; "Which sentence forms the strongest reflective hinge after the project evidence?"; "…the most focused personal expository response?". Rationales: "experience–insight–transfer chain", "bounded school experience".
- **Problem:** Terms like reflective hinge, reflective route and personal expository response sit on top of a 115-word stimulus and 30–60-word options. This is beyond 11–12 ESL readers, even at difficulty 4.
- **Proposed correction:** "Which sentence best states the main idea of Lina's composition?"; "Which sentence best explains what Lina learned from the project?"; "Which paragraph plan keeps the whole composition focused?" Shorten the notes to the facts the parts use.

### ex-l2-013 part 6 — Model ending: illogical image; "panels/boards" confusion (also part 5)
- **Location:** `ex-l2-013.json` part 6 option A; part 5 option B
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "…though one warped panel corner lay drying beside the door; Mira looked at the three-board route…"; "Mira saw the empty library boards and proposed carrying in only the three panels…"
- **Problem:** A corner cannot lie beside a door by itself, and it is unclear whether the warped panel was displayed. "Panels" and "display boards" are used for different objects, and "three-board route" mixes them. This will confuse young ESL readers in a keyed model text.
- **Proposed correction:** "…though one panel, its corner warped by the rain, leaned against the wall to dry; Mira looked at the three panels on the library boards and understood that…" Use "panel" consistently for exhibition items and "stand" for the empty boards.

### ex-l2-013 part 1–6 — Reading load for an exit ticket at this level
- **Location:** `ex-l2-013.json` instructions (131 words) plus six parts with options up to about 60 words
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "…wind-driven rain began spotting handwritten labels and the route map…"; "Water feathered the ink at the edge of the route map."
- **Problem:** The literary vocabulary ("feathered", "spotting") and the total reading volume are heavy for 11–12 ESL learners in a single exit ticket.
- **Proposed correction:** Trim the planning record to the facts the parts use. Replace "feathered the ink" with "made the ink spread". Consider splitting the item into two three-part exit tickets.

---

## Slice summary

**Counts (41 findings):** S1: 0 · S2: 21 · S3: 20. ex-l2-005 part 5 is borderline S1: a literal reading makes D also correct.

**Cross-cutting patterns**
1. **Length, hedging and position cue (S2, slice-wide).** In 86 of 95 single-choice keys, the key is the longest option. D is keyed only 7 times. Every multiple-response key set includes A, and five sets are exactly A-B-C. Distractors are often absurd or self-refuting. This is worst in the protected checkpoints ex-l1-008, ex-l1-009, ex-l1-010, ex-l1-011, ex-l2-007, ex-l2-008, ex-l2-009, ex-l2-010, ex-l2-011 and ex-l2-012, where difficulty labels of 3–4 are not credible.
2. **Exit tickets copy their own lesson's worked examples (S2).** Affected items: ex-l1-001 (e6-lesson-01), ex-l1-002 (e7-lesson-01), ex-l1-003 (e8-lesson-01), ex-l1-004 (e9-lesson-01), ex-l2-001 (e6-lesson-02), ex-l2-002 (e7-lesson-02) and ex-l2-003 (e8-lesson-02). Only ex-l2-013 (e9-lesson-02) uses a reasonably fresh realisation.
3. **"Use only the stated or verified notes" broken by the keys themselves (S2).** Affected items: ex-l2-006, ex-l2-009 (with ex-l2-010), ex-l2-011 and ex-l2-012. The keyed observations or results are absent from the notes, while distractors are rejected for exactly that reason. The fix is to expand the notes.
4. **Evidence-status inconsistency in EX0.1.** ex-l1-005 and ex-l1-008 treat candidate-reported timing and format as "evidence-backed" or "supported", but treat the about-300-word figure from the same single report as provisional. Keyed numbers are otherwise consistent with `catalogue.json` and the exam profile, and the editing exclusion is correct.
5. **Metalanguage and NextScholar jargon above the 11–12 ESL band (S2).** Examples: ex-l1-002 (controlling purpose, dominant function, reverse outline); ex-l1-004 (reflective hinge, personal expository response); ex-l2-001 (I-S-A-R); ex-l1-001 (T-C-A-S-P, personal-application requirement); ex-l2-004 and ex-l2-005 (legitimately, norm, construct, confounds, blueprint).
6. **EX0.2 items assess platform test-integrity policy** (matched forms, blueprint, what "the course" should publish) rather than the outcome "complete an untutored diagnostic". Affected items: ex-l2-004, ex-l2-005, ex-l2-007, ex-l2-008, ex-l1-006 part 5 and ex-l1-008 part 3.
7. **Multiple-response hints list the keyed categories** (for example ex-l1-004 part 2, ex-l2-013 part 2, ex-l2-001 part 3 and ex-l1-002 part 2), so they give the answer away. This is acceptable for practice because hint use voids mastery, but note it (S3).
8. **Paired checkpoint forms are not parallel** (E0 A vs B sample different facts). The same decision is rated difficulty 2 in practice and 3 in a checkpoint.

**Items considered sound in key and logic (subject to the cross-cutting patterns above):** ex-l1-001 parts 1–4; ex-l1-002 parts 2–3, 5–6; ex-l1-003 parts 1, 5; ex-l1-004 parts 2, 5; ex-l1-007 parts 2–4, 6; ex-l1-010 part 3; ex-l2-001 parts 1, 4–6; ex-l2-002 parts 3, 6; ex-l2-003 parts 1, 3; ex-l2-007 (keys sound); ex-l2-013 parts 1–4. Every keyed answer was checked and none is wrong. The model paragraphs in ex-l1-003 part 6, ex-l2-003 part 6 and ex-l2-013 part 3 are grammatical and well controlled, apart from the S3 notes above.
