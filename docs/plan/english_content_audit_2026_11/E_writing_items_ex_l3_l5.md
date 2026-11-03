# Findings — slice E_writing2 (ex-l3-*, ex-l4-*, ex-l5-*)

Scope: 21 items, 112 parts (101 single-choice, 11 multiple-response). Source: `backend_resources/english/v1/questions/`.
Level-fit is judged against the audit level-fit basis: the only exam profile (`exam_profiles/asean-english-sec1-id-reported-v1.json`) has `entry_level: secondary_1_entry`, so the learner band is about **11–12-year-old ESL learners** in their final primary year, not 13–16.
Checked against `catalogue.json` `exam_blueprint`: Section 1 is 90 min and Section 2 is 30 min, both `evidence_status: candidate_reported`. The blueprint says nothing about whether time can be moved between sections. Option-shuffling logic was not found anywhere in the repo, so the key-position and length patterns below are assumed to reach learners as authored.

---

## S1 findings

### ex-l5-007 part 2: the stem states the defect, and the key is the only option that fixes it
- **Location:** `backend_resources/english/v1/questions/ex-l5-007.json` (part 2; protected module_checkpoint, form `english-checkpoint-e6-planning-a-v1`)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** Prompt: "The plan names roles and events but never explains how they solved the problem. What is the most important repair before drafting?" Key A: "Add a link-back after each body example explaining how clear responsibility reduced confusion or enabled adaptation." Distractors: "Add a second unrelated school habit…", "Replace the specific evidence with general statements…", "Remove the conclusion…"
- **Problem:** The stem does the diagnosis ("never explains how"), and A is the only option that adds an explanation. The other options are plainly harmful, so the part is answered by matching words. It is one of only two parts in this checkpoint item.
- **Proposed correction:** Show the faulty plan instead of describing it. For example: "Body 1: roles assigned: collection, sorting, supplies. Body 2: one volunteer absent; Ravi moved to sorting. Conclusion: roles help." Ask "What is the most important repair before drafting?" with plausible competing repairs: (A) add an explanation after each body example of how clear roles reduced confusion or kept work moving [key]; (B) add a vivid opening detail about the clean-up; (C) add a third body example about another event; (D) make the conclusion longer by restating both body examples.

### ex-l4-005 part 3: the instructions name the irrelevant sentence before the deletion question
- **Location:** `backend_resources/english/v1/questions/ex-l4-005.json` (instructions; parts 3 and 5; protected module_checkpoint, form `english-checkpoint-e8-revision-a-v1`)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** Instructions: "The flawed draft omits the final learning, begins with book-cover colours, gives the result before the method and contains one agreement error." Part 3 key C: "Several donated novels had blue or green covers." Part 5 key D: "Change ‘each jobs were assigned’ to ‘each job was assigned’." This is the only sentence-level option; the others are "Change the verified result into a stronger universal claim", "Move the result before the method again" and "Add another unrelated example".
- **Problem:** The checkpoint instructions list every flaw, so part 3 (delete the cover colours) and part 5 (fix the agreement error) only test matching. Part 5's distractors are not even sentence-level corrections. That leaves parts 1, 2 and 4 to measure prioritisation.
- **Proposed correction:** Present the flawed draft as a short text (4–6 sentences) and remove the flaw list from the instructions, so learners have to find the problems. In part 5, use distractors that are real sentence-level edits but not needed (for example, a correct sentence "corrected" into an error such as "each job were assigned", or an unnecessary comma).

### ex-l4-006 part 3: the instructions name the supermarket-music sentence, and parts 1, 2 and 5 are pre-diagnosed too
- **Location:** `backend_resources/english/v1/questions/ex-l4-006.json` (instructions; parts 1, 2, 3, 5; protected module_checkpoint, form `english-checkpoint-e8-revision-b-v1`)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** Instructions: "The flawed draft opens with supermarket music, claims the choice is best for every family, places the choice before the comparison and has a comma splice." Part 3 key C: "A cheerful song was playing through the supermarket speakers." Part 5 key A: "Change ‘I compared the labels, the difference became clear’ to two complete sentences."
- **Problem:** Each flaw is named in the instructions, so part 3 (and largely part 5) can be answered without editing judgement. Part 1 still needs a priority decision, but its distractors ("A repeated word.", "The length of one sentence.") are not among the described flaws, which makes the higher-order option obvious.
- **Proposed correction:** As for ex-l4-005: show the draft instead of describing it. In part 1, offer competing higher-order options, for example universal claim vs choice-before-comparison vs off-topic music opening vs comma splice, and use the rationale to explain why evidence accuracy outranks order.

