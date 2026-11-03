# Slice L — Lessons audit (41 authored lessons, E0.1–E9.5)

Scope: all 41 files in `backend_resources/english/v1/lessons/`, checked against
`docs/plan/LAYER_1_ENGLISH_CURRICULUM.md` §3–4, `catalogue.json` `exam_blueprint`, the exam profile
and every linked question file (plus related retry, reserve and checkpoint items where lesson text overlaps with them).

**Level-fit basis (audit basis):** the only exam profile
(`exam_profiles/asean-english-sec1-id-reported-v1.json`) is `entry_level: secondary_1_entry`, so the
intended learners are about 11–12 years old and learning English as a second language (final primary year). The level-fit
judgements below use that band, not the 13–16 band assumed at the start of the audit.

Finding headings use `<lesson stable_key> section <n>`.

---

## A. Leakage: lesson text that gives away linked practice items or exit tickets

### e1-lesson-01 section 3 — Worked example is a near-copy of guided item ev-l1-001
- **Location:** `backend_resources/english/v1/lessons/e1-lesson-01.json` (section 3, bullets 1–2) vs `questions/ev-l1-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “In ‘The slope was treacherous—dangerous and unstable after the rain,’ the dash introduces a direct definition. ‘Narrow’ may describe some difficult paths, but it is unsupported here. ‘Hazardous’ matches both dangerous and unstable.” Item ev-l1-001: “The mountain path was treacherous—so dangerous and unstable that…” options safe / **hazardous** / familiar / narrow.
- **Problem:** The item tests the same word with the same dash definition, and the lesson has already given its key (hazardous) and ruled out its main distractor (narrow). The first guided item therefore checks recall, not use of context.
- **Proposed correction:** Change the worked example to a different word and clue, e.g. “The bridge was precarious—balanced so badly that one strong wind could tip it.” (meaning *unsafe/likely to fall*; distractor *ancient*). Keep ev-l1-001 unseen.

### e1-lesson-02 section 2 — Sentence-frame model gives the answers to all five practice items
- **Location:** `lessons/e1-lesson-02.json` (section 2, bullet 1; section 3, bullet 1) vs `questions/ev-l2-001…005`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘the decision’, ‘her accuracy’ … ‘must verify’ … ‘the route is accessible’ … ‘explained clearly’”; section 3 repeats ev-l2-001 word for word: “‘After reviewing the trial, the committee reached a final ___’ … Decision fits that slot.”
- **Problem:** Each guided and independent item (decision, clearly, accessible, verify, accuracy) is shown in the model with its keyed form. Section 3 is the guided item itself, with all four options already eliminated.
- **Proposed correction:** Use family members that no item tests: ‘the *arrival*’, ‘must *compare*’, ‘seemed *reliable*’, ‘worked *carefully*’. Base the section 3 worked example on another family (e.g. *protect / protection / protective / protectively*).

### e1-lesson-04 sections 1, 2 and 5 — Model and prediction prompts give the keys to all five practice items
- **Location:** `lessons/e1-lesson-04.json` (section 1 bullet 1; section 2 bullets 2–3; section 5 bullet 1) vs `questions/ev-l4-001…005`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Compare ‘a narrow path’, ‘a thin sheet’ and ‘a cramped room’” (ev-l4-001: path, options narrow/thin/cramped); “Warm, hot and scorching” (ev-l4-002 options); “Assertive can praise clear confidence; aggressive suggests harmful force” (ev-l4-003 key and distractor); “write a short prediction such as ‘confident but respectful’, ‘small in seriousness’ or ‘brief without losing essential meaning’” (these are the hint predictions for ev-l4-003, -004 and -005, in the same order).
- **Problem:** Section 5 tells learners to predict before looking at the options, then gives them the predictions for exactly the three “unseen” independent items. Sections 1–2 already give the guided keys.
- **Proposed correction:** Use different near-synonym sets in sections 1–2 (e.g. *tidy / spotless / sterile*; *chilly / cold / freezing*; *confident / boastful*). In section 5, give generic prediction examples that no item uses (e.g. ‘slightly worried’, ‘happy to share’).

### e1-lesson-06 section 3 — Worked example duplicates the retry item ev-l5-002 part 2
- **Location:** `lessons/e1-lesson-06.json` (section 3) vs `questions/ev-l5-002.json` (retry_review, part 2)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “‘The plan was viable because the team had enough time and materials’ … viable must mean workable.” Retry: “The smaller design was viable because available time and materials were enough. What does viable mean?” Key: workable.
- **Problem:** A learner who fails the exit ticket gets a retry item that the lesson has already solved word for word, so the retry cannot show remediation.
- **Proposed correction:** Change the worked word (e.g. “The path was *impassable* because fallen trees blocked every route” → *impossible to travel along*). The phrase “must mean” also overstates certainty; change it to “probably means”.

### e2-lesson-01 sections 2–3 — Lesson models the exact repair keyed in exit ticket eg-l1-006
- **Location:** `lessons/e2-lesson-01.json` (section 2 bullet 4; section 3 bullets 1–2) vs `questions/eg-l1-006.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “The head subject controls the finite verb: ‘The row of plants needs shade.’” and “‘The rehearsal ended late, so everyone missed the final bus’ shows cause and result.” Exit ticket: “The row of young plants need shade in the afternoon, the gardening team moves a screen…”; key A: “The row of young plants **needs** shade in the afternoon, **so** the gardening team moves…”.
- **Problem:** The exit ticket is meant to be an unseen transfer item, but the lesson already gives its agreement fix almost word for word (“The row of plants needs shade”) plus the “comma + so for cause” pattern. Section 1 also nearly copies guided item eg-l1-001 option B (“The volunteers checked every name”).
- **Proposed correction:** Change the agreement model to a noun phrase that no item uses (e.g. “The box of pencils sits on the shelf.”). Keep the comma-splice model, but use a contrast relationship (“, but”) so the exit item still asks learners to choose the cause/result connector themselves.

### e2-lesson-02 section 3 — Worked analysis quotes two keyed exit-ticket answers word for word
- **Location:** `lessons/e2-lesson-02.json` (section 2 bullet 1; section 3 bullet 1) vs `questions/eg-l2-001.json` parts 1–4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “‘The collection of maps is locked’ agrees with collection … ‘When Sara returned the laptop, Mei noticed its cracked screen’ names both important referents.” Exit ticket P1 key B: “The collection of maps is locked.” P4 key B: “When Sara returned the laptop, Mei noticed its cracked screen.” Section 2 (“each … singular; distinct subjects joined by and are plural”) also gives the rules for P2 and P3.
- **Problem:** Two of the five exit-ticket keys appear verbatim in the lesson, and the rules for the other two are stated just before the ticket. The ticket only checks whether learners recognise sentences they have just read.
- **Proposed correction:** Change the worked examples (e.g. “The basket of mangoes is heavy”; “When Dewi gave the book to Lia, Lia noticed its torn cover”). Alternatively, rewrite eg-l2-001 parts 1 and 4 with new nouns and names.

