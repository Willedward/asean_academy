"""Generate the approved 60-minute English diagnostic v2 source records.

The generated JSON remains draft and must receive human English and editorial review.
Run from the repository root with:

    uv run --project question_bank python question_bank/scripts/generate_english_diagnostic_v2.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGLISH = ROOT / "backend_resources/english/v1"
CREATED_AT = "2026-11-06T10:30:00+08:00"
SOURCE_REFS = [
    "candidate-report-2026-english-format",
    "ies-adolescent-literacy-guide",
    "nextscholar-english-curriculum-design-v1",
]


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def provenance(label: str) -> dict:
    return {
        "authoring_method": "original_authored",
        "source_refs": SOURCE_REFS,
        "created_at": CREATED_AT,
        "authored_by": label,
        "reviewed_at": None,
        "reviewed_by": None,
        "review_notes": None,
    }


def passage_hash(payload: dict) -> str:
    source = {
        key: payload[key]
        for key in ("stable_key", "revision", "title", "text_type", "paragraphs", "attribution")
    }
    canonical = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def make_passage(key: str, title: str, text_type: str, paragraphs: list[str]) -> dict:
    payload = {
        "schema_version": "1.0.0",
        "revision": 1,
        "stable_key": key,
        "title": title,
        "text_type": text_type,
        "paragraphs": paragraphs,
        "attribution": "Original NextScholar passage.",
        "content_sha256": "",
        "status": "draft",
        "provenance": provenance("Codex English diagnostic v2 milestone"),
    }
    payload["content_sha256"] = passage_hash(payload)
    return payload


def passage_ref(passage: dict) -> dict:
    return {
        "stable_key": passage["stable_key"],
        "revision": passage["revision"],
        "content_sha256": passage["content_sha256"],
    }


def choice_part(
    position: int,
    prompt: str,
    options: list[str],
    correct_index: int,
    explanation: str,
    hint: str,
) -> dict:
    keys = [chr(ord("A") + index) for index in range(len(options))]
    correct_key = keys[correct_index]
    return {
        "position": position,
        "prompt": prompt,
        "response": {
            "type": "single_choice",
            "options": [
                {"key": key, "text": text} for key, text in zip(keys, options, strict=True)
            ],
            "correct_key": correct_key,
            "choice_rationales": {
                key: (
                    explanation
                    if key == correct_key
                    else "This meaning does not fit the complete sentence or passage evidence."
                )
                for key in keys
            },
        },
        "hint": hint,
        "correct_explanation": explanation,
    }


def base_question(
    key: str,
    bank: str,
    outcome: str,
    title: str,
    difficulty: int,
    question_type: str,
    exposure_pool: str,
    instructions: str,
    parts: list[dict],
    passage: dict | None = None,
) -> dict:
    return {
        "schema_version": "1.0.0",
        "revision": 1,
        "stable_key": key,
        "bank_key": bank,
        "curriculum_version": "asean_scholarship_english_v1_draft",
        "audience_band": "secondary_school",
        "outcome_code": outcome,
        "title": title,
        "difficulty": difficulty,
        "question_type": question_type,
        "exposure_pool": exposure_pool,
        "feedback_timing": "after_group",
        "status": "draft",
        "passage_ref": passage_ref(passage) if passage else None,
        "instructions": instructions,
        "parts": parts,
        "provenance": provenance("Codex English diagnostic v2 milestone"),
    }


VOCABULARY = {
    "baseline": [
        ("prudent", "Before spending the entire grant, the committee kept a reserve for unexpected repairs.", "careful about future risks", ["eager to impress others", "unable to reach a decision", "careless with limited funds"]),
        ("undecided", "The first schedule remained undecided because transport times had not been confirmed.", "not yet settled or final", ["secretly arranged", "impossible to change", "unusually detailed"]),
        ("lucid", "Her explanation was lucid: each reason followed logically from the evidence before it.", "clear and easy to understand", ["brief and incomplete", "emotional but sincere", "copied from another source"]),
        ("scant", "Clean drinking water became scant after the pipes failed and only two tanks remained.", "available in very small amounts", ["safe for everyone to use", "stored in several locations", "expensive but plentiful"]),
        ("impartial", "The judge had no connection to either team and applied the same rules to both.", "fair and not favouring either side", ["strictly opposed to both sides", "uncertain about the rules", "appointed only for one team"]),
        ("feasible", "Engineers concluded that the bridge could be repaired within the budget and before the rainy season.", "practical and possible", ["dangerous but exciting", "temporary and untested", "unlikely to receive support"]),
        ("subtle", "The colour difference was subtle; most visitors noticed it only after the guide pointed it out.", "small and not immediately obvious", ["bright enough to cause discomfort", "deliberately hidden from inspectors", "completely absent from the display"]),
        ("adverse", "The organisers moved the event indoors because strong winds could create adverse conditions.", "harmful or unfavourable", ["unexpected but helpful", "ordinary for the season", "suitable for outdoor games"]),
        ("compel", "The safety rule may compel cyclists to wear lights after sunset.", "force or strongly require", ["invite without any pressure", "teach through repeated practice", "permit as a rare exception"]),
        ("diminish", "As the storm moved away, the sound of thunder began to diminish.", "become less intense", ["change direction suddenly", "continue at the same level", "return without warning"]),
        ("stringent", "The laboratory introduced stringent checks, rejecting samples with even minor labelling errors.", "very strict and demanding", ["informal and optional", "simple enough for beginners", "temporary but widely ignored"]),
        ("tenable", "Her account was tenable because the bus records and two witnesses supported it.", "reasonable and defensible", ["proven beyond any doubt", "deliberately misleading", "too confusing to examine"]),
        ("noncommittal", "The reply was noncommittal: it neither accepted the proposal nor rejected it.", "avoiding a clear decision or opinion", ["written in a rude manner", "based on false information", "expressing complete agreement"]),
        ("rectify", "The supplier promised to rectify the invoice by removing the duplicated charge.", "correct a problem", ["explain why it occurred", "delay payment permanently", "copy the original document"]),
        ("fitful", "Rainfall was fitful: brief showers appeared on only three days during the month.", "irregular and occasional", ["heavy throughout every day", "predictable at the same hour", "too light to be measured"]),
    ],
    "endline": [
        ("judicious", "Rather than replace every computer, the school made a careful choice based on repair costs and age.", "showing sensible judgement", ["avoiding all responsibility", "designed to attract attention", "made without enough evidence"]),
        ("unsettled", "The results remain unsettled until the second laboratory confirms the measurements.", "not yet decided or final", ["kept private forever", "certain to be incorrect", "recorded without permission"]),
        ("unified", "The report felt unified because its examples, charts and conclusion all supported one central claim.", "forming a well-connected whole", ["containing several unrelated sections", "using language that is too technical", "repeating the same sentence exactly"]),
        ("exhaustible", "The rescue team's battery supply was exhaustible and could not be replaced during the journey.", "able to be completely used up", ["damaged beyond repair", "shared equally by everyone", "hidden from public view"]),
        ("dispassionate", "To remain dispassionate, the reviewer scored every proposal against the published criteria.", "guided by evidence rather than emotion", ["determined to reject all proposals", "unaware of the judging criteria", "personally involved in one proposal"]),
        ("practicable", "The coastal route was practicable because it was safe, affordable and open throughout the year.", "capable of working successfully", ["popular despite being unsafe", "shorter but legally forbidden", "useful only in perfect weather"]),
        ("nuanced", "His nuanced answer recognised both the benefits of tourism and the pressure it places on residents.", "showing fine distinctions and complexity", ["supporting only one extreme view", "avoiding the question entirely", "using facts that cannot be checked"]),
        ("detrimental", "Skipping maintenance was detrimental to the machines, which began failing more often.", "causing harm or damage", ["producing an unexpected saving", "making no measurable difference", "improving performance gradually"]),
        ("oblige", "The signed agreement will oblige the contractor to replace unsafe wiring.", "require someone to act", ["allow someone to choose freely", "warn someone without consequences", "reward someone for past work"]),
        ("wane", "Public interest began to wane after several weeks without new information.", "gradually decrease", ["spread to a wider audience", "become more intense", "change to a different topic"]),
        ("rigorous", "The study used rigorous procedures, including repeated trials and independent checks.", "thorough and exacting", ["quick and inexpensive", "flexible enough to ignore errors", "based mainly on personal opinion"]),
        ("well-founded", "The estimate seemed well-founded because three independent surveys produced similar figures.", "supported by sound evidence", ["guaranteed to remain unchanged", "too precise to understand", "invented for entertainment"]),
        ("equivocal", "Her reply was equivocal; it could be understood as support or as a polite refusal.", "uncertain or having two possible meanings", ["directly insulting", "supported by strong evidence", "expressed with complete confidence"]),
        ("remedy", "The council acted quickly to remedy the drainage fault before more homes flooded.", "put a problem right", ["identify who first reported it", "measure the damage only", "postpone action until next year"]),
        ("intermittent", "The radio signal was intermittent, disappearing for a few seconds and then returning.", "stopping and starting at intervals", ["weak but completely continuous", "clearer than expected", "broadcast from several stations"]),
    ],
    "reserve": [
        ("circumspect", "The editor was circumspect and checked the source before printing the dramatic claim.", "careful to avoid risk or error", ["eager to publish first", "unable to understand the claim", "openly hostile to the source"]),
        ("revisable", "The count was revisable because officials still had to inspect the remaining boxes.", "still open to change", ["kept secret from officials", "known to contain no errors", "completed later than planned"]),
        ("congruent", "Her argument was congruent with the principles stated at the start.", "remaining logically in agreement", ["changing whenever challenged", "supported by emotional language", "shorter than the other arguments"]),
        ("meagre", "The hikers shared a meagre supply of food that was barely enough for one day.", "very small or insufficient", ["carefully packed and labelled", "freshly prepared", "available in unlimited amounts"]),
        ("even-handed", "The mediator used even-handed language and did not blame either neighbour.", "fair and not supporting either side", ["critical of both sides", "unfamiliar with the dispute", "chosen by the louder neighbour"]),
        ("implementable", "After a short trial, the team agreed that the revised timetable was implementable.", "practical enough to put into effect", ["perfect in every detail", "popular but impossible to fund", "designed only for emergencies"]),
        ("implicit", "The warning was implicit rather than stated directly, but everyone understood the possible consequence.", "suggested without being openly expressed", ["stated repeatedly in exactly the same words", "deliberately made false", "too complex to translate"]),
        ("unfavourable", "Unfavourable currents forced the swimmers to postpone the crossing.", "likely to hinder success", ["unusual but harmless", "ideal for a fast crossing", "measured inaccurately"]),
        ("necessitate", "Damage to the main cable may necessitate closing the lift for repairs.", "make an action necessary", ["make an action optional", "prevent anyone noticing", "reward an earlier decision"]),
        ("subside", "The evacuation order remained until the floodwater began to subside.", "fall to a lower level", ["move towards the town", "rise more quickly", "remain completely unchanged"]),
        ("exacting", "Restoring the old map was exacting work because every torn edge had to align precisely.", "requiring great care and effort", ["completed without any skill", "guided by uncertain standards", "repetitive but unimportant"]),
        ("cogent", "The explanation was cogent because it accounted for every observation, including the exception.", "clear and persuasive through strong reasons", ["guaranteed to be legally correct", "difficult to hear", "based on a single unsupported guess"]),
        ("indeterminate", "With two records missing, the cause of the error remained indeterminate.", "not possible to decide from available evidence", ["obvious to every observer without further evidence", "deliberately concealed", "unimportant to the investigation"]),
        ("amend", "The chair asked members to amend the proposal by adding a clear spending limit.", "change it to improve or correct it", ["withdraw it without discussion", "approve it exactly as written", "translate it into another language"]),
        ("infrequent", "Power cuts were infrequent, occurring only twice during the entire year.", "not happening often", ["lasting for many hours", "following a fixed daily pattern", "affecting every neighbourhood"]),
    ],
}


POOL = {
    "baseline": "baseline_diagnostic",
    "endline": "endline_diagnostic",
    "reserve": "protected_reserve",
}
HINT = {
    "baseline": "Protected baseline: no hint is available.",
    "endline": "Protected endline: no hint is available.",
    "reserve": "Protected reserve: no hint is available.",
}


def make_vocab(form: str, key: str) -> dict:
    positions = [1, 2, 0, 3, 1, 0, 2, 3, 0, 1, 3, 2, 1, 0, 2]
    parts = []
    for number, ((target, context, meaning, distractors), correct_index) in enumerate(
        zip(VOCABULARY[form], positions, strict=True), start=1
    ):
        options = list(distractors)
        options.insert(correct_index, meaning)
        parts.append(
            choice_part(
                number,
                f'{context} What does “{target}” most nearly mean?',
                options,
                correct_index,
                f"In this sentence, {target} means {meaning}.",
                HINT[form],
            )
        )
    return base_question(
        key,
        "english-ev-v1",
        "EV1.6",
        f"{form.title()} diagnostic vocabulary set",
        4,
        "vocabulary_in_context",
        POOL[form],
        "Choose the meaning that best fits each independent sentence. Complete all 15 items before submitting the protected group.",
        parts,
    )


BANKED_CLOZE = {
    "baseline": {
        "key": "english-passage-diagnostic-v2-baseline-ferry-notice",
        "title": "The delayed ferry notice",
        "paragraphs": [
            "Mira reached the island jetty before sunrise and found a crowd facing a blank noticeboard. The overnight storm had damaged the radio, so nobody knew whether the first ferry would arrive. Instead of repeating rumours, she {{1}} the harbour office using the emergency telephone beside the ticket window.",
            "An officer confirmed that the ferry was safe but would be two hours late. Mira wrote the message in large letters and asked a shopkeeper to translate it for older residents. She then {{2}} the paper inside the glass case, where the wind could not tear it away. The crowd became more {{3}} once the delay and the reason were clear.",
            "One passenger suggested hiring small fishing boats, but Mira explained that the sea remained too {{4}} for an unplanned crossing. Most people accepted the advice and moved to the covered market. Volunteers {{5}} drinking water and helped families find seats. When the ferry finally appeared, passengers formed an {{6}} queue rather than rushing towards the gate.",
            "The harbour officer later thanked Mira for giving information that was accurate, {{7}} and easy to see. Her response did not make the ferry arrive sooner, but it prevented confusion from becoming panic. The damaged radio was {{8}} that afternoon, and the notice stayed in place as a reminder of the morning.",
        ],
        "bank": ["contacted", "secured", "settled", "rough", "distributed", "orderly", "concise", "repaired", "ignored", "fragile", "secret"],
        "answers": ["contacted", "secured", "settled", "rough", "distributed", "orderly", "concise", "repaired"],
    },
    "endline": {
        "key": "english-passage-diagnostic-v2-endline-theatre-rehearsal",
        "title": "The rehearsal without lights",
        "paragraphs": [
            "During the final rehearsal for the community play, every light in the hall suddenly went out. The actors stopped, but Hana, the stage manager, remained {{1}}. She checked that nobody was near the raised platforms and asked the cast to switch on their phone torches.",
            "The caretaker discovered that water had entered an outdoor power box. Because the fault might be dangerous, he {{2}} the team from restoring the electricity themselves. Hana considered cancelling the rehearsal, yet the opening night was only two days away. She proposed a {{3}} plan: practise the dialogue and movement in the foyer, where daylight still entered through high windows.",
            "The narrow space forced the actors to {{4}} their movements, but it also exposed moments when they relied too heavily on scenery. Hana marked these sections and gave {{5}} instructions between scenes. By sunset, the cast had completed the whole play without using the stage.",
            "Electricians repaired the fault the next morning. When the actors returned to the hall, their timing was more {{6}} and their voices carried further. What had first seemed like a serious {{7}} had become a useful test of their preparation. Hana still recorded the electrical failure in the safety log, ensuring that the cause was fully {{8}} rather than forgotten after a successful rehearsal.",
        ],
        "bank": ["composed", "prevented", "viable", "adapt", "precise", "coordinated", "setback", "investigated", "decorative", "casual", "concealed"],
        "answers": ["composed", "prevented", "viable", "adapt", "precise", "coordinated", "setback", "investigated"],
    },
    "reserve": {
        "key": "english-passage-diagnostic-v2-reserve-clinic-delivery",
        "title": "The mountain clinic delivery",
        "paragraphs": [
            "A landslide blocked the only road to a mountain clinic on the morning its medicine delivery was due. The driver stopped at a safe distance and sent a {{1}} report with photographs and map coordinates. At the clinic, Nurse Rani checked the remaining supplies and identified which items were most {{2}}.",
            "A walking route crossed the hillside above the damaged road, but recent rain had made it {{3}}. The village rescue team inspected the path before agreeing to carry two lightweight boxes. They divided the load evenly and wrapped each container in a {{4}} cover. Meanwhile, the driver kept the rest of the medicine cool inside the vehicle.",
            "The team moved at a {{5}} pace and reported its position every fifteen minutes. At one stream, rising water forced the group to choose a longer route. This change was {{6}}, because the original crossing had become unsafe. The clinic received the urgent supplies before noon, and every package arrived {{7}}.",
            "Road workers cleared one lane the following day. The clinic director praised the teams for making a careful plan instead of taking an {{8}} risk. She also ordered a larger emergency stock, so that a future delay would not create the same pressure.",
        ],
        "bank": ["detailed", "urgent", "unstable", "waterproof", "steady", "prudent", "intact", "needless", "vague", "rapid", "decorative"],
        "answers": ["detailed", "urgent", "unstable", "waterproof", "steady", "prudent", "intact", "needless"],
    },
}


OPEN_CLOZE = {
    "baseline": {
        "key": "english-passage-diagnostic-v2-baseline-coral-log",
        "title": "A shared coral-observation log",
        "paragraphs": [
            "Three coastal schools wanted to compare weekly observations of a shallow reef. At first, each group kept notes in {{1}} own format, so colours, locations and dates could not be compared reliably. The teachers therefore agreed {{2}} a shared digital log with the same fields for every visit.",
            "Students recorded water clarity, visible damage and the number of selected fish species. They also uploaded one photograph from a fixed point. A photograph was accepted only {{3}} the marker post appeared in the frame, because this showed that the camera position was consistent. If rough weather prevented a visit, the group entered ‘not observed’ rather {{4}} guessing a value.",
            "After eight weeks, one school seemed to report far fewer fish. The difference might have reflected the reef, {{5}} it might also have resulted from visits at a different time of day. The groups added visit time to the log and agreed to collect the next four records within the same two-hour period.",
            "The shared system did not prove why fish numbers changed. It did, {{6}}, make the evidence easier to inspect. Students could trace every value back {{7}} a dated note and photograph. By keeping missing observations visible, they avoided presenting an incomplete record {{8}} if it were certain.",
        ],
        "answers": [
            ("its", []), ("on", ["upon"]), ("if", ["when", "provided"]), ("than", []),
            ("but", ["yet", "or"]), ("however", ["nevertheless"]), ("to", []), ("as", []),
        ],
    },
    "endline": {
        "key": "english-passage-diagnostic-v2-endline-night-bus",
        "title": "Measuring demand for a later bus",
        "paragraphs": [
            "Residents asked the transport office to run a later bus from the town centre. The existing service ended at 9 p.m., which was earlier {{1}} many evening classes and work shifts. Before changing the timetable, the office needed evidence of how many people would use an additional journey.",
            "For two weeks, volunteers counted passengers waiting near the closed bus stop between 9 and 10 p.m. They asked each person where they were travelling, but names were not collected. The volunteers used the same questions {{2}} that answers from different nights could be combined. They also recorded rain, public events and road closures, {{3}} these conditions might affect demand.",
            "Saturday produced the largest count, partly because a concert ended nearby. Removing that night entirely would hide genuine demand, {{4}} treating it as typical would exaggerate the weekly pattern. The report therefore showed the result both with and {{5}} the concert night.",
            "The evidence suggested enough demand for a three-month trial on Thursdays, Fridays and Saturdays. The office would review ticket records after the trial rather than assume the first estimate was exact. This approach allowed the service to begin {{6}} committing funds permanently. It also made clear which evidence would be needed {{7}} decide whether the bus should continue. Residents supported the trial because the decision was neither a refusal {{8}} an unlimited promise.",
        ],
        "answers": [
            ("than", []), ("so", []), ("because", ["as", "since"]), ("but", ["yet"]),
            ("without", []), ("before", ["without"]), ("to", []), ("nor", []),
        ],
    },
    "reserve": {
        "key": "english-passage-diagnostic-v2-reserve-library-heat",
        "title": "Mapping heat inside a library",
        "paragraphs": [
            "A public library received complaints that its upper floor became uncomfortable in the afternoon. Rather {{1}} rely only on impressions, staff placed temperature sensors in six reading areas. Each sensor recorded a value every fifteen minutes for ten days.",
            "The first map appeared to show one corner as much hotter than the rest. A librarian noticed, {{2}}, that its sensor sat beside a sunny window while the others were farther from glass. The team moved all sensors the same distance from walls and windows, then repeated the measurements. They kept the original results {{3}} deleting them, because the first placement explained why the early pattern was misleading.",
            "The second set still showed higher afternoon temperatures upstairs, especially after 3 p.m. Staff opened internal doors to improve airflow and adjusted blinds before direct sunlight reached the windows. These changes reduced the difference, {{4}} they did not remove it completely.",
            "The library used the findings to move children's activities to the lower floor on the hottest days. It also requested an engineering inspection, since the sensors could show {{5}} and where heat accumulated but not the condition of ventilation equipment. By repeating the test under clearer conditions, staff had evidence {{6}} which to act. They continued monitoring so that any improvement could be compared {{7}} the same standard. The project turned a general complaint {{8}} a specific, testable problem.",
        ],
        "answers": [
            ("than", []), ("however", ["though"]), ("instead", ["rather"]), ("but", ["although", "yet"]),
            ("when", []), ("on", ["upon"]), ("against", ["with"]), ("into", []),
        ],
    },
}


def make_banked(form: str, key: str) -> tuple[dict, dict]:
    spec = BANKED_CLOZE[form]
    passage = make_passage(spec["key"], spec["title"], "narrative", spec["paragraphs"])
    option_keys = [chr(ord("A") + index) for index in range(len(spec["bank"]))]
    options = [
        {"key": option_key, "text": word}
        for option_key, word in zip(option_keys, spec["bank"], strict=True)
    ]
    word_to_key = dict(zip(spec["bank"], option_keys, strict=True))
    parts = []
    for position, answer in enumerate(spec["answers"], start=1):
        correct_key = word_to_key[answer]
        parts.append(
            {
                "position": position,
                "prompt": f"Gap {position}: choose the word that best completes the full passage.",
                "response": {
                    "type": "single_choice",
                    "options": options,
                    "correct_key": correct_key,
                    "choice_rationales": {
                        option_key: (
                            f'“{answer}” fits both the grammar and meaning of gap {position}.'
                            if option_key == correct_key
                            else f'“{word}” does not fit both the grammar and meaning of gap {position}.'
                        )
                        for option_key, word in zip(option_keys, spec["bank"], strict=True)
                    },
                },
                "hint": HINT[form],
                "correct_explanation": f'“{answer}” fits both the grammar and meaning of gap {position}.',
            }
        )
    question = base_question(
        key,
        "english-eb-v1",
        "EB3.1",
        f"{form.title()} diagnostic banked cloze",
        4,
        "banked_cloze",
        POOL[form],
        "Read the complete passage. Choose one bank word for each gap; three words remain unused. Complete all eight gaps without feedback.",
        parts,
        passage,
    )
    return passage, question


def make_open(form: str, key: str) -> tuple[dict, dict]:
    spec = OPEN_CLOZE[form]
    passage = make_passage(spec["key"], spec["title"], "informational", spec["paragraphs"])
    parts = []
    for position, (answer, alternatives) in enumerate(spec["answers"], start=1):
        rationale = f'“{answer}” completes the grammar and meaning of gap {position}.'
        parts.append(
            {
                "position": position,
                "prompt": f"Gap {position}: write one word.",
                "response": {
                    "type": "short_text",
                    "canonical_answer": answer,
                    "accepted_alternatives": alternatives,
                    "normalisation": {
                        "unicode_form": "NFKC",
                        "collapse_whitespace": True,
                        "case_sensitive": False,
                        "strip_terminal_punctuation": True,
                    },
                    "rationale": rationale,
                },
                "hint": HINT[form],
                "correct_explanation": rationale,
            }
        )
    question = base_question(
        key,
        "english-eo-v1",
        "EO4.5",
        f"{form.title()} diagnostic open cloze",
        4,
        "open_cloze",
        POOL[form],
        "Read the complete passage and enter exactly one word in each gap. Complete all eight gaps without feedback.",
        parts,
        passage,
    )
    return passage, question


READING = {
    "baseline": {
        "informational": {
            "key": "english-passage-diagnostic-v2-baseline-floating-gardens",
            "title": "Testing floating gardens on a city pond",
            "paragraphs": [
                "A city park contained a shallow pond that often turned green during hot, dry weeks. Park workers suspected that nutrients washed from nearby paths were encouraging rapid plant growth in the water. Removing the growth helped briefly, but it did not address the water entering the pond. A local college proposed testing small floating gardens: rafts holding wetland plants whose roots would hang in the water rather than soil.",
                "The team built six identical rafts and placed them in one sheltered half of the pond. The other half remained open so that water conditions could be compared. Every week for three months, students measured water clarity and the concentration of two nutrients at fixed points. They also photographed the roots and counted insects using the rafts. The rafts were tied far enough apart to avoid forming a barrier for fish or maintenance boats.",
                "Water near the gardens became clearer during the first six weeks, and nutrient readings there fell more than readings in the comparison area. However, a period of heavy rain changed both halves of the pond. Runoff increased, the water mixed strongly, and the difference between the areas narrowed. The students therefore avoided claiming that the gardens alone had caused every change. They noted that wind, rain and movement between the two halves limited the comparison.",
                "The trial still influenced the park's next decision. Instead of covering the pond with more rafts, managers kept the six gardens and repaired a drain that carried muddy water from a car park. They planned to continue measurements through another wet season. The floating gardens had shown possible value, but the strongest lesson was that water quality depended on several connected sources, not one visible symptom.",
            ],
            "questions": [
                ("Why did the college propose floating gardens?", ["To test whether plant roots could help improve pond water", "To create a solid bridge across the pond", "To stop maintenance boats entering the pond", "To replace every plant growing near the paths"], 0, "The gardens were tested as a possible way to reduce nutrients and improve water quality."),
                ("Why was one half of the pond left without rafts?", ["To provide deeper water for the insects", "To provide a comparison for the measured changes", "To keep all runoff away from the gardens", "To make the water mix more rapidly"], 1, "The open half acted as a comparison area."),
                ("What does “the difference between the areas narrowed” mean?", ["The rafts moved physically closer together", "Both areas became completely free of nutrients", "The measurements in the two areas became more similar", "Students measured a smaller part of the pond"], 2, "After heavy rain, the readings from the two areas were less different."),
                ("Which limitation is emphasised in paragraph 3?", ["The plants could not survive in pond water", "The team forgot to take weekly readings", "The comparison area contained no insects", "Weather and water movement affected both test areas"], 3, "Rain, wind and mixing made it hard to isolate the gardens' effect."),
                ("Why did managers repair the drain as well as keep the gardens?", ["They recognised that runoff was another source of the problem", "They wanted the pond to receive more muddy water", "They had proved that the gardens were ineffective", "They needed a place to attach additional rafts"], 0, "The decision addressed a connected source of nutrients and muddy runoff."),
                ("Which statement best expresses the passage's main idea?", ["Floating gardens always restore polluted urban ponds", "A useful trial can guide action while still leaving uncertainty", "Park managers should avoid measuring natural systems", "Heavy rain makes environmental testing impossible"], 1, "The trial produced useful evidence but supported a cautious, combined response."),
            ],
        },
        "narrative": {
            "key": "english-passage-diagnostic-v2-baseline-storm-lantern",
            "title": "The lantern at the upstairs window",
            "paragraphs": [
                "By late afternoon, the river had risen over the lowest steps of Lela's street. Her family had already moved boxes upstairs, but her grandfather remained at the front window, watching the rain. Decades earlier, he had worked on the river ferry. He insisted that the water would stop below the doorway because it had done so during another storm. Lela wanted to believe him, yet the current was carrying branches past houses that had never flooded before.",
                "A message from the district office advised residents to leave before dark. The evacuation truck would wait at the school for one hour. Grandfather folded the message and placed it under a cup. He disliked travelling in bad weather and worried that the crowded shelter would worsen his cough. Lela did not argue about the height of the river. Instead, she packed his medicine, a dry shirt and the small battery lantern he used during power cuts.",
                "When the electricity failed, the room became silent except for rain on the roof. Lela switched on the lantern and set it in the upstairs window. Across the street, another light answered, then a third. A rescue boat came slowly around the corner. Its crew called to residents who needed help reaching the school. Grandfather looked at the water now spreading across the floor and picked up the bag without speaking.",
                "At the shelter, he sat near an open door and accepted a blanket from a neighbour. The next morning, Lela learned that the lanterns had helped the boat crew identify occupied houses after the streetlights failed. Grandfather did not apologise for waiting. He simply cleaned the mud from the lantern and said they should keep fresh batteries beside it. Lela understood this as his way of admitting that experience could guide a decision without guaranteeing the future.",
            ],
            "questions": [
                ("Why did Grandfather initially believe the house would remain safe?", ["A rescue crew had inspected the doorway", "An earlier storm had stopped below the entrance", "The district office had withdrawn its warning", "Neighbouring families had promised to stay"], 1, "He relied on what had happened during an earlier storm."),
                ("Why does Lela pack the medicine instead of continuing the argument?", ["She prepares for leaving while avoiding a direct confrontation", "She believes the river will fall before dark", "She wants Grandfather to stay without his medicine", "She plans to send the bag on the truck alone"], 0, "Her practical preparation moves them towards safety without prolonging the disagreement."),
                ("What is the effect of the other lights answering Lela's lantern?", ["They show that the electricity has returned", "They signal that the rain is ending", "They reveal a shared need across the dark street", "They warn the boat to avoid occupied homes"], 2, "The sequence of lights shows several occupied houses needing attention."),
                ("What can be inferred from Grandfather picking up the bag without speaking?", ["He has forgotten why the bag was packed", "He intends to remain upstairs alone", "He is angry that the rescue boat arrived", "He accepts that leaving has become necessary"], 3, "His action shows acceptance even though he does not state it."),
                ("What does cleaning the lantern mainly reveal about Grandfather?", ["He plans to prepare differently for later storms", "He thinks the lantern caused the flood damage", "He plans to return to work on the ferry", "He wants to hide the lantern from neighbours"], 0, "Maintaining it and requesting batteries show a changed approach to preparedness."),
                ("Which theme is developed most clearly?", ["Old knowledge should always overrule warnings", "Experience is valuable but cannot remove uncertainty", "Families should avoid discussing difficult choices", "Technology makes community action unnecessary"], 1, "The ending explicitly distinguishes useful experience from certainty."),
            ],
        },
    },
    "endline": {
        "informational": {
            "key": "english-passage-diagnostic-v2-endline-forest-sound",
            "title": "Listening for change in a restored forest",
            "paragraphs": [
                "A conservation group had replanted native trees on land once used for grazing. Counting every animal returning to the area was impossible, so researchers installed sound recorders at twelve locations. The devices captured one minute of sound every ten minutes from sunset to sunrise. Software then marked likely calls from frogs, insects, birds and bats for a person to check.",
                "The recorders did not identify every species perfectly. Wind, rain and motorbikes sometimes produced patterns that the software mistook for animals. Some species also called more often than others, so a silent recording did not prove that an animal was absent. To reduce these problems, researchers checked random samples by ear and kept the devices in the same positions and at the same recording settings.",
                "After two years, the restored sites contained a wider variety of call patterns than nearby open fields. The increase was strongest during the wet season, when frogs and insects were most active. Yet two older forest sites still had more complex night-time sound. This result suggested that replanting was helping, while also showing that a young forest did not quickly replace every feature of an established one.",
                "The group used the recordings to decide where to add small ponds and where to connect isolated tree patches. It also published the unclassified sound files, allowing other researchers to test improved identification methods. Sound monitoring could cover many nights at relatively low cost, but it worked best as one source of evidence alongside vegetation surveys and direct observation. The project measured recovery without pretending that a single number could describe an entire forest.",
            ],
            "questions": [
                ("Why were sound recorders used?", ["To capture evidence across many places and nights", "To prevent animals entering the open fields", "To replace the newly planted native trees", "To broadcast calls from older forests"], 0, "The recorders sampled many locations repeatedly when direct counting was impractical."),
                ("Why did people check random recordings by ear?", ["To make every species call more frequently", "To detect and estimate software classification errors", "To remove the sound of rain from the forest", "To change the recording settings each night"], 1, "Human checks helped assess false classifications made by the software."),
                ("What does a silent recording fail to prove?", ["That the device was placed in the forest", "That rain was absent during the recording", "That a species was absent from the area", "That the recording lasted one minute"], 2, "An animal may be present without calling during that sample."),
                ("What is the main significance of the older forest comparison?", ["Open fields recover faster than planted land", "Sound files cannot be shared with researchers", "Ponds prevent insects from becoming active", "Recovery was occurring but remained incomplete"], 3, "The restored sites improved but had not matched older forest complexity."),
                ("Why were unclassified files published?", ["So other researchers could test better identification methods", "So visitors could choose louder forest routes", "So software errors would no longer need checking", "So all animals could be named immediately"], 0, "Shared files allow independent development and testing of classification methods."),
                ("Which statement best captures the writer's view of sound monitoring?", ["It is too unreliable to support conservation work", "It is useful when combined with other evidence", "It provides a complete description by itself", "It should be limited to old forests"], 1, "The final paragraph presents it as valuable but not sufficient alone."),
            ],
        },
        "narrative": {
            "key": "english-passage-diagnostic-v2-endline-unclaimed-parcel",
            "title": "The parcel with no room number",
            "paragraphs": [
                "Niko was covering the reception desk at a student residence when a courier left a small parcel. The label gave the building address and the name ‘A. Rahman’, but no room number. Two residents shared that initial and surname. One was away at a sports match; the other was studying in the common room. The courier, already late, asked Niko to sign and decide who should receive it.",
                "The parcel was light, and a corner of the cardboard had split. Through the gap, Niko could see the edge of a framed photograph. The student in the common room said she was expecting a birthday gift from home. She recognised the sender's town on the label and reached for the box. Niko almost handed it over, but the residence rule required identity to be confirmed when a label was incomplete.",
                "He photographed the damaged corner, placed the parcel in the locked cupboard and messaged both residents through the official system. The student frowned. She said the photograph might be fragile and accused him of hiding behind a rule. Niko agreed that waiting was frustrating, then called the courier company to report the damaged packaging. It promised to contact the sender and confirm the recipient.",
                "An hour later, the other A. Rahman replied from the match. The parcel was hers: the photograph showed her grandmother beside a house the family had recently sold. The student in the common room apologised, admitting that she had focused on the birthday and the familiar town. When the owner returned, Niko asked her to check the frame before signing. The glass was intact. The rule had delayed the parcel, but the delay protected both the object and the trust between residents.",
            ],
            "questions": [
                ("What created the main difficulty at reception?", ["Two residents matched the incomplete name", "The courier refused to leave the parcel", "The building address was missing", "The cupboard could not be locked"], 0, "The incomplete label could refer to either of two residents."),
                ("Why was the common-room student's claim initially believable?", ["She had already opened the damaged corner", "She expected a gift and recognised the sender's town", "She produced a receipt with the room number", "She knew what appeared in the photograph"], 1, "Her expected gift and recognition of the town made the claim plausible."),
                ("Why does the writer mention that Niko almost handed over the box?", ["To show that he wanted to keep the photograph", "To prove that the rule was unclear", "To show the tension between convenience and verification", "To suggest that the courier had threatened him"], 2, "The moment highlights the pressure to act quickly despite incomplete evidence."),
                ("What does “hiding behind a rule” suggest the student believed?", ["Niko had written the residence rule himself", "The parcel was hidden somewhere unsafe", "The rule applied only to sports teams", "Niko was using procedure to avoid helping her"], 3, "She viewed his reliance on procedure as an excuse rather than assistance."),
                ("What caused the student to make the wrong assumption?", ["Several familiar details supported what she hoped was true", "Niko gave her incorrect information about the frame", "The other resident had asked her to collect the parcel", "The courier changed the name on the label"], 0, "Expectation and a familiar town led her to interpret limited evidence in her favour."),
                ("Which idea is most strongly supported by the ending?", ["Damaged parcels should always be rejected", "Careful delay can protect property and relationships", "Rules are useful only when nobody complains", "Official messages solve every identification problem"], 1, "Verification delayed delivery but prevented a wrongful handover and preserved trust."),
            ],
        },
    },
    "reserve": {
        "informational": {
            "key": "english-passage-diagnostic-v2-reserve-cool-pavement",
            "title": "A cooler pavement trial",
            "paragraphs": [
                "A neighbourhood council wanted to reduce afternoon heat around a busy market. One proposal was to coat a section of dark pavement with a pale material that reflected more sunlight. Before treating the entire square, the council created two equal test strips, one coated and one unchanged. Both were away from trees and received sunlight for most of the day.",
                "For six weeks, sensors recorded surface temperature every fifteen minutes. Volunteers also measured air temperature one metre above each strip and asked pedestrians whether the area felt comfortable. The coated surface was usually cooler than the dark pavement at midday. However, air temperatures above the two strips differed only slightly, and comfort responses changed with wind, cloud and how long people had been walking.",
                "The coating created other questions. It became stained near food stalls and was brighter after rain, causing glare for some cyclists. Cleaning restored much of the colour but required extra water and staff time. Engineers also warned that six weeks was too short to show how the material would wear under years of delivery traffic. The council added these costs and risks to the temperature results instead of treating the coolest reading as the only measure of success.",
                "The final plan used the coating on a smaller pedestrian zone, added shaded seating and scheduled a year of monitoring. Delivery lanes remained untreated until durability data were available. This mixed decision disappointed people who wanted an immediate transformation, but it reflected the trial's actual evidence. The coating could lower surface heat; it could not by itself guarantee cooler air, comfort, easy maintenance or safe use in every part of the square.",
            ],
            "questions": [
                ("Why did the council create two equal test strips?", ["To compare the coated and dark surfaces", "To separate cyclists permanently from pedestrians", "To measure the effect of mature shade trees", "To double the area cleaned by market staff"], 0, "Matched strips allowed a more useful comparison of the coating."),
                ("What did the trial show most clearly?", ["Pedestrians always preferred the brighter surface", "The coating generally reduced pavement surface temperature", "Air temperature fell sharply across the whole market", "The material remained clean without maintenance"], 1, "The consistent finding was a cooler coated surface around midday."),
                ("Why were comfort responses difficult to interpret?", ["Volunteers asked different questions each day", "Pedestrians could not see either test strip", "Several conditions besides pavement affected comfort", "Only delivery drivers were interviewed"], 2, "Wind, clouds and walking time also influenced people's responses."),
                ("What concern could not be resolved in six weeks?", ["Whether the market received sunlight", "Whether sensors could record temperature", "Whether pale colours reflect sunlight", "How the coating would survive long-term traffic"], 3, "The short trial could not establish years of durability."),
                ("Why were delivery lanes left untreated?", ["Evidence about durability under heavy use was still missing", "The lanes were cooler than all pedestrian areas", "Cyclists had requested a darker market square", "Cleaning was forbidden near delivery vehicles"], 0, "The council postponed high-wear use until longer-term evidence existed."),
                ("Which description best fits the council's final decision?", ["It ignored the trial because results were mixed", "It used the evidence cautiously and combined several measures", "It coated every surface to maximise one result", "It replaced temperature evidence with public opinion"], 1, "The plan used a limited coating plus shade and continued monitoring."),
            ],
        },
        "narrative": {
            "key": "english-passage-diagnostic-v2-reserve-last-train-notebook",
            "title": "The notebook on the last train",
            "paragraphs": [
                "On the last train home, Salma found a small notebook wedged between her seat and the wall. Its cover was plain, but the first page carried a name and a sketch of the old railway station. The remaining pages held careful drawings of shopfronts, bridges and trees, each labelled with a date. Salma recognised several places that had recently been demolished or rebuilt.",
                "There was no telephone number. A station employee offered to place the notebook in the general lost-property box, which would be sent to a central office at the end of the week. Salma worried that the owner might return to the same station first. She asked whether she could post a photograph of the cover online, but the employee pointed out that showing the name could allow a stranger to claim it.",
                "Together they photographed only the plain cover and wrote a notice saying that a dated sketchbook had been found on the final northbound train. Claimants would need to describe the first drawing and give the name inside. Salma also left her email address with the station, then went home wondering whether the effort was excessive for an object that looked inexpensive.",
                "Two days later, an architecture student wrote to the station. He described the railway sketch and the ink stain beneath it. The notebook contained field drawings for a project on changing public spaces; some recorded details that no longer existed. When he collected it, he explained that he had spent a year building the sequence. Salma realised that the notebook's value could not be guessed from its cover. The careful claim process had taken longer than posting the name, but it returned the record without exposing it to an easy false claim.",
            ],
            "questions": [
                ("What first made the notebook seem worth protecting?", ["Its drawings recorded places that were changing", "Its cover appeared expensive and rare", "A telephone number was written inside", "The station had announced a reward"], 0, "The dated drawings preserved details of altered or demolished places."),
                ("Why did the employee advise against posting the owner's name?", ["The name was impossible to read", "A stranger could use it to make a false claim", "Station rules banned all online notices", "The owner had requested complete secrecy"], 1, "Publishing the identifying detail would weaken verification."),
                ("Why did the notice mention a dated sketchbook but not the first drawing?", ["Salma had forgotten what the drawing showed", "The first page had been damaged", "It advertised the find but kept a test for ownership", "The station wanted several people to claim it"], 2, "The withheld detail could distinguish the real owner from others."),
                ("What does Salma's thought that the effort might be excessive reveal?", ["She planned to keep the notebook herself", "She disliked the architecture drawings", "She believed the employee had lost it", "Her plain object seemed unworthy of the effort"], 3, "She questioned whether an inexpensive-looking object justified the careful process."),
                ("How does the student's explanation change Salma's understanding?", ["It confirms that personal value may be hidden from an observer", "It proves that every lost item is financially valuable", "It shows that online notices are unnecessary", "It reveals that the train route caused the demolitions"], 0, "The year-long record had importance that its cover did not display."),
                ("Which statement best expresses the passage's central idea?", ["Lost property should always go directly to a central office", "Careful verification can protect value that is not immediately visible", "Public sketches are more useful than private records", "Simple objects rarely matter to their owners"], 1, "The recovery succeeds because useful publicity is balanced with withheld evidence."),
            ],
        },
    },
}


def make_reading(form: str, genre: str, key: str) -> tuple[dict, dict]:
    spec = READING[form][genre]
    passage = make_passage(spec["key"], spec["title"], genre, spec["paragraphs"])
    parts = [
        choice_part(position, prompt, options, correct, explanation, HINT[form])
        for position, (prompt, options, correct, explanation) in enumerate(
            spec["questions"], start=1
        )
    ]
    question = base_question(
        key,
        "english-er-v1",
        "ER5.7",
        f"{form.title()} diagnostic {genre} reading",
        4,
        "reading_comprehension",
        POOL[form],
        "Read the passage and answer all six questions without hints or feedback.",
        parts,
        passage,
    )
    return passage, question


FORM_KEYS = {
    "baseline": {
        "vocab": "ev-l5-201",
        "banked": "eb-l5-201",
        "open": "eo-l5-201",
        "informational": "er-l5-201",
        "narrative": "er-l5-204",
    },
    "endline": {
        "vocab": "ev-l5-202",
        "banked": "eb-l5-202",
        "open": "eo-l5-202",
        "informational": "er-l5-202",
        "narrative": "er-l5-205",
    },
    "reserve": {
        "vocab": "ev-l5-203",
        "banked": "eb-l5-203",
        "open": "eo-l5-203",
        "informational": "er-l5-203",
        "narrative": "er-l5-206",
    },
}


def update_bank(bank_key: str, expected: int, pool_updates: dict[str, int]) -> None:
    path = ENGLISH / "banks" / f"{bank_key}.json"
    payload = json.loads(path.read_text())
    payload["expected_question_count"] = expected
    payload["pool_distribution"].update(pool_updates)
    write_json(path, payload)


def update_form(filename: str, keys: dict[str, str]) -> None:
    path = ENGLISH / "forms" / filename
    payload = json.loads(path.read_text())
    payload["revision"] = 3
    payload["expected_scored_part_count"] = 43
    payload["task_part_distribution"] = {
        "vocabulary_in_context": 15,
        "banked_cloze": 8,
        "open_cloze": 8,
        "reading_comprehension": 12,
    }
    payload["question_keys"] = [
        keys["vocab"],
        keys["banked"],
        keys["open"],
        keys["informational"],
        keys["narrative"],
    ]
    write_json(path, payload)


def write_batch(batch_id: str, bank_key: str, module: str, question_keys: list[str]) -> None:
    write_json(
        ENGLISH / "authoring/batches" / f"{batch_id}.json",
        {
            "schema_version": "1.0.0",
            "batch_id": batch_id,
            "bank_key": bank_key,
            "module_code": module,
            "status": "ready_for_review",
            "expected_question_count": len(question_keys),
            "question_keys": question_keys,
            "review": {"english": "pending", "editorial": "pending"},
        },
    )


def main() -> None:
    questions: dict[str, dict] = {}
    passages: dict[str, dict] = {}
    for form, keys in FORM_KEYS.items():
        questions[keys["vocab"]] = make_vocab(form, keys["vocab"])
        banked_passage, banked = make_banked(form, keys["banked"])
        open_passage, open_question = make_open(form, keys["open"])
        info_passage, info = make_reading(form, "informational", keys["informational"])
        narrative_passage, narrative = make_reading(form, "narrative", keys["narrative"])
        for passage in (
            banked_passage,
            open_passage,
            info_passage,
            narrative_passage,
        ):
            passages[passage["stable_key"]] = passage
        questions.update(
            {
                keys["banked"]: banked,
                keys["open"]: open_question,
                keys["informational"]: info,
                keys["narrative"]: narrative,
            }
        )

    for key, payload in sorted(passages.items()):
        write_json(ENGLISH / "passages" / f"{key}.json", payload)
    for key, payload in sorted(questions.items()):
        write_json(ENGLISH / "questions" / f"{key}.json", payload)

    update_bank(
        "english-ev-v1",
        47,
        {"baseline_diagnostic": 2, "endline_diagnostic": 2, "protected_reserve": 2},
    )
    update_bank(
        "english-eb-v1",
        33,
        {"baseline_diagnostic": 2, "endline_diagnostic": 2, "protected_reserve": 2},
    )
    update_bank(
        "english-eo-v1",
        19,
        {"baseline_diagnostic": 2, "endline_diagnostic": 2, "protected_reserve": 2},
    )
    update_bank(
        "english-er-v1",
        25,
        {"baseline_diagnostic": 3, "endline_diagnostic": 3, "protected_reserve": 3},
    )

    update_form("english-baseline-sec3-id-v1.json", FORM_KEYS["baseline"])
    update_form("english-endline-sec3-id-v1.json", FORM_KEYS["endline"])
    update_form("english-endline-reserve-sec3-id-v1.json", FORM_KEYS["reserve"])

    write_batch(
        "english-ev-b018",
        "english-ev-v1",
        "E1",
        [FORM_KEYS[form]["vocab"] for form in ("baseline", "endline", "reserve")],
    )
    write_batch(
        "english-eb-b015",
        "english-eb-v1",
        "E3",
        [FORM_KEYS[form]["banked"] for form in ("baseline", "endline", "reserve")],
    )
    write_batch(
        "english-eo-b013",
        "english-eo-v1",
        "E4",
        [FORM_KEYS[form]["open"] for form in ("baseline", "endline", "reserve")],
    )
    write_batch(
        "english-er-b015",
        "english-er-v1",
        "E5",
        [
            FORM_KEYS[form][genre]
            for form in ("baseline", "endline", "reserve")
            for genre in ("informational", "narrative")
        ],
    )
    print(
        json.dumps(
            {
                "status": "complete",
                "questions": len(questions),
                "passages": len(passages),
                "forms": 3,
                "parts_per_form": 43,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()



