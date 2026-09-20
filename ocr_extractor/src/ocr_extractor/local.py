"""Conservative single-column segmentation; extracted text is never verified maths."""

import re
from dataclasses import dataclass

from .models import Box, Fragment, Option, PageExtraction, Subpart
from .pdf import Line, margin_key

ANCHOR = re.compile(
    r"^(?:(?:Question|Q)\s*\.?\s*)?(\d{1,3})"
    r"(?:[.)](?!\d)\s*|\s+(?=[A-Za-z(\[])|(?=\([a-zivx]+\))|$)",
    re.IGNORECASE,
)
PAPER = re.compile(r"\bPaper\s+([12]|I{1,2})\b", re.IGNORECASE)
SECTION = re.compile(r"^Section\s+([A-Z]|\d+)\b", re.IGNORECASE)
SOLUTION = re.compile(
    r"\b(?:answers|answer\s+key|(?:worked|suggested)\s+solutions?|"
    r"marking\s+scheme|solutions)\b",
    re.IGNORECASE,
)
MARKS = re.compile(r"\[(\d+(?:\.\d+)?)\s*(?:marks?)?\]", re.IGNORECASE)
PART = re.compile(r"(?m)^\s*\(([a-z]|[ivx]{1,5})\)\s+(.+)")
OPTION = re.compile(r"(?m)^\s*\(?([A-D])\)\s+(.+)")


def solution_heading(text: str) -> bool:
    if ANCHOR.match(text):
        return False
    if re.fullmatch(r"\s*(?:answers|solutions)\s*[:\-]?\s*", text, re.I):
        return True
    return bool(
        re.search(
            r"\b(?:answer\s+key|marking\s+scheme|(?:worked|suggested)\s+solutions?)\b",
            text,
            re.I,
        )
        or (PAPER.search(text) and SOLUTION.search(text))
    )


@dataclass
class Context:
    paper: str | None = None
    section: str | None = None
    solution_mode: bool = False
    last_number: str | None = None
    reaches_bottom: bool = False

    def as_dict(self) -> dict:
        return vars(self).copy()


def _fragment(
    lines: list[Line],
    number: str | None,
    context: Context,
    top: float,
    bottom: float,
    height: float,
    continued: bool,
) -> Fragment:
    text = "\n".join(line.text for line in lines)
    leading = ANCHOR.match(text)
    if number and leading and str(int(leading[1])) == number:
        text = ANCHOR.sub("", text, count=1).strip()
    marks = MARKS.findall(text)
    parts = [Subpart(label=m[1], text=m[2], latex=None, marks=None) for m in PART.finditer(text)]
    options = [Option(label=m[1], text=m[2]) for m in OPTION.finditer(text)]
    return Fragment(
        kind="solution" if context.solution_mode else "question",
        question_number=number,
        paper=context.paper,
        section=context.section,
        continues_previous=continued,
        bbox=Box(x0=0, y0=max(0, top / height), x1=1, y1=min(1, bottom / height)),
        text=text,
        latex=None,
        subparts=parts,
        options=options,
        # Multiple mark labels may be per-part or a total: do not guess a sum.
        marks=float(marks[0]) if len(marks) == 1 else None,
        answer_type="multiple_choice" if options else "unknown",
        official_answer_raw=text if context.solution_mode else None,
        solution_steps=[],
        diagram_present=None,
        confidence=None,
        warnings=["local_text_unverified", "heuristic_boundaries"],
    )


