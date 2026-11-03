# Slice B — Banked cloze (eb-*) and open cloze (eo-*) findings

Scope: 7 banked-cloze items (eb-l1-001…007) and 14 open-cloze items (eo-l1-001…eo-l5-007) with their passages.
Method: each banked passage was solved from the bank before reading the key, testing every bank word (including surplus words) at every gap and checking two-word swaps across the whole bank. For each open-cloze gap I listed every one-word answer a competent writer could defend, and compared that list with `canonical_answer` + `accepted_alternatives`. Pool membership was checked against `forms/*.json` and the lesson `question_keys`.
Level-fit note: following the audit level-fit basis, level fit is judged for the `secondary_1_entry` profile (final primary year, about 11–12, ESL).

Convention for open cloze: an alternative is marked **S1** when it is genuinely correct both in the passage and under the visible prompt, so a learner who writes it is marked wrong. When the alternative is ruled out only because the prompt names the word class or meaning, I treat that as prompt leakage. Those alternatives are listed as "conditional": they must be added once the prompt is de-leaked.

---

## Banked cloze

### eb-l1-003 part 1 — Keyed "bare" contradicts the passage (no correct bank word exists)
- **Location:** `backend_resources/english/v1/questions/eb-l1-003.json` (part 1 / gap 1 / option A); passage `passages/english-passage-baseline-club-noticeboard.json` P1
- **Severity:** S1 · **Category:** correctness
- **Evidence:** "the environmental club found its noticeboard unusually {{1}}. Posters from the previous term still covered every corner, so new announcements were difficult to see." Key A = "bare". Rationale A: "“bare” is an adjective showing the board had too little free space."
- **Problem:** "Bare" means empty, which is the opposite of a board covered in old posters. The rationale gives "bare" a meaning it does not have. No other bank word (bare, explained, sorted, scattered, proud, quietly, repaired, ordinary) fits either, so a competent learner cannot answer correctly. The item is in the baseline diagnostic form (`forms/english-baseline-sec1-id-v1.json`).
- **Proposed correction:** Replace option A "bare" with "cluttered" (or "crowded"). Rationale A becomes: "“Cluttered” describes a surface covered untidily with too many papers." Do not add "bare" back as a distractor, because it would then be a tempting near-antonym trap in a diagnostic.

### eb-l1-002 part 1 — "calmly" fits gap 1 as well as "early"
- **Location:** `backend_resources/english/v1/questions/eb-l1-002.json` (part 1 / gap 1 / options A, I); passage `english-passage-community-garden-opening` P1
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "On Saturday, Nara arrived {{1}} at the community garden. Volunteers had {{2}} beside the tool shed…" Key A "early". Bank also contains I "calmly".
- **Problem:** "Nara arrived calmly at the community garden" is grammatical and fits the story: nothing before the gap rules it out, and "calmly" is not needed at any other gap. The past perfect "Volunteers had gathered" actually shows that others got there first, which weakens the case for "early". The surplus-word solution {1: calmly} leaves a fully valid passage.
- **Proposed correction:** Rewrite as "On Saturday, Nara reached the community garden {{1}} in the morning, an hour before the gates opened." and replace distractor "calmly" with a non-adverb such as "heavy". Rationale I can then say "an adverb of manner cannot follow 'reached the garden' and precede 'in the morning'".

### eb-l1-001 part 3 (and part 2) — "whispered" is a valid reporting verb at gap 3 and a valid rain verb at gap 2
- **Location:** `backend_resources/english/v1/questions/eb-l1-001.json` (parts 2–3 / option K); passage `english-passage-afternoon-broadcast` P1–P2
- **Severity:** S2 · **Category:** ambiguity
- **Evidence:** "Mr Lim {{3}} that a loose cable had stopped the microphones." Rationale K for gap 3: "Gap 3 needs a past-tense reporting verb … “whispered” does not satisfy both the grammar and story context." Also "while rain {{2}} against the windows".
- **Problem:** "Mr Lim whispered that a loose cable had stopped the microphones" is a grammatical past-tense reporting verb with an acceptable meaning, and "explained" is not needed elsewhere. So the bank has two whole-passage solutions, and the rationale's claim that the grammar fails is false. At gap 2, "rain whispered against the windows" is a familiar literary image. The passage never says the rain is heavy; only the hint does.
- **Proposed correction:** Replace distractor "whispered" with a word that fails grammatically, e.g. "shivered". Make gap 2 explicit: "while heavy rain {{2}} against the windows".

### eb-l1-001 part 1 — Studio is "deserted" while Mr Lim is in it
- **Location:** `backend_resources/english/v1/passages/english-passage-afternoon-broadcast.json` P1; question part 1 (key C)
- **Severity:** S2 · **Category:** validity
- **Evidence:** "she arrived to find the studio unusually {{1}}. The presenter, Mr Lim, stood beside a silent mixing desk…"
- **Problem:** The keyed answer "deserted" (= no people there) is contradicted by the very next sentence. A careful reader who checks the whole passage, which is the skill the lesson teaches, may reject the key. The worked example in `lessons/e3-lesson-01.json` ("favours a word describing an empty place") repeats the inconsistency.
- **Proposed correction:** "…she arrived to find the studio almost {{1}}: only the presenter, Mr Lim, was there, standing beside a silent mixing desk while heavy rain {{2}} against the windows." Alternatively, change the target word to "quiet" and keep the sentence.