### ex-l5-008 part 1: the stem reveals another scored item's answer in the same protected form
- **Location:** `backend_resources/english/v1/questions/ex-l5-008.json` (part 1 prompt and option A; form `english-checkpoint-e6-planning-b-v1` = [`ex-l1-011`, `ex-l5-008`], feedback after_form)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** ex-l5-008 P1 prompt: "Which pair of body-paragraph jobs best develops the community-court booking-board focus?" Option A: "Body 1: record when and why clashes occur before changing anything. Body 2: test a one-week booking board…" ex-l1-011 P3 (same form) asks "Which proposed focus best satisfies the scope and personal-application requirements?", and its key A is "Use the scientific idea of observing before changing variables to test a booking board for…"
- **Problem:** Inside one protected checkpoint form, the second item names the focus that the first item asks learners to choose. Within ex-l5-008 P1 itself, option A is also the only option about the booking board, so the stem points to the key.
- **Proposed correction:** Change the ex-l5-008 stem to neutral wording ("Which pair of body-paragraph jobs best develops the chosen focus?") and add plausible distractors that also mention the court or the booking board but have overlapping or undeveloped jobs. For example: "Body 1: introduce the booking board. Body 2: describe the booking board again in more detail." Apply the same check to form A: the ex-l5-007 P1 stem ("using role assignment during a neighbourhood clean-up") confirms that ex-l1-010 P3 option A is on-task (S3 there).

---

## S2 findings

### ex-l3-003 parts 1, 2, 5, 6: keyed sentences are copied word for word from the E8.3 lesson
- **Location:** `backend_resources/english/v1/questions/ex-l3-003.json` (P1 A, P2 B, P5 B, P6 B) vs `lessons/e8-lesson-03.json` sections[1], [4]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "‘Because queues were longest during the first ten minutes of lunch, the school opened a temporary second refill point.’" and "‘The fall occurred during the week in which the second point operated, which is consistent with reduced congestion, although the short trial cannot establish a long-term effect.’" Item P5 key B: "The wait fell during the week in which the second point operated, which is consistent with reduced congestion, although the trial did not measure a long-term effect." P1 A and P6 B open with the lesson's cause sentence.
- **Problem:** The exit ticket rewards recognising the lesson's worked sentences instead of applying the skill to new facts.
- **Proposed correction:** Give the exit ticket a fresh scenario, for example a library-return trolley trial or a bike-rack pilot with different numbers. Alternatively, keep the refill scenario but rewrite every keyed sentence so that no seven-word string matches the lesson.

### ex-l3-003 parts 3–6: causal-reasoning metalanguage is beyond 11–12 ESL learners
- **Location:** `backend_resources/english/v1/questions/ex-l3-003.json` (P4, P5 prompts and options)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Which statement best avoids treating sequence alone as proof of a long-term causal effect?"; "…which is consistent with reduced congestion…"; "Which THREE phrases would correctly qualify a claim about the pilot?"
- **Problem:** "Treating sequence alone as proof of a long-term causal effect", "qualify a claim" and "consistent with" are terms from academic research methods. Learners of 11–12 cannot be expected to process them in the stem before they reach the writing decision.
- **Proposed correction:** P5 stem: "Which sentence does NOT claim more than the one-week trial showed?" P4 stem: "Which THREE phrases make the claim match exactly what was measured?" Replace "consistent with reduced congestion" with "which suggests the second point helped".

### ex-l3-004 part 3: the "evidence-bounded" model paragraph overstates the record
- **Location:** `backend_resources/english/v1/questions/ex-l3-004.json` (part 3, option C, the key)
- **Severity:** S2 · **Category:** correctness
- **Evidence:** Record (instructions): "the reading-support coordinator says irregular attendance makes pairing volunteers with younger readers difficult". Model: "In the fictional record, irregular attendance prevents the coordinator from preparing stable reading pairs". Rationale: "uses a relevant record detail… and limits what can be concluded"; hint: "whose conclusion stays within the supplied fictional evidence".
- **Problem:** "Prevents" turns "makes… difficult" into impossibility, which breaks the evidence-scope rule the item is teaching. The model also writes "In the fictional record" inside essay prose, which is a planning note and should not appear in a learner's paragraph.
- **Proposed correction:** "…According to the programme coordinator, irregular attendance makes it difficult to prepare stable reading pairs; choosing a defined role and schedule would make each volunteer's contribution predictable. This supports a structured commitment, though it does not prove that every compulsory programme succeeds."

