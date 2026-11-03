# Slice C — Reading comprehension (er-*) findings

Scope: 15 reading sets (er-l1-001 … er-l5-009), 89 parts, plus 15 passages. I answered every item from the passage before checking the key. Level fit is judged against the audit level-fit basis: profile `secondary_1_entry`, so the target is ESL learners aged about 11–12 in their final primary year.

Platform checks that affect the findings:
- The practice player (`apps/web/src/components/english-practice-player.tsx` l.706–722) labels every element of `passage.paragraphs` as "PARAGRAPH n", and this includes the "PASSAGE A — …" and "PASSAGE B — …" heading lines in the paired passages.
- The diagnostic/checkpoint player shows paragraphs without numbers, but it renders each heading line as its own `<p>` block.
- Short-text normalisation: case-insensitive, terminal punctuation stripped, nothing else.

---

### er-l1-001 part 4 — Clause-length exact-match answer rejects the passage's own wording
- **Location:** `backend_resources/english/v1/questions/er-l1-001.json` (part 4, short_text)
- **Severity:** S1 · **Category:** correctness
- **Evidence:** canonical "the soil absorbed the pooled water within a few hours"; alternatives only "the rain garden absorbed the pooled water within a few hours", "the garden absorbed the water within a few hours", "the soil absorbed the water within a few hours". The passage says: "Within a few hours, the soil had absorbed the pooled water. This result persuaded…"
- **Problem:** A learner who copies the source sentence ("within a few hours, the soil had absorbed the pooled water") or writes "the soil had absorbed the pooled water" / "the soil absorbed the pooled water" is marked wrong. "This result" can also fairly be read as the whole storm test ("a strong storm filled the shallow beds without flooding the walkway"), and that answer is not accepted either.
- **Proposed correction:** Make this a single-choice item (key: "The soil absorbed the pooled storm water within a few hours"; distractors: the beds being planted, the canteen beds, the butterflies). If it stays short-text, at minimum add: "within a few hours, the soil had absorbed the pooled water", "within a few hours the soil had absorbed the pooled water", "the soil had absorbed the pooled water", "the soil absorbed the pooled water", "the soil had absorbed the pooled water within a few hours", "the pooled water was absorbed within a few hours", "the storm filled the beds without flooding the walkway and the soil absorbed the water".

### er-l1-001 part 5 — Prompt asks why we can "infer" something the passage states
- **Location:** `backend_resources/english/v1/questions/er-l1-001.json` (part 5 prompt)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Why can we reasonably infer that teachers began holding short lessons in the courtyard?" The passage says: "teachers sometimes hold short lessons in the cooler courtyard".
- **Problem:** The lessons are stated, not inferred. The thing to infer is the reason. The prompt's logic is confusing for a level-2 learner. The key also repeats the passage's words ("cooler", "useful to people"), and no other option does.
- **Proposed correction:** "Why did teachers most likely start holding short lessons in the courtyard?"

### er-l2-001 part 2 — "Dr. Arun" and other obvious variants not accepted
- **Location:** `backend_resources/english/v1/questions/er-l2-001.json` (part 2, short_text)
- **Severity:** S1 · **Category:** correctness
- **Evidence:** canonical "Dr Arun"; alternatives "Dr Arun, the coastal ecologist", "the coastal ecologist".
- **Problem:** "Dr. Arun", with a full stop, is standard in Indonesian and US-influenced writing and is very likely. Because marking is exact-match it is marked wrong. "Arun", "Doctor Arun", "a coastal ecologist", "the ecologist" and "Dr. Arun, the coastal ecologist" are also correct and rejected.
- **Proposed correction:** Add "Dr. Arun", "Arun", "Doctor Arun", "Dr. Arun, the coastal ecologist", "Dr Arun the coastal ecologist", "a coastal ecologist", "the ecologist", "the coastal ecologist Dr Arun".