### eb-l1-006 part 1 — Rooftop "deserted" yet Ms Hana is present; explanation says Rafi was alone
- **Location:** `backend_resources/english/v1/questions/eb-l1-006.json` (part 1, correct_explanation); passage `english-passage-checkpoint-rooftop-eclipse` P1–P2
- **Severity:** S2 · **Category:** validity
- **Evidence:** "found the rooftop unusually {{1}} … no other member had arrived" / "Ms Hana {{2}} that the key had gone home… While she telephoned him" / Explanation: "the whole-story clue that Rafi was alone."
- **Problem:** Ms Hana is on the scene, so Rafi was not alone. The explanation contradicts the passage, and the passage repeats the "deserted but occupied" flaw from eb-l1-001 in a protected checkpoint.
- **Proposed correction:** P2: "When Ms Hana arrived a few minutes later, she {{2}} that the key…". Explanation: "‘Deserted’ fits because no other member had arrived when Rafi reached the rooftop."

### eb-l1-006 part 1–3 — Checkpoint is a near-copy of the exit ticket and lesson worked example
- **Location:** `backend_resources/english/v1/questions/eb-l1-006.json` (gaps 1–2, bank) vs `eb-l1-001.json` gaps 1, 3 and `lessons/e3-lesson-01.json` worked_analysis
- **Severity:** S2 · **Category:** leakage
- **Evidence:** eb-l1-006: "found the rooftop unusually {{1}}" = deserted; "Ms Hana {{2}} that the key had gone…" = explained. eb-l1-001: "find the studio unusually {{1}}" = deserted; "Mr Lim {{3}} that a loose cable…" = explained. Lesson: "For “the studio was unusually ___” … favours a word describing an empty place." Four of eight eb-l1-006 bank words (deserted, explained, postponed, wandered) also appear in the eb-l1-001 bank.
- **Problem:** The protected checkpoint repeats the same frames with the same answers that were practised in the lesson and the exit ticket. That rewards recall rather than transfer.
- **Proposed correction:** Give the checkpoint a different opening frame and different target words (e.g. "the rooftop was strangely {{1}}" → "silent"), and cut the shared bank words to at most one.

### eb-l1-001 part 1–8 — Exit ticket is pre-solved in the lesson worked example
- **Location:** `backend_resources/english/v1/lessons/e3-lesson-01.json` (section 3 worked_analysis) vs `questions/eb-l1-001.json` gaps 1, 4
- **Severity:** S2 · **Category:** leakage
- **Evidence:** Lesson: "Example map: setting—community radio station during a storm; characters—Maya, a presenter and an electrician … For “the studio was unusually ___” … For “the programme would be ___ unless…” … a delayed event". The exit ticket uses the same passage.
- **Problem:** The lesson walks through the exit-ticket passage and two of its gaps, so the exit ticket is not an independent check.
- **Proposed correction:** Base the worked analysis on a different short story, or move eb-l1-001 to guided practice and write a fresh exit-ticket passage.

### eb-l1-005 parts 2–5 — Rationales name "Silently", which is not in the bank (bank has "quietly")
- **Location:** `backend_resources/english/v1/questions/eb-l1-005.json` (parts 2–5 / option G choice_rationales)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** Option G text "quietly"; rationales: "Silently cannot be the main verb." / "Silently lacks a main verb." / "Silently is an adverb."
- **Problem:** The rationales were copied from eb-l1-004, whose bank has "silently". Learners see feedback about a word they were never offered.
- **Proposed correction:** Replace "Silently" with "Quietly" in all four rationales.

### eb-l1-005 part 3 — "labelled each box by size and period" is an unnatural collocation; other passage wording
- **Location:** `backend_resources/english/v1/passages/english-passage-reserve-costume-library.json` P1–P2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Her team {{3}} each box by size and period" (key "labelled"); "Boxes … had been returned without any order."
- **Problem:** You sort or arrange *by* a category, but you label *with* information, so "labelled … by" reads like a sorting verb was intended. "Without any order" is ambiguous (it could mean without an order form).
- **Proposed correction:** "Her team {{3}} each box with its size and period"; "…had been returned in no particular order."

### eb-l1-004 part 4 — "the most borrowed tapes" is a weak but grammatical alternative
- **Location:** `backend_resources/english/v1/questions/eb-l1-004.json` (part 4 / option H)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** "placed the most {{4}} tapes in protective cases" — key "fragile"; bank includes "borrowed".
- **Problem:** "The most borrowed tapes" is a natural phrase, and protecting heavily used items makes sense. Only the absence of any lending in the story rules it out (rationale: "Borrowed does not explain protection"). This is low risk, but the item is in the endline form.
- **Proposed correction:** Swap distractor "borrowed" for a non-participle adjective that cannot follow "most" here, e.g. "sudden".

### eb-l1-006 part 3 — "wandered" across the sky is marginally defensible
- **Location:** `backend_resources/english/v1/questions/eb-l1-006.json` (part 3 / option H)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** "dark clouds {{3}} across the sky, leaving the club less time to prepare." Key "drifted"; bank has "wandered" (and "hurried", which is needed at gap 4).
- **Problem:** "Clouds wandered across the sky" is a recognised literary image. The rationale itself only calls it "less precise", which concedes that it is not wrong.
- **Proposed correction:** Replace "wandered" with a clearly impossible verb (e.g. "whispered"), or add a cue: "dark clouds slowly {{3}} across the sky".

### eb-l1-001 part 1–8 — Hints state the answer's meaning; rationales falsely claim grammar fails
- **Location:** `backend_resources/english/v1/questions/eb-l1-001.json` (hints parts 1, 2, 5, 6) and choice_rationales; same pattern in `eb-l1-002.json`
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Hint 1: "describes the empty studio"; hint 5: "makes Maya worried"; hint 6: "freely offers to help"; eb-l1-002 hint 1: "an adverb showing that Nara arrived before the expected time". Distractor template: "“wandered” does not satisfy both the grammar and story context" (wandered *is* a past-tense verb, as gap 2 requires).
- **Problem:** One click reveals all eight hints, and each is a near-definition of the key. The distractor rationales are boilerplate and often say the grammar fails when only the meaning fails. eb-l1-002 rationales are also ungrammatical ("“gathered” does not satisfy an adverb…").
- **Proposed correction:** Make hints point to evidence ("Look at what Mr Lim is standing beside and at the next sentence") rather than define the answer. Write distractor rationales that say whether the word fails on form or on meaning.

