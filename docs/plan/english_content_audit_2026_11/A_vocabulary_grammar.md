# Slice A: vocabulary (ev-*) and grammar (eg-*) audit findings

Scope: 38 items (`ev-l1-001`…`ev-l5-007`, `eg-l1-001`…`eg-l2-004`), plus lesson cross-check against
`e1-lesson-01/02/04/06` and `e2-lesson-01/02`. Level fit judged against the audit level-fit basis: the only exam
profile is `secondary_1_entry`, so applicants are about 11–12 (final primary year), ESL.

Two platform facts I checked in code, because several findings depend on them:
- **Question titles are shown to learners.** `apps/web/src/components/english-practice-player.tsx:785` renders
  `<H2>{question.title}</H2>` above the instructions for every non-passage item, and
  `english-diagnostic-player.tsx:300` does the same in diagnostics and checkpoints.
- **Options are not shuffled at delivery.** No shuffle or randomise call appears in `services/learning_api/.../english_*.py`
  or the players, so the authored key position is the position the learner sees.

---

## A. Answer leakage through learner-visible titles (EV1.2 and EV1.4)

### ev-l2-006 part 1 — Exit-ticket title states the answer
- **Location:** `backend_resources/english/v1/questions/ev-l2-006.json` (`title`; exposure_pool exit_ticket)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** title “Transfer item: provisional”; key B “provisional”. The title is rendered as the H2 above the item (`english-practice-player.tsx:785`).
- **Problem:** The learner sees the correct option word in the heading of the mastery exit ticket, so the item measures nothing. The scale sets exit tickets at S2, but this should be fixed before release.
- **Proposed correction:** Retitle with neutral text that does not name the target, e.g. “Word family: transfer item”. Apply the same rule to all EV1.2 and EV1.4 titles (see the next finding).

### ev-l4-006 part 1 — Exit-ticket title states the answer
- **Location:** `backend_resources/english/v1/questions/ev-l4-006.json` (`title`; exit_ticket)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** title “Transfer item: cautious”; key B “cautious”.
- **Problem:** The title names the key, as in ev-l2-006.
- **Proposed correction:** Use “Synonym precision: transfer item”.

### ev-l2-001 part 1 — Practice titles name the keyed word (EV1.2 set)
- **Location:** `questions/ev-l2-001.json`, `ev-l2-002.json`, `ev-l2-003.json`, `ev-l2-004.json`, `ev-l2-005.json`, `ev-l2-007.json` (`title`)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Noun slot: decision” (key decision), “Adverb slot: clearly” (key clearly), “Adjective slot: accessible” (key accessible), “Verb slot: verify” (key verify), “Noun slot: accuracy” (key accuracy), “Parallel transfer item: clear” (key clear).
- **Problem:** Each title gives the word class and the exact keyed form. Both are the skill being assessed, and both appear in the visible H2.
- **Proposed correction:** Use neutral titles such as “Word family in context 1…7”, and keep the slot and word in a non-rendered field (for example `provenance` or a review note).

### ev-l4-001 part 1 — Practice titles name the keyed word (EV1.4 set)
- **Location:** `questions/ev-l4-001.json`, `ev-l4-002.json`, `ev-l4-003.json`, `ev-l4-004.json`, `ev-l4-005.json`, `ev-l4-007.json` (`title`)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Core meaning: narrow”, “Degree: warm”, “Attitude: assertive”, “Degree: minor”, “Core meaning: concise”, “Parallel transfer item: frank”. Each named word is the key.
- **Problem:** The title names the correct option on every EV1.4 item.
- **Proposed correction:** Use “Precise word choice 1…7”, optionally with the dimension (“Degree”) but never the word.

### eg-l1-002 part 1 — Title signals the repair strategy
- **Location:** `questions/eg-l1-002.json` (`title`)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** “Repair a comma splice with a shared subject”. Only option A joins the verb phrases under the shared subject.
- **Problem:** The visible title tells the learner the method of the correct repair. The level is low and this is practice, so the severity is minor.
- **Proposed correction:** “Repair a comma splice”.

---

## B. Grammar keys and ambiguity

### eg-l2-001 part 3 — “The coach and captain” can be one person, so the singular is defensible
- **Location:** `questions/eg-l2-001.json` (part 3, options A/B; exit_ticket)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** “Which compound-subject sentence is correct? A) The coach and captain is reviewing. B) The coach and captain are reviewing.” Rationale A: “Two people require plural agreement.” Hint: “Count the people.”
- **Problem:** With a single determiner, “the coach and captain” is the standard way to name **one** person who holds both roles (compare “my friend and colleague is…”). Nothing in the sentence says there are two people, so A is grammatical on that reading, and a well-informed learner would be marked wrong.
- **Proposed correction:** Repeat the determiner or name two people, e.g. “The coach and the captain ___ reviewing the match video.” (A is, B are). Also give the verb an object; “are reviewing.” with no object reads as a fragment.