### ex-l3-004 parts 1, 3, 4, 5: keyed options are copied from the E9.3 lesson
- **Location:** `backend_resources/english/v1/questions/ex-l3-004.json` vs `lessons/e9-lesson-03.json` sections[1], [2]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "‘Schools should expect one service contribution each term, provided students can choose from accessible roles and use a genuine hardship alternative’" and "Claim: a structured term commitment can make participation more dependable than an unplanned invitation." Item P1 key B: "Schools should expect one bounded service contribution each term, provided students can choose accessible roles…"; P3 key C: "A bounded term commitment could make participation more dependable than an unplanned invitation."
- **Problem:** The exit ticket uses the same prompt, record and thesis as the lesson's worked example, so learners can recognise the answer instead of building one.
- **Proposed correction:** Use a different position prompt for the exit ticket, for example "Should every student be required to join one after-school club?", with its own fictional record, and write new keyed sentences.

### ex-l3-004 whole item: a conditional policy argument is beyond the 11–12 band
- **Location:** `backend_resources/english/v1/questions/ex-l3-004.json` (instructions, P1–P6)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Schools should expect one bounded service contribution each term, provided students can choose accessible roles and use a genuine equivalent or exemption when circumstances require it."; "Which THREE details are most relevant to judging whether the requirement can be both dependable and accessible?"; P6 key B is 455 characters long.
- **Problem:** The item expects primary-final-year ESL learners to read a dense policy brief and judge conditional theses, concessions and five-paragraph discursive routes. The language ("bounded", "genuine equivalent or exemption", "dependable and accessible") and the length go far beyond the band, even at difficulty 4.
- **Proposed correction:** Simplify the scenario to three plain facts. Use plain wording: "Students should do one helping project each term, but they should be able to choose a project they can reach." Cut P6 options to under 200 characters.

### ex-l4-002 parts 1 and 4: the keyed opening and ending are the lesson's worked examples
- **Location:** `backend_resources/english/v1/questions/ex-l4-002.json` (P1 C, P4 B) vs `lessons/e7-lesson-04.json` sections[1], [3]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson section 1: "‘School projects taught me that a large problem becomes manageable when it is divided into clear next actions. I later relied on that method while organising a charity sale, especially when sudden rain forced our team to change plans.’" This is identical to item P1 C. Lesson section 3: "‘The sale showed me that planning is not the same as predicting every problem. Its real value is giving people a clear next action when circumstances change.’" This is identical to item P4 B.
- **Problem:** The two central exit-ticket decisions can be answered from memory of the lesson.
- **Proposed correction:** Write new keyed opening and ending sentences, for example for the basil or book-swap scenario, or paraphrase them substantially and change the scenario.

### ex-l4-004 part 6: the keyed "complete revision" has an unclear referent and leaves out the repair from Part 1
- **Location:** `backend_resources/english/v1/questions/ex-l4-004.json` (part 6, option C, the key)
- **Severity:** S2 · **Category:** grammar
- **Evidence:** "In mathematics I learned to compare like quantities. I recorded five ordinary shower durations, then tested a timer across five later days. Four were shorter, which suggested the timer could help my routine, although I had not measured water flow or proved the result for others. The trial taught me to make a limited claim from limited evidence." Part 1 key: "The draft never explains how the mathematics idea guided Arif's home trial." Part 2 key: "Learning to compare like quantities helped me design a small, fairer test of my shower routine."
- **Problem:** "Four were shorter" has no clear referent: four of the days, or four showers, and shorter than what? The paragraph is offered as the version that "best completes all four passes", but it still never explains how comparing like quantities shaped the trial (the Part 1 repair). It also does not use the Part 2 focus, and its reflection drifts to evidence limits rather than the mathematics transfer.
- **Proposed correction:** "Learning to compare like quantities in mathematics helped me design a fairer test of my shower routine. First, I recorded how long I showered on five ordinary days. Then I used a timer on five later days, so I was comparing the same kind of measurement under two conditions. On four of the five timer days, my shower was shorter than my ordinary-day average. This suggested that the timer could help me, although I had not measured water flow or proved that it would work for anyone else. The trial taught me that a fair comparison needs like quantities, and that a small test supports only a small claim."

### ex-l4-005 / ex-l4-006 whole items: checkpoint distractors are not plausible, and the key is usually the longest option
- **Location:** `backend_resources/english/v1/questions/ex-l4-005.json`, `ex-l4-006.json` (all parts)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** ex-l4-005 P1 distractors "Shorten the title by one word."; P4 C "Exactly 99 per cent of organisers now prefer my system."; P5 A "Change the verified result into a stronger universal claim." ex-l4-006 P5 B "Restore the universal claim."; C "Move the choice before the comparison." In 8 of 10 parts the key is the longest option (up to 2.3×).
- **Problem:** Distractors that undo repairs or announce invention ("invented", "unverified", "unrelated") eliminate themselves. These difficulty-4 module checkpoints therefore cannot tell learners who can edit by priority from those who cannot.
- **Proposed correction:** Write each distractor as a real but lower-priority edit, for example "Replace ‘good’ with ‘beneficial’ throughout", "Add a sentence explaining what a book swap is", or "Combine the two short opening sentences". Match option lengths to within about ±20%.