### eb-l1-001 part 4 — Title/time inconsistency
- **Location:** `backend_resources/english/v1/passages/english-passage-afternoon-broadcast.json` P1–P2
- **Severity:** S3 · **Category:** validity
- **Evidence:** Title "The afternoon broadcast"; "One afternoon … The evening programme would be {{4}}".
- **Problem:** The programme at risk is the evening one, not the afternoon broadcast in the title.
- **Proposed correction:** Retitle "The evening broadcast", or change the text to "The afternoon programme".

### eb-l1-002 — Minor wording
- **Location:** `backend_resources/english/v1/passages/english-passage-community-garden-opening.json` P2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "delayed by a broken lorry"
- **Problem:** The natural British phrase is "a broken-down lorry".
- **Proposed correction:** "delayed by a broken-down lorry".

### eb-l1-003 part 2 — "explained that the board should be reorganised"
- **Location:** `backend_resources/english/v1/questions/eb-l1-003.json` part 2
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "Mina {{2}} that the board should be reorganised" — key "explained"; rationale: "reporting verb introducing Mina's reasoned proposal".
- **Problem:** A proposal with "should" calls for "suggested" or "proposed". "Explained" is acceptable but not the most natural verb, and the parallel forms eb-l1-004/005 use proposed/suggested.
- **Proposed correction:** Replace option B with "suggested", or keep "explained" and add a reason clause: "Mina {{2}} why the board should be reorganised".

---

## Open cloze

### eo-l5-002 part 6 — Keyed "again" makes the sentence ungrammatical
- **Location:** `backend_resources/english/v1/questions/eo-l5-002.json` (part 6); passage `english-passage-ridge-weather-station` P3
- **Severity:** S1 · **Category:** correctness
- **Evidence:** "He checked the reading {{6}} the class left and wrote down the repair time." Canonical "again"; prompt "show that Arun repeated the check."
- **Problem:** "He checked the reading again the class left" is ungrammatical, because the gap must hold a subordinator before the clause "the class left". The passage also records no earlier check by Arun, so "again" has no anchor. The lesson's own rule (`e4-lesson-05`: "again … becomes secure only when an earlier sentence records the first count") rejects it.
- **Proposed correction:** Either key "before" (accept "before"; consider "as", "when"; prompt "show when Arun checked the reading in relation to the class leaving"). Or rewrite: "He had checked the reading at the start of the day, so he checked it {{6}} before the class left" → "again".

### eo-l5-003 part 5 — Prompt points to the wrong answer; valid alternatives unlisted
- **Location:** `backend_resources/english/v1/questions/eo-l5-003.json` (part 5); passage `english-passage-baseline-cycle-library` P2
- **Severity:** S1 · **Category:** correctness
- **Evidence:** Prompt: "mark the time before which the second check occurred." Passage: "checked every bicycle before it was lent out and again {{5}} it was returned." Key "after"; alternatives [].
- **Problem:** The prompt says the check happened *before* the time marked, which steers learners to "before". In a baseline diagnostic that is the opposite of the key. "when", "once" and "as" ("and again when it was returned") are also fully correct and not accepted.
- **Proposed correction:** Prompt: "Gap 5: show when the second check happened." Add `accepted_alternatives`: ["when", "once", "as"].

### eo-l5-003 part 3 — Determiners fill "worried ___ bicycles" (complementiser "that" is optional)
- **Location:** `backend_resources/english/v1/questions/eo-l5-003.json` (part 3)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "The organisers had worried {{3}} bicycles would be returned late" — key "that", alternatives [].
- **Problem:** "that" can be omitted, so "had worried some/many/the/their bicycles would be returned late" are all grammatical and natural. The prompt ("complete the clause") does not exclude them. This is a baseline diagnostic.
- **Proposed correction:** Accept ["that", "some", "many", "the", "their"], or rebuild the gap so "that" is required and no determiner can fit: "The organisers' main worry was {{3}} the bicycles would be returned late" (after "was … the", only "that" fits).

### eo-l5-003 part 4 — "yet/although/though/while/whereas" all correct
- **Location:** `backend_resources/english/v1/questions/eo-l5-003.json` (part 4)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "…would be returned late, {{4}} most borrowers followed the schedule carefully." Key "but", alternatives [].
- **Problem:** Every listed contrast connector is grammatical here, and each is "a conjunction contrasting the concern with actual behaviour".
- **Proposed correction:** `accepted_alternatives`: ["yet", "although", "though", "while", "whilst", "whereas"].

### eo-l5-002 parts 2, 3, 4, 7 — Several valid unlisted answers in the retry form
- **Location:** `backend_resources/english/v1/questions/eo-l5-002.json` (parts 2, 3, 4, 7)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** P2 "{{2}} the lower path seemed sheltered, Leena still measured…" (key although, alts []). P3 "so that one record would not be confused with {{3}}" (another, []). P4 "found a sensor hanging {{4}} after its fastening had shifted" (loose, []). P7 "comparable only {{7}} every group used the same five-minute interval" (if, []).
- **Problem:** The following answers are genuinely correct but unlisted: P2 "though", "while", "whilst" (eo-l1-001 and eo-l5-004 do accept "though", so the bank is inconsistent); P3 "others"; P4 "free", "loosely", "down", "awkwardly", "precariously", because the passage does not constrain the adverb; P7 "when", "once".
- **Proposed correction:** P2 alts ["though", "while", "whilst"]; P3 alts ["others"]; P4: rewrite to force the collocation, e.g. "its fastening had worked {{4}}", and accept ["loose", "free"]; P7 alts ["when", "once"].