### eg-l2-002 part 1 — “A series of workshops begin” is widely attested, especially in British English
- **Location:** `questions/eg-l2-002.json` (part 1, option B; retry_review)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** “A) A series of workshops begins next week. B) A series of workshops begin next week.” Rationale B: “Workshops is not the head.”
- **Problem:** The singular is the safer prescriptive choice, but “a series of + plural verb” is common notional agreement (it behaves like “a number of”). The item also teaches a “strip the of-phrase” rule that breaks on “a number of students are”.
- **Proposed correction:** Use an unambiguous head, e.g. “The timetable of workshops ___ on the noticeboard.” (is / are).

### ev-l4-007 part 1 — “Blunt” is a defensible near-synonym for the context
- **Location:** `questions/ev-l4-007.json` (option B; retry_review)
- **Severity:** S2 · **Category:** ambiguity
- **Evidence:** “The coach's feedback was ___: it named the mistake directly while remaining respectful and focused on improvement.” Options: harsh / blunt / frank / rude. Rationale B: “Blunt **often** suggests directness without enough sensitivity…”
- **Problem:** “Blunt but respectful feedback” is a common collocation, and the “while remaining respectful” contrast actually suits a word that carries some risk of tactlessness, which is blunt. The rationale only says “often”. This is the classic EV1.4 frank/blunt trap. Frank is still the best answer, but the margin is too small for learners aged 11–12.
- **Proposed correction:** Replace B with a clearly negative-attitude word such as “scornful”, or strengthen the context, e.g. “…it named the mistake honestly but kindly and suggested how to improve.” Keep frank as the key.

### eg-l2-001 part 5 — “Revision” prompt with no original; key does not fully secure the meaning
- **Location:** `questions/eg-l2-001.json` (part 5)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “The tray, not the bowl, was heated. Which revision is clear?” Key A: “Before the metal tray was heated, the glass bowl was placed beside it.”
- **Problem:** There is no original sentence to revise. The key also does not state that the bowl was **not** heated, which the prompt sets up as the point.
- **Proposed correction:** “Which sentence makes it clear that only the tray was heated?” Key: “The metal tray was heated while the glass bowl stayed on the table.”

---

## C. Checkpoint and diagnostic prompts that pre-state the analysis

### eg-l2-004 part 2 — Checkpoint prompt states that the head subject is plural
- **Location:** `questions/eg-l2-004.json` (part 2 prompt; module_checkpoint)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** “Which sentence correctly identifies the **plural** head subject?” Options: shows / show / is showing / has shown. Only “show” is plural.
- **Problem:** The item is meant to test whether learners pick `results`, not `survey`, as the head. The prompt does that step for them and tells them to choose the only plural verb. That gives the answer away in a protected checkpoint.
- **Proposed correction:** “Which sentence has correct subject–verb agreement?” (options unchanged).

### eg-l2-004 part 1 — Checkpoint prompt labels the subject “distributive” (and uses metalanguage beyond the band)
- **Location:** `questions/eg-l2-004.json` (parts 1 and 3 prompts; module_checkpoint)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** P1 “Which sentence has correct agreement with a **distributive** subject?”; P3 “Which sentence correctly agrees with **all items in a compound subject**?”
- **Problem:** Both prompts give the controlling analysis: distributive means singular, and all items in a compound subject means plural. “Distributive” is also linguistics metalanguage that 11–12-year-old ESL learners will not know.
- **Proposed correction:** For both parts, use “Which sentence has correct subject–verb agreement?”

### eg-l2-003 part 1 — Checkpoint prompts pre-state the grammatical analysis
- **Location:** `questions/eg-l2-003.json` (parts 1 and 3 prompts; module_checkpoint)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** P1 “…correctly controls agreement **despite the interrupting phrase**?”; P3 “…correctly treats **two distinct people** as a compound subject?”
- **Problem:** P1 tells learners to ignore the of-phrase, and P3 tells them the subject is two people, so plural. Those are the decisions being assessed.
- **Proposed correction:** For both parts, use “Which sentence has correct subject–verb agreement?”