### er-l2-001 part 3 — Verbatim referent and "a covered walkway" variant rejected
- **Location:** `backend_resources/english/v1/questions/er-l2-001.json` (part 3, short_text)
- **Severity:** S1 · **Category:** correctness
- **Evidence:** The passage says: "The club moved half the trays to a covered walkway but left the others beside the sports shed." Accepted: "…moved half the trays to a covered walkway **and** left the others…", "moving half the trays to **the** covered walkway".
- **Problem:** The exact source sentence ("…**but** left the others…") is rejected. So is the short form with the passage's own article ("moving half the trays to **a** covered walkway"), and so are "moved half the trays to a covered walkway" and "the club moved half the trays to a covered walkway". The accepted list happens to include the short form only with "the".
- **Proposed correction:** Convert to single choice. If not, add at least: "the club moved half the trays to a covered walkway but left the others beside the sports shed", "moved half the trays to a covered walkway but left the others beside the sports shed", "moving half the trays to a covered walkway", "moved half the trays to a covered walkway", "the club moved half the trays to a covered walkway", "moving half of the trays to a covered walkway", "moving half the trays to the walkway".

### er-l2-002 part 5 — "The devices" can fairly be read as the paper streamers
- **Location:** `backend_resources/english/v1/questions/er-l2-002.json` (part 5); `passages/english-passage-solar-dryer-trial.json` P3–P4
- **Severity:** S2 · **Category:** ambiguity
- **Evidence:** "…the club added paper streamers near both vents to observe it. / The streamers moved more consistently… The devices were left in place for four more trials…" Key: "B) Both solar dryers". Distractor: "A) The paper streamers only". Rationale A: "Streamers are not the trial devices."
- **Problem:** The streamers are the nearest plural object, they were "added" "near both vents", and "left in place" fits something that was attached. A careful reader can defend A, and the rationale asserts the answer without showing why.
- **Proposed correction:** Change the passage to "The two dryers were left in place…" and test another reference, or change it to "Both devices were left in place, with their streamers, for four more trials…" so that "both" points to the two dryers.

### er-l3-001 part 1 — Rationale A answers a different option
- **Location:** `backend_resources/english/v1/questions/er-l3-001.json` (part 1, choice_rationales.A)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** Option A is "rarely used"; the rationale says: "The age of the tapes does not define fragile…"
- **Problem:** The rationale talks about age, not use, so the feedback does not explain why "rarely used" is wrong.
- **Proposed correction:** "Nothing in the sentence is about how often the tapes are used; the reason given is that heat and moisture could damage them."

### er-l3-001 parts 2, 4, 5 / er-l3-002 parts 1–5 — Target words far above an 11–12 ESL band
- **Location:** `backend_resources/english/v1/questions/er-l3-001.json`, `er-l3-002.json`; passages `english-passage-river-town-radio-archive.json`, `english-passage-community-seed-archive.json`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** Target words: "cryptic", "meticulous", "tentative", "corroborated" (l3-001); "dormant", "ambiguous", "meticulous", "provisional", "corroborated" (l3-002). Keys and glosses use "provisional" (l3-001 P4 key), "painstaking" (l3-002 P3 key) and "independent evidence". Rationale language includes "Storage quality is conditional, not definitional."
- **Problem:** Most of these are C1/C2 academic words, well beyond what a final-year primary ESL applicant needs. In several cases the answer or gloss is harder than the word being tested (tentative → "provisional"; meticulous → "painstaking").
- **Proposed correction:** Swap in upper-primary/B1 targets that can be learnt from context ("fragile", "faded", "careful", "doubtful", "confirmed", "puzzling", "temporary", "reluctant"). Keep "meticulous" at most as one stretch item. Rewrite keys with B1 words: tentative → "not yet final; might change"; meticulous → "very careful".

### er-l3-001 part 5 — Passage defines "corroborated" redundantly
- **Location:** `backend_resources/english/v1/passages/english-passage-river-town-radio-archive.json` P4
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "their accounts corroborated the students' identification by providing additional support for it."
- **Problem:** The phrase repeats the meaning of "corroborated" ("supported … by providing support"). The wording is unnatural and gives the definition away. The hint ("the verb immediately followed by an explanation…") then points straight at the word.
- **Proposed correction:** "When several residents independently recognised the same speaker, their accounts corroborated the students' identification." The context clue "independently recognised the same speaker" is enough.