### eo-l1-002 parts 2, 5, 7, 8 — Unlisted valid answers in the parallel form
- **Location:** `backend_resources/english/v1/questions/eo-l1-002.json` (parts 2, 5, 7, 8); passage `english-passage-library-photo-exhibition`
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** P2 "{{2}} contained images of the town" (it, []); P5 "labelled with a date and place, {{5}} several names had faded" (although, []); P7 "He waited {{7}} they identified the missing people" (until, []); P8 "recorded what {{8}} remembered" (they, []).
- **Problem:** P2 "This" is a pronoun referring to the envelope, so it is valid even under the prompt (eo-l4-001 accepts This/That). P5 "but", "yet", "though", "while", "whilst" are all contrast conjunctions. P7 "till" is accepted in eo-l1-001 and eo-l1-003 but not here, which contradicts the lesson rule ("until and till … must name both", e4-lesson-01). "while" is conditional on the prompt. P8 "residents"/"people" are plural subjects referring to the former residents (S2).
- **Proposed correction:** P2 alts ["this"]; P5 alts ["but", "yet", "though", "while", "whilst"]; P7 alts ["till"]; P8 alts ["residents", "people"]. Also replace "the missing people" with "the unnamed people" (S3: it reads as "missing persons").

### eo-l1-001 part 5 — "while/whilst" unlisted
- **Location:** `backend_resources/english/v1/questions/eo-l1-001.json` (part 5)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "{{5}} the paper was fragile, the writing was still clear." Alts ["though"].
- **Problem:** Concessive "While" (and British "Whilst") is standard and is "a conjunction that contrasts", so it fits the prompt.
- **Proposed correction:** `accepted_alternatives`: ["though", "while", "whilst"].

### eo-l5-004 part 3 (and parts 1, 4, 5) — Endline alternatives
- **Location:** `backend_resources/english/v1/questions/eo-l5-004.json` (parts 1, 3, 4, 5); passage `english-passage-endline-rain-gauges`
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** P3 "{{3}} the students used identical containers, the readings sometimes differed greatly." (although, ["though"]); P4 "Each team checked {{4}} gauge at the same time every morning" (its, ["their"]); P1 "built {{1}} inexpensive rain gauge for each of five neighbourhoods"; P5 "compared the records {{5}} presenting its findings".
- **Problem:** P3: "While"/"Whilst" are correct and unlisted (S1). P4: "the" is a correct determiner ("Each team checked the gauge…"), excluded only by the prompt's "its own" (S2). Two answers are excluded only by the leaky prompts and must be added if those prompts are fixed: P1 "one" and P5 "when"/"while".
- **Proposed correction:** P3 alts ["though", "while", "whilst"]; P4 alts ["their", "the"]; after de-leaking, P1 alts ["one"] and P5 alts ["when", "while"] (or make P5 unambiguous: "…the records {{5}} it presented its findings a week later").

### eo-l3-001 parts 2 and 4 — "care/control" and "standstill" unlisted
- **Location:** `backend_resources/english/v1/questions/eo-l3-001.json` (parts 2, 4); passage `english-passage-rehearsal-rescue` P1–P2
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "Mei agreed to take {{2}} of the new schedule" (charge, []); "the performance came to a {{4}}" (halt, ["stop"]).
- **Problem:** P2: "take care of" and "take control of" both mean accepting responsibility for something, which matches the prompt's own gloss; "take ownership of" is also used. P4: "came to a standstill" is the most frequent of all these collocations.
- **Proposed correction:** P2 alts ["care", "control", "ownership"] (or change the frame to "take {{2}} for" → "responsibility"); P4 alts ["stop", "standstill"].

### eo-l4-001 part 4 — "later/afterwards" unlisted in "Only ___ did he notice"
- **Location:** `backend_resources/english/v1/questions/eo-l4-001.json` (part 4)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "Farid tested the battery and speaker before tracing the internal wires. Only {{4}} did he notice a loose connection" (then, []).
- **Problem:** "Only later did he notice" and "Only afterwards did he notice" both follow the sequence of tests, which is what the prompt asks for, and both trigger inversion correctly.
- **Proposed correction:** `accepted_alternatives`: ["later", "afterwards"].

### eo-l2-001 part 3 — Key repeats "checks"; other verbs fit the prompt
- **Location:** `backend_resources/english/v1/questions/eo-l2-001.json` (part 3); passage `english-passage-rooftop-garden-record` P2
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "the club leader checks the watering chart and {{3}} the weather forecast." Key "checks"; prompt: "use the present-tense form that matches “the club leader” and parallels “checks”."
- **Problem:** The keyed sentence repeats "checks … and checks", which a careful writer avoids. "reads", "studies", "consults", "reviews" and "monitors" are present-tense forms that match the subject and parallel "checks", so they are correct under the prompt as worded. Unlike the other gaps, no different-form anchor is transformed here.
- **Proposed correction:** Either accept ["reads", "studies", "consults", "reviews", "examines", "monitors"], or redesign so a real anchor changes form, e.g. "Last term the leader only studied the chart; now she also {{3}} the weather forecast (study)" → "studies", with the base word shown explicitly.

### eo-l5-001 part 2 — "although/though" unlisted
- **Location:** `backend_resources/english/v1/questions/eo-l5-001.json` (part 2)
- **Severity:** S1 · **Category:** ambiguity
- **Evidence:** "The water looked clear, {{2}} Aisha still collected a sample for testing." Alts ["yet"]. Rationale: "the two independent clauses require a coordinating contrast".
- **Problem:** "The water looked clear, although/though Aisha still collected a sample" is standard English. The rationale's claim that a coordinator is required is wrong.
- **Proposed correction:** alts ["yet", "although", "though"]; rationale: "A contrast connector is needed; but, yet, although and though all work."

