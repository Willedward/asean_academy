"""Report transcription quality independently from successful pipeline execution."""

import re
from collections import Counter

from .recognition import intersection


def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for i, char in enumerate(a, 1):
        row = [i]
        for j, other in enumerate(b, 1):
            row.append(min(row[-1] + 1, previous[j] + 1, previous[j - 1] + (char != other)))
        previous = row
    return previous[-1]


def text_key(value):
    return " ".join(value.casefold().split())


def formula_key(value):
    # Cosmetic normalization only; never algebraically "correct" OCR mistakes.
    value = (
        re.sub(r"\s+", "", value.replace("\\left", "").replace("\\right", ""))
        .replace("\\dfrac", "\\frac")
        .replace("\\leq", "\\le")
        .replace("\\geq", "\\ge")
    )
    return re.sub(r"([_^])\{(\\[A-Za-z]+|[^{}])\}", r"\1\2", value)


def evaluate(result, fixture):
    expected = fixture["questions"]
    actual = Counter(q.question_number for q in result.questions)
    target = Counter(q["number"] for q in expected)
    matched = sum((actual & target).values())
    source_matches = (
        not fixture.get("source_sha256") or result.document.sha256 == fixture["source_sha256"]
    ) and result.document.page_count == fixture["expected_page_count"]
    classification_matches = [
        p.page_number for p in result.pages if p.page_type == "cover"
    ] == fixture.get("expected_cover_pages", []) and set(
        fixture.get("expected_document_warnings", [])
    ).issubset(result.warnings)
    details = []
    for reference in expected:
        candidates = [q for q in result.questions if q.question_number == reference["number"]]
        if len(candidates) != 1:
            details.append({"number": reference["number"], "found_once": False, "passed": False})
            continue
        question = candidates[0]
        pages = sorted({a.page_number for a in question.assets if a.kind == "question"})
        formulas = [formula_key(b.latex) for b in question.content if b.latex]
        joined = " ".join(formulas)
        formula_hits = [formula_key(f) in joined for f in reference["formulas"]]
        prose = " ".join(b.text for b in question.content if b.type == "text")
        gold_text = " ".join(c["text"] for c in reference["content"] if c["type"] == "text")
        gold, observed = text_key(gold_text), text_key(prose)
        cer = edit_distance(gold, observed) / max(1, len(gold))
        rows = [row for b in question.content if b.type == "table" for row in b.rows]
        expected_cells = [text_key(cell) for row in reference["table_rows"] for cell in row]
        observed_cells = [text_key(cell) for row in rows for cell in row]
        cell_hits = sum(a == b for a, b in zip(expected_cells, observed_cells, strict=False))
        box = reference["bbox"]
        area = (box[2] - box[0]) * (box[3] - box[1])
        coverage = max(
            (
                intersection(box, tuple(a.bbox.model_dump().values())) / area
                for a in question.assets
                if a.page_number == reference["pages"][0]
            ),
            default=0,
        )
        diagram = not reference["diagram"] or any(b.type == "image" for b in question.content)
        passed = (
            pages == reference["pages"]
            and coverage >= 0.95
            and all(formula_hits)
            and cer <= 0.05
            and diagram
            and (not expected_cells or expected_cells == observed_cells)
        )
        details.append(
            {
                "number": reference["number"],
                "found_once": True,
                "source_pages_correct": pages == reference["pages"],
                "crop_coverage": round(coverage, 4),
                "prose_character_error_rate": round(cer, 4),
                "formulas_matched": sum(formula_hits),
                "formulas_expected": len(formula_hits),
                "table_cells_matched": cell_hits,
                "table_cells_expected": len(expected_cells),
                "diagram_retained": diagram,
                "passed": passed,
            }
        )
    return {
        "document_id": str(result.document.id),
        "run_key": result.run_key,
        "fixture_human_verified": fixture.get("human_verified", False),
        "source_matches_fixture": source_matches,
        "classification_matches_fixture": classification_matches,
        "question_recall": matched / max(1, len(expected)),
        "question_precision": matched / max(1, len(result.questions)),
        "questions": details,
        "passed": source_matches
        and classification_matches
        and actual == target
        and all(q["passed"] for q in details),
        "note": "Transcription metrics only; academic verification and publication are separate.",
    }