class LocalExtractor:
    def extract(
        self,
        lines: list[Line],
        width: float,
        height: float,
        context: Context,
        *,
        has_visual_content: bool,
        ignored_margins: set[str] | None = None,
    ) -> PageExtraction:
        # Footers and running headers must not become question anchors.
        body = [
            line
            for line in lines
            if line.y0 < height * 0.94
            and not (
                (line.y0 < height * 0.12 or line.y0 > height * 0.9)
                and margin_key(line.text) in (ignored_margins or set())
            )
        ]
        header = "\n".join(line.text for line in body if line.y0 < height * 0.25)
        warnings = []
        if not body:
            context.last_number = None
            return PageExtraction(
                page_type="unknown" if has_visual_content else "blank",
                paper=context.paper,
                section=context.section,
                fragments=[],
                warnings=["no_text_anchors"] if has_visual_content else [],
            )
        if context.last_number is None and not any(ANCHOR.match(line.text) for line in body):
            if re.search(
                r"\b(?:worksheet|online class|candidate name)\b",
                "\n".join(line.text for line in body),
                re.I,
            ):
                return PageExtraction(
                    page_type="cover",
                    paper=context.paper,
                    section=context.section,
                    fragments=[],
                    warnings=[],
                )
        # A question asking for "two solutions" is not a solution-section heading.
        header_lines = [line.text for line in body if line.y0 < height * 0.25]
        is_solution_page = any(solution_heading(text) for text in header_lines)
        paper_match = PAPER.search(header)
        if paper_match:
            label = paper_match[1].upper().replace("II", "2").replace("I", "1")
            paper = f"Paper {label}"
            if paper != context.paper:
                context.paper, context.section, context.last_number = paper, None, None
                if not is_solution_page:
                    context.solution_mode = False
        if is_solution_page and not context.solution_mode:
            context.solution_mode, context.last_number, context.section = True, None, None
            if not paper_match:
                context.paper = None

        # Cover/instruction lists often look exactly like numbered questions.
        if re.search(
            r"\b(?:instructions? to candidates|read these instructions|"
            r"information for candidates)\b",
            header,
            re.I,
        ):
            context.last_number = None
            return PageExtraction(
                page_type="instructions",
                paper=context.paper,
                section=context.section,
                fragments=[],
                warnings=[],
            )
        if re.search(r"\b(?:formula(?:e)? sheet|list of formulae)\b", header, re.I):
            context.last_number = None
            return PageExtraction(
                page_type="formula_sheet",
                paper=context.paper,
                section=context.section,
                fragments=[],
                warnings=[],
            )

        fragments = []
        active: list[Line] = []
        previous_number = context.last_number
        number = None
        continued = False
        top = height * 0.04

        def flush(bottom: float):
            if active and number is not None and bottom > top:
                fragments.append(
                    _fragment(
                        active,
                        number,
                        context,
                        top,
                        bottom,
                        height,
                        continued,
                    )
                )

        for line in body:
            section_match = SECTION.match(line.text)
            if section_match:
                new_section = f"Section {section_match[1].upper()}"
                if new_section != context.section:
                    flush(max(top, line.y0 - 3))
                    active = []
                    number = None
                    context.last_number = None
                context.section = new_section
                continue
            if (
                (PAPER.search(line.text) or solution_heading(line.text))
                and not ANCHOR.match(line.text)
                and line.y0 < height * 0.25
            ):
                continue
            if re.match(r"^(?:Page\s+)?\d+\s+(?:of|/)\s+\d+$", line.text, re.I):
                continue
            if line.y0 < height * 0.1 and re.search(
                r"\b(?:january|february|march|april|may|june|july|august|september|"
                r"october|november|december|oktober)\b.*\b(?:19|20)\d{2}\b",
                line.text,
                re.I,
            ):
                continue
            if re.match(r"^(?:end of (?:paper|questions)|blank page|turn over)\b", line.text, re.I):
                flush(max(top, line.y0 - 3))
                active, number, context.last_number = [], None, None
                continue
            match = ANCHOR.match(line.text) if line.x0 < width * 0.25 else None
            if match and int(match[1]) > 0:
                candidate = str(int(match[1]))
                explicit_continuation = bool(
                    re.search(r"\bcont(?:inued|['’]?d)\b", line.text, re.I)
                )
                # Unpunctuated numbers within an equation are a common false anchor.
                remainder = line.text[match.end() :]
                if re.match(r"^[a-z]\s*[=+*/^−-]", remainder) and not re.match(
                    r"^(?:Q|\d+[.)])",
                    line.text,
                    re.I,
                ):
                    match = None
                else:
                    flush(max(top, line.y0 - 4))
                    active = []
                    number = candidate
                    continued = explicit_continuation or (
                        candidate == context.last_number
                        and bool(re.match(r"^\((?:[b-z]|[ivx]{2,5})\)", remainder))
                    )
                    top = max(0, line.y0 - 5)
                    context.last_number = number
            if (
                number is None
                and previous_number is not None
                and not fragments
                and (
                    re.match(r"^\((?:[b-z]|[ivx]{2,5})\)\s", line.text)
                    or (context.reaches_bottom and line.y0 > height * 0.09)
                )
            ):
                number, continued = previous_number, True
                top = max(0, line.y0 - 5)
            if number is not None:
                active.append(line)
            elif line.y0 > height * 0.25 or context.solution_mode:
                warnings.append(
                    "unrecognized_solution_row"
                    if context.solution_mode
                    else "unassigned_page_content"
                )
        flush(height * 0.94)
        context.reaches_bottom = bool(active and active[-1].y1 > height * 0.83)
        if fragments:
            page_type = "worked_solution" if context.solution_mode else "question"
            if all(f.continues_previous for f in fragments):
                page_type = "worked_solution" if context.solution_mode else "continuation"
        else:
            page_type = "unknown"
            warnings.append("no_question_boundaries")
            context.last_number = None
        return PageExtraction(
            page_type=page_type,
            paper=context.paper,
            section=context.section,
            fragments=fragments,
            warnings=sorted(set(warnings)),
        )
