"""Reusable synchronous worker entry point; invoke from a job runner or the CLI."""

import hashlib
import json
import logging
import re
import shutil
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pymupdf

from .assemble import Assembler
from .content import display_text, make_content
from .files import atomic_json, sha256_file
from .local import ANCHOR, Context, LocalExtractor
from .models import (
    PIPELINE_VERSION,
    Asset,
    ExtractionResult,
    Settings,
    SourceDocument,
    SourcePage,
)
from .pdf import (
    ExtractionError,
    analyze_page,
    margin_key,
    metadata_evidence,
    open_pdf,
    read_lines,
    render_page,
    repeated_margins,
    words_to_lines,
)
from .preprocess import prepare_image
from .recognition import PaddleRecognizer, Recognition
from .vision import VisionExtractor

logger = logging.getLogger(__name__)


class ExtractionService:
    def __init__(
        self,
        output_dir: Path | str,
        settings: Settings | None = None,
        *,
        vision=None,
        recognizer=None,
    ):
        self.output_dir = Path(output_dir).resolve()
        self.settings = settings or Settings()
        # A local job never instantiates a provider client, including on failure.
        self.vision = vision
        if self.settings.backend == "vision" and self.vision is None:
            self.vision = VisionExtractor(self.settings, self.output_dir / "cache" / "vision")
        self.recognizer = recognizer or PaddleRecognizer(
            self.settings, self.output_dir / "cache" / "paddle"
        )

    def result_path(self, result: ExtractionResult) -> Path:
        return self.output_dir / str(result.document.id) / result.run_key / "questions.json"

    def _cache_valid(self, result: ExtractionResult) -> bool:
        # An unavailable OCR engine can become available without changing settings.
        if not result.questions or any(
            page.page_type == "unknown"
            or any(
                reason in page.warnings
                for reason in (
                    "ocr_unavailable",
                    "local_models_unavailable",
                    "local_models_failed",
                    "local_models_no_regions",
                    "local_models_invalid_output",
                )
            )
            for page in result.pages
        ):
            return False
        files = [(result.document.storage_path, result.document.sha256)]
        files.extend((p.image_path, p.image_sha256) for p in result.pages)
        files.extend((a.path, a.sha256) for q in result.questions for a in q.assets)
        files.extend((a.path, a.sha256) for a in result.unpaired_solutions)
        files.extend((b.source_path, b.source_sha256) for q in result.questions for b in q.content)
        for name, checksum in files:
            path = (self.output_dir / name).resolve()
            if not path.is_relative_to(self.output_dir):
                return False
            if not path.is_file() or sha256_file(path) != checksum:
                return False
        return True

    def extract_file(self, path: Path | str, *, force: bool = False) -> ExtractionResult:
        path = Path(path).resolve()
        # Validate before allocating output or hashing potentially oversized inputs.
        with open_pdf(path, self.settings):
            pass
        digest = sha256_file(path)
        document_id = uuid5(NAMESPACE_URL, f"asean-academy:pdf:{digest}")
        signature = json.dumps(
            {
                "document": digest,
                "settings": self.settings.model_dump(mode="json"),
                "pipeline": PIPELINE_VERSION,
                "pymupdf": pymupdf.VersionBind,
                "local_engine_versions": self._local_versions(),
                "filename_years": sorted(set(re.findall(r"\b(?:19|20)\d{2}\b", path.name))),
            },
            sort_keys=True,
        )
        run_key = hashlib.sha256(signature.encode()).hexdigest()[:24]
        relative_dir = Path(str(document_id)) / run_key
        work_dir = self.output_dir / relative_dir
        manifest = work_dir / "questions.json"
        if manifest.is_file() and not force:
            try:
                result = ExtractionResult.model_validate_json(manifest.read_text())
                if result.run_key == run_key and self._cache_valid(result):
                    logger.info("Reusing completed extraction for %s", path.name)
                    return result
            except ValueError:
                pass

        original = self.output_dir / str(document_id) / "original.pdf"
        original.parent.mkdir(parents=True, exist_ok=True)
        if not original.is_file() or sha256_file(original) != digest:
            shutil.copyfile(path, original)
        if sha256_file(original) != digest:
            raise ExtractionError("source_changed", "Source PDF changed during intake; retry.")
        try:
            result = self._process(original, path.name, document_id, digest, relative_dir, run_key)
            atomic_json(manifest, result.model_dump(mode="json"))
            atomic_json(
                work_dir / "status.json",
                {
                    "status": "complete",
                    "review_status": "needs_review",
                    "run_key": run_key,
                    "questions_needing_review": len(result.questions),
                },
            )
            return result
        except Exception as exc:
            code = exc.code if isinstance(exc, ExtractionError) else "processing_failed"
            atomic_json(work_dir / "status.json", {"status": "failed", "error_code": code})
            raise

    def _process(self, original, filename, document_id, digest, relative_dir, run_key):
        assembler = Assembler(document_id)
        pages, runs, warnings = [], [], []
        context = Context()
        local = LocalExtractor()
        content_by_asset = {}
        with open_pdf(original, self.settings) as document:
            for page in document:
                page.remove_rotation()
            ignored_margins = repeated_margins(document)
            evidence, document_warnings = metadata_evidence(document, filename, self.settings)
            warnings.extend(document_warnings)
            for page_index, page in enumerate(document):
                number = page_index + 1
                logger.info("Processing %s: page %s/%s", filename, number, len(document))
                atomic_json(
                    self.output_dir / relative_dir / "status.json",
                    {
                        "status": "processing",
                        "page_number": number,
                        "page_count": len(document),
                    },
                )
                # Normalize rotation in this in-memory copy, preserving visible content.
                # Text coordinates, render and crops then share one coordinate system.
                page.remove_rotation()
                image_relative = relative_dir / "pages" / f"page-{number:04d}.png"
                image_path = self.output_dir / image_relative
                analysis = analyze_page(page, self.settings)
                render_page(page, image_path, self.settings, dpi=analysis.render_dpi)
                prepared = prepare_image(
                    image_path,
                    image_path.parent.parent / "prepared" / image_path.name,
                    enabled=self.settings.preprocess and analysis.image_backed,
                )
                lines, method, page_warnings = read_lines(
                    page,
                    self.settings,
                    analysis=analysis,
                    prepared=prepared,
                )
                recognition = Recognition()
                embedded_lines = words_to_lines(page.get_text("words"))
                preliminary = local.extract(
                    embedded_lines,
                    page.rect.width,
                    page.rect.height,
                    Context(),
                    has_visual_content=bool(page.get_images() or page.get_drawings()),
                    ignored_margins=ignored_margins,
                )
                if (
                    self.settings.backend == "hybrid"
                    and self.settings.ocr != "off"
                    and (
                        preliminary.page_type
                        not in {"cover", "instructions", "formula_sheet", "blank"}
                    )
                ):
                    logger.info(
                        "Running local layout, formula and table recognition: page %s", number
                    )
                    recognition = self.recognizer.extract(prepared)
                    page_warnings.extend(recognition.warnings)
                    if recognition.lines and (
                        method == "none" or "ocr_unavailable" in page_warnings
                    ):
                        lines = words_to_lines(
                            [
                                (
                                    line.x0 * page.rect.width,
                                    line.y0 * page.rect.height,
                                    line.x1 * page.rect.width,
                                    line.y1 * page.rect.height,
                                    line.text,
                                )
                                for line in recognition.lines
                            ]
                        )
                        method = "paddleocr"
                        if "ocr_unavailable" in page_warnings:
                            page_warnings.remove("ocr_unavailable")
                            page_warnings.append("tesseract_unavailable_using_paddle")
                text = "\n".join(line.text for line in lines)
                if self.settings.backend == "vision":
                    extracted, run = self.vision.extract(image_path, text, number, context)
                    runs.append(run)
                    context.paper, context.section = extracted.paper, extracted.section
                    if extracted.fragments:
                        last = extracted.fragments[-1]
                        context.last_number = last.question_number
                        context.solution_mode = last.kind == "solution"
                    elif extracted.page_type != "blank":
                        context.last_number = None
                else:
                    # Number-only PDF overlays are stronger anchors than OCR of the
                    # formula/diagram body. Do not let graph ticks become questions.
                    use_embedded_anchors = analysis.image_backed and (
                        analysis.embedded_characters < 250
                        and any(ANCHOR.match(line.text) for line in embedded_lines)
                    )
                    extracted = local.extract(
                        embedded_lines if use_embedded_anchors else lines,
                        page.rect.width,
                        page.rect.height,
                        context,
                        has_visual_content=bool(page.get_images() or page.get_drawings()),
                        ignored_margins=ignored_margins,
                    )
                    if use_embedded_anchors:
                        for fragment in extracted.fragments:
                            # Rasterized question bodies may start ABOVE their PDF
                            # number (superscripts/fractions). Include that ink too.
                            for image in page.get_image_info():
                                bounds = pymupdf.Rect(image["bbox"])
                                midpoint = (bounds.y0 + bounds.y1) / (2 * page.rect.height)
                                if (
                                    bounds.height < page.rect.height * 0.8
                                    and fragment.bbox.y0 <= midpoint < fragment.bbox.y1
                                    and bounds.y1 / page.rect.height <= fragment.bbox.y1
                                ):
                                    fragment.bbox.y0 = min(
                                        fragment.bbox.y0, max(0, (bounds.y0 - 3) / page.rect.height)
                                    )
                            region_lines = [
                                line.text
                                for line in lines
                                if fragment.bbox.y0 <= line.y0 / page.rect.height < fragment.bbox.y1
                                and margin_key(line.text) not in ignored_margins
                            ]
                            fragment.text = "\n".join(region_lines).strip()
                            leading = ANCHOR.match(fragment.text)
                            if leading and str(int(leading[1])) == fragment.question_number:
                                fragment.text = fragment.text[leading.end() :].strip()
                page_warnings.extend(extracted.warnings)
                if extracted.page_type == "unknown":
                    page_warnings.append("page_requires_review")
                page_id = uuid5(document_id, f"page:{number}")
                pages.append(
                    SourcePage(
                        id=page_id,
                        page_number=number,
                        width=page.rect.width,
                        height=page.rect.height,
                        image_path=image_relative.as_posix(),
                        image_sha256=sha256_file(image_path),
                        text=text,
                        text_method=method,
                        page_type=extracted.page_type,
                        warnings=sorted(set(page_warnings)),
                        analysis=analysis,
                        preprocessing=prepared.steps,
                        layout_regions=[
                            {
                                "label": r.label,
                                "bbox": list(r.bbox),
                                "layout_confidence": r.layout_confidence,
                            }
                            for r in recognition.regions
                        ],
                    )
                )
                for order, fragment in enumerate(extracted.fragments):
                    box = fragment.bbox
                    clip = pymupdf.Rect(
                        box.x0 * page.rect.width,
                        box.y0 * page.rect.height,
                        box.x1 * page.rect.width,
                        box.y1 * page.rect.height,
                    )
                    if clip.width < 2 or clip.height < 2:
                        raise ExtractionError("invalid_crop", f"Tiny crop on page {number}")
                    asset_id = uuid5(page_id, f"{fragment.kind}:{order}")
                    crop_relative = relative_dir / "crops" / f"{asset_id}.png"
                    crop_path = self.output_dir / crop_relative
                    crop_path.parent.mkdir(parents=True, exist_ok=True)
                    pixmap = page.get_pixmap(
                        dpi=analysis.render_dpi,
                        clip=clip,
                        colorspace=pymupdf.csRGB,
                        alpha=False,
                    )
                    pixmap.save(crop_path)
                    thumbnail = page.get_pixmap(
                        matrix=pymupdf.Matrix(0.5, 0.5),
                        clip=clip,
                        colorspace=pymupdf.csGRAY,
                        alpha=False,
                    )
                    dark_pixels = sum(value < 235 for value in thumbnail.samples)
                    if dark_pixels / (thumbnail.width * thumbnail.height) < 0.001:
                        fragment.warnings.append("nearly_blank_crop")
                    if pixmap.width < 100 or pixmap.height < 30:
                        fragment.warnings.append("small_crop")
                    fragment.warnings.extend(page_warnings)
                    fragment.warnings.extend(document_warnings)
                    asset = Asset(
                        id=asset_id,
                        page_number=number,
                        kind=fragment.kind,
                        order=order,
                        path=crop_relative.as_posix(),
                        sha256=sha256_file(crop_path),
                        bbox=box,
                        width=pixmap.width,
                        height=pixmap.height,
                    )
                    assembler.add(fragment, asset)
                    if fragment.kind == "question":
                        content_by_asset[asset.id] = make_content(
                            page,
                            fragment,
                            asset,
                            recognition,
                            self.output_dir,
                            self.settings,
                        )
                warnings.extend(f"page_{number}:{w}" for w in page_warnings)

        if self.settings.backend == "hybrid":
            refine = getattr(self.recognizer, "refine_blocks", None)
            if callable(refine):
                warnings.extend(
                    refine(
                        [block for blocks in content_by_asset.values() for block in blocks],
                        self.output_dir,
                    )
                )

        questions, unpaired = assembler.finish()
        for question in questions:
            question.raw_ocr_text = question.question_text
            question.content = [
                block for asset in question.assets for block in content_by_asset.get(asset.id, [])
            ]
            reasons = set(question.review_reasons)
            reasons.update(reason for block in question.content for reason in block.review_reasons)
            if self.settings.backend == "hybrid":
                question.question_text = display_text(question.content)
                question.question_latex = (
                    "\n\n".join(block.latex for block in question.content if block.latex) or None
                )
                confidences = [block.confidence for block in question.content]
                question.extraction_confidence = (
                    min(confidences)
                    if (confidences and all(value is not None for value in confidences))
                    else None
                )
                question.diagram_present = (
                    True
                    if any(block.type == "image" for block in question.content)
                    else question.diagram_present
                )
            question.review_reasons = sorted(reasons)
        warnings.extend(assembler.warnings)
        if not questions:
            warnings.append("no_questions_extracted")
        return ExtractionResult(
            run_key=run_key,
            created_at=datetime.now(UTC).isoformat(),
            settings=self.settings,
            document=SourceDocument(
                id=document_id,
                sha256=digest,
                original_filename=filename,
                storage_path=original.relative_to(self.output_dir).as_posix(),
                page_count=len(pages),
                metadata=self.settings.metadata,
                metadata_evidence=evidence,
                review_reasons=document_warnings,
            ),
            pages=pages,
            questions=questions,
            unpaired_solutions=unpaired,
            warnings=sorted(set(warnings)),
            ai_runs=runs,
        )

    def _local_versions(self):
        names = ["numpy", "opencv-contrib-python"]
        if self.settings.backend == "hybrid":
            names.extend(["paddleocr", "paddlex", "paddlepaddle"])
        versions = {}
        for name in names:
            try:
                versions[name] = version(name)
            except PackageNotFoundError:
                versions[name] = None
        return versions


def discover_pdfs(path: Path | str) -> list[Path]:
    path = Path(path)
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            raise ExtractionError("invalid_pdf", "Input file must have a .pdf extension")
        return [path]
    if not path.is_dir():
        raise ExtractionError("missing_input", f"Input path does not exist: {path}")
    files = sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf")
    if not files:
        raise ExtractionError("no_pdfs", f"No PDFs found in {path}. Add sample papers and rerun.")
    return files