### eg-l2-003 part 4 — Reference parts can be solved by picking the longest, most noun-heavy option (both checkpoint forms)
- **Location:** `questions/eg-l2-003.json` parts 4–5; `eg-l2-004.json` parts 4–5; same pattern in `eg-l2-001.json` parts 4–5 and `eg-l2-002.json` parts 4–5
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Key eg-l2-003 P4 C “After Aisha lent Nur the calculator, Nur discovered that one of the calculator's keys was loose.” Distractors include “After she lent it to her, she discovered its loose key.” and “It damaged it beside it.” (P5 C). In eg-l2-004 P4/P5 and eg-l2-003 P5 the key is the longest option. Distractors such as “He showed it to him, who noticed it.” are obviously broken.
- **Problem:** In every set, the key is the only option that repeats the nouns, and two or three distractors are pronoun strings no learner would pick. A test-wise strategy (choose the longest or most explicit option) beats the construct, so these checkpoint parts are far below difficulty 4.
- **Proposed correction:** Make every option a full, natural sentence and leave exactly one problem in each distractor: one ambiguous pronoun, or a meaning shift such as “After Aisha lent Nur the calculator, Aisha discovered a loose key.” Match option lengths to within a few words.

### eg-l2-003 part 5 — Checkpoint reuses the practice “notice on the gate” scenario
- **Location:** `questions/eg-l2-003.json` part 5 (module_checkpoint) vs `eg-l2-002.json` part 5 (retry_review)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Practice: “The notice was on the gate, but it was hard to read.” / “Rain blurred the notice's ink…”. Checkpoint: “A storm damaged the notice, not the gate… A) The notice was attached to the gate when it was damaged.”
- **Problem:** The checkpoint repeats the same nouns, the same ambiguity and the same distractor shape that the learner has already seen with feedback.
- **Proposed correction:** Use a new pair of objects in the checkpoint, e.g. “The kite, not the tree, was torn” or “a phone and its case”.

---

## D. Diagnostic, reserve and checkpoint set comparability and cross-pool overlap

Word map: Baseline ev-l5-003: concise, durable, vague, **reluctant**, resilient. Endline ev-l5-004: **meticulous**,
**reluctant**, feasible, **deteriorated**, impartial. Reserve ev-l5-005: **tentative**, **scarce**, **coherent**,
hindered, **verify**. Exit ticket ev-l5-001: tentative, deteriorated, meticulous, scarce, conceded. Guided/exit EV1.1:
meticulous (ev-l1-002), coherent (ev-l1-006). EV1.2: verify (ev-l2-004 key, lesson “must verify”).

### ev-l5-004 part 2 — Endline repeats a baseline word with the same key
- **Location:** `questions/ev-l5-004.json` part 2 (endline_diagnostic) vs `ev-l5-003.json` part 4 (baseline_diagnostic)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** Baseline: “The committee was reluctant to close the playground; members delayed the vote…” key D “unwilling or hesitant”. The after-group explanation reads “Reluctant means hesitant to act.” Endline: “The committee was reluctant to cancel the outdoor event, so it waited…” key B “unwilling or hesitant”.
- **Problem:** The baseline’s own post-submission feedback gives the endline answer. The key wording is identical, and so are the committee and delay frames. Pre/post gain on this part measures recall of a revealed answer.
- **Proposed correction:** Replace the endline target with a word that appears in no baseline, practice or exit-ticket pool and is of similar frequency, e.g. “The children were **eager** to start: they arrived an hour early and asked to begin at once.” (key “keen and excited”).

### ev-l5-004 part 1 — Endline items are near-copies of practice and exit-ticket items
- **Location:** `questions/ev-l5-004.json` parts 1 and 4 vs `ev-l1-002.json` (guided), `ev-l5-001.json` parts 2–3 (exit_ticket)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Endline P1: “Lina was meticulous…: she compared every date… and corrected even minor spacing errors.” Practice ev-l1-002: “Noor was meticulous…: she checked every label… and corrected even tiny spelling errors.” Endline P4: “The unused court deteriorated… cracks widened…” key “became worse”. Exit ev-l5-001 P2: “the road deteriorated; holes appeared…” key “became worse”.
- **Problem:** Three of five endline words (meticulous, reluctant, deteriorated) have already been practised with answers revealed, while every baseline word was unseen. The endline is therefore systematically easier than the baseline and inflates measured growth. For EV1.6 (unknown-word protocol) the words are also no longer unknown.
- **Proposed correction:** Rebuild the endline with five words that appear in no other pool, matched to the baseline’s frequency band. Keep a register of used target words per pool.