### eo-l5-001 part 7 / eo-l5-006 part 2 — "until" is also correct
- **Location:** `backend_resources/english/v1/questions/eo-l5-001.json` (part 7); `eo-l5-006.json` (part 2)
- **Severity:** S2 · **Category:** ambiguity
- **Evidence:** "Ms Tan insisted that the data would be useless {{7}} every group used the same method." / "the digital inventory would be unreliable {{2}} every group used the same numbering method." Key "unless", alts [].
- **Problem:** "useless/unreliable until every group used the same method" is grammatical and meaningful: it says the data stays unusable up to the point of standardisation. In eo-l5-006 the gap is one of only two in a protected checkpoint.
- **Proposed correction:** Accept "until", or force the conditional reading: "would be useless {{7}} every group used the same method, even if each reading looked accurate". Consider "even if" in the passage but keep the gap at "unless".

### eo-l5-001 part 4 — "free" fits "worked ___"
- **Location:** `backend_resources/english/v1/questions/eo-l5-001.json` (part 4)
- **Severity:** S2 · **Category:** ambiguity
- **Evidence:** "one plank had worked {{4}} in the rain" (loose, []).
- **Problem:** "work free" is an established collocation for something gradually becoming unfastened, and it matches the prompt ("a plank that has become unsecured").
- **Proposed correction:** alts ["free"].

### Open-cloze prompt leakage — diagnostics, reserve and checkpoints (one finding per item)

#### eo-l5-003 parts 1–5 — Baseline prompts name the word class and the referent
- **Location:** `backend_resources/english/v1/questions/eo-l5-003.json` (part prompts)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "supply the article required before “bicycle library”"; "supply the pronoun referring to registered members"; "supply the conjunction contrasting the concern with actual behaviour".
- **Problem:** Naming "article" + consonant-initial noun, or "pronoun" + plural referent, reduces open cloze to choosing from two or three words. The baseline then measures prompt-following, not the EO skill. For 11–12-year-olds the metalanguage ("article", "conjunction") is also a reading load.
- **Proposed correction:** Use neutral prompts in all protected forms: "Gap N: enter one word." If a per-gap prompt is required, describe only the location ("the word before ‘bicycle library’").

#### eo-l5-004 parts 1–5 — Endline prompts state the answer
- **Location:** `backend_resources/english/v1/questions/eo-l5-004.json`
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "supply the indefinite article required before “inexpensive rain gauge”" (→ an); "supply the relative pronoun linking the locations…" (→ which/that); "supply the preposition marking the comparison as earlier than the presentation" (→ before).
- **Problem:** "Indefinite article" before a vowel sound has exactly one answer, and "earlier than" is simply a definition of "before". The endline cannot measure growth with these prompts.
- **Proposed correction:** "Gap N: enter one word." Add the alternatives listed above once the prompts are neutral.

#### eo-l5-005 parts 1–5 — Reserve prompts state the answer
- **Location:** `backend_resources/english/v1/questions/eo-l5-005.json`
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "supply the indefinite article required before “map”"; "supply the relative word referring to places used during lunch" (→ where); "supply the determiner showing that all groups individually used the same symbols" (→ each/every); "showing that reviewing observations happened earlier than making recommendations" (→ before).
- **Problem:** The same issue as the endline, in the protected reserve.
- **Proposed correction:** Neutral prompts. Once neutral, P5 needs alts ["when", "while"] or a passage rewrite that forces "before"; P3 may accept "for" (formal causal, S3).

#### eo-l1-003 parts 1–3 — Checkpoint prompts give the answer
- **Location:** `backend_resources/english/v1/questions/eo-l1-003.json`
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "supply the article required before ‘note’ when it is first introduced" (→ a); "supply the relative pronoun referring to Mr Sadiq after the comma" (→ who); "complete the time span beginning ‘from nine o’clock’ and ending when Mr Sadiq returned" (→ until).
- **Problem:** Each prompt states the word class plus the deciding rule (first mention + consonant; person + comma; time-span end point).
- **Proposed correction:** "Gap N: enter one word."

#### eo-l1-004 parts 1–3 — Checkpoint prompts give the answer
- **Location:** `backend_resources/english/v1/questions/eo-l1-004.json`
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "supply the object pronoun referring to Sara after ‘asked’" (→ her); "complete the passive past-perfect phrase before ‘been sent’" (→ had); "complete the fixed pattern ‘consisted ___ six charcoal sketches’".
- **Problem:** Naming "object pronoun referring to Sara" or "past-perfect" leaves one possible word. If de-leaked, P1 should also accept "Sara" (eo-l4-001 accepts a proper name) (S3).
- **Proposed correction:** Neutral prompts; P1 alts ["Sara"] after de-leaking.

#### eo-l5-006 part 1 — Checkpoint prompt gives "again"; without it, many adverbs fit
- **Location:** `backend_resources/english/v1/questions/eo-l5-006.json` (part 1)
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "At the first stop, he counted them {{1}} after noticing that one securing strap had loosened." Prompt: "show that Niko repeated the box count recorded before departure."
- **Problem:** The prompt defines "again". With a neutral prompt the gap has many valid answers ("immediately/soon/shortly/right/just/only/straight after noticing"), so the gap is determinate only because of the leak.
- **Proposed correction:** Use the neutral prompt "Gap 1: enter one word." Move the gap away from "after" so that intensifiers cannot fill it: "At the first stop, one securing strap had loosened, so he counted the boxes {{1}}." Key "again"; review alts (e.g. "twice", "carefully") before release.