### ex-l4-007 parts 1–4: the process-compression metalanguage is too abstract for the band
- **Location:** `backend_resources/english/v1/questions/ex-l4-007.json` (P1 prompt and options; P2–P4 options)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Which rehearsal sequence best represents safe process compression?"; "Use a supported 45-minute fresh response to locate bottlenecks, fade support on a fresh 35-minute response…"; "a separately controlled 30-minute clock"; "complete the claim–detail–explanation chain". Rationales: "confounds memory with transfer", "would contaminate the learner's independent writing evidence".
- **Problem:** "Process compression", "fade support", "bottleneck", "confounds" and "contaminate" are teacher-education or research terms. An 11–12 ESL learner is tested on reading this metalanguage more than on planning a timed write.
- **Proposed correction:** P1 stem: "Which practice plan is the safest way to get ready for writing in 30 minutes?" Key: "Practise with 45 minutes and help, then 35 minutes with less help, then 30 minutes alone, using a new question each time." Use plain words in the rationales ("You might just remember the answer", "Someone else's help means it is not your own work").

### ex-l5-001 parts 3 and 4: the keyed planning notes are copied from the E6.5 lesson
- **Location:** `backend_resources/english/v1/questions/ex-l5-001.json` (P3 A, P4 C) vs `lessons/e6-lesson-05.json` sections[2]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "Body 2 job: show the same method during disruption. Evidence: rain forces the stalls indoors; rank urgent moving and safety tasks; reassign helpers before handling decorations. Link-back: one-priority-at-a-time thinking supports calm adaptation." Item P4 key C: "When conditions changed: rain moved stalls indoors. Rank urgent moving and safety tasks; reassign helpers. Explain: the same step-by-step method supported calm adaptation." P3 key A repeats the lesson's "divide publicity, supplies, prices and staffing; assign deadlines".
- **Problem:** The exit ticket's body-plan decisions reproduce the lesson's worked plan.
- **Proposed correction:** Use a new scenario for the five-minute plan, as the parallel item ex-l5-006 already does with the recycling trial, or rewrite the keyed notes with different evidence.

### ex-l5-002 parts 1 and 3: the key is copied from the lesson, and "reverse outline" / "abstracts" are too abstract
- **Location:** `backend_resources/english/v1/questions/ex-l5-002.json` (P1 B; P1 and P3 prompts) vs `lessons/e7-lesson-05.json` sections[1]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "A reverse outline names functions, not topics: initial approach → concrete problem and consequence → targeted response → observable result → wider significance. That sequence is the model’s reusable move." Item P1 key B: "initial approach → specific weakness and consequence → targeted response → observable result → wider significance". P3 stem: "Which planning note abstracts the model before transferring it?"
- **Problem:** P1 can be answered by recalling the lesson's own outline, which also uses the lesson's repair-café model. "Reverse outline", "structural move" and "abstracts the model" are writing-pedagogy jargon that is too hard for 11–12 learners.
- **Proposed correction:** Use a different model paragraph in the exit ticket from the one analysed in the lesson. P1 stem: "Which list shows what each sentence of the model DOES?" P3 stem: "Which planning note keeps the model's steps but drops its topic words?"

### ex-l5-004 / ex-l5-005 whole items: telegraphic options and jargon make the protocol hard to read
- **Location:** `backend_resources/english/v1/questions/ex-l5-004.json` (P2 B, P3 B, P5 B and all rationales); `ex-l5-005.json` (P4 hint and explanation, P5)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** ex-l5-004 P2 key: "Reserve both readings and a checking buffer; adjust earlier budgets."; P3 key: "Choose the best, flag it and move for a possible return."; P5 key: "Use strand errors for practice, then later use a matched fresh form."; rationales "Transfer is unconfirmed.", "Recall confounds growth.", "That adds help."; explanation "Commit–flag–move preserves the whole paper." ex-l5-005 hint "Record timing and contamination status."; explanation "Specific metadata preserves an audit trail."
- **Problem:** The options read like compressed internal notes ("adjust earlier budgets", "strand errors", "matched fresh form"). The rationales are too short and abstract for 11–12 ESL learners to learn from after submitting. Several parts test NextScholar's own routine names ("commit–flag–move", "strand", "form") rather than exam-taking judgement.
- **Proposed correction:** Write full plain sentences. P2 key: "Keep enough time for both reading passages and a few minutes to check; spend less time on the earlier parts if needed." P5 key: "Look at which kinds of questions you got wrong, practise those, and later try a new practice test of the same type." Rationales should be one plain sentence that says why, for example "Moving essay time to Section 1 may not be allowed in the real test, so practise with separate clocks."

