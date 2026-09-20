"""PDF rendering and text anchors. Crops always come from the original page."""

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pymupdf

from .models import PageAnalysis, Settings
from .preprocess import PreparedImage


class ExtractionError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


@dataclass
class Line:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


def union_area(rectangles) -> float:
    """Area of a rectangle union, so repeated image masks don't inflate coverage."""
    rectangles = [r for r in rectangles if r[2] > r[0] and r[3] > r[1]]
    xs = sorted({x for r in rectangles for x in (r[0], r[2])})
    total = 0.0
    for left, right in zip(xs, xs[1:], strict=False):
        intervals = sorted((r[1], r[3]) for r in rectangles if r[0] < right and r[2] > left)
        end, covered = -float("inf"), 0.0
        for start, stop in intervals:
            covered += max(0, stop - max(start, end))
            end = max(end, stop)
        total += (right - left) * covered
    return total


def analyze_page(page: pymupdf.Page, settings: Settings) -> PageAnalysis:
    words = page.get_text("words")
    area = page.rect.get_area()
    images = [pymupdf.Rect(i["bbox"]) & page.rect for i in page.get_image_info()]
    image_coverage = min(1.0, union_area(images) / area)
    text_coverage = min(1.0, union_area([w[:4] for w in words]) / area)
    characters = sum(len(w[4]) for w in words)
    image_backed = image_coverage > 0.1 and (
        image_coverage > 0.45 or characters < 250 or image_coverage > text_coverage * 6
    )
    reasons = []
    if image_backed:
        reasons.append("image_backed_page")
    if characters < 40:
        reasons.append("sparse_text_layer")
    return PageAnalysis(
        embedded_characters=characters,
        text_coverage=text_coverage,
        image_coverage=image_coverage,
        image_backed=image_backed,
        render_dpi=300 if image_backed else settings.dpi,
        reasons=reasons,
    )


def margin_key(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def repeated_margins(document) -> set[str]:
    counts = Counter()
    for page in document:
        candidates = set()
        for line in words_to_lines(page.get_text("words")):
            if line.y1 < page.rect.height * 0.09 or line.y0 > page.rect.height * 0.92:
                key = margin_key(line.text)
                # Preserve Paper/Section labels because they carry pairing context.
                if len(key) > 8 and not re.search(r"\b(paper|section|question|answer)\b", key):
                    candidates.add(key)
        counts.update(candidates)
    return {text for text, count in counts.items() if count >= 2}


def metadata_evidence(document, filename: str, settings: Settings) -> tuple[dict, list[str]]:
    def years(value):
        return sorted({int(v) for v in re.findall(r"\b(?:19|20)\d{2}\b", value)})

    evidence = {
        "filename_years": years(filename),
        "printed_years": years("\n".join(page.get_text() for page in document)),
        "pdf_created_years": years((document.metadata.get("creationDate") or "")[2:6]),
        "supplied_years": [settings.metadata.year] if settings.metadata.year else [],
    }
    primary = set(
        evidence["filename_years"] + evidence["printed_years"] + evidence["supplied_years"]
    )
    warnings = ["metadata_year_conflict"] if len(primary) > 1 else []
    if (
        primary
        and evidence["pdf_created_years"]
        and not primary.intersection(evidence["pdf_created_years"])
    ):
        warnings.append("metadata_creation_year_differs")
    return evidence, warnings


def open_pdf(path: Path, settings: Settings) -> pymupdf.Document:
    if not path.is_file():
        raise ExtractionError("missing_file", f"PDF does not exist: {path}")
    if path.stat().st_size > settings.max_file_mb * 1024 * 1024:
        raise ExtractionError("file_too_large", f"PDF exceeds {settings.max_file_mb} MB")
    try:
        document = pymupdf.open(path)
    except (RuntimeError, ValueError) as exc:
        raise ExtractionError("invalid_pdf", f"Cannot open PDF: {path.name}") from exc
    if not document.is_pdf:
        document.close()
        raise ExtractionError("invalid_pdf", "Input must be a PDF document")
    if document.needs_pass:
        document.close()
        raise ExtractionError("encrypted_pdf", "Password-protected PDFs are not supported")
    if not 0 < len(document) <= settings.max_pages:
        document.close()
        raise ExtractionError("page_limit", f"PDF must contain 1–{settings.max_pages} pages")
    return document


def render_page(page: pymupdf.Page, path: Path, settings: Settings, *, dpi=None) -> None:
    dpi = dpi or settings.dpi
    pixels = page.rect.width * page.rect.height * (dpi / 72) ** 2
    if pixels > settings.max_page_pixels:
        raise ExtractionError("page_too_large", "Rendered page exceeds max_page_pixels")
    path.parent.mkdir(parents=True, exist_ok=True)
    page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False).save(path)


def read_lines(
    page: pymupdf.Page,
    settings: Settings,
    *,
    analysis: PageAnalysis | None = None,
    prepared: PreparedImage | None = None,
) -> tuple[list[Line], str, list[str]]:
    textpage = page.get_textpage()
    words = page.get_text("words", textpage=textpage)
    method = "embedded" if words else "none"
    warnings = []
    # Sparse text (often just a header over a scan) also needs OCR.
    sparse = sum(len(word[4]) for word in words) < 40
    if settings.ocr == "required" or (
        settings.ocr == "auto" and (sparse or (analysis and analysis.image_backed))
    ):
        try:
            if prepared:
                with pymupdf.open() as scan:
                    raster_page = scan.new_page(width=prepared.width, height=prepared.height)
                    raster_page.insert_image(raster_page.rect, filename=str(prepared.path))
                    textpage = raster_page.get_textpage_ocr(
                        language=settings.language,
                        dpi=72,
                        full=True,
                        tessdata=settings.tessdata,
                    )
                    recognized = raster_page.get_text("words", textpage=textpage)
                    words = []
                    for word in recognized:
                        x0, y0, x1, y1 = prepared.original_box(word[:4])
                        words.append(
                            (
                                x0 / prepared.width * page.rect.width,
                                y0 / prepared.height * page.rect.height,
                                x1 / prepared.width * page.rect.width,
                                y1 / prepared.height * page.rect.height,
                                *word[4:],
                            )
                        )
            else:
                textpage = page.get_textpage_ocr(
                    language=settings.language,
                    dpi=analysis.render_dpi if analysis else settings.dpi,
                    full=True,
                    tessdata=settings.tessdata,
                )
                words = page.get_text("words", textpage=textpage)
            method = "tesseract"
        except Exception as exc:
            if settings.ocr == "required":
                raise ExtractionError(
                    "ocr_unavailable",
                    "OCR failed. Install Tesseract language data or set --tessdata.",
                ) from exc
            warnings.append("ocr_unavailable")
    return words_to_lines(words), method, warnings


def words_to_lines(words) -> list[Line]:
    # Join nearby words, including numbers in separate PDF text blocks. This baseline
    # assumes one column; vision is the supported route for complex layouts.
    rows: list[list[tuple]] = []
    for word in sorted(words, key=lambda word: (word[1], word[0])):
        if rows and abs(word[1] - rows[-1][0][1]) <= max(3, (word[3] - word[1]) * 0.35):
            rows[-1].append(word)
        else:
            rows.append([word])
    lines = []
    for row in rows:
        row.sort(key=lambda word: word[0])
        lines.append(
            Line(
                text=" ".join(word[4] for word in row),
                x0=min(word[0] for word in row),
                y0=min(word[1] for word in row),
                x1=max(word[2] for word in row),
                y1=max(word[3] for word in row),
            )
        )
    return lines
