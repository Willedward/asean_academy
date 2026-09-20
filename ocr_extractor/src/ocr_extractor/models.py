"""Versioned contracts shared by extraction, JSON exports and repositories."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.1.0"
PIPELINE_VERSION = "2.1.0"
PROMPT_VERSION = "page-extraction-1.0.0"
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"
Confidence = Annotated[float, Field(ge=0, le=1)]
PageType = Literal[
    "cover",
    "instructions",
    "formula_sheet",
    "question",
    "continuation",
    "answer_key",
    "worked_solution",
    "blank",
    "advertisement",
    "unknown",
]
AnswerType = Literal[
    "integer",
    "decimal",
    "fraction",
    "percentage",
    "algebraic_expression",
    "equation",
    "coordinate",
    "decimal_with_unit",
    "multiple_choice",
    "short_text",
    "multipart",
    "unknown",
]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Box(Model):
    """Normalized coordinates in the displayed page, top left origin."""

    x0: float = Field(ge=0, le=1)
    y0: float = Field(ge=0, le=1)
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def nonempty(self):
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("A crop must have positive width and height")
        return self


class Option(Model):
    label: str
    text: str


class Subpart(Model):
    label: str
    text: str
    latex: str | None
    marks: float | None = Field(ge=0)


class Fragment(Model):
    """One question/solution region on one page; required nullable fields suit strict output."""

    kind: Literal["question", "solution"]
    question_number: str | None
    paper: str | None
    section: str | None
    continues_previous: bool
    bbox: Box
    text: str
    latex: str | None
    subparts: list[Subpart]
    options: list[Option]
    marks: float | None = Field(ge=0)
    answer_type: AnswerType
    official_answer_raw: str | None
    solution_steps: list[str]
    diagram_present: bool | None
    confidence: Confidence | None
    warnings: list[str]


class PageExtraction(Model):
    page_type: PageType
    paper: str | None
    section: str | None
    fragments: list[Fragment]
    warnings: list[str]


class Metadata(Model):
    school: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2200)
    assessment_type: str | None = None
    source_level: str | None = None
    target_track: Literal["sec1_entry", "sec3_entry"] | None = None


class Settings(Model):
    backend: Literal["hybrid", "local", "vision"] = "hybrid"
    ocr: Literal["auto", "off", "required"] = "auto"
    language: str = "eng"
    tessdata: str | None = None
    dpi: int = Field(default=220, ge=100, le=300)
    preprocess: bool = True
    review_threshold: Confidence = 0.9
    paddle_device: str = "cpu"
    formula_model: Literal["PP-FormulaNet_plus-M", "PP-FormulaNet_plus-L", "UniMERNet"] = (
        "PP-FormulaNet_plus-M"
    )
    max_pages: int = Field(default=100, ge=1, le=1000)
    max_file_mb: int = Field(default=100, ge=1, le=1000)
    max_page_pixels: int = Field(default=25_000_000, ge=1)
    model: str = DEFAULT_MODEL
    max_output_tokens: int = Field(default=12000, ge=1000, le=32000)
    metadata: Metadata = Field(default_factory=Metadata)


class PageAnalysis(Model):
    embedded_characters: int = Field(ge=0)
    text_coverage: Confidence
    image_coverage: Confidence
    image_backed: bool
    render_dpi: int
    reasons: list[str]


class ContentBlock(Model):
    """Ordered display content with a crop from the unmodified PDF as evidence.

    Recognition confidence is not academic correctness. None means the recognizer
    does not provide a usable score. Layout scores are recorded separately.
    """

    id: UUID
    type: Literal["text", "math", "table", "image"]
    page_number: int = Field(ge=1)
    bbox: Box
    source_path: str
    source_sha256: str
    text: str = ""
    latex: str | None = None
    rows: list[list[str]] = Field(default_factory=list)
    raw_text: str = ""
    engine: str
    model: str | None = None
    confidence: Confidence | None = None
    layout_confidence: Confidence | None = None
    review_reasons: list[str] = Field(default_factory=list)
    status: Literal["needs_review"] = "needs_review"


class SourcePage(Model):
    id: UUID
    page_number: int = Field(ge=1)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    image_path: str
    image_sha256: str
    text: str
    text_method: Literal["embedded", "tesseract", "paddleocr", "none"]
    page_type: PageType
    warnings: list[str]
    analysis: PageAnalysis | None = None
    preprocessing: dict = Field(default_factory=dict)
    layout_regions: list[dict] = Field(default_factory=list)


class Asset(Model):
    id: UUID
    page_number: int = Field(ge=1)
    kind: Literal["question", "solution"]
    order: int = Field(ge=0)
    path: str
    sha256: str
    bbox: Box
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class AnswerKey(Model):
    raw_text: str
    normalized: str | None = None
    solution_steps: list[str] = Field(default_factory=list)
    pairing_confidence: Confidence | None = None
    source_pages: list[int]
    verified: Literal[False] = False


class Question(Model):
    id: UUID
    document_id: UUID
    question_number: str
    paper: str | None
    section: str | None
    occurrence: int = Field(ge=1)
    question_text: str
    question_latex: str | None
    subparts: list[Subpart]
    options: list[Option]
    marks: float | None = Field(ge=0)
    answer_type: AnswerType
    diagram_present: bool | None
    extraction_confidence: Confidence | None
    status: Literal["needs_review"] = "needs_review"
    review_reasons: list[str]
    assets: list[Asset] = Field(min_length=1)
    answer_key: AnswerKey | None = None
    topic: Literal["unclassified"] = "unclassified"
    content: list[ContentBlock] = Field(default_factory=list)
    raw_ocr_text: str = ""


class AIRun(Model):
    page_number: int
    model: str
    prompt_version: str
    input_sha256: str
    response_id: str | None
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cached: bool


class SourceDocument(Model):
    id: UUID
    sha256: str
    original_filename: str
    storage_path: str
    page_count: int = Field(ge=1)
    metadata: Metadata
    status: Literal["needs_review"] = "needs_review"
    metadata_evidence: dict[str, list[int]] = Field(default_factory=dict)
    review_reasons: list[str] = Field(default_factory=list)


class ExtractionResult(Model):
    schema_version: Literal["1.0.0", "1.1.0"] = SCHEMA_VERSION
    pipeline_version: str = PIPELINE_VERSION
    run_key: str
    created_at: str
    settings: Settings
    document: SourceDocument
    pages: list[SourcePage]
    questions: list[Question]
    unpaired_solutions: list[Asset]
    warnings: list[str]
    ai_runs: list[AIRun]

    @model_validator(mode="after")
    def consistent_references(self):
        page_numbers = {page.page_number for page in self.pages}
        if len(self.pages) != self.document.page_count or page_numbers != set(
            range(1, self.document.page_count + 1)
        ):
            raise ValueError("Source pages must cover the entire document exactly once")
        if len({page.id for page in self.pages}) != len(self.pages):
            raise ValueError("Source page IDs must be unique")
        if len({question.id for question in self.questions}) != len(self.questions):
            raise ValueError("Question IDs must be unique")
        assets = list(self.unpaired_solutions)
        if any(asset.kind != "solution" for asset in assets):
            raise ValueError("Unpaired assets must be solutions")
        for question in self.questions:
            if question.document_id != self.document.id:
                raise ValueError("Question belongs to another source document")
            if not any(asset.kind == "question" for asset in question.assets):
                raise ValueError("Each question needs a question source crop")
            if len({b.id for b in question.content}) != len(question.content):
                raise ValueError("Content block IDs must be unique within a question")
            if any(b.page_number not in page_numbers for b in question.content):
                raise ValueError("Content block references a missing source page")
            if [asset.order for asset in question.assets] != list(range(len(question.assets))):
                raise ValueError("Question assets must have consecutive ordered positions")
            if question.answer_key:
                solution_pages = {a.page_number for a in question.assets if a.kind == "solution"}
                if not question.answer_key.source_pages or not set(
                    question.answer_key.source_pages
                ).issubset(solution_pages):
                    raise ValueError("An official answer needs matching source solution crops")
            assets.extend(question.assets)
        if len({asset.id for asset in assets}) != len(assets):
            raise ValueError("Asset IDs must be unique")
        if any(asset.page_number not in page_numbers for asset in assets):
            raise ValueError("Asset references a missing source page")
        return self