### ev-l5-005 part 2 — Protected reserve is a near-copy of an exit-ticket item
- **Location:** `questions/ev-l5-005.json` parts 1, 2, 3 (protected_reserve) vs `ev-l5-001.json` parts 1, 4 and `ev-l1-006.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Reserve P2: “Clean water became scarce after the pipe broke, so each household received only one container.” Exit P4: “Fresh water was scarce, so every home received only two containers.” Reserve P1 tentative (key “provisional and not final”) vs exit P1 tentative (“cautious and not final”). Reserve P3 coherent (“logically connected and clear”) vs exit ev-l1-006 (“logically connected”).
- **Problem:** A protected reserve should be unseen. Three of five words, and one near-verbatim context, have already been answered with feedback. P5 “verify” is also the key of ev-l2-004 and appears in the lesson. The reserve is not comparable to the baseline it would replace.
- **Proposed correction:** Replace parts 1, 2, 3 and 5 with words used nowhere else in the bank, e.g. “vacant”, “fragile”, “abundant”, “cautious” (if cautious is retired from EV1.4).

### ev-l5-007 part 4 — Checkpoint form B tests the negation of a form A word
- **Location:** `questions/ev-l5-007.json` part 4 vs `ev-l5-006.json` part 4 (module_checkpoint)
- **Severity:** S2 · **Category:** validity
- **Evidence:** Form A P4 “conventional” with explanation “Conventional describes what follows established practice.” Form B (hint text “Protected checkpoint retry”) P4 “unconventional” with key “different from usual practice”.
- **Problem:** Form B is the retry for form A. A learner who saw A’s feedback gets B P4 by adding the prefix, so the retry does not measure transfer.
- **Proposed correction:** Replace B P4 with an unrelated word of similar difficulty, e.g. “The design was **innovative**: no other team had tried movable walls.”

### ev-l5-006 part 1 — Every checkpoint key is A in both forms, and options are not shuffled
- **Location:** `questions/ev-l5-006.json` and `ev-l5-007.json` (all parts `correct_key: "A"`)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Key positions are A A A A A in both forms. Across the whole slice: A 36, B 32, C 10, D 3. The only D keys are eg-l2-003 P2, ev-l4-005 and ev-l5-003 P4. No delivery-time shuffle exists.
- **Problem:** After seeing form A’s feedback, a learner can pass the form B retry by choosing A every time. The slice-wide skew towards A and B, with almost no D, is exploitable.
- **Proposed correction:** Rebalance keys within each set (for example B, D, A, C, B), or add option shuffling at delivery. Spread C and D keys across the bank.

### ev-l5-006 part 1 — Context does not actually show ambiguity
- **Location:** `questions/ev-l5-006.json` part 1 (module_checkpoint)
- **Severity:** S2 · **Category:** validity
- **Evidence:** “The announcement was ambiguous: one sentence said the hall would open at seven, while another suggested that registration ended at seven.”
- **Problem:** The hall opening at seven and registration ending at seven can both be true. These are two compatible facts, not one wording with two readings, so the context clue contradicts the key “open to more than one interpretation”.
- **Proposed correction:** “The announcement was ambiguous: ‘Meet at the hall at seven’ did not say whether it meant seven in the morning or seven in the evening.”

### ev-l5-003 part 4 — The two-part gloss key stands out against single-word distractors (diagnostic and reserve)
- **Location:** `questions/ev-l5-003.json` P4 (baseline), `ev-l5-005.json` P4 (reserve), `ev-l5-002.json` P1 and P4, `ev-l5-006.json` P1
- **Severity:** S3 · **Category:** leakage
- **Evidence:** “A) eager B) unable C) unaware **D) unwilling or hesitant**”; “A) guided **B) delayed or obstructed** C) protected D) surprised”; “A) regular **B) irregular and occasional** C) compulsory D) early”; “**A) open to more than one interpretation**” (longest).
- **Problem:** The key is the only hedged “X or Y” or multi-word gloss among one-word distractors, which is a classic test-wise cue. Across ev-l5-003/005/006/007 the key is the uniquely longest option in 3 or 4 of the 5 parts.
- **Proposed correction:** Make every option the same shape, e.g. “eager to act / unable to act / unaware of the issue / unwilling to act”, and “helped / slowed / protected / surprised”.

---

## E. Lesson worked examples that are near-copies of assessed items

### ev-l2-001 part 1 — Guided item is verbatim the lesson worked example
- **Location:** `questions/ev-l2-001.json` vs `lessons/e1-lesson-02.json` sections[2].content[0–1]
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “In ‘After reviewing the trial, the committee reached a final ___’, … Decision fits that slot. Decide is a verb, decisive is an adjective and decisively is an adverb…”. The item has the identical stem and identical four options.
- **Problem:** The learner meets a fully solved copy and then the “guided” item, so the guided item tests recall.
- **Proposed correction:** Keep the lesson example and change the item to a new family, e.g. “The coach praised the team's ___ (prepare / preparation / prepared / preparedly).”

### ev-l2-003 part 1 — Lesson frames give the keys of the independent EV1.2 items
- **Location:** `lessons/e1-lesson-02.json` sections[1].content[0] vs `questions/ev-l2-002.json`, `ev-l2-003.json`, `ev-l2-004.json`, `ev-l2-005.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “‘her accuracy’ … ‘must verify’ … ‘the route is accessible’ … ‘explained clearly’.” Items: “The map's ___ improved” (accuracy), “must ___ its measurements” (verify), “The revised route is more ___” (accessible), “explained the safety steps ___” (clearly).
- **Problem:** Each of the four practice keys is shown in the same frame, with the same noun where there is one (route), in the teaching text. Combined with the titles in section A, the independent practice gives no independent evidence.
- **Proposed correction:** Change the lesson illustrations to other families, e.g. “her patience”, “must measure”, “the room is comfortable”, “spoke politely”.