### er-l3-002 part 6 — Part 6 key reveals the part 3 answer
- **Location:** `backend_resources/english/v1/questions/er-l3-002.json` (part 6 option A vs part 3)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Part 3 asks: "Which word best replaces 'meticulous'… C) painstaking". Part 6, option A: "dormant → inactive; meticulous → painstaking". Options B, C and D are plainly wrong ("ambiguity", "contradiction", "hurried / permanent").
- **Problem:** A learner can spot P6-A by elimination, and it then gives away P3. "inactive" also repeats P1's passage gloss ("Although the seeds were inactive").
- **Proposed correction:** P6 option A → "ambiguous → unclear; provisional → temporary". Change B, C and D so they no longer contain "meticulous".

### er-l3-002 part 1 — Key repeats the passage's own gloss and is much longer
- **Location:** `backend_resources/english/v1/questions/er-l3-002.json` (part 1)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Key "inactive but capable of becoming active" (2.9× the average distractor length). The passage says: "Although the seeds were inactive, some could still grow".
- **Problem:** This is the only long, qualified option, and it reuses the passage's word "inactive". It can be answered without understanding the word.
- **Proposed correction:** Use options of the same length: "resting / not growing for now" (key), "dead", "freshly picked", "poorly packed".

### er-l4-001 part 2 — "one metre", "1 m" and "meter" spellings rejected
- **Location:** `backend_resources/english/v1/questions/er-l4-001.json` (part 2, short_text)
- **Severity:** S1 · **Category:** correctness
- **Evidence:** Prompt: "At what height did the teams hold the sensor?" Accepted: "one metre above the ground", "one metre above ground", "1 metre above the ground", "1 metre above ground".
- **Problem:** "one metre" and "1 metre" fully answer "At what height". They are the most likely responses and are marked wrong. "1 m", "1m", "a metre above the ground" and the US spelling "meter", which is common in Indonesian schooling, are also rejected.
- **Proposed correction:** Add "one metre", "1 metre", "1 m", "1m", "1 m above the ground", "1m above the ground", "a metre above the ground", "one meter", "1 meter", "one meter above the ground", "1 meter above the ground", "one meter above ground", "1 metre from the ground", "one metre from the ground".

### er-l4-001 part 5 — The proposal's own wording is not accepted
- **Location:** `backend_resources/english/v1/questions/er-l4-001.json` (part 5, short_text)
- **Severity:** S1 · **Category:** correctness
- **Evidence:** Prompt: "Which proposal did the town council approve for an immediate trial?" The passage proposal is "shade sails **near** the main gate". Accepted: "…shade sails **at** the main gate" variants only.
- **Problem:** The prompt asks which *proposal* was approved, and the proposal is worded "shade sails near the main gate". That answer, plus "shade sails", "the shade sails", "six-week trial of shade sails at the main gate" (no article) and "a six week trial…" (no hyphen), are all marked wrong. Also, "immediate" is not in the passage.
- **Proposed correction:** Prompt: "Which proposal did the town council approve for a trial?" Add "shade sails", "the shade sails", "shade sails near the main gate", "the shade sails near the main gate", "the shade sails at the main gate", "six-week trial of shade sails at the main gate", "a six week trial of shade sails at the main gate", "a 6-week trial of shade sails at the main gate", "a shade-sail trial at the main gate". Or convert to single choice (shade sails / refill point / trees / bus-stop move).

### er-l4-001 part 6 — Key turns a comparison into a "reduction"
- **Location:** `backend_resources/english/v1/questions/er-l4-001.json` (part 6 option A)
- **Severity:** S2 · **Category:** correctness
- **Evidence:** Key: "The sails **reduced** the average midday surface temperature beneath them **by five degrees Celsius**…". The passage says: "the surface beneath the sails averaged five degrees Celsius cooler **than nearby exposed pavement** at midday."
- **Problem:** The passage compares two places at the same time, not before and after. "Reduced … by five degrees" is a causal before/after claim that the text does not make. The item's own instructions say to keep "every required fact and limitation", so a careful learner is penalised for noticing. The key is also the longest and most hedged option (1.5×).
- **Proposed correction:** A → "Under the sails, the midday surface averaged five degrees Celsius cooler than nearby exposed pavement, but the report could not prove this caused more people to use the entrance."