#### eo-l5-007 parts 1–2 — Checkpoint prompts give the answer
- **Location:** `backend_resources/english/v1/questions/eo-l5-007.json`
- **Severity:** S1 · **Category:** leakage
- **Evidence:** "show that Omar repeated the photograph from the marked position" (→ again); "complete the earlier action in the ‘By the time’ sequence" (→ had).
- **Problem:** The prompts define "again" and signal the past perfect. Without them, P1 also accepts "carefully" and other adverbs ("photographed it carefully from exactly the same position").
- **Proposed correction:** Neutral prompts. For P1, either accept a reviewed adverb set or rewrite so that only repetition fits ("he returned to the marked spot and photographed the footbridge {{1}}." with the following clause removed).

### Open-cloze prompt leakage — exit tickets and retry pools

#### eo-l1-001 parts 1–8 — Prompts name word class and form
- **Location:** `backend_resources/english/v1/questions/eo-l1-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** "enter the article required before “unopened wooden box”"; "enter the auxiliary that completes the past-perfect verb phrase"; "enter the relative word required after the comma"; "enter the pronoun that refers to the letters".
- **Problem:** Each prompt converts the gap to recall of a closed set. The passage alone leaves several gaps open, and only the prompt closes them: P2 "anything" ("asked us not to touch anything"); P3 any adverb ("nobody knew who originally/first packed it"); P8 "these"/"each". The exit ticket is also near-copied by the e4-lesson-01 worked analysis ("Nobody knew who ___ packed it", "the concert, ___ had taken place").
- **Proposed correction:** Neutral prompts. Tighten P3 so an adverb cannot fit ("nobody knew who {{3}} packed it so carefully years before"), or accept the adverbs. P2 alts ["anything"]; consider P4 "by"; P8 alts ["these", "each"]. Change the lesson's worked examples to a different passage.

#### eo-l2-001 parts 1–8 — Every prompt names the base word and the exact form
- **Location:** `backend_resources/english/v1/questions/eo-l2-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** "use the past-tense form of “meets”"; "use the plural form of “planter”"; "use the comparative form of “bright”"; "use the reflexive pronoun that agrees with the plural noun “students”".
- **Problem:** This is a word-formation drill presented as open cloze. EO4.2 should test whether learners notice which form the context demands. Without the prompts the gaps are lexically open (P4 "flowed/seeped/soaked", P5 "sunnier/warmer", P6 "progress/success", P7 "readings/records/observations"), so the item depends on the prompt to have a single answer.
- **Proposed correction:** Either relabel it as a word-formation task with the base word shown in capitals beside each gap and no form name, or keep open cloze and target function/agreement words that the passage alone determines.

