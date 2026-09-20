"""Assemble ordered regions and conservatively associate official solutions."""

import json
from dataclasses import dataclass, field
from uuid import UUID, uuid5

from .models import AnswerKey, Asset, Fragment, Question


@dataclass
class Candidate:
    number: str
    paper: str | None
    section: str | None
    fragments: list[Fragment] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)


class Assembler:
    def __init__(self, document_id: UUID):
        self.document_id = document_id
        self.questions: list[Candidate] = []
        self.solutions: list[Candidate] = []
        self.warnings: list[str] = []

    def add(self, fragment: Fragment, asset: Asset):
        candidates = self.questions if fragment.kind == "question" else self.solutions
        previous = candidates[-1] if candidates else None
        number = fragment.question_number
        if fragment.continues_previous and previous:
            if (
                (number is None or number == previous.number)
                and fragment.paper == previous.paper
                and fragment.section == previous.section
            ):
                previous.fragments.append(fragment)
                previous.assets.append(asset)
                return
        if not number:
            number = f"unlabelled-page-{asset.page_number}-{asset.order}"
            fragment.warnings.append("missing_question_number")
        if fragment.continues_previous:
            fragment.warnings.append("orphan_continuation")
        candidate = Candidate(number, fragment.paper, fragment.section, [fragment], [asset])
        candidates.append(candidate)

    def finish(self) -> tuple[list[Question], list[Asset]]:
        output = []
        occurrences: dict[tuple, int] = {}
        pairings: dict[int, list[Candidate]] = {}
        unpaired = []
        for solution in self.solutions:
            # Missing labels are unknown, not evidence for the last paper/section.
            matches = [
                i
                for i, question in enumerate(self.questions)
                if question.number == solution.number
                and (solution.paper is None or question.paper == solution.paper)
                and (solution.section is None or question.section == solution.section)
            ]
            if len(matches) == 1:
                pairings.setdefault(matches[0], []).append(solution)
            else:
                unpaired.extend(solution.assets)
                self.warnings.append("ambiguous_or_unmatched_solution")

        for index, candidate in enumerate(self.questions):
            key = candidate.paper, candidate.section, candidate.number
            occurrence = occurrences.get(key, 0) + 1
            occurrences[key] = occurrence
            identity = json.dumps([*key, occurrence])
            question_id = uuid5(self.document_id, identity)
            fragments = candidate.fragments
            reasons = {warning for fragment in fragments for warning in fragment.warnings}
            reasons.update(["academic_verification_not_run", "unclassified"])
            if sum((q.paper, q.section, q.number) == key for q in self.questions) > 1:
                reasons.add("duplicate_question_number")
            if any(
                fragment.confidence is not None and fragment.confidence < 0.9
                for fragment in fragments
            ):
                reasons.add("low_extraction_confidence")
            if not any(fragment.text.strip() for fragment in fragments):
                reasons.add("missing_question_text")
            answer = None
            assets = candidate.assets.copy()
            solutions = pairings.get(index, [])
            if len(solutions) == 1:
                solution = solutions[0]
                source_fragments = solution.fragments
                answer = AnswerKey(
                    raw_text="\n".join(f.official_answer_raw or f.text for f in source_fragments),
                    solution_steps=[step for f in source_fragments for step in f.solution_steps],
                    source_pages=sorted({a.page_number for a in solution.assets}),
                )
                assets.extend(solution.assets)
                reasons.add("official_answer_unverified")
                reasons.update(w for f in source_fragments for w in f.warnings)
            else:
                reasons.add("ambiguous_official_answer" if solutions else "missing_official_answer")
                unpaired.extend(a for solution in solutions for a in solution.assets)
            assets = [asset.model_copy(update={"order": i}) for i, asset in enumerate(assets)]
            confidences = [f.confidence for f in fragments if f.confidence is not None]
            mark_values = [f.marks for f in fragments if f.marks is not None]
            # Repeated totals and per-page subtotals are not distinguishable here.
            marks = mark_values[0] if len(mark_values) == 1 else None
            if len(mark_values) > 1:
                reasons.add("ambiguous_marks")
            answer_types = {f.answer_type for f in fragments} - {"unknown"}
            diagram_values = [f.diagram_present for f in fragments]
            output.append(
                Question(
                    id=question_id,
                    document_id=self.document_id,
                    question_number=candidate.number,
                    paper=candidate.paper,
                    section=candidate.section,
                    occurrence=occurrence,
                    question_text="\n\n".join(f.text for f in fragments),
                    question_latex="\n\n".join(f.latex for f in fragments if f.latex) or None,
                    subparts=[part for f in fragments for part in f.subparts],
                    options=[option for f in fragments for option in f.options],
                    marks=marks,
                    answer_type=next(iter(answer_types)) if len(answer_types) == 1 else "unknown",
                    diagram_present=True
                    if True in diagram_values
                    else (False if all(v is False for v in diagram_values) else None),
                    extraction_confidence=min(confidences)
                    if len(confidences) == len(fragments)
                    else None,
                    review_reasons=sorted(reasons),
                    assets=assets,
                    answer_key=answer,
                )
            )
        return output, unpaired