### er-l4-001 passage — A sensor held at one metre is reported as measuring surface temperature
- **Location:** `backend_resources/english/v1/passages/english-passage-cooler-school-route.json` P2–P3, P5
- **Severity:** S3 · **Category:** validity
- **Evidence:** "using the same sensor, held one metre above the ground for thirty seconds" vs "the exposed asphalt **surface** was eight degrees Celsius warmer than the **surface** under the trees". Part 6, rationale B, depends on the surface vs air distinction.
- **Problem:** A science-literate learner would read a sensor at 1 m as measuring air temperature, so the surface vs air contrast the item relies on is muddled.
- **Proposed correction:** "using the same infrared thermometer, pointed at the ground from one metre away for thirty seconds".

### er-l4-001 parts 1, 3 — Key is the only option that repeats the passage, and the hint names it
- **Location:** `backend_resources/english/v1/questions/er-l4-001.json` (parts 1, 3; hint part 1)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** P1 key: "To compare conditions along the route…". Hint: "Use the purpose clause beginning 'to compare'". P3 key: "Wet surfaces would be temporarily cooler and distort the comparison", which is nearly the passage's wording.
- **Problem:** Word-matching alone finds both keys, so a stated-evidence (ER5.4) item tests location, not paraphrase.
- **Proposed correction:** Paraphrase the keys ("To find out which parts of the walk were hottest and where shade would help"; "Wet ground cools for a while, so the readings would not be fair"). Take the quoted phrase out of the hint.

### er-l5-001 parts 1–2 — Two parts test the same stated sentence; part 1 key answers part 2
- **Location:** `backend_resources/english/v1/questions/er-l5-001.json` (parts 1, 2)
- **Severity:** S3 · **Category:** validity
- **Evidence:** P1 key: "…but their separate effects are unknown." P2 asks: "Why can the report not determine whether the new location or the picture signs contributed more…?" The passage says: "Because both changes were introduced together, the records could not show how much each one contributed."
- **Problem:** P2 is literal retrieval inside an inference (ER5.5) set, and P1's key already gives its answer.
- **Proposed correction:** Replace P2 with a real inference, e.g. "What does the 62 % → 86 % change most likely suggest about the first-night queues?", or ask which extra trial would separate the two changes.

### er-l5-002 passage / part 5 — "amplified phone calls"; garbled distractor
- **Location:** `backend_resources/english/v1/passages/english-passage-library-quiet-hour.json` P1; `questions/er-l5-002.json` part 5 option E
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "older visitors said that amplified phone calls made concentration difficult"; option E: "The library doors opened before some waiting visitors entered."
- **Problem:** "amplified phone calls" is unnatural (the meaning is speakerphone or loud calls). Option E is an awkward, trivially true restatement of the waiting-visitors scene. It is still a defensible distractor, but it reads as broken English.
- **Proposed correction:** "loud phone calls on speaker"; E → "Some visitors waited outside before the doors opened."

### er-l5-003 part 2 — "paragraph 3" points to the wrong paragraph in the practice player
- **Location:** `backend_resources/english/v1/questions/er-l5-003.json` (part 2); `passages/english-passage-harbour-voices-pair.json`
- **Severity:** S2 · **Category:** validity
- **Evidence:** Prompt: "Passage A: In paragraph 3, what does 'provisional' most nearly mean?" The `paragraphs` array is [ "PASSAGE A — A map made of sound", body1, body2, body3 (contains "provisional"), "PASSAGE B — …", … ]. The practice player labels these "PARAGRAPH 1…8".
- **Problem:** On screen, "provisional" sits under the label **PARAGRAPH 4**. PARAGRAPH 3 is "The first week showed why consistent methods matter…". The learner is sent to the wrong block.
- **Proposed correction:** Move the passage headings out of `paragraphs` (e.g. a `sections` field, or put them in the title) or skip them when numbering. Otherwise reword as "In the last paragraph of Passage A".