### ex-l5-009 / ex-l5-010 whole items: difficulty-5 checkpoints with implausible distractors and a strong length cue
- **Location:** `backend_resources/english/v1/questions/ex-l5-009.json`, `ex-l5-010.json` (all parts)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** ex-l5-009 P5 B "Treat the total as a guaranteed scholarship-admission prediction."; P2 D "Ask someone which flagged answers should be changed."; P4 D "Use the interruption to look up every flagged answer." ex-l5-010 P3 D "Count every word before checking whether the prompt was answered."; P5 C "The score guarantees scholarship admission." In 10 of 10 parts the key is the longest option (1.2×–2.4×).
- **Problem:** These are labelled difficulty 5, the top level, but each distractor openly breaks independence or makes an absurd claim. The key can be found by length and by its careful wording ("bounded", "cautious"), so the checkpoint gives little evidence of readiness.
- **Proposed correction:** Use near-miss distractors, for example "Move to reading and spend all 40 minutes on the first passage so that it is done well" (part 2), "Resume the attempt but restart the 90-minute clock from zero" (part 4), or "Use the score to decide which section to stop practising" (part 5). Equalise option lengths.

---

## S3 findings

### ex-l3-001 parts 1, 5, 6: NextScholar lesson codes and routine names appear in learner-facing text
- **Location:** `backend_resources/english/v1/questions/ex-l3-001.json` (instructions, P1, P5, P6); likewise `ex-l4-001.json` (instructions "E6.3 plan", P5 hint "link-back check", P6 "prepares the composition for E6.5"), `ex-l5-001.json` (instructions "E6 focus map")
- **Severity:** S3 · **Category:** validity
- **Evidence:** "Continue from the task contract and E6.2 idea pool."; "pass the relevance, development and link tests"; "Which plan shows list planning rather than selection for depth?"; "Which selected plan best prepares for E6.4…"
- **Problem:** Internal lesson codes and coined routine names test knowledge of the product's vocabulary. Learners who arrive through retry or review routes may not recognise them.
- **Proposed correction:** "Continue from your idea list"; "Which TWO ideas should you keep because they are on the topic, can be explained in detail and connect to your main idea?"; "Which plan tries to cover too many topics?"; "Which plan is best for writing your main idea next?"

### ex-l3-001 part 3: a distractor states its own flaw
- **Location:** `backend_resources/english/v1/questions/ex-l3-001.json` (part 3, option B)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** "The response to the sudden rain before the reader knows the original plan"
- **Problem:** The phrase "before the reader knows…" tells the learner why the option is wrong. The same pattern appears in ex-l4-007 P3 B ("whether or not it supports the focus") and P5 B ("even if the response ends mid-sentence"), ex-l5-002 P5 D ("although no measurements were recorded"), ex-l5-003 P3 B–D ("although no spelling error appears in the log"; "because every single error must become an active pattern"; "ignoring that entry 7 was a single error…") and ex-l5-008 P2 C ("even though the evidence and paragraph jobs are unclear").
- **Proposed correction:** Remove the self-refuting clauses, for example "The response to the sudden rain". Leave learners to judge the order themselves.

### ex-l3-002 parts 1, 2, 5: cohesion metalanguage is too abstract, and the reference-chain key includes a new referent
- **Location:** `backend_resources/english/v1/questions/ex-l3-002.json` (P1 stem, P2 stem and option C, P5 stem)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "clearest given-to-new progression"; "Which THREE phrases create the clearest reference chain after ‘Water was spreading towards an extension lead’ ?"; key includes C "the decision to move electrical equipment first"; "Which thread-word chain preserves one central idea without mechanical repetition or synonym drift?"
- **Problem:** "Given-to-new progression", "reference chain" and "synonym drift" are linguistics terms that are too hard for this band, so they should arguably be S2 for 11–12. C does not refer back to the water or the risk; it introduces a new referent, so it is part of a noun-phrase sequence, not a reference chain. Learners must pick three, so they are forced to accept it. There is also a stray space before "?".
- **Proposed correction:** P2: "Which THREE phrases help the reader follow the story clearly after ‘Water was spreading towards an extension lead’?" (delete the space before "?"). P1: "Which order makes each sentence follow on from the one before?" P5: "Which set of phrases keeps the same main idea without just repeating one word?"