### e3-lesson-01 section 3 — Story map and gap analysis solve the exit-ticket passage
- **Location:** `lessons/e3-lesson-01.json` (section 3, bullets 1–3; section 5) vs `questions/eb-l1-001.json` / `passages/english-passage-afternoon-broadcast.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Example map: setting—community radio station during a storm; characters—Maya, a presenter and an electrician; conflict—the microphones fail; resolution—the damaged plug is repaired; tone—anxiety changes to relief.” “For ‘the studio was unusually ___’ … favours a word describing an empty place.” “For ‘the programme would be ___ unless…’ … must describe a delayed event.”
- **Problem:** This is the exit-ticket story. The worked analysis points to gap 1 (*deserted*) and gap 4 (*postponed*). The “tone” line gives gaps 5 and 8 (*anxious*, *relieved*), and “repaired” gives gap 7. About five of the eight gaps are solved before the learner starts. Section 5 (“Fill the eight gaps from a twelve-word bank … four words will remain unused”) has no linked item, so the independent application is the exit ticket itself.
- **Proposed correction:** Write a separate model story (e.g. a school bus breakdown) for sections 3–4, and link a practice passage (a new guided item, or reuse the pattern of eb-l1-002) to section 5. Keep eb-l1-001 unseen until section 7.

### e4-lesson-01 section 3 — Worked examples give exit-ticket gaps 1, 3, 6 and 7 (and copy the retry)
- **Location:** `lessons/e4-lesson-01.json` (section 1 bullet 1; section 3 bullets 1–4; section 5) vs `questions/eo-l1-001.json` and `questions/eo-l1-002.json` (retry_review)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “In ‘Nobody knew who ___ packed it’ … needs the auxiliary ‘had’” (exit passage: “nobody knew who {{3}} packed it”); “In ‘the concert, ___ had taken place…’ … ‘Which’ fits” (exit: “a school concert, {{6}} had taken place”); “such as ‘until’ and ‘till’” (exit gap 7 key until/till); “She opened ___ envelope … selects ‘an’” (exit gap 1 an; retry eo-l1-002 gap 1: “supply the article before ‘envelope’”).
- **Problem:** Two of the worked sentences are copied from the exit passage. Together the examples give four of the eight keys. The retry item has the same key sequence (an, it, had, with, although, which, until, they) and the same “envelope” frame, so the retry route is compromised too. Section 5 names the exit passage (“The workshop box”) as the independent task.
- **Proposed correction:** Write new frames for every example (e.g. “She bought ___ umbrella”; “Nobody knew where the key ___ been hidden”; “the river, ___ flooded last year”). Change section 5 to a separate practice passage, and change eo-l1-002 so it is not a clone of the exit ticket's key sequence.

### e4-lesson-02 sections 1, 3, 4 and 7 — Lesson states the transformed answers for gaps 1, 2, 5 and 6
- **Location:** `lessons/e4-lesson-02.json` (section 1 bullet 1; section 3 bullets 1–4; section 4 bullet 1; section 7) vs `questions/eo-l2-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Section 1: “Say each family aloud: ‘meet, met’; ‘planter, planters’; ‘bright, brighter’; and ‘grow, growth’.” Section 3: “‘The club meets weekly. Last term, it ___ monthly’ … ‘met’”; “‘one planter … four more ___’ … ‘planters’”; “‘became even ___ than before’ … ‘brighter’”; “‘their unexpected ___’ … ‘growth’”. Section 4 lists labels in the passage's gap order: “past, plural, third-person singular, past participle, comparative, noun or reflexive pronoun”.
- **Problem:** The warm-up and the worked analysis each give the same four exit-ticket keys, and sections 4 and 7 tell learners the form type of every remaining gap in order.
- **Proposed correction:** Base sections 1 and 3 on anchors that the passage does not use (e.g. *swim/swam*, *bench/benches*, *cold/colder*, *decide/decision*). Remove the ordered label list from sections 4 and 7.

### e4-lesson-03 sections 1 and 3 — Lesson completes exit-ticket gaps 1, 2, 4 and 7 and reveals the accepted alternatives
- **Location:** `lessons/e4-lesson-03.json` (section 1 bullet 1; section 3 bullets 1–4) vs `questions/eo-l3-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “at short ___ … retrieve notice”; “Mei agreed to take ___ of the schedule … charge”; “the rehearsal came to a ___ … halt; stop is also natural and must be explicitly approved”; “the group played a crucial ___ … role; part is an approved equivalent”. Section 1 also lists “take charge … play a role”.
- **Problem:** The four worked frames come from the exit passage (“at short {{1}}”, “take {{2}} of the new schedule”, “came to a {{4}}”, “played a crucial {{7}}”), and the lesson even tells learners which alternatives are accepted.
- **Proposed correction:** Teach collocations that the passage does not use (e.g. *at first sight*, *take care of*, *come to an end*, *play a part in* only if gap 7 is changed). Do not mention accepted-answer sets in learner text.

### e4-lesson-04 sections 1 and 3 — Lesson resolves five of the eight exit-ticket gaps
- **Location:** `lessons/e4-lesson-04.json` (section 1 bullet 1; section 3 bullets 1–4) vs `questions/eo-l4-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Rina registers visitors and Farid examines devices … identify Farid” (gap 1 Farid); “After a repaired lamp lights, ‘This encouraged the waiting visitors’” (gap 2 This); “a difficult radio creates contrast, so however or yet” (gap 3 However/Yet); “‘Only then did he notice the loose wire’” (gap 4 then); “‘switched it on again’” (gap 6 again).
- **Problem:** The worked analysis is a commentary on the exit passage and gives five of its eight answers.
- **Proposed correction:** Use a different scenario with different characters (e.g. a library book-sorting day) to model the reference, demonstrative, contrast, inversion and repetition links.

### e4-lesson-05 section 3 — Worked analysis gives exit-ticket gaps 1, 2, 6 and 7
- **Location:** `lessons/e4-lesson-05.json` (section 3 bullets 1–4) vs `questions/eo-l5-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘divide the route ___ three sections’ … divide into”; “The water looked clear … but or yet fits”; “again … becomes secure only when an earlier sentence records the first count”; “‘the data would be useless ___ every group used the same method’ … Unless”.
- **Problem:** The four timed-practice examples are lifted from the hillside-water exit passage and come with their keys, so half the timed checkpoint is answered in advance.
- **Proposed correction:** Write the examples from another scenario (e.g. “split the class ___ four teams”; “The sky looked dark, ___ we still went outside”).

### e5-lesson-01 section 3 — Worked map is the exit passage's map and answer
- **Location:** `lessons/e5-lesson-01.json` (section 3 bullets 1–3) vs `questions/er-l1-001.json` parts 2 and 4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Suppose paragraph 1 describes a flooded courtyard, paragraph 2 explains a student investigation, paragraph 3 reports the first test and paragraph 4 lists later benefits. The map is problem → investigation and proposal → evidence → wider impact.” Exit P2 key: “A problem is introduced, a response is planned, evidence is observed, and wider effects are reported.” The lesson also says “‘this result’ must point to an earlier event” (exit P4 asks what “This result” refers to).
- **Problem:** The worked example summarises the exit passage (courtyard rain garden) and gives the P2 answer. It also signals the P4 target.
- **Proposed correction:** Model the map on a different text type and structure (e.g. a comparison of two school canteens: two options → criteria → comparison → recommendation), and use a different reference phrase.

### e5-lesson-03 section 3 — Worked word “tentative → provisional” is reused by the exit ticket and the protected reserve
- **Location:** `lessons/e5-lesson-03.json` (section 1 bullet 1; section 3 bullets 1–2) vs `questions/er-l3-001.json` parts 3–4 and `questions/ev-l5-005.json` (protected_reserve, part 1)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** Lesson: “‘The committee made a tentative decision and promised to review it after the trial.’ … tentative means provisional or not yet final.” Exit P4: “tentative rather than final” → key “provisional and open to correction”. Protected reserve ev-l5-005 P1: “The team made a tentative booking because the competition date had not yet been confirmed” → key “provisional and not final”. Section 1's “careful” vs “cautiously” contrast also predicts exit P3 (meticulous → careful vs carefully).
- **Problem:** The lesson teaches the exact word-and-meaning pair that the exit ticket tests and that the protected reserve form also tests. The word appears again in the E1.6 exit (ev-l5-001 P1) and the retry er-l5-004, so the reserve item no longer measures unaided inference. That compromises the protected pool.
- **Proposed correction:** Change the worked word in section 3 (e.g. *interim*, or a non-tested word such as *makeshift*). Also tell the item-bank owner to replace “tentative” in ev-l5-005 with a word that has not been exposed. Change the section 1 pair to a word family that no item uses.

### e5-lesson-04 section 3 — Worked paraphrase uses the exit passage's sentence and P3 answer
- **Location:** `lessons/e5-lesson-04.json` (section 3 bullets 1–2) vs `questions/er-l4-001.json` part 3
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “Example statement: ‘Rain days were excluded because wet surfaces become temporarily cooler.’ … Accurate answer: Wet surfaces would temporarily lower the readings and distort the comparison. … It does not invent a broken sensor…” Passage: “Rain days were excluded because wet surfaces become temporarily cooler and would distort the comparison.” Exit P3 key C: “Wet surfaces would be temporarily cooler and distort the comparison”; distractor A: “permanently inaccurate” sensor.
- **Problem:** The lesson quotes the passage sentence, gives the keyed paraphrase and rules out the main distractor.
- **Proposed correction:** Use a sentence that is not in the passage (e.g. “Readings taken after 4 p.m. were omitted because shadows from the hall covered two of the points.”).

### e5-lesson-05 sections 3 and 5 — Worked inference gives exit-ticket parts 1, 2 and 4
- **Location:** `lessons/e5-lesson-05.json` (section 3 bullets 1–2; section 5 bullet 2) vs `questions/er-l5-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “a return station was moved nearer the bus exit, picture signs were added, and the container-return rate then rose. Supported inference: the combined changes likely made returns easier.” (P1 key B: “…likely made returns easier, but their separate effects are unknown”). “it cannot show which change produced the result” (P2 key C). “Evidence from six stalls over four Fridays does not automatically describe every stall … or the whole market” (P4 key D).
- **Problem:** Three of the six exit-ticket answers are stated in the lesson, including the passage's own details (six stalls, four Fridays, bus exit, picture signs).
- **Proposed correction:** Model the inference on a different trial (e.g. a class that changed the seating plan and the lesson start time together). In section 5, use a different population/time example (e.g. “two classes over three weeks”).