### er-l5-008 part 1 / er-l5-009 part 1 — Paragraph numbers ambiguous in protected checkpoints
- **Location:** `backend_resources/english/v1/questions/er-l5-008.json` (part 1); `er-l5-009.json` (part 1); pair passages `english-passage-checkpoint-rain-routes-pair.json`, `english-passage-checkpoint-night-journeys-pair.json`
- **Severity:** S2 · **Category:** validity
- **Evidence:** "Passage A: In paragraph 2, what does 'That pattern' refer to?" and "Passage A: In paragraph 2, who does 'It' in 'It repeated the riverside count' refer to?" The diagnostic player renders the "PASSAGE A — …" heading as a separate `<p>` with no numbers.
- **Problem:** Counting visible blocks, which is what practice-player users are trained to do since that player counts headings, puts "paragraph 2" on the first body paragraph. Neither target phrase is there. Quoting the phrase limits the damage, but a protected checkpoint should not have a misleading location.
- **Proposed correction:** Same structural fix as er-l5-003. Otherwise write "In the second paragraph of Passage A (beginning 'The first week…' / 'The first survey…')".

### er-l5-004 (whole set) — Difficulty 5 and an 18-minute target for a 203-word pair
- **Location:** `backend_resources/english/v1/questions/er-l5-004.json` (difficulty, instructions); `passages/english-passage-market-and-clocktower-pair.json`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "Use an eighteen-minute rehearsal target and answer both passages before checking." The passage is 203 words, versus 427 words for its parallel form er-l5-003. 15 of 16 key/option comparisons favour the longest option (8/8 keys are the longest, ratio 1.4–2.1×).
- **Problem:** As a parallel form for practising pacing (ER5.7), it is half the reading load in the same time, so it cannot rehearse pacing. With very short, cue-heavy options it is not a level-5 item either. "answer both passages" is also unidiomatic.
- **Proposed correction:** Expand each passage to about 200 words, or set a 10-minute target and difficulty 4. Instructions: "…and answer the questions on both passages before checking." Even out option lengths.

### er-l5-004 parts 5–8 — Near-copy of er-l5-003 Passage B; rationale assumes a first-person narrator; style drift
- **Location:** `backend_resources/english/v1/questions/er-l5-004.json` (parts 5–8; part 7 rationales)
- **Severity:** S3 · **Category:** validity
- **Evidence:** Both texts follow the same plot: a child dislikes a bell, a phone recording sounds "thin", and the child realises the bell carries communal meaning. In both, P7's key is "reflective and affectionate". P7 rationale A says "The narrator reassesses…", but the clocktower text is third person ("Suri"). Options are lower-case with no full stops, unlike er-l5-003.
- **Problem:** A learner who has done er-l5-003 can answer er-l5-004 parts 5–8 from memory. The feedback names a narrator who does not exist.
- **Proposed correction:** Give Passage B a different situation or insight. Change "narrator" to "Suri" in the rationales. Capitalise options to match house style.

### er-l5-005 (baseline) — Longest option is the key in all 5 parts, and keys repeat the passage
- **Location:** `backend_resources/english/v1/questions/er-l5-005.json` (parts 1–5)
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Key/average-distractor length ratios: P1 2.4×, P2 2.1×, P3 1.9×, P4 1.9×, P5 1.5×. P1 key: "…mistaken for a roof-colour effect" (passage: "mistaken for an effect of roof colour"). P4 key: "…make a limited comparison more trustworthy" (passage: "made the limited comparison more trustworthy"). The distractors are short absolutes ("Cloudy weather makes experiments impossible").
- **Problem:** Choosing the longest, hedged option scores 5/5 on the protected baseline without reading, which spoils the growth measure. The endline (er-l5-006) and reserve (er-l5-007) each have the longest option as the key in 4/5 parts.
- **Proposed correction:** Rewrite the distractors to the same length and level of hedging as the keys, and include at least one plausible but unsupported hedged distractor per item. Paraphrase the keys away from the passage's wording.