### ex-l3-004 parts 4–5: the counterargument targets a design that was never proposed, and the model has an awkward collocation
- **Location:** `backend_resources/english/v1/questions/ex-l3-004.json` (P4 B, P5 A, P5 C)
- **Severity:** S3 · **Category:** validity
- **Evidence:** Proposal (instructions): "would let each student choose one bounded role and schedule; supervised on-campus roles and a genuine equivalent or exemption would be available". P4 key: "A fixed external or weekend requirement could unfairly burden students…"; P5 A: "the original weekend rule should remain unchanged"; P5 C (model): "The requirement would therefore need choices of time, supervised on-campus roles…"
- **Problem:** The record's proposal already contains the protections that P5 says the writer "therefore" needs, and no "weekend rule" exists in the record. The concession is therefore circular, and the "strongest counterargument" attacks a straw design. "Choices of time" is unidiomatic.
- **Proposed correction:** Make the record's proposal a "fixed Saturday litter collection for all students", so the concession leads to the changes. In the model, write "a choice of times".

### ex-l4-001 part 1: "mathematics" appears without being set up
- **Location:** `backend_resources/english/v1/questions/ex-l4-001.json` (P1 B, P2 B)
- **Severity:** S3 · **Category:** validity
- **Evidence:** Key: "Breaking a large task into smaller parts is useful beyond mathematics…"; P2 key B: "It shows an application beyond the original mathematics setting." The instructions only say "The school-learned method is breaking a large task into smaller parts."
- **Problem:** The learner is never told that the method was learned in mathematics.
- **Proposed correction:** Add "learned in mathematics" to the instructions.

### ex-l4-002 part 6: the keyed opening is a question, but Part 1 rejected a question opening
- **Location:** `backend_resources/english/v1/questions/ex-l4-002.json` (P1 B rationale vs P6 B)
- **Severity:** S3 · **Category:** validity
- **Evidence:** P1 why B: "The rhetorical question and essay announcement occupy space without identifying the lesson or direction." P6 key: "Opening: ‘Can one simple classroom method remain useful when a real plan fails?’"
- **Problem:** Within one item, learners may conclude that question openings are both bad and good.
- **Proposed correction:** In the P1 rationale, say "The general question and essay announcement do not name the lesson…". In the P6 rationale, add a note that a question works when it names the specific method and situation.

### ex-l4-003 parts 1 and 5: the same error is described two different ways
- **Location:** `backend_resources/english/v1/questions/ex-l4-003.json` (P1 C, P5 C)
- **Severity:** S3 · **Category:** validity
- **Evidence:** P1 C: "The word ‘seedling’ is misspelled once." P5 C: "Correct ‘seedling were’ to ‘seedlings were’." (rationale: "repairs number agreement"). The flaw list in the instructions mentions neither error.
- **Problem:** The same surface error is called a spelling error in one part and an agreement error in another.
- **Proposed correction:** P1 C: "One verb does not agree with its subject (‘seedling were’)." Add "and contains a comma splice and an agreement error" to the instructions.

### ex-l4-004 whole item: the retry form has no prompt or draft, and its rationales are terse and refer to options by position
- **Location:** `backend_resources/english/v1/questions/ex-l4-004.json` (instructions; all rationales and explanations)
- **Severity:** S3 · **Category:** validity
- **Evidence:** Instructions give only the notes plus "Edit by task, structure, development, then conventions." There is no prompt and no draft. The rationales say "Conventions come later.", "The third sentence controls the response.", "The second order supports interpretation.", "The third revision preserves…" (ex-l5-006 P1 has the same pattern: "The first sequence…").
- **Problem:** This parallel retry form is much thinner than ex-l4-003. Learners judge a draft they cannot see. Rationales that refer to options by position break if options are ever reordered.
- **Proposed correction:** Add the prompt and a one-line description of the draft, as in ex-l4-003. Replace position references with content ("The focus sentence about comparing like quantities…").

### ex-l4-007 part 1: "toward" uses US spelling
- **Location:** `backend_resources/english/v1/questions/ex-l4-007.json` (P1 rationale D)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "a controlled move toward the reported independent limit"
- **Problem:** "Towards" is used everywhere else in the slice.
- **Proposed correction:** "towards".