#### eo-l4-001 parts 1–8 — Prompts name class and referent, which defeats the EO4.4 cohesion skill
- **Location:** `backend_resources/english/v1/questions/eo-l4-001.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** "use the possessive determiner that continues the reference to Mr Lee" (→ his); "use a plural object pronoun that refers to the lamp owners" (→ them); "use a singular object pronoun that refers to the shared notebook" (→ it); "show that Farid repeated the action" (→ again).
- **Problem:** The outcome is cross-sentence reference tracking, and the prompt does the tracking for the learner. The worked analysis in e4-lesson-04 also reproduces gaps 1, 2, 3, 4 and 6 almost verbatim ("This encouraged the waiting visitors", "Only then did he notice the loose wire"). With neutral prompts, P7 "this", P8 "them" and P1 "he" become defensible and must be reviewed.
- **Proposed correction:** Neutral prompts; give the lesson a different passage. After de-leaking, P7 alts ["this"] and P8 alts ["them"], or rewrite so the referent is forced. See the level-fit section for the "Only then did he…" inversion.

#### eo-l5-001 parts 1, 5, 6, 8 / eo-l5-002 parts 1, 5, 6, 8 — Form-naming prompts, and checkpoints near-copy these items
- **Location:** `backend_resources/english/v1/questions/eo-l5-001.json`, `eo-l5-002.json`, `eo-l5-006.json`, `eo-l5-007.json`; `lessons/e4-lesson-05.json`
- **Severity:** S2 · **Category:** leakage
- **Evidence:** eo-l5-001: "complete the fixed verb–preposition pattern…"; "show that Ben repeated an action…"; "complete the earlier action in the “By the time” sequence with the correct auxiliary". Checkpoint eo-l5-006: "would be unreliable {{2}} every group used the same numbering method" vs eo-l5-001 "would be useless {{7}} every group used the same method" vs e4-lesson-05 "the data would be useless ___ every group used the same method". eo-l5-007: "By the time the last volunteers arrived, the water level {{2}} fallen" vs eo-l5-001 "By the time the sun appeared, the wind {{8}} fallen".
- **Problem:** The two E4 checkpoints reuse the exact frames, answers and nearly the same prompts as the exit ticket, the retry form and the lesson worked example (again / unless / had). They measure memory of those items.
- **Proposed correction:** Write new checkpoint frames (e.g. a different conditional such as "as long as", a different past-perfect trigger such as "already … when"), and use neutral prompts.

#### eo-l3-001 parts 1–8 — Prompts gloss each idiom's meaning
- **Location:** `backend_resources/english/v1/questions/eo-l3-001.json`
- **Severity:** S3 · **Category:** leakage
- **Evidence:** "complete the fixed expression meaning “with little warning”: at short ___"; "complete the expression meaning “decided”: made up their ___".
- **Problem:** The prompts remove the need to read the context, leaving pure idiom recall. The e4-lesson-03 worked analysis also pre-teaches gaps 1, 2, 4 and 7 with the same frames.
- **Proposed correction:** Prompts "Gap N: enter one word"; move the meaning glosses to the practice hint; give the lesson different examples.

### eo-l3-001 parts 5–6 — Borderline variants
- **Location:** `backend_resources/english/v1/questions/eo-l3-001.json` (parts 4–6)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** "on the {{5}} of cancelling" (verge, brink, point); "made up their {{6}}" (minds); "Halfway through the rehearsal … the performance came to a {{4}}".
- **Problem:** "edge" is used in this frame, though less idiomatically. Collective "made up their mind" occurs, and the hint stresses that the actors decided *together*. The passage calls the rehearsal a "performance".
- **Proposed correction:** Consider alts ["edge"] and ["mind"]; change "the performance came to a" to "the rehearsal came to a".

### eo-l4-001 parts 1–3 — Minor alternative risk
- **Location:** `backend_resources/english/v1/questions/eo-l4-001.json` (parts 1–3)
- **Severity:** S3 · **Category:** ambiguity
- **Evidence:** "{{1}} arrived first and unlocked the hall. He then…" (Farid); "{{2}} encouraged the waiting visitors" (This/That); "{{3}}, the next visitor brought…" (However/Yet/Instead).
- **Problem:** "He" is grammatical at P1 (it is the only male referent), and the prompt's "identify who" is the only thing excluding it. "It" and "Success" are possible at P2; "Unfortunately" and "But" at P3.
- **Proposed correction:** Keep the keys. Add "Unfortunately" only if the prompt says "show the outcome went against expectations", otherwise leave as is.

---

## Level fit and difficulty labels

### eo-l1-003, eo-l1-004, eo-l5-006, eo-l5-007 — Checkpoint difficulty labels inflated
- **Location:** `backend_resources/english/v1/questions/eo-l1-003.json`, `eo-l1-004.json` (difficulty 4), `eo-l5-006.json`, `eo-l5-007.json` (difficulty 5)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** 2–3 gaps each, all single function words (a / who / until; her / had / of; again / unless; again / had) in two-paragraph texts of about 60–80 words.
- **Problem:** These are much easier than the difficulty-3 exit tickets (eight gaps, about 150–330 words), and the prompts make them easier still. The labels disagree with comparable items, so mastery decisions based on them will be miscalibrated.
- **Proposed correction:** Relabel as difficulty 2–3, or lengthen to 5–8 gaps with integrated passage reasoning.

### eo-l5-003 vs eo-l5-004 / eo-l5-005 — Baseline harder than endline/reserve
- **Location:** `backend_resources/english/v1/questions/eo-l5-003.json` (difficulty 4) vs `eo-l5-004.json`, `eo-l5-005.json` (difficulty 3)
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "difficulty": 4 (baseline) / 3 (endline, reserve). All three are 5-gap function-word passages of similar length.
- **Problem:** Pre/post forms should be equated. A higher-labelled baseline (or real difficulty mismatch) biases the growth estimate.
- **Proposed correction:** Align labels after calibration; make the three forms structurally parallel (same gap types in the same order).

### Cross-item — Learner-visible prompts use metalanguage beyond the 11–12 ESL band
- **Location:** prompts in `eo-l1-001`, `eo-l1-004`, `eo-l2-001`, `eo-l4-001`, `eo-l5-001`; hints in `eo-l1-001`
- **Severity:** S2 · **Category:** level-fit
- **Evidence:** "past-perfect verb phrase", "passive past-perfect phrase", "non-defining relative clause", "complete the inversion", "possessive determiner", "demonstrative", "fixed verb–preposition pattern", "reflexive pronoun".
- **Problem:** Given the corrected profile (final primary year, about 11–12, ESL), these labels are more abstract than the task itself, and they also leak the answer (see above).
- **Proposed correction:** Drop the grammar labels from prompts; use "Gap N: enter one word."

### eo-l4-001 part 4 / eo-l3-001 — Structures above the entry band
- **Location:** `backend_resources/english/v1/questions/eo-l4-001.json` (part 4); `eo-l3-001.json` (parts 5, 8)
- **Severity:** S3 · **Category:** level-fit
- **Evidence:** "Only {{4}} did he notice"; "on the {{5}} of cancelling"; "made all the {{8}}".
- **Problem:** Negative-adverbial inversion and idioms such as "on the verge of" are upper-intermediate (around B2). That is acceptable at difficulty 4–5 but at the edge of what an 11–12 ESL entrant would meet.
- **Proposed correction:** Keep at difficulty 5 only, or swap for "only then" in non-inverted form and more frequent collocations.

---

## Other editorial

### eo-l5-001 — Passage consistency
- **Location:** `backend_resources/english/v1/passages/english-passage-hillside-water-survey.json` P1, P4, P5
- **Severity:** S3 · **Category:** validity
- **Evidence:** "Ben counted the six students assigned to his group" / "Ben's careful headcount explained why the class returned together"; "a dark cloud hid the sun … waited for the rain to pass"; "repeated the depth reading twice".
- **Problem:** Ben counted only his own group, not the class. Rain appears without being introduced (only a cloud is mentioned). "Repeated … twice" means three readings, which is probably not intended.
- **Proposed correction:** "…explained why his group returned together"; "a dark cloud brought a sudden shower"; "took the depth reading twice".

### eo-l2-001 part 5 — "even brighter" presupposes the western side was bright
- **Location:** `backend_resources/english/v1/passages/english-passage-rooftop-garden-record.json` P3
- **Severity:** S3 · **Category:** validity
- **Evidence:** "The eastern side of the roof is bright for most of the morning. After the club installed a reflective panel, the western side became even {{5}} than before."
- **Problem:** Only the eastern side has been described as bright, so "even" has no anchor.
- **Proposed correction:** "…the western side, which was already fairly bright in the afternoon, became even {{5}} than before."

### eo-l1-002 / eo-l5-002 — Boilerplate hints and rationales
- **Location:** `backend_resources/english/v1/questions/eo-l1-002.json` (all hints), `eo-l5-002.json` (all hints and rationales)
- **Severity:** S3 · **Category:** leakage
- **Evidence:** Every hint: "Check the local grammar and the sentence's role in the passage." / "Test grammar, collocation and cross-sentence logic." Rationales: "Again marks repetition."; "Although introduces the concession."
- **Problem:** The hints are identical and give no help. The rationales are one-line boilerplate.
- **Proposed correction:** Write gap-specific evidence hints and rationales, as in eo-l1-001.

### All open cloze — Normalisation does not strip terminal punctuation
- **Location:** every `eo-*.json` part, `normalisation.strip_terminal_punctuation: false`
- **Severity:** S3 · **Category:** validity
- **Evidence:** `"strip_terminal_punctuation": false`
- **Problem:** A learner who types "an." or "However," is marked wrong even though the word is right.
- **Proposed correction:** Set it to `true` for single-word gaps.

### Checkpoint items — Quote-mark style inconsistency
- **Location:** `eo-l1-003`, `eo-l1-004`, `eo-l5-006`, `eo-l5-007`, `eb-l1-006`, `eb-l1-007` (single curly quotes) vs the other items (double curly quotes)
- **Severity:** S3 · **Category:** grammar
- **Evidence:** "supply the article required before ‘note’" vs "enter the article required before “unopened wooden box”".
- **Problem:** House style is inconsistent across the bank.
- **Proposed correction:** Standardise on one quote style.

---

## Slice summary

**Counts by severity (finding blocks; several open-cloze blocks bundle multiple gaps):**
- **S1: 21.** Wrong key or wrong-pointing prompt: 2 (eo-l5-002 g6, eo-l5-003 g5). Banked cloze with no correct bank word: 1 (eb-l1-003). Banked cloze with a second whole-passage solution: 1 (eb-l1-002). Open-cloze blocks with genuinely correct unlisted alternatives: 10. Protected-pool prompt leakage: 7.
- **S2: 14.**
- **S3: 17.**

**Most serious:**
1. eb-l1-003 (baseline): the key "bare" contradicts "Posters … covered every corner", and no bank word is correct.
2. eo-l5-002 gap 6 (retry): the key "again" produces an ungrammatical sentence, and there is no earlier check to repeat.
3. eo-l5-003 gap 5 (baseline): the prompt says "the time *before which* the second check occurred", but the key is "after".
4. All 7 protected open-cloze items (baseline, endline, reserve, 4 checkpoints) have prompts that name the word class or define the answer ("indefinite article", "relative pronoun referring to Mr Sadiq", "earlier than" = before, "show that Niko repeated" = again).
5. Missing alternatives that are genuinely correct: while/whilst/though/but/yet for concession gaps across eo-l1-001, eo-l1-002, eo-l5-002, eo-l5-003, eo-l5-004; "till" in eo-l1-002; "This" in eo-l1-002; "the/some" in eo-l5-003 g3; "standstill" and "care/control" in eo-l3-001; "later/afterwards" in eo-l4-001; "when/once" in eo-l5-002/003; "others" in eo-l5-002.

**Cross-cutting patterns:**
- **Prompts name the word class or exact form (open cloze is reduced to recall).** Every eo item: eo-l1-001, eo-l1-002, eo-l1-003, eo-l1-004, eo-l2-001, eo-l4-001, eo-l5-001, eo-l5-002, eo-l5-003, eo-l5-004, eo-l5-005, eo-l5-006, eo-l5-007 (eo-l3-001 by meaning gloss). Many gaps are determinate *only* because of the prompt; de-leaking will expose alternatives that must be added (listed per item as "conditional"). Severity is S1 in protected pools and S2 in exit and retry pools.
- **Inconsistent alternative sets across parallel forms.** "though" is accepted in eo-l1-001 and eo-l5-004 but not in eo-l1-002 or eo-l5-002. "till" is accepted in eo-l1-001 and eo-l1-003 but not in eo-l1-002. "while/whilst" is never accepted. Proper names are accepted in eo-l4-001 but not considered in eo-l1-004.
- **Lesson worked examples are near-copies of the assessed items.** e3-lesson-01 → eb-l1-001; e4-lesson-01 → eo-l1-001; e4-lesson-03 → eo-l3-001; e4-lesson-04 → eo-l4-001; e4-lesson-05 → eo-l5-001. The E3 and E4 checkpoints (eb-l1-006, eo-l5-006, eo-l5-007) reuse the same frames and answers again.
- **Places called "deserted" or "alone" while a person is present.** eb-l1-001, eb-l1-006.
- **Banked-cloze distractor rationales are boilerplate and claim grammatical failure for words that are grammatical.** eb-l1-001, eb-l1-002. eb-l1-005 rationales name "Silently", which is not in the bank.
- **Checkpoint difficulty labels are inflated, and baseline/endline labels are not equated.** eo-l1-003, eo-l1-004, eo-l5-006, eo-l5-007; eo-l5-003 vs eo-l5-004/005.
- **Grammar metalanguage in learner-visible prompts is beyond the 11–12 ESL entry band.** eo-l1-001, eo-l1-004, eo-l2-001, eo-l4-001, eo-l5-001.

**Items I consider sound in substance (only minor or pattern-level notes):** eb-l1-004 (key and bank solve uniquely; one weak distractor), eb-l1-005 (unique solution; rationale typos), eb-l1-007 (unique solution; well-built rationales). eo-l1-003 and eo-l1-004 have correct keys and no genuine alternatives under any prompt; their problems are leakage and level only. eo-l5-005 has a correct key set; its problem is leakage only.