### er-l5-005 / er-l5-006 / er-l5-007 — "Matched" baseline and endline differ in difficulty and length
- **Location:** `backend_resources/english/v1/questions/er-l5-005.json` (difficulty 4, 163 words), `er-l5-006.json` (difficulty 3, 129 words), `er-l5-007.json` (difficulty 3, 129 words); `forms/english-endline-sec1-id-v1.json` ("English Core matched endline form A", paired with the baseline)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** `"difficulty": 4` (baseline) vs `"difficulty": 3` (endline and reserve).
- **Problem:** The endline reading set is labelled easier and is shorter than the baseline it is matched to, so it inflates measured reading gain.
- **Proposed correction:** Match difficulty, length and part types (both sets are reference, word meaning, main idea, inference and purpose). Either raise er-l5-006/007 to difficulty 4 with a passage of about 160 words, or re-label after checking the content really is matched.

### er-l5-005 / 006 / 007 — Single-passage diagnostics tagged ER5.7 (two-passage pacing)
- **Location:** `backend_resources/english/v1/questions/er-l5-005.json`, `er-l5-006.json`, `er-l5-007.json` (`outcome_code`)
- **Severity:** S3 · **Category:** validity
- **Evidence:** `"outcome_code": "ER5.7"` on a single 129–163-word passage with no timing instruction.
- **Problem:** These sets do not assess two-passage pacing, so any ER5.7 mastery reporting drawn from them is misleading.
- **Proposed correction:** Re-tag with a mixed or general reading code (or ER5.5/5.6), or make the diagnostics two short passages with a time target.

### er-l5-006 passage — "at the longest paths"
- **Location:** `backend_resources/english/v1/passages/english-passage-endline-mangrove-walkway.json` P2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Visitors rarely became confused at the longest paths"
- **Problem:** Wrong preposition with "paths".
- **Proposed correction:** "Visitors rarely became confused on the longest paths".

### er-l5-007 part 2 — Rationale wrongly calls the referent the "nearest" noun
- **Location:** `backend_resources/english/v1/questions/er-l5-007.json` (part 2, rationale B)
- **Severity:** S3 · **Category:** correctness
- **Evidence:** "The pronoun refers to the nearest relevant singular washing point." The passage says: "…lower at the washing point near the market entrance. Volunteers initially assumed that its location…"
- **Problem:** The nearest singular noun is "the market entrance", so the "nearest noun" rule taught here gives the wrong answer. The correct reasoning is about meaning and topic.
- **Proposed correction:** "'Its' refers to the washing point whose return rate was low; the entrance is only where that point is."

### er-l5-007 (reserve) vs er-l5-001 (exit ticket) — Overlapping content
- **Location:** `backend_resources/english/v1/passages/english-passage-reserve-reusable-bowls.json` vs `english-passage-container-return-experiment.json`
- **Severity:** S3 · **Category:** validity
- **Evidence:** Both texts share: a night or riverside market, six food stalls, a deposit, reusable bowls or containers, a return point whose location is blamed, and signs as the fix.
- **Problem:** Practising er-l5-001 gives learners a background advantage on the protected endline reserve.
- **Proposed correction:** Change the reserve topic (e.g. a library book-return box or a school lost-property trial).

### er-l5-008 part 2 — Same word and nearly the same key as the baseline; passage gives the key's wording
- **Location:** `backend_resources/english/v1/questions/er-l5-008.json` (part 2) vs `er-l5-005.json` (part 3)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Checkpoint key: "encouraging but not yet conclusive". The passage says: "described the improvement as promising rather than conclusive". The baseline asks the same word, "promising", and its key is "showing useful potential but not yet conclusive".
- **Problem:** The word was already tested at baseline, and the passage contains the key's distinguishing word ("conclusive").
- **Proposed correction:** Test a different word in the checkpoint (e.g. "persisted" or "recurring"), or remove "rather than conclusive" from the passage.

### er-l5-008 passage — "crossing Meranti School"
- **Location:** `backend_resources/english/v1/passages/english-passage-checkpoint-rain-routes-pair.json` P2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "After several pupils slipped while crossing Meranti School during heavy rain"
- **Problem:** People cross the grounds, not the school.
- **Proposed correction:** "while crossing the grounds of Meranti School".

---

## Slice summary

**Counts:** S1 = 5 · S2 = 9 · S3 = 16 (total 30 findings)