### ev-l4-001 part 1 — The EV1.4 lesson pre-solves the guided and independent items
- **Location:** `lessons/e1-lesson-04.json` sections[0], [1], [4] vs `questions/ev-l4-001.json` to `ev-l4-005.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** “Compare ‘a narrow path’, ‘a thin sheet’ and ‘a cramped room’” (ev-l4-001 options narrow/thin/cramped, path context). “Warm, hot and scorching” (ev-l4-002 options). “Assertive can praise clear confidence; aggressive suggests harmful force” (ev-l4-003 key and distractor). Section 4 predictions “‘confident but respectful’, ‘small in seriousness’ or ‘brief without losing essential meaning’” are the hints and keys of ev-l4-003, -004 and -005.
- **Problem:** The “unseen” independent items are announced in the lesson with their predicted meanings.
- **Proposed correction:** Use different word sets in the lesson (e.g. damp/wet/soaked; curious/nosy), and use generic predictions in section 4.

### eg-l2-001 part 1 — Exit-ticket keys appear verbatim in the E2.2 lesson
- **Location:** `lessons/e2-lesson-02.json` sections[2].content[0] vs `questions/eg-l2-001.json` parts 1 and 4 (exit_ticket)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “‘The collection of maps is locked’ agrees with collection… ‘When Sara returned the laptop, Mei noticed its cracked screen’ names both important referents.” These are the exact keys of P1 (B) and P4 (B).
- **Problem:** Two of five exit-ticket parts are answered word for word in the lesson.
- **Proposed correction:** Change the exit-ticket sentences, e.g. “The box of pencils ___ on the shelf” and a new pair of names and object for P4.

### eg-l1-006 part 1 — Exit ticket mirrors the E2.1 lesson’s agreement and cause-result examples
- **Location:** `lessons/e2-lesson-01.json` sections[1].content[3] and sections[2].content[1] vs `questions/eg-l1-006.json` (exit_ticket)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “The head subject controls the finite verb: ‘The row of plants needs shade.’” and “‘The rehearsal ended late, so everyone missed the final bus’ shows cause and result.” Item: “The row of young plants need shade in the afternoon, the gardening team moves a screen beside them.” Key: “…needs shade…, so the gardening team…”
- **Problem:** The exit-ticket subject phrase and the repair pattern are both lifted from the lesson.
- **Proposed correction:** Use a new head noun in the item, e.g. “The box of library books need covering, the volunteers wrap them in plastic.”

### ev-l5-002 part 2 — Retry item copies the EV1.6 lesson example
- **Location:** `lessons/e1-lesson-06.json` sections[2].content[0] vs `questions/ev-l5-002.json` part 2 (retry_review)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: “‘The plan was viable because the team had enough time and materials’ … viable must mean workable.” Item: “The smaller design was viable because available time and materials were enough.” Key “workable”.
- **Problem:** The retry is meant to be a fresh context, but it repeats the lesson word, clue and key.
- **Proposed correction:** Replace with a new word, e.g. “The bridge was **sturdy**: even when ten people stood on it, it did not move.” (key “strong and solid”).

### ev-l1-001 part 1 — Guided item duplicates the EV1.1 lesson example
- **Location:** `lessons/e1-lesson-01.json` sections[2].content[0–1] vs `questions/ev-l1-001.json`
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Lesson: “The slope was treacherous—dangerous and unstable…” with “‘Narrow’ … unsupported… ‘Hazardous’ matches”. Item: “The mountain path was treacherous—so dangerous and unstable…” key “hazardous”, distractor “narrow”.
- **Problem:** Same word, clue, key and distractor. This is guided practice, so the impact is minor.
- **Proposed correction:** Change the item word, e.g. “The water was murky—so cloudy and dirty that we could not see the bottom.”

---

## F. Level fit for the 11–12 ESL band

### ev-l1-003 part 1 — “Gregarious” at difficulty 2 is mislabelled and beyond the band
- **Location:** `questions/ev-l1-003.json` (`difficulty: 2`)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** “gregarious” at difficulty 2, while “coherent”, “systematic” and “wistful” are difficulty 3.
- **Problem:** “Gregarious” is a low-frequency C2 word and the hardest target in EV1.1, yet it carries one of the lowest labels. It is not plausible vocabulary for 11–12-year-olds, although the contrast clue makes it solvable.
- **Proposed correction:** Use “sociable” or “talkative” as the target with key “friendly and enjoys meeting people”, or relabel as difficulty 4.

### ev-l1-004 part 1 — “Conciliatory” and the gloss wording are beyond the band
- **Location:** `questions/ev-l1-004.json`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Target “conciliatory”; options “intended to restore peace”, “designed to cause confusion”.
- **Problem:** “Conciliatory” is C2 and abstract for primary-final ESL learners. The gloss options are fine, but the target is out of band.
- **Proposed correction:** Use “calm” or “polite”, or “The two teams **compromised**: each agreed to give up something” (key “agreed to meet halfway”).

### ev-l5-006 part 5 — Checkpoint form A word list is well above the band
- **Location:** `questions/ev-l5-006.json` parts 2, 3, 5; also `ev-l5-001.json` P5 (conceded), `ev-l5-002.json` P1, P4 (sporadic, obsolete), `ev-l2-006.json` (provisional)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** “scrutinised”, “negligible”, “compelling”, “conceded”, “sporadic”, “obsolete”, “provisional”. Key glosses include “open to more than one interpretation”, “generally accepted or traditional”, “free from unfair preference”, “delayed or obstructed”.
- **Problem:** Several targets are C1–C2, and several gloss options use vocabulary (interpretation, obstructed, preference, provisional) as hard as the targets, so the item tests the gloss rather than the word. The contexts are, however, very strong and the distractors very weak (“arranged by colour”, “too quiet to hear”), so the measured difficulty will be low even though the visible vocabulary is intimidating. This combination gives poor information.
- **Proposed correction:** Draw targets from a B1–B2 list (e.g. careful, ancient, fragile, rapid, vacant, examine, reduce, deny). Write glosses in A2–B1 words, e.g. “too small to matter”, “looked at very carefully”. Replace throwaway distractors with near-misses (e.g. for scrutinised: “signed quickly”, “counted roughly”).

### eg-l2-001 part 2 — Non-word distractors make the EG2.2 practice parts two-option items
- **Location:** `questions/eg-l2-001.json` P2, P3; `eg-l2-002.json` P1, P2, P3
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** “have receive”, “were receiving always”, “has review”, “A series have begins.”, “were be”, “have being”.
- **Problem:** Two of four options in each part are forms no learner produces, so each part is a coin-flip between the singular and plural forms. Error data is uninformative.
- **Proposed correction:** Use plausible learner errors, e.g. “received / receives / receive / are receiving”.

### eg-l1-001 part 1 — Metalanguage in hints and rationales
- **Location:** `questions/eg-l1-001.json` hint; `ev-l2-002.json` to `ev-l2-007.json` rationales; `eg-l1-006.json` hint
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** “finite verb”, “dependent-clause signal”, “head subject”, “linking verb”, “subject complement”, “modal”.
- **Problem:** These terms are taught in the lessons, but they are dense for 11–12-year-old ESL learners, and “subject complement” is not taught.
- **Proposed correction:** Pair each term with a plain gloss, e.g. “the main verb that shows time (finite verb)”, and replace “subject complement” with “the describing word after ‘were’”.

---

## G. Editorial and minor accuracy

### eg-l1-001 part 1 — Rationale calls a clause a “phrase”
- **Location:** `questions/eg-l1-001.json` choice_rationales D
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “This time phrase contains a subject and verb but begins with after…”
- **Problem:** A phrase cannot contain a subject and finite verb. This is the exact clause/phrase distinction EG2.1 teaches.
- **Proposed correction:** “This time clause has a subject and verb but begins with after, so it needs a main clause.”

### eg-l1-004 part 1 — Hint points to the only option with a signal word
- **Location:** `questions/eg-l1-004.json` hint
- **Severity:** S3 · **Category:** leakage
- **Evidence:** “Find the opening word that promises a contrast…” Only C begins with a subordinator (Although).
- **Problem:** The hint identifies the answer outright, not the method.
- **Proposed correction:** “Check each option: does it have a main clause that could stand alone?”

### eg-l2-002 part 2 — Unnatural preposition in the stem
- **Location:** `questions/eg-l2-002.json` part 2 prompt
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “Everyone in the teams ___ responsible.”
- **Problem:** The natural collocation is “on the team(s)”, and the sentence is incomplete in meaning (responsible for what?).
- **Proposed correction:** “Everyone on the two teams ___ responsible for cleaning up.”

### eg-l2-002 part 4 — The original is already clear, and the prompt is awkward
- **Location:** `questions/eg-l2-002.json` parts 4 and 5 prompts
- **Severity:** S3 · **Category:** grammar
- **Evidence:** P4 “Daniel sent the message, then called Yusuf. Which revision is clear?” P5 “Which rain-damaged notice sentence is clearest?”
- **Problem:** The P4 “original” is already unambiguous, so asking for a revision is confusing. The P5 noun stack is hard to parse.
- **Proposed correction:** P4: “Which sentence makes it clear that Daniel sent the message?” P5: “Rain damaged a notice on a gate. Which sentence is clearest?”

### eg-l2-001 part 2 — Instructions do not fit a gap-fill part
- **Location:** `questions/eg-l2-001.json` instructions / part 2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** Instructions “Choose the sentence with correct agreement…”; P2 is a single-word gap-fill (“Each of the volunteers ___ a badge.”).
- **Problem:** The instructions and task format do not match. The same mismatch occurs in eg-l2-002 P2 and eg-l2-003 P2.
- **Proposed correction:** “Choose the answer that gives correct agreement or clear reference.”

### ev-l4-004 part 1 — Rationales describe content the sentence does not contain
- **Location:** `questions/ev-l4-004.json` choice_rationales B, C
- **Severity:** S3 · **Category:** correctness
- **Evidence:** B “…matches the small repair described.” C “…that the sentence explicitly rules out.”
- **Problem:** No repair is described, and seriousness is implied rather than explicitly ruled out.
- **Proposed correction:** B: “Minor matches two loose panels and rooms that stayed safe and dry.” C: “Serious would suggest danger, but every room remained safe and dry.”

### ev-l5-001 part 5 — Awkward pronoun and assumed gender
- **Location:** `questions/ev-l5-001.json` part 5 prompt and rationales B, D
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “The captain denied moving the marker but conceded it after seeing the video.” Rationales: “She acknowledges it.” and “…not her action.”
- **Problem:** “Conceded it” is awkward, and the captain’s gender is never given.
- **Proposed correction:** “…but conceded that she had moved it after seeing the video.” (or name the captain, e.g. “Captain Siti”).

### ev-l5-002 part 4 — Unnatural collocation
- **Location:** `questions/ev-l5-002.json` part 4 prompt
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “Old machines became obsolete when they could not read the new system.”
- **Problem:** Machines do not “read a system”.
- **Proposed correction:** “The old computers became obsolete when they could not run the new software.”

### ev-l5-007 part 2 — Rationales refer to a passage that does not exist; odd distractor rationale
- **Location:** `questions/ev-l5-007.json` P2 rationale B; P1 rationale B
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “The passage says confirmation is still needed.” and “The details improve accessibility.”
- **Problem:** These are single sentences, not passages, and “accessibility” is not the reason “understood only by experts” fails.
- **Proposed correction:** “The sentence says the team still needs evidence.” and “Anyone could follow these exact steps.”

### ev-l2-005 part 1 — Option D is not a word-family form
- **Location:** `questions/ev-l2-005.json` option D
- **Severity:** S3 · **Category:** validity
- **Evidence:** “D) accurate enough” among accurate / accurately / accuracy.
- **Problem:** The instructions ask for “the word-family form”, but D is a phrase, which makes it an odd one out and easy to eliminate.
- **Proposed correction:** Replace D with another family member, e.g. “inaccurate” (an adjective, so it fails the noun slot in the same way as A).

### ev-l2-007 part 1 — Parallel retry reuses a guided-practice word family
- **Location:** `questions/ev-l2-007.json` vs `ev-l2-002.json`
- **Severity:** S3 · **Category:** validity
- **Evidence:** Both items use the options clear / clearly / clarity / clarify.
- **Problem:** The retry for the exit ticket (provisional) reuses the family already practised in guided practice, so it is not a fresh transfer.
- **Proposed correction:** Use a new family, e.g. “The instructions were sufficiently ___ (simple / simply / simplicity / simplify).”

### eg-l2-001 part 1 — Terse boilerplate rationales
- **Location:** `questions/eg-l2-001.json`, `eg-l2-002.json`, `ev-l5-001.json`, `ev-l5-002.json` (choice_rationales)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** “The phrase is ungrammatical.” / “This is ungrammatical.” (twice in one part) / “She is working.” / “They are old.” / “Spread is absent.”
- **Problem:** The rationales are three-word stubs that do not teach the learner why the option fails, unlike the full rationales elsewhere in the slice.
- **Proposed correction:** Expand to one full explanatory sentence each, matching the style of eg-l1 and ev-l4.

---

## Slice summary

**Counts:** S1 = 3 · S2 = 23 · S3 = 19 (45 findings; several findings cover multiple items as listed).

Item-level S2 count, expanding grouped findings: the title-leak findings cover 14 items (ev-l2-001…007,
ev-l4-001…007). Lesson leakage covers 12 items.

**S1 (blockers)**
1. `eg-l2-001` P3: “The coach and captain is…” is grammatical on the one-person reading, so it is a second correct answer (exit ticket).
2. `eg-l2-004` P2: the checkpoint prompt says “plural head subject”, which gives away the answer.
3. `ev-l5-004` P2: the endline repeats the baseline word “reluctant”, and the baseline’s own feedback reveals the identical key.

**Cross-cutting patterns**
- **Titles leak keys (highest-impact issue, S2 by the scale but should be treated as release-blocking).** Titles are rendered as H2 in both players. Every EV1.2 and EV1.4 title names the keyed word: ev-l2-001…007, ev-l4-001…007, including exit tickets ev-l2-006 and ev-l4-006. Fix by policy: titles must never contain the target word or form.
- **Pool contamination.** Endline, reserve and checkpoint form B reuse words, contexts or derivations from baseline, practice and exit tickets: ev-l5-004 P1/P2/P4; ev-l5-005 P1/P2/P3/P5; ev-l5-007 P4; eg-l2-003 P5. As a result, the endline (3/5 words already seen) and the reserve (4/5 seen) are easier than the baseline (0/5), and pre/post comparison is biased.
- **Lessons pre-solve items.** e1-lesson-02 → ev-l2-001…005; e1-lesson-04 → ev-l4-001…005; e1-lesson-06 → ev-l5-002 P2; e2-lesson-01 → eg-l1-006; e2-lesson-02 → eg-l2-001 P1/P4; e1-lesson-01 → ev-l1-001.
- **Checkpoint prompts state the grammar decision.** eg-l2-003 P1/P3 and eg-l2-004 P1/P2/P3.
- **Key-position and length cues with no shuffle.** ev-l5-006/007 are keyed all A. The slice has only 3 D keys out of 81. Reference parts (eg-l2-001…004 P4/P5) and EV1.6 glosses tend to make the longest or “X or Y” option the key.
- **Level fit for ages 11–12.** Many EV targets are C1–C2 (gregarious, conciliatory, scrutinised, negligible, conceded, sporadic, provisional) and some gloss options are as hard as the targets. Distractors are often throwaway, so difficulty labels (3–4) overstate the reasoning demand while the visible vocabulary is out of band.
- **Format note (S3, validity).** The exam profile describes Section 1 part 1 as “choose the word whose meaning best completes or fits a sentence”. EV1.2 and EV1.4 match that format. EV1.1 and EV1.6, including all diagnostics and checkpoints, use the reverse “What does X mean?” gloss format, so the diagnostics do not sample the exam task format.

**Items I consider sound** (apart from cross-cutting title or pool issues already noted): eg-l1-002 (content),
eg-l1-003, eg-l1-005, ev-l1-002, ev-l1-005, ev-l1-006, ev-l1-007, ev-l2-002/003/004 (content), ev-l4-002, ev-l4-003,
ev-l4-005, ev-l4-006 (content), ev-l5-003 P1/P2/P3/P5, ev-l5-004 P3/P5, ev-l5-006 P2–P5 (content), ev-l5-007
P1–P3/P5 (content), eg-l2-003 P2, eg-l2-004 P3–P5 (keys correct; see the cue and prompt findings).