### e5-lesson-06 sections 1, 2, 3 and 4 — Lesson names the exit topic and gives its purpose and tone answers
- **Location:** `lessons/e5-lesson-06.json` (section 1 bullet 2; section 2 bullet 1; section 3 bullet 2; section 4 bullet 1) vs `questions/er-l5-002.json` parts 2–3
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “A topic such as a library quiet hour…”; “A report may explain a promising experiment, evaluate its limits and maintain a cautiously positive tone”; “its larger purpose may be to evaluate an initiative rather than merely announce it”; “Words such as encouraging, may, however and worth refining can combine to create a cautiously positive tone.” Passage: “Those figures are encouraging … a small service worth refining”. P2 key: “To evaluate an early library trial…”; P3 key: “Cautiously positive and measured”.
- **Problem:** The lesson quotes the exit passage's signal words (“encouraging”, “worth refining”) and states the keyed tone and purpose.
- **Proposed correction:** Use a different topic and different tone signals in the lesson (e.g. a mildly critical review of a sports day with “disappointing”, “although”, “could improve”).

### e5-lesson-02 sections 4–5 — Lesson previews exit-ticket reference expressions (minor)
- **Location:** `lessons/e5-lesson-02.json` (section 4 bullet 1; section 5 bullet 1) vs `questions/er-l2-001.json` parts 3 and 6
- **Severity:** S3 · **Category:** leakage
- **Evidence:** “For a phrase such as this change or that finding…”; “A later phrase may depend on an earlier label such as the first group”. The exit passage uses “This change”, “That finding” and “The first group”.
- **Problem:** These are generic examples, but all three are the expressions tested in the exit passage. This is a light cue only; the Maya/Idris worked example itself is clean.
- **Proposed correction:** Use “this decision”, “that result” and “the second team” as the examples.