- **S1 (would mark a correct learner wrong):** er-l1-001 P4, er-l2-001 P2, er-l2-001 P3, er-l4-001 P2, er-l4-001 P5. All are short-text answer sets that leave out the passage's own wording or the most likely form of a correct answer. All five are in exit tickets.
- **S2:** er-l2-002 P5 (ambiguous "The devices"), er-l3-001/er-l3-002 (vocabulary level), er-l3-002 P6 (gives away P3), er-l4-001 P6 (key misparaphrases the result), er-l5-003 P2 (paragraph-number mismatch), er-l5-008 P1 + er-l5-009 P1 (paragraph numbering in checkpoints), er-l5-004 (difficulty and timing), er-l5-005 (longest-option cue across the baseline), er-l5-005/006/007 (unmatched baseline vs endline).

**Cross-cutting patterns**

1. **Clause-length short-text answers.** er-l1-001 P4 and er-l2-001 P3 ask for a whole event as free text under exact-match marking. They cannot be marked fairly. Use single choice for event/idea referents; keep short text for one-word or name answers, with full variant lists (Dr./Dr, metre/meter, numerals, articles).
2. **Longest or most hedged option is the key in 58 of 75 single-choice parts (77 %).** Rates by set: er-l5-004 8/8, er-l5-003 7/8, er-l5-005 5/5, er-l5-002 5/5, er-l3-002 5/6. Distractors are usually short absolutes ("always", "every", "proved", "guarantee"). The bank teaches "pick the cautious long answer". Rewrite distractors to the same length, including plausible hedged wrong answers.
3. **Topic and genre sameness.** About 13 of 19 passage texts are "students or a committee run a small trial and report its limits", and the right answer to main-idea and inference items is almost always the "promising but not conclusive" option. Both the practice sets and the exam reportedly need narrative and descriptive texts. Add more narrative and general informational passages, and vary the answer logic.
4. **Paragraph numbering in paired passages.** Heading lines are stored inside `paragraphs`. This affects er-l5-003, er-l5-004, er-l5-008 and er-l5-009. Fix this once in the data model or player, not item by item.
5. **Level fit for 11–12-year-old ESL learners.**
   - Vocabulary tests and glosses use C1 words: corroborated, cryptic, tentative, provisional, dormant, ambiguous, painstaking (er-l3-001, er-l3-002, er-l5-003).
   - Passages use research and method vocabulary: salinity, estuary, ecologist, median, consecutive, deferred, verge, soundscape, verdict (er-l2-001, er-l4-001, er-l5-001, er-l5-003).
   - Rationales use abstract metalanguage ("conditional, not definitional", "embodied communal experience", "self-selection").
   - Passage lengths (129–438 words) are fine. Concept density, mostly controls and confounds, is the main load.
6. **Hints that name the location or the answer** in practice sets: er-l2-001 P2, er-l3-001 P2/P5, er-l4-001 P1/P6 ("the words 'could not prove'"), er-l5-002 P3. This is low impact because using a hint fails mastery, and one click shows all hints in the group.
7. **Terse, boilerplate rationales in the retry-review parallel forms** (er-l2-002, er-l3-002, er-l5-004), e.g. "They are not preparing the trays.", "Neither endpoint fits." These are low severity.

**Timing of the two-passage sets.**
- er-l5-003: 427 words, 8 questions, 18 minutes. Realistic, slightly generous for able applicants.
- er-l5-008 and er-l5-009: about 430 words, 5 questions, 18 minutes. Generous, so they test pacing only weakly. Consider 12–14 minutes or 7–8 questions.
- er-l5-004: 203 words, 8 questions, 18 minutes. Not a credible pacing rehearsal (see S2 above).

**Sound with no or only minor issues:**
- er-l1-001 parts 1, 2, 3, 6
- er-l2-001 parts 1, 4, 5, 6
- er-l2-002 parts 1–4, 6
- er-l3-001 parts 3, 6
- er-l4-001 part 4
- er-l5-001 parts 3–6
- er-l5-002 parts 1–4, 6
- er-l5-003 parts 1, 3–8 (apart from the length cue)
- er-l5-006 parts 1–5
- er-l5-007 parts 1, 3–5
- er-l5-008 parts 3–5
- er-l5-009 parts 2–5

In all of these I found no wrong keys and no second defensible answer.