### ex-l5-001 part 6: ASCII arrows
- **Location:** `backend_resources/english/v1/questions/ex-l5-001.json` (P6 A)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "initial division of tasks -> manageable plan … reprioritising -> calm adaptation"
- **Problem:** Other items use "→".
- **Proposed correction:** Replace "->" with "→".

### ex-l5-001 / ex-l5-006 part 1: the parallel forms teach different planning orders
- **Location:** `backend_resources/english/v1/questions/ex-l5-001.json` P1 B; `ex-l5-006.json` P1 A (`parallel_form_of: ex-l5-001`)
- **Severity:** S3 · **Category:** validity
- **Evidence:** ex-l5-001 key: "Check the task and focus; plan body jobs and evidence; sketch the introduction and conclusion…"; ex-l5-006 key: "Decode requirements, choose one focus, map introduction/body/conclusion, then audit"
- **Problem:** One form teaches body-first planning and the other introduction-first, so the retry form does not reinforce the same routine.
- **Proposed correction:** Bring ex-l5-006 into line: "Check the task, choose one focus, plan the body paragraphs, then the introduction and conclusion, then check."

### ex-l5-002 parts 4 and 6: the keyed audit sentence claims causation, and the model has an awkward clause
- **Location:** `backend_resources/english/v1/questions/ex-l5-002.json` (P4 B, P6 C)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** P4 B: "…revealing that oversized servings caused most avoidable waste." P6 C: "…but the bins revealed no reason for what was discarded."
- **Problem:** A three-day sort can show what was thrown away, not what caused it. That overclaim is at odds with the module's evidence-scope teaching (P6 C itself softens it to "produced many untouched portions"). "Revealed no reason for what was discarded" is unidiomatic.
- **Proposed correction:** P4 B: "…showing that most avoidable waste was untouched portions from oversized servings." P6 C: "…but the bins did not show why food was being thrown away."

### ex-l5-004 part 4: "checks synonyms" is ambiguous
- **Location:** `backend_resources/english/v1/questions/ex-l5-004.json` (P4 B)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** "The learner checks synonyms." (rationale: "That is external support.")
- **Problem:** Checking synonyms mentally is legitimate exam behaviour. The key is unaffected because B is not an interruption either way.
- **Proposed correction:** "The learner checks synonyms in an online thesaurus."

### ex-l5-004 / ex-l5-005 / ex-l5-009 / ex-l5-010 part 1: candidate-reported timing is sometimes written as an official rule
- **Location:** `ex-l5-004.json` P1 rationale D; `ex-l5-005.json` P1 rationale C; `ex-l5-009.json` P1 explanation, P3 rationale B; `ex-l5-010.json` P1 explanation
- **Severity:** S3 · **Category:** validity
- **Evidence:** "Section 1 is timed."; "Difficulty does not change rules."; "A valid rehearsal reproduces the separate 90-minute and 30-minute boundaries."; "within the fixed clock"; "Unused time remains inside its section rather than changing the next section's limit." The catalogue blueprint gives `reported_minutes` 90/30 with `evidence_status: candidate_reported` and says nothing about moving time between sections.
- **Problem:** The keys are defensible as rehearsal protocol, and most stems correctly say "reported". These rationales, however, present a candidate report as fixed rules. ex-l5-004 P1 rationale A ("Transfer is unconfirmed") shows the correct hedging.
- **Proposed correction:** "Candidates report a separately timed Section 1, so practise that way."; "Practise as if unused time cannot be moved, because we do not know that it can."; "A valid rehearsal reproduces the reported 90-minute and 30-minute boundaries."

### ex-l5-006 parts 3 and 5: advanced vocabulary
- **Location:** `backend_resources/english/v1/questions/ex-l5-006.json` (P3 rationale C; P5 D)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "This operationalises fair comparison."; "Return to how testing one change before scaling altered the writer's decisions"
- **Problem:** "Operationalises" and "scaling" are far above the 11–12 band.
- **Proposed correction:** "This shows a fair test in action."; "Return to how testing one sign before changing every bin changed the writer's decisions."

### ex-l4-005 / ex-l4-006: metadata type mismatch
- **Location:** `ex-l4-005.json`, `ex-l4-006.json` (`question_type: composition_planning`)
- **Severity:** S3 · **Category:** validity
- **Evidence:** Outcome EW8.4 "Edit by priority". The sibling items ex-l4-003 and ex-l4-004 have `question_type: editing`.
- **Problem:** The type is inconsistent with the sibling items. The forms' `task_part_distribution` also inherits "composition_planning".
- **Proposed correction:** Either set `editing` on these items or document why the checkpoint uses composition_planning.

---

## Slice summary

**Counts:** S1 = 4 · S2 = 13 · S3 = 16 (33 findings).