### e6-lesson-01 sections 3 and 5 — Exit ticket analyses the same prompt the lesson fully decoded
- **Location:** `lessons/e6-lesson-01.json` (section 3 bullets 1–2; section 5 bullet 1; section 7) vs `questions/ex-l1-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Section 3 quotes the full “ASEAN Youth Learning Blog” prompt and gives “Topic: one school-learned skill or idea. Command: explain its use … Audience: secondary-school readers of a youth blog. Scope: one skill or idea, one different area of life, and at least one specific example.” Section 5's contract: “‘I will explain to secondary-school readers how one school-learned skill applies in another area of life, using one specific actual or realistic example.’” Exit P1–P6 use the same prompt; the P6 key is that sentence with only “or idea” added. Section 7 says: “Analyse the original practice prompt in six steps.”
- **Problem:** Every exit-ticket answer appears in the lesson, so the “unseen transfer item” required by curriculum §3 is a recall check.
- **Proposed correction:** Give the exit ticket a fresh prompt (e.g. the newsletter/group-habit prompt pattern used in checkpoint ex-l1-010, written new), or decode a different prompt in the lesson.

### e6-lesson-02 sections 2–4 and 6 — Charity-sale I-S-A-R and honesty frame reappear as exit keys
- **Location:** `lessons/e6-lesson-02.json` (section 2 bullet 1; section 3 bullet 2; section 4 bullet 2; section 6 bullet 2) vs `questions/ex-l2-001.json` parts 2, 3 and 5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Observation is something you have noticed another person or group doing” (P2 key “Observation of another person”); “Idea—breaking a task into parts. Situation—planning a charity sale. Action—divide the work into publicity, supplies, prices and staffing” (P3 keys); “‘I could use this when…’” (P5 key “I could use the checklist method when…”).
- **Problem:** The exit ticket asks learners to pick the lesson's own worked frame.
- **Proposed correction:** Give the exit ticket a different worked idea (e.g. using a science-lab safety checklist to plan a family trip).

### e6-lesson-03 sections 3–5 — Exit keys repeat the lesson's two candidates, combination example and order
- **Location:** `lessons/e6-lesson-03.json` (section 3 bullet 1; section 4 bullet 1; section 5 bullet 1) vs `questions/ex-l3-001.json` parts 1–4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Candidate one … divide publicity, supplies, prices and staffing, then give each part a deadline. Candidate two … when rain forced the stalls indoors: identify urgent parts, reassign people”; “‘I listed the sale tasks’ and ‘I separated the sale into four areas’ are one planning point”; “the reader needs the learned method before the initial plan, the initial plan before the unexpected rain”. Exit P1 keys = the same two candidates; P2 = the combination example; P3–P4 = the same order.
- **Problem:** Four of the six decisions were made in the lesson.
- **Proposed correction:** Build the exit ticket around a new example, or demonstrate selection in the lesson with a different scenario.

### e6-lesson-04 sections 1–3 — Exit key for the controlling focus is the lesson sentence almost word for word
- **Location:** `lessons/e6-lesson-04.json` (section 1 bullet 2; section 2 bullet 1; section 3 bullets 1–2; section 5 bullet 1) vs `questions/ex-l4-001.json` parts 1–4 and 6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “this method is useful beyond mathematics because it turns a complicated event into manageable decisions and helps the writer adapt when plans change.” Exit P1 key: “Breaking a large task into smaller parts is useful beyond mathematics because it makes a complicated event manageable and helps me adapt when plans change.” Section 2's three focus features match the P2 keys, and the section 3 paragraph jobs and section 5 thread words match P3, P4 and P6.
- **Problem:** The exit ticket asks learners to recognise the lesson's model statement.
- **Proposed correction:** Use a fresh plan in the exit ticket (another school skill and life setting).

### e6-lesson-05 sections 2–4 — Five-minute routine and body notes are the exit keys
- **Location:** `lessons/e6-lesson-05.json` (section 2 bullet 1; section 3 bullets 1–2; section 4 bullet 1) vs `questions/ex-l5-001.json` parts 1–4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Minute-by-minute routine (section 2) = P1 key; “Body 1 job … divide publicity, supplies, prices and staffing; assign deadlines … Link-back: separate tasks turned confusion into manageable action” = P3 key; “rain forces the stalls indoors; rank urgent moving and safety tasks; reassign helpers” = P4 key; introduction note “maths problem-solving method -> charity sale -> manageable decisions and adaptation” = P2 keys.
- **Problem:** Same pattern: the exit ticket restates the lesson's worked plan.
- **Proposed correction:** Give the exit ticket a new prompt and new notes, as in checkpoint ex-l5-007 (role assignment at a clean-up).

### e7-lesson-01 sections 1, 3, 4 and 6 — Paragraph promises, sentences and reverse outline are exit keys
- **Location:** `lessons/e7-lesson-01.json` (section 1 bullet 2; section 3 bullets 1–2; section 4 bullet 2; section 6 bullet 1) vs `questions/ex-l1-002.json` parts 1, 2, 4, 5 and 6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “body paragraph one promises to show how dividing the event into tasks created a manageable initial plan” (P1 key); evidence “separated publicity, supplies, prices and staffing, assigned a deadline … no one had confirmed the drinks order” (P2 keys); “A long history of the school hall would interrupt” (P5 key); “‘Create the initial task plan’ and ‘Adapt the method after rain’” (P6 key).
- **Problem:** Five of the six decisions repeat the lesson's worked material.
- **Proposed correction:** Write the exit ticket on a new scenario.

### e7-lesson-02 sections 1, 3, 4 and 5 — Development examples are the exit keys
- **Location:** `lessons/e7-lesson-02.json` (section 1 bullet 2; section 3 bullet 2; section 4 bullet 1; section 5 bullet 1) vs `questions/ex-l2-002.json` parts 1, 3 and 4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Compare ‘The plan helped us’ with ‘Assigning a deadline to publicity, supplies, prices and staffing exposed the unconfirmed drinks order before the sale.’” (P1 key: “Assigning deadlines to … exposed the unconfirmed drinks order while there was still time to act.”); “‘This mattered because the unfinished order became visible while there was still time to act’” (P3 key); “water nearing an extension lead justifies treating electrical safety as urgent” (P4 key).
- **Problem:** The exit ticket's “which revision develops ‘The plan helped us’” uses the lesson's own before/after pair.
- **Proposed correction:** Use a new assertion and notes in the exit ticket.

### e7-lesson-03 sections 2–5 — Reference chain, thread words and transition are exit keys word for word
- **Location:** `lessons/e7-lesson-03.json` (section 2 bullet 1; section 3 bullet 1; section 4 bullet 2; section 5 bullet 2) vs `questions/ex-l3-002.json` parts 2–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘water approached the extension lead. The approaching water created a safety risk. That risk changed the order of the move.’” (P2 keys: “the approaching water”, “that safety risk”…); “‘step-by-step method’, ‘one priority at a time’ and ‘clear next action’” (P5 key: “step-by-step method → one priority at a time → clear next action”); the drinks-order sentence in section 2 is the P3 stem.
- **Problem:** The lesson already demonstrates four of the six decisions.
- **Proposed correction:** Write the exit ticket on a new paragraph topic.

### e7-lesson-04 sections 2 and 4 — Model introduction and ending are the keyed answers, word for word
- **Location:** `lessons/e7-lesson-04.json` (section 2 bullet 1; section 4 bullets 1–2) vs `questions/ex-l4-002.json` parts 1 and 4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson model: “‘School projects taught me that a large problem becomes manageable when it is divided into clear next actions. I later relied on that method while organising a charity sale, especially when sudden rain forced our team to change plans.’” This is identical to the P1 key. Lesson ending: “‘The sale showed me that planning is not the same as predicting every problem. Its real value is giving people a clear next action when circumstances change.’” This is identical to the P4 key. The lesson's mechanical-ending example is also a P4 distractor pattern.
- **Problem:** This is the most direct leakage in the slice: the learner only has to recognise two paragraphs they have just read.
- **Proposed correction:** Write a new response context for the exit ticket. As a minimum, rewrite the P1 and P4 keys so they share no sentences with the lesson.

### e7-lesson-05 sections 2, 4 and 5 — Reverse outline and food-waste transfer are exit keys
- **Location:** `lessons/e7-lesson-05.json` (section 2 bullet 2; section 4 bullets 1–2; section 5 bullet 1) vs `questions/ex-l5-002.json` parts 1, 3, 4 and 6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “initial approach → concrete problem and consequence → targeted response → observable result → wider significance” (P1 key differs only in “specific weakness”); “For a food-waste paragraph, the initial weakness might be an undifferentiated bin … a short sorting audit followed by smaller serving options” (P4 and P6 keys: three-day sorting audit, smaller first serving).
- **Problem:** The exit ticket uses the same model paragraph, and the transfer topic and evidence were also prepared in the lesson.
- **Proposed correction:** Keep the model paragraph in the lesson, but give the exit ticket a new transfer topic (e.g. organising a class library). Alternatively, analyse a different model in the lesson.

### e8-lesson-01 sections 2–6 — Every revision tested in the exit ticket is modelled with the exit's own wording
- **Location:** `lessons/e8-lesson-01.json` (section 2 bullet 1; section 3 bullet 1; section 4 bullet 1; section 5 bullet 1; section 6 bullet 1) vs `questions/ex-l1-003.json` parts 1–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘Did a new shelf arrangement’ becomes ‘introduced labelled return trays’; ‘got advice’ becomes ‘collected pupil feedback’; ‘a bad system’ becomes ‘returns remained unsorted until the next session’”; “‘Returned books were sorted into labelled trays. Most returns were reshelved that day.’”; “‘Everyone always found every book immediately’ overstates…”. The exit draft contains exactly “did a new shelf arrangement”, “got advice from pupils”, “bad system” and “everyone always found every book immediately”.
- **Problem:** The lesson edits the exit ticket's draft paragraph for the learner.
- **Proposed correction:** Write the exit draft on a different project (e.g. a lost-property box) with different vague phrases.

### e8-lesson-02 sections 2–5 — Combined sentences and the agreement/reference repair are exit keys
- **Location:** `lessons/e8-lesson-02.json` (section 2 bullet 1; section 3 bullet 1; section 4 bullet 1; section 5 bullets 1–2) vs `questions/ex-l2-003.json` parts 2–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘Because the front room faced a bus stop, traffic obscured parts of two recordings.’” (P2 key, identical); “‘Because traffic had obscured two recordings, the club moved the next session.’” (P3 key); “‘The club moved to the back room, where each interviewer tested a microphone.’” (P5 key, identical); “‘Each of the interviewers was asked’ … ‘this improved them’ … ‘After the move and sound checks, the later recordings were clearer.’” (P4 key).
- **Problem:** Four of the six decisions are solved in the lesson.
- **Proposed correction:** Write a different set of notes for the exit ticket.

### e8-lesson-03 sections 2–5 — Cause, concession, qualifier and sequence models are exit keys
- **Location:** `lessons/e8-lesson-03.json` (section 2 bullet 1; section 3 bullet 1; section 4 bullet 1; section 5 bullet 2) vs `questions/ex-l3-003.json` parts 1, 3, 4 and 5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘Because queues were longest during the first ten minutes of lunch, the school opened a temporary second refill point.’” (P1 key); “‘Although most respondents found refilling easier, the survey did not measure long-term habits.’” (P3 key); “‘at the original station’, ‘among the 48 surveyed users’, ‘during the one-week trial’” (P4 keys); “‘The fall occurred during the week in which the second point operated, which is consistent with reduced congestion, although the short trial cannot establish a long-term effect.’” (P5 key, near-identical).
- **Problem:** The exit ticket repeats the lesson.
- **Proposed correction:** Give the exit ticket a new pilot study (e.g. a library late-opening trial).

### e8-lesson-04 sections 3–5 — Lesson predicts the exit's deletion, order and convention answers
- **Location:** `lessons/e8-lesson-04.json` (section 3 bullet 2; section 4 bullet 2; section 5 bullet 2) vs `questions/ex-l4-003.json` parts 3–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “a clear route is often problem, relevant school learning, application, observed result and reflection” (P3 key: “Home problem → relevant school method → controlled home comparison → bounded result → reflection”); “A vivid description of classroom wall colours … transferring fair-testing skills to a home problem” (P4 key: classroom walls sentence); “Correcting ‘seedling were’ to ‘seedlings were’” (P5 key, identical).
- **Problem:** The lesson's examples come from the exit draft.
- **Proposed correction:** Use different illustrative errors and irrelevant details in the lesson.

### e8-lesson-05 sections 2 and 4 — Pattern labels and checks are exit keys word for word
- **Location:** `lessons/e8-lesson-05.json` (section 2 bullets 1–2; section 4 bullet 2) vs `questions/ex-l5-003.json` parts 1–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘I join two independent clauses with only a comma.’” (P2 key, identical); “‘The trial was short, it produced useful observations’” (entry 1 of the log, identical); “I use absolute words such as every, always or proves” (P3); the section 4 comma-splice and overclaim checks (P4–P5 keys).
- **Problem:** Five of the six decisions repeat the lesson.
- **Proposed correction:** Change the patterns in the exit log (e.g. article omission and tense drift), or change the lesson's examples.

### e9-lesson-01 sections 2–5 — Focus, hinge, transfer and limitation are exit keys
- **Location:** `lessons/e9-lesson-01.json` (section 2 bullet 2; section 3 bullets 1–2; section 4 bullet 1; section 5 bullets 1–2) vs `questions/ex-l1-004.json` parts 1–5
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘Learning to compare evidence before changing our science experiment taught me to test assumptions; the same habit can make my planning for community projects more reliable.’” (P1 key); basil seedlings and watering, plus “test one collection point, record when and what people donate” (= Lina's notes; P4 key); “urgent choices may not permit a long trial, but the writer can still check the available evidence and remain ready to revise” (P5 key).
- **Problem:** The exit ticket uses the lesson's own scenario and model sentences.
- **Proposed correction:** Give the exit ticket a new experience and transfer (e.g. a debate rehearsal applied to a family decision).

### e9-lesson-02 sections 2–6 — Exhibition story plan is the exit ticket's planning record
- **Location:** `lessons/e9-lesson-02.json` (section 2 bullet 2; section 3 bullet 2; section 5 bullet 1; section 6 bullet 1) vs `questions/ex-l2-013.json` parts 2, 5 and 6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Empty display boards inside the library may seem unimportant at first” (P2 key); “The narrator remembers the empty library boards, proposes selecting the three panels needed … assigns separate teams to move, relabel and guide visitors” (P5 key); “The doors open six minutes late … one warped corner … protecting a plan's purpose may require changing its shape” (P6 key: “…preserving a plan's purpose could mean changing its shape”).
- **Problem:** The lesson plans the exit ticket's story.
- **Proposed correction:** Write a new disruption scenario for the exit ticket (e.g. a power cut at a class concert).

### e9-lesson-03 sections 2–6 — Position, reason chain, objection and concession are exit keys
- **Location:** `lessons/e9-lesson-03.json` (section 2 bullet 1; section 3 bullet 1; section 4 bullet 1; section 5 bullet 1; section 6 bullet 1) vs `questions/ex-l3-004.json` parts 1 and 3–6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “‘Schools should expect one service contribution each term, provided students can choose from accessible roles and use a genuine hardship alternative’” (P1 key); the reading-support coordinator chain (P3 key); “Students with long journeys, caregiving duties or limited transport…” (P4 key); “‘A fixed weekend project could exclude students with travel or family responsibilities; therefore, a fair requirement would need supervised on-campus roles…’” (P5 key); the five-job route (P6).
- **Problem:** All of the lesson's worked content is reused as the keyed answers.
- **Proposed correction:** Use a fresh policy question in the exit ticket (e.g. “Should schools ban phones at lunch?”).

### e9-lesson-04 sections 3–6 — Fictional pacing record and decisions are solved in the lesson
- **Location:** `lessons/e9-lesson-04.json` (section 3 bullet 2; section 4 bullet 1; section 5 bullet 1; section 6 bullet 2) vs `questions/ex-l4-007.json` parts 3–6
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “the 35-minute record is complete with four minutes of checking but has an overlong opening and a thin second reason. The next action … cap the opening, preserve the compact route and practise developing the second reason” (P3 key); the section 4 valid-run conditions (P4); the section 5 recovery order (P5); “If the 30-minute response is incomplete or depends on help, return to the 35-minute stage” (P6).
- **Problem:** The exit record (Nara) is the lesson's hypothetical, and its key decisions are stated in the lesson.
- **Proposed correction:** Give the exit record a different bottleneck (e.g. planning overflow) so learners have to apply the routine.

---

## B. Correctness of stated rules and terminology

### e8-lesson-02 section 3 — Non-defining relative clause described as “identifying detail”
- **Location:** `lessons/e8-lesson-02.json` (section 3, bullet 1)
- **Severity:** S2 · **Category:** correctness
- **Evidence:** “Use a relative clause for attached identifying detail: ‘The club moved to the back room, where each interviewer tested a microphone.’”
- **Problem:** “Identifying” is the standard name for defining relative clauses, which take no comma. The example is a non-identifying (non-defining) clause after a comma that adds extra information. This contradicts E4.1 section 3, which correctly calls the comma clause non-defining.
- **Proposed correction:** “Use a relative clause to add extra detail about a noun: ‘The club moved to the back room, where each interviewer tested a microphone.’ The comma shows the detail is extra, not needed to identify the room.”

### e2-lesson-02 section 2 — Over-general rule: “Of-phrases do not normally control the verb”
- **Location:** `lessons/e2-lesson-02.json` (section 2, bullet 1)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** “Of-phrases do not normally control the verb; each and everyone are singular; distinct subjects joined by and are plural.”
- **Problem:** The rule fails with quantity words, where the of-noun decides agreement (“Most of the maps **are** locked”, “A lot of water **was** lost”, “Half of the students **were** absent”). Young learners will apply the rule too widely.
- **Proposed correction:** “After a noun such as *collection*, *row* or *box*, the of-phrase does not control the verb (‘The box of pens **is**…’). After quantity words such as *most of*, *half of*, *a lot of*, look at the noun after *of* (‘Most of the pens **are**…’).”

### e1-lesson-04 section 1 — “thin” does not mean limited space
- **Location:** `lessons/e1-lesson-04.json` (section 1, bullet 1)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** “Compare ‘a narrow path’, ‘a thin sheet’ and ‘a cramped room’. All three suggest limited space…”
- **Problem:** *Thin* describes small thickness, not limited space, so the core-meaning contrast is inaccurate as stated.
- **Proposed correction:** “All three describe something small in one way: *narrow* = small in width, *thin* = small in thickness, *cramped* = too little room for people or things.” (This also needs a new example set; see leakage finding A.)

### e1-lesson-01 section 2 — Cause/result clue defined inaccurately; purpose clue missing
- **Location:** `lessons/e1-lesson-01.json` (section 2, bullet 4)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** “A cause or result shows what the word makes happen.”
- **Problem:** A cause clue explains *why* the situation happened, and a result clue shows *what followed*. Neither is “what the word makes happen”. Practice item ev-l1-004 is titled “Purpose clue”, but purpose is not among the five taught clues.
- **Proposed correction:** “A cause or result clue tells you why something happened or what happened next (‘because…’, ‘so…’). A purpose clue tells you what someone wanted to achieve (‘to…’, ‘so that…’).”

### e5-lesson-05 section 3 — Temporal sequence equated with association
- **Location:** `lessons/e5-lesson-05.json` (section 3, bullet 3)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** “A result that follows a change is associated with it. Causation needs stronger evidence…”
- **Problem:** Coming after a change does not establish association either. E8.3 section 5 correctly calls this “sequence”. The two lessons use inconsistent concepts.
- **Proposed correction:** “A result that comes after a change may be linked to it, but coming after something does not prove it was caused by it.”

### e8-lesson-03 section 3 — “Correct” concession model is logically weak
- **Location:** `lessons/e8-lesson-03.json` (section 3, bullet 2)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “Write either ‘Although most respondents approved, the trial was short’ or ‘Most respondents approved, but the trial was short.’”
- **Problem:** The grammar is correct, but approval and a short trial are not in tension, so the model presents a strained concession as good writing in a lesson about matching connectors to real relationships.
- **Proposed correction:** “Although most respondents approved, the trial was too short to show whether the change would last.”

### e4-lesson-02 section 1 — Inflections called “families”; “anchor” means different things in E4.2 and E4.4
- **Location:** `lessons/e4-lesson-02.json` (section 1, bullet 1; section 2, bullet 1) and `lessons/e4-lesson-04.json` (section 2, bullet 2)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** E4.2: “Say each family aloud: ‘meet, met’; ‘planter, planters’…”; “Find the anchor: look for the same word, or a clearly related member of its word family”. E4.4: “Locate the anchor: the person, object, action or idea that the missing word must connect to.”
- **Problem:** *met*, *planters* and *brighter* are inflections of one word, not a “word family” in the E1.2 sense. In addition, “anchor” means a related word form in E4.2 but a referent in E4.4, a few lessons apart.
- **Proposed correction:** In E4.2 say “Say each pair aloud … the word changes its form”. In E4.4 rename the term “link word” or “what it points back to”.

---

## C. Grammar and editorial issues in learner-visible text

### e5-lesson-03 section 1 — Ungrammatical example sentence not marked as wrong
- **Location:** `lessons/e5-lesson-03.json` (section 1, bullet 1)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “Compare: ‘The notes were careful’ and ‘The notes were cautiously.’”
- **Problem:** The incorrect sentence appears like a model with no ✗ or asterisk. Young readers may copy it.
- **Proposed correction:** “Compare: ✓ ‘The notes were careful.’ ✗ ‘The notes were cautiously.’”

### e6-lesson-01 section 2 — US spelling “judgment”
- **Location:** `lessons/e6-lesson-01.json` (section 2, bullet 2)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “…a realistic future use or a personal judgment.”
- **Problem:** The house style is British, and E1.4 and E9.3 use “judgement”.
- **Proposed correction:** “judgement”.

### e7-lesson-02 section 4 — Unpunctuated title “Explain the so what”
- **Location:** `lessons/e7-lesson-02.json` (section 4 title)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “Explain the so what”
- **Problem:** The colloquial nominalisation without quotation marks reads as an error and is opaque to 11–12-year-old learners of English.
- **Proposed correction:** “Explain why the detail matters”.

### e4-lesson-01 section 3 (also e4-lesson-03 section 3, e4-lesson-04 section 4) — Author/reviewer instructions shown to learners
- **Location:** `lessons/e4-lesson-01.json` (section 3, bullet 4); `lessons/e4-lesson-03.json` (section 3, bullets 3–4); `lessons/e4-lesson-04.json` (section 4, bullet 2)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** “the reviewed answer set must name both before learners are scored”; “stop is also natural and must be explicitly approved if accepted”; “keep both for review rather than inventing a rule that the passage does not support”.
- **Problem:** This is content-authoring guidance, not learner instruction. Learners cannot “approve” answers or keep candidates “for review”.
- **Proposed correction:** Remove these lines or rewrite them for learners: “Sometimes two words both fit (for example *until* and *till*). Check that your word fits both the grammar and the meaning.”

---

## D. Level fit (11–12-year-old ESL band per audit basis)

### e6-lesson-01 … e9-lesson-04 (all sections) — Lesson prose far above the target reading level
- **Location:** `lessons/e6-lesson-0[1-5].json`, `e7-lesson-0[1-5].json`, `e8-lesson-0[1-5].json`, `e9-lesson-0[1-4].json`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Estimated Flesch–Kincaid grade 10.4–12.8 for E6.3–E9.4, with 15–19 words per sentence (E8.2 18.9; E9.3 12.8 grade). Typical sentences: “This advances my focus because reprioritising the separate tasks shows how the same method supports calm adaptation when the original plan changes” (E6.4 section 4); “Use a concession-response chain: acknowledge the valid concern, explain its effect on the proposal, then show what position remains defensible” (E9.3 section 5); “Structural mismatch forces a problem–response sequence onto material that does not contain a meaningful change” (E7.5 section 6); “Classify the main loss as planning overflow, drafting stall, incomplete development, missing ending, checking loss or contaminated conditions” (E9.4 section 6).
- **Problem:** Final-primary ESL learners (about grade 6, reading in their second language) cannot process abstract nominal style and metalanguage at this density (controlling focus, given-to-new, structural abstraction, conceptual closure, qualification, concession, straw-man, false balance, bottleneck). The strategy is buried under its own terminology.
- **Proposed correction:** Rewrite to about grade 5–6: at most 12–14 words per sentence, one new term per section with a plain gloss (“controlling focus = your main message”), and short worked examples instead of abstract descriptions. Cut E7–E9 bullets by about 40%.

### e2-lesson-01 sections 1–2 and e2-lesson-02 sections 1–2 — Core grammar terms used without definition
- **Location:** `lessons/e2-lesson-01.json` (section 1 bullet 2; section 2 bullets 1 and 4; section 6); `lessons/e2-lesson-02.json` (sections 1–2)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** “Underline the subject once and the finite verb twice”; “The head subject controls the finite verb”; “identify the head subject rather than the closest noun. Circle every pronoun and its intended antecedent.”
- **Problem:** *Finite verb*, *head subject* and *antecedent* are never defined, yet the routine depends on them. Curriculum E2 says to “Teach grammar as meaning and sentence control rather than terminology memorisation.”
- **Proposed correction:** Gloss each term on first use: “finite verb = the verb that shows time and changes with the subject (*is/are*, *was/were*, *walks/walk*)”; “head subject = the main noun the sentence is about, not the nouns inside ‘of…’ phrases”; “antecedent = the noun a pronoun points back to”.

### e0-lesson-01, e0-lesson-02, e9-lesson-05 — Product and assessment jargon in learner instructions
- **Location:** `lessons/e0-lesson-01.json` (section 4 bullet 2; section 6); `lessons/e0-lesson-02.json` (sections 4, 5 and 6); `lessons/e9-lesson-05.json` (section 5)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** “Write configurable instead of inventing unsupported counts.”; “Classify mistakes as paper format, instruction control, timing control or evidence boundary”; “Separate valid and contaminated attempts”; “over-interpretation”; “rather than shopping for a better score”; “Use one quiet session and one immutable attempt.”
- **Problem:** *Configurable*, *contaminated*, *immutable* and *evidence boundary* are internal design terms, and “shopping for” is an idiom. These lessons have the highest estimated reading grade (about 12) despite being the learner's first contact with the course.
- **Proposed correction:** “If you don't know a number, write ‘not confirmed’.”; “Was the attempt done alone, or did someone or something help?”; “Submit once. Don't restart to get a higher score.”; “Use one attempt only.”

### Cross-lesson — Too many named routines, overlapping or conflicting
- **Location:** E1.2 (slot–form–meaning–sentence), E1.4 (Core/Degree/Attitude/Sentence), E1.6 (S-C-A-N), E3.1 (three-filter), E4.1 (gap-role), E4.2 (anchor–controller–form), E4.3 (frame–meaning–cohesion), E4.4 (anchor–relation–timeline), E5.1 (topic/job/link), E5.2 (Locate/Match/Substitute), E5.3 (Frame/Clues/Precision/Substitute), E5.4 (Locate/Link/Prove), E5.5 (Claim/Clues/Limit), E5.6 (Topic/Message/Job/Attitude), E5.7 (Survey/Solve/Park/Return), E6.1 (T-C-A-S-P), E6.2 (I-S-A-R), E6.3 (R-D-L), E8.4 (four-pass ladder), E8.5 (Notice/Name/Correct/Check/Retest)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** About 20 different acronyms and routines in 41 lessons. “Locate” begins two different E5 routines; “Substitute” ends two; “anchor” and “job” change meaning between lessons.
- **Problem:** Young learners will spend effort remembering routine names rather than the skill, which is the brief's “routine names that obscure the skill” risk. Curriculum §4 names only one reading routine (Locate → Link → Prove).
- **Proposed correction:** Keep one routine per module (e.g. E4: “Grammar → Meaning → Whole passage”; E5: Locate → Link → Prove). Present the other steps as plain checklists without acronyms.

---

## E. Anatomy and curriculum fidelity

### Cross-lesson (E1.6, E2.2, E3.1–E9.4) — Guided practice and independent application have no linked items
- **Location:** sections 4 and 5 of `lessons/e1-lesson-06.json`, `e2-lesson-02.json`, `e3-lesson-01.json`, `e4-lesson-01…05.json`, `e5-lesson-01…07.json`, `e6-lesson-01…05.json`, `e7-lesson-01…05.json`, `e8-lesson-01…05.json`, `e9-lesson-01…04.json` (all `question_keys: []`)
- **Severity:** S2 · **Category:** validity
- **Evidence:** E3.1 section 5: “Fill the eight gaps from a twelve-word bank” (no item). E4.1 section 5: “Read all four paragraphs of ‘The workshop box’” and section 7, titled “The workshop box”. The same pattern appears in E4.2 (rooftop garden), E4.3 (rehearsal rescue), E4.4 (repair café), E4.5 (hillside water survey) and E5.7 (harbour report → “Harbour voices”). Only E1.1, E1.2, E1.4 and E2.1 link practice items, and the bank has no guided or independent items for any other outcome.
- **Problem:** Curriculum §3 requires scaffolded guided items (4) and unseen independent items in target format (5), then one unseen exit ticket (7). In 37 of 41 lessons the learner gets no practice. In E3–E5 the independent application *is* the exit-ticket passage, so the exit ticket is neither unseen nor a separate check.
- **Proposed correction:** Write at least one guided and one independent item per lesson for E3–E5 (one passage-based group each), and short planning or editing items for E6–E9. Point each section 5 at its own item, not the exit passage.

### Cross-lesson (E6.1–E9.4) — Exit tickets reuse the worked scenario, so they are not “unseen transfer”
- **Location:** section 7 of `lessons/e6-lesson-01…05.json`, `e7-lesson-01…05.json`, `e8-lesson-01…05.json`, `e9-lesson-01…04.json`
- **Severity:** S2 · **Category:** validity
- **Evidence:** E6.1–E7.4 all run on the charity-sale scenario both in the lesson and in the exit ticket (“Continue from the charity-sale composition plan…”). E8.1–E9.4 each introduce one scenario (reading room, media club, refill pilot, basil, exhibition, service policy, Nara) that is reused in the exit ticket (see section A).
- **Problem:** Curriculum §3.7 says the exit ticket is “one unseen transfer item”. As written, a learner can pass by matching options to remembered lesson sentences, so the retry-queue decision does not reflect mastery.
- **Proposed correction:** Keep the charity-sale thread for the teaching sections, but give every E6–E9 exit ticket a fresh prompt or scenario (the module checkpoints ex-l1-010 and ex-l5-007 already show the right pattern).

### Cross-lesson (E6–E9) — Writing outcomes assessed only by multiple-choice recognition
- **Location:** section 7 of `lessons/e7-lesson-05.json` (“transfer one structural move into a new paragraph”), `e7-lesson-0[1-4].json`, `e9-lesson-0[1-4].json`; curriculum §4 E7 and E9
- **Severity:** S2 · **Category:** validity
- **Evidence:** Curriculum E7.5 outcome: “Analyse an original model and transfer one structural move into a new paragraph.” Curriculum §3: writing lessons follow “Model–Practice–Reflect … practise one controllable move, apply it independently”. Every E6–E9 exit ticket is six single- or multiple-choice parts.
- **Problem:** No lesson asks the learner to produce a sentence, paragraph or plan. Recognising the best paragraph is not the same skill as writing one, so the declared writing outcomes are not assessed.
- **Proposed correction:** Add a short production task in section 5 of each E7–E9 lesson (e.g. “Write one paragraph using the five-step move about your own topic”), checked with a rubric or self-check list, and keep the MCQ exit ticket as a recognition check.

### e6-lesson-03 section 3 (and E6.4–E7.4) — Hypothetical scenario turns into a narrated true memory, contradicting the lesson's honesty rule
- **Location:** `lessons/e6-lesson-02.json` (section 3 bullet 2; section 2 bullet 2) vs `lessons/e6-lesson-03.json` (section 3 bullet 1), `e6-lesson-04.json` (section 3 bullet 1), `e7-lesson-02.json` (section 1 bullet 2), `e7-lesson-04.json` (section 2 bullet 1)
- **Severity:** S2 · **Category:** validity
- **Evidence:** E6.2: “I *could* use the same method to organise a school charity sale…” and “Do not present an invented event as a true memory.” E6.3: “the same method *helped* when rain forced the stalls indoors”. E7.4 model: “I later relied on that method while organising a charity sale, especially when sudden rain forced our team to change plans.”
- **Problem:** The running example starts as an honestly signalled possibility and becomes a past event with invented details (rain, drinks order, extension lead). The model essay therefore does what E6.2 section 6 and E7.2 section 6 tell learners not to do.
- **Proposed correction:** In E6.2, present the charity sale as an actual past experience (“I used the same method when our class organised a charity sale”), or keep the later models in conditional/future form.

### e1-lesson-06 sections 1–7 — Skeleton lesson: no practice items, morphology missing, exit ticket reuses a taught word
- **Location:** `lessons/e1-lesson-06.json` (sections 2, 4, 5 and 7) vs curriculum E1.6 and `questions/ev-l5-001.json` part 3
- **Severity:** S2 · **Category:** validity
- **Evidence:** The whole lesson is 123 words, with one sentence per section and `estimated_minutes: 30`. Section 2 S-C-A-N has no morphology step, although the curriculum outcome says “Combine syntax, context, morphology and option elimination”. Section 7: “Resolve five unfamiliar words”, but P3 is *meticulous*, already taught and keyed as “careful” in E1.1 guided item ev-l1-002.
- **Problem:** The lesson cannot fill 30 minutes or meet the 7-section anatomy. The exit ticket's “unfamiliar” word was explicitly taught. E1.3 (roots and affixes), which S-C-A-N would depend on, is not authored.
- **Proposed correction:** Expand to the standard depth (model, worked analysis, linked guided and independent items), add a word-part step to S-C-A-N (e.g. “un-, re-, -less”), and replace *meticulous* in ev-l5-001 with an unexposed word.

### e2-lesson-02 sections 1–7 — Skeleton lesson with no practice
- **Location:** `lessons/e2-lesson-02.json` (sections 4–5)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Section 4: “Strip interrupting phrases to test agreement, then replace any pronoun that could point to two nouns.” (`question_keys: []`); section 5: “Run a two-pass edit” (`question_keys: []`). The lesson is 139 words in total.
- **Problem:** The grammar lesson has no items to practise on before the exit ticket, and the worked analysis is two sentences long (which are also exit keys).
- **Proposed correction:** Expand to E2.1's depth and link guided and independent agreement and reference items.

### e9-lesson-05 sections 1–7 — “Full simulation” lesson contains no simulation and contradicts its time estimate
- **Location:** `lessons/e9-lesson-05.json` (summary; sections 1–7; `estimated_minutes: 30`)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Summary: “Execute the complete reported English profile under controlled timing”. Section 1: “Write the separate 90-minute and 30-minute clocks…”. Each section is a single sentence, and the only item is the 5-part MCQ ex-l5-004.
- **Problem:** The curriculum outcome (“Complete Section 1 and Section 2 under their separate reported limits”) needs a 120-minute mock, but the lesson estimates 30 minutes and links no mock form. Section 1 also presents the candidate-reported 90/30 timings as fixed rules.
- **Proposed correction:** Link the endline/mock form in section 5, set the time estimate to show a separate 120-minute sitting, and write “the reported 90-minute and 30-minute clocks (not yet officially confirmed)”.

### e0-lesson-01 / e0-lesson-02 — Thin orientation lessons; exit tickets only check recall of section 2
- **Location:** `lessons/e0-lesson-01.json` (sections 2 and 7) vs `questions/ex-l1-005.json`; `lessons/e0-lesson-02.json` (sections 2–3 and 7) vs `questions/ex-l2-004.json`
- **Severity:** S3 · **Category:** validity
- **Evidence:** E0.1 section 2: “Treat approximately 300 words as practice guidance until an official source confirms whether it is strict” → ex-l1-005 P5 key: “As provisional guidance until official confirmation.” E0.2 section 2: “Resume the same saved attempt after a technical interruption and record the interruption” → ex-l2-004 P2 key: “Resume the same saved session and record the interruption.”
- **Problem:** This is acceptable for an orientation check, but it is recall rather than the “unseen transfer” in curriculum §3. Each lesson is about 120–180 words for a 30-minute estimate.
- **Proposed correction:** Add short scenario-based transfer decisions (e.g. “A friend says the test has 40 vocabulary questions. What do you write on your plan?”), and expand the worked analysis.

---

## F. Internal consistency with catalogue and timing

### e4-lesson-05 sections 1 and 7 — Timing target not labelled as a training target; exit ticket called a module checkpoint
- **Location:** `lessons/e4-lesson-05.json` (section 1 bullet 2; section 7) vs `catalogue.json` exam_blueprint (section-1 `configurable_fields: part timing`) and `questions/eo-l5-001.json` (`exposure_pool: exit_ticket`)
- **Severity:** S3 · **Category:** validity
- **Evidence:** “Your target is eight gaps in eight minutes.”; “Complete one original eight-gap module checkpoint in eight minutes.”
- **Problem:** Unlike E5.7 and E6.5, this lesson does not say the timing is a NextScholar training target and not reported exam timing. The section 7 item is an exit ticket; the E4 module checkpoints are eo-l5-006 and eo-l5-007.
- **Proposed correction:** Write “Training target (not an official timing): eight gaps in eight minutes” and “Complete one original eight-gap exit ticket…”.

### e9-lesson-04 summary — 35-minute estimate for a lesson built on 45-, 35- and 30-minute writing runs
- **Location:** `lessons/e9-lesson-04.json` (`estimated_minutes: 35`; sections 2–4)
- **Severity:** S3 · **Category:** validity
- **Evidence:** “Begin with a fresh 45-minute supported rehearsal”; “Use a fresh comparable prompt at 35 minutes”; “Attempt 30 minutes only after…”
- **Problem:** The described runs total 110 minutes of writing, yet the lesson is estimated at 35 minutes and has no session structure.
- **Proposed correction:** Mark sections 2–4 as separate sessions outside the lesson (“over the next three practice sessions…”), or split the lesson into three.

### e7-lesson-04 section 2 vs keyed exit answer — Rhetorical-question opening discouraged, then keyed as best
- **Location:** `lessons/e7-lesson-04.json` (section 2 bullet 2; section 5 bullet 2) vs `questions/ex-l4-002.json` part 6
- **Severity:** S3 · **Category:** validity
- **Evidence:** Lesson: “It does not waste time … asking a rhetorical question”. Exit P6 key: “Opening: ‘Can one simple classroom method remain useful when a real plan fails?’…”
- **Problem:** Learners who follow the lesson may reject the keyed answer. The lesson needs to say when an opening question is acceptable.
- **Proposed correction:** In section 2 add: “A question can work if the essay later answers it exactly; avoid empty questions such as ‘Have you ever wondered…?’”

### Cross-lesson — Running example details drift between lessons
- **Location:** `lessons/e6-lesson-02.json`/`e6-lesson-04.json` (“mathematics”) vs `lessons/e7-lesson-04.json` (section 2: “School projects taught me…”); `lessons/e8-lesson-04.json`/`ex-l4-003` (Mira, basil, sun) vs `lessons/e9-lesson-01.json`/`ex-l1-004` (Lina, basil, watering); Mira also appears in E9.2
- **Severity:** S3 · **Category:** validity
- **Evidence:** E6.4: “this method is useful beyond mathematics”; E7.4: “School projects taught me that a large problem becomes manageable…”.
- **Problem:** The source of the school learning changes from a maths lesson to “school projects”. Two different basil experiments, and Mira as two different characters, may confuse learners who follow the threads.
- **Proposed correction:** Keep “mathematics” throughout E6–E7, and give the E8.4 and E9.1 experiments different plants and different names.

---

## Slice summary

**Counts:** S1 = 1 · S2 = 45 · S3 = 18 (64 findings in total). The S2 total includes 35 per-lesson leakage findings and 10 others. By section: A 37 (1 S1, 35 S2, 1 S3), B 7 (1 S2, 6 S3), C 4 (all S3), D 4 (2 S2, 2 S3), E 8 (7 S2, 1 S3) and F 4 (all S3).

**Cross-cutting patterns**
1. **Lesson-to-assessment leakage is systematic (36 lessons at S1/S2, plus light cueing in e5-02).** Worked examples, warm-ups or models reuse the exit-ticket passage, scenario or keyed sentences, often word for word. Affected lessons: e1-01, e1-02, e1-04 (practice items), e1-06 (retry), e2-01, e2-02, e3-01, e4-01…05, e5-01, e5-03 (exit and **protected reserve ev-l5-005**), e5-04, e5-05, e5-06, e6-01…05, e7-01…05, e8-01…05 and e9-01…04. In addition, e0-01, e0-02 and e9-05 have recall-type exit tickets, and e5-02 has light cueing. The worst case is e7-lesson-04, where the exit keys P1 and P4 are copied verbatim from the lesson. The only lessons whose section-3 worked examples are independent of their exit ticket are e5-lesson-02 and e5-lesson-07.
2. **Practice sections are empty.** 37 of 41 lessons have no question_keys in sections 4 and 5. In E3–E5 the independent application names the exit passage, so sections 5 and 7 are the same task.
3. **Exit tickets are not “unseen transfer”** (curriculum §3.7) for all of E6–E9, and writing outcomes are assessed only by MCQ recognition.
4. **Level fit for the 11–12 band:** E6–E9 estimate at FK grade 10–13. E0.x carry product jargon. E2 uses undefined core terms. About 20 named routines in total.
5. **Five skeleton lessons** (e0-01, e0-02, e1-06, e2-02, e9-05) are 120–180 words for a 30-minute estimate. The curriculum lessons E0.3, E1.3, E1.5, E2.3–E2.6 and E3.2–E3.4 are not authored, which leaves E1.6's morphology step and E3.1's filters without support.
6. **Repeated target words across pools** (for the item-bank owner): *tentative* (ev-l5-001 exit, er-l3-001 exit, ev-l5-005 reserve, er-l5-004 retry, E5.3 worked example); *meticulous* (ev-l1-002, ev-l5-001, er-l3-001); *coherent* (ev-l1-006 exit and ev-l5-005 reserve, both keyed “logically connected”); *scarce* (ev-l5-001 exit and ev-l5-005 reserve). Reserve ev-l5-005 therefore overlaps exit-ticket content on three of its five parts.

**Rule and terminology accuracy:** generally sound. Rules on articles (vowel sound), non-defining *which*, modal + base form, comma splices, *because* vs *because of*, *despite* + noun phrase, and *however* punctuation are stated correctly. The errors are the ones listed in section B: E8.2 “identifying”, the E2.2 of-phrase rule, the E1.4 “thin”, the E1.1 cause clue, and E5.5 association.

**Evidence boundary:** handled well. E0.1, E5.7, E6.5, E9.2, E9.3 and E9.4 correctly mark candidate-reported facts and training targets as provisional. The only gaps are E4.5's unlabelled 8-minute target and E9.5 section 1. No lesson states a word count or timing that contradicts `catalogue.json` (90 + 30 minutes, about 300 words).

**Lessons sound apart from cross-cutting items:** e5-lesson-02 and e5-lesson-07 (clean worked examples, accurate content, timing clearly labelled as a training target). The model sentences in e2-lesson-01, e4-lesson-01 (rules), e5-lesson-04 and e8-lesson-05 are grammatically accurate; their only problems are the leakage and practice gaps above.