**Cross-cutting patterns**

1. **Test-wise length cue and key-position skew (affects every item; S2 as a pattern).** In 92 of 101 single-choice parts the key is the longest option, often 2–5× longer (e.g. ex-l3-004 P3 3.8×, ex-l4-003 P6 3.4×, ex-l4-004 P6 5.4×, ex-l5-006 P4 3.3×). The key is usually also the only hedged option ("bounded", "cautious", "without overclaiming"). Key positions are B 47, A 29, C 19, **D 6**. In 8 of 11 multiple-response parts the key is exactly A+B+C, with the distractors always in positions D and E (ex-l3-002, ex-l3-003, ex-l3-004, ex-l4-001, ex-l4-002, ex-l4-007, ex-l5-001, ex-l5-002). No option-shuffling code was found. A learner who always picks the longest option, or A–C for "THREE", scores near the ceiling. Fix by balancing option lengths, rotating keys and adding plausible near-miss distractors.
2. **Straw-man distractors.** Most parts have 2–3 distractors that are absurd or self-refuting ("Rain is a kind of weather", "Invent awards", "Ask an adult to draft…", "guarantees scholarship admission"). This matters most in the module checkpoints ex-l4-005, ex-l4-006, ex-l5-007, ex-l5-008, ex-l5-009 and ex-l5-010, which then cannot discriminate. Difficulty labels of 4–5 are not credible.
3. **Lesson worked examples reused as keys in exit tickets.** ex-l3-003 (e8-lesson-03), ex-l3-004 (e9-lesson-03), ex-l4-002 (e7-lesson-04), ex-l5-001 (e6-lesson-05), ex-l5-002 (e7-lesson-05). ex-l3-002 shows a minor overlap ("step-by-step method → one priority at a time"). ex-l3-001 and ex-l4-003 are clean.
4. **Checkpoint leakage by pre-diagnosis.** In ex-l4-005, ex-l4-006 and ex-l5-007 P2 the instructions or stem name the flaw. In ex-l5-008 one item gives away its partner's answer in the same form.
5. **Metalanguage and product jargon beyond the 11–12 band.** "Given-to-new", "reference chain", "synonym drift", "process compression", "fade support", "reverse outline", "abstracts the model", "contamination", "audit trail", "metadata", "strand", "matched form", "commit–flag–move", internal codes "E6.2/E6.4/E6.5", "link-back check" and "task contract". Affected items: ex-l3-001, ex-l3-002, ex-l3-003, ex-l3-004, ex-l4-001, ex-l4-007, ex-l5-002, ex-l5-004, ex-l5-005, ex-l5-006, ex-l5-009, ex-l5-010. Many of the EW9.5 parts test NextScholar's protocol vocabulary rather than test-taking judgement.
6. **Terse, boilerplate rationales in the retry/parallel forms** (ex-l4-004, ex-l5-004, ex-l5-005, ex-l5-006): two- to five-word rationales, and references to options by position.

**Model texts checked.** These are grammatical and accurate to their notes: ex-l3-002 P1 B, P4 B, P6 A; ex-l3-003 P1 A, P2 B, P3 C, P5 B, P6 B; ex-l4-001 P1 B, P3 A, P4 A; ex-l4-002 P1 C, P4 B, P6 B; ex-l4-003 P6 B; ex-l4-005 P4 A; ex-l4-006 P4 B; ex-l5-002's instructions model and P5 A; ex-l5-003 P4 B. Defective models: ex-l3-004 P3 C (overstates "prevents") and P5 C ("choices of time"), ex-l4-004 P6 C (unclear "Four were shorter"; leaves out the transfer), ex-l5-002 P4 B / P6 C (causal overclaim, awkward clause). The E8.x "corrected" forms are error-free: ex-l4-003 P5 C/D, ex-l4-004 P5 A, ex-l4-005 P5 D, ex-l4-006 P5 A.

**EW9.5 consistency with the catalogue.** Every item uses 90 + 30 minutes, two reading passages and ~300 words, which matches `exam_blueprint`. Item counts are consistently treated as unconfirmed. Only the rationale and explanation wording noted above presents the reported timing as fixed rules.

**Items with no key or ambiguity defects (problems limited to the cross-cutting patterns):** ex-l3-001 (apart from jargon), ex-l4-001, ex-l4-003, ex-l5-003 (the strongest item in the slice: clear evidence, sound multiple-response set and well-designed routines) and ex-l5-006. No wrong keys were found anywhere in the slice, and no multiple-response set had a clearly correct excluded option. The closest case is ex-l3-002 P2 C, where a keyed option does not fit the "reference chain" label.
