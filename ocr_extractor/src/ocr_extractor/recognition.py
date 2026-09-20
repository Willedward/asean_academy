"""Local PP-StructureV3 adapter: layout, prose, PP-FormulaNet and table models.

No provider client or API fallback exists here. Missing/failed models are returned
as review reasons. Layout probability is never reported as transcription accuracy.
"""

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import cv2

from .files import atomic_json, sha256_file
from .models import Settings
from .pdf import Line
from .preprocess import PreparedImage


@dataclass
class Region:
    label: str
    bbox: tuple[float, float, float, float]  # normalized ORIGINAL page coordinates
    text: str = ""
    confidence: float | None = None
    layout_confidence: float | None = None
    rows: list[list[str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Recognition:
    regions: list[Region] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    engine: str = "paddleocr"


class TableParser(HTMLParser):
    """Extract inert cell text. Provider HTML is never trusted or rendered."""

    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], [], None
        self.has_spans = False

    def handle_starttag(self, tag, attrs):
        if tag in {"td", "th"}:
            self.cell = []
            self.has_spans |= any(k in {"rowspan", "colspan"} and v != "1" for k, v in attrs)
        elif tag == "br" and self.cell is not None:
            self.cell.append("\n")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)
            self.row = []


def score(value):
    try:
        value = float(value)
        return value if math.isfinite(value) and 0 <= value <= 1 else None
    except (TypeError, ValueError):
        return None


def intersection(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def normalized_box(prepared, bbox):
    x0, y0, x1, y1 = prepared.original_box(bbox)
    return x0 / prepared.width, y0 / prepared.height, x1 / prepared.width, y1 / prepared.height


def formula_consensus(values: list[str]) -> str | None:
    """Return a strict local majority; never guess when recognition variants disagree."""

    cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if len(cleaned) < 2:
        return None
    value, count = Counter(cleaned).most_common(1)[0]
    return value if count > len(cleaned) / 2 else None


def formula_crop_variants(image, bbox) -> list:
    """Create conservative padded and binarized crops for formula-only recognition."""

    height, width = image.shape[:2]
    try:
        x0, y0, x1, y1 = (int(round(float(value))) for value in bbox)
    except (TypeError, ValueError):
        return []
    x0, x1 = max(0, x0), min(width, x1)
    y0, y1 = max(0, y0), min(height, y1)
    if x1 <= x0 or y1 <= y0:
        return []
    gray = cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
    binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    variants = []
    for crop in (gray, binary):
        pad = max(4, crop.shape[0] // 8)
        padded = cv2.copyMakeBorder(
            crop, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=255
        )
        variants.append(cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR))
    return variants


def decode_result(payload: dict, prepared: PreparedImage) -> Recognition:
    result = Recognition()
    payload = payload.get("res", payload)
    ocr = payload.get("overall_ocr_res", {})
    text_boxes = ocr.get("rec_boxes", [])
    if not len(text_boxes):
        text_boxes = [
            [
                min(p[0] for p in poly),
                min(p[1] for p in poly),
                max(p[0] for p in poly),
                max(p[1] for p in poly),
            ]
            for poly in ocr.get("rec_polys", [])
        ]
    scores = ocr.get("rec_scores", [])
    formulas = payload.get("formula_res_list", [])
    # Paddle inserts formulas into prose as $...$. Split only strings that came
    # from the formula model: prices such as $240 and $212 must stay ordinary text.
    formula_tokens = {}
    for formula in formulas:
        if formula.get("rec_formula"):
            formula_tokens.setdefault(f"${formula['rec_formula']}$", []).append(formula)
    token_pattern = (
        re.compile("|".join(re.escape(t) for t in sorted(formula_tokens, key=len, reverse=True)))
        if formula_tokens
        else None
    )
    for text, box in zip(ocr.get("rec_texts", []), text_boxes, strict=False):
        result.lines.append(Line(text, *normalized_box(prepared, box)))
    layouts = payload.get("layout_det_res", {}).get("boxes", [])
    for item in payload.get("parsing_res_list", []):
        box = item["block_bbox"]
        normalized = normalized_box(prepared, box)
        if normalized[0] >= normalized[2] or normalized[1] >= normalized[3]:
            result.warnings.append("invalid_layout_region")
            continue
        label = item["block_label"]
        text = item.get("block_content", "") or ""
        region = Region(label, normalized, text)
        if label == "formula":
            formula_matches = [
                formula
                for formula in formulas
                if intersection(box, formula.get("dt_polys", [])) > 0
            ]
            if formula_matches:
                formula = max(
                    formula_matches,
                    key=lambda entry: intersection(box, entry["dt_polys"]),
                )
                region.text = formula.get("rec_formula", region.text)
                region.warnings.extend(formula.get("_ocr_extractor_warnings", []))
        matched = [
            entry
            for entry in layouts
            if entry.get("label") == label and intersection(box, entry["coordinate"]) > 0
        ]
        if matched:
            best = max(matched, key=lambda entry: intersection(box, entry["coordinate"]))
            region.layout_confidence = score(best.get("score"))
        if label not in {"formula", "table", "image", "chart"}:
            matched_scores = [
                score(conf)
                for rect, conf in zip(text_boxes, scores, strict=False)
                if intersection(box, rect) > 0.5 * (rect[2] - rect[0]) * (rect[3] - rect[1])
            ]
            if matched_scores and all(v is not None for v in matched_scores):
                region.confidence = min(matched_scores)
        if label == "table":
            parser = TableParser()
            parser.feed(text)
            region.rows = parser.rows
            if parser.has_spans:
                region.warnings.append("table_merged_cells_require_review")
            if not region.rows:
                region.warnings.append("table_structure_missing")
        # The formula/table models don't supply calibrated transcription scores.
        if region.confidence is None:
            region.warnings.append("recognition_confidence_unknown")
        if label in {"text", "paragraph_title", "doc_title", "content"} and token_pattern:
            previous = 0
            for match in token_pattern.finditer(text):
                if text[previous : match.start()].strip():
                    result.regions.append(
                        Region(
                            label,
                            normalized,
                            text[previous : match.start()].strip(),
                            region.confidence,
                            region.layout_confidence,
                            warnings=region.warnings.copy(),
                        )
                    )
                formula = max(
                    formula_tokens[match[0]], key=lambda f: intersection(box, f["dt_polys"])
                )
                result.regions.append(
                    Region(
                        "formula",
                        normalized_box(prepared, formula["dt_polys"]),
                        formula["rec_formula"],
                        layout_confidence=region.layout_confidence,
                        warnings=[
                            "recognition_confidence_unknown",
                            *formula.get("_ocr_extractor_warnings", []),
                        ],
                    )
                )
                previous = match.end()
            if text[previous:].strip():
                result.regions.append(
                    Region(
                        label,
                        normalized,
                        text[previous:].strip(),
                        region.confidence,
                        region.layout_confidence,
                        warnings=region.warnings.copy(),
                    )
                )
        else:
            result.regions.append(region)
    # The reading-order parser can discard a diagram when it overlaps an equation
    # label. The layout detector's image evidence must still reach the reviewer.
    for layout in layouts:
        if layout.get("label") not in {"image", "chart", "figure"}:
            continue
        bbox = normalized_box(prepared, layout["coordinate"])
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area <= 0 or any(
            r.label in {"image", "chart", "figure"} and intersection(r.bbox, bbox) > area * 0.8
            for r in result.regions
        ):
            continue
        # Formula labels inside this image remain visible in its original pixels.
        result.regions = [
            r
            for r in result.regions
            if not (
                r.label == "formula"
                and intersection(r.bbox, bbox)
                > ((r.bbox[2] - r.bbox[0]) * (r.bbox[3] - r.bbox[1]) * 0.9)
            )
        ]
        image = Region(
            "image",
            bbox,
            layout_confidence=score(layout.get("score")),
            warnings=["layout_image_recovered", "recognition_confidence_unknown"],
        )
        position = next(
            (i for i, r in enumerate(result.regions) if r.bbox[1] > bbox[1]), len(result.regions)
        )
        result.regions.insert(position, image)
    if not result.regions:
        result.warnings.append("local_models_no_regions")
    return result


class PaddleRecognizer:
    def __init__(self, settings: Settings, cache: Path):
        self.settings, self.cache = settings, cache
        self.pipeline = None
        self.refiner = None
        self.failure = None

    def _load(self):
        model_cache = self.cache.parent.parent / "model-cache"
        os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(model_cache))
        os.environ.setdefault("HF_HOME", str(model_cache / "huggingface"))
        from paddleocr import PPStructureV3

        self.pipeline = PPStructureV3(
            layout_detection_model_name="PP-DocLayout_plus-L",
            text_detection_model_name="PP-OCRv5_mobile_det",
            text_recognition_model_name="en_PP-OCRv4_mobile_rec",
            formula_recognition_model_name=self.settings.formula_model,
            use_formula_recognition=True,
            use_table_recognition=True,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            use_seal_recognition=False,
            use_chart_recognition=False,
            use_region_detection=False,
            device=self.settings.paddle_device,
            enable_mkldnn=False,
            cpu_threads=2,
        )

    def _formula_model(self):
        formula_pipeline = getattr(
            getattr(self.pipeline, "paddlex_pipeline", None),
            "formula_recognition_pipeline",
            None,
        )
        model = getattr(formula_pipeline, "formula_recognition_model", None)
        if callable(model):
            return model
        if self.refiner is None:
            from paddleocr import FormulaRecognition

            self.refiner = FormulaRecognition(
                model_name=self.settings.formula_model,
                device=self.settings.paddle_device,
                enable_mkldnn=False,
                cpu_threads=2,
            )
        return self.refiner.predict

    def refine_blocks(self, blocks, output: Path) -> list[str]:
        """Refine exact evidence crops; update only when two local variants agree."""

        formulas = [block for block in blocks if block.type == "math"]
        if not formulas:
            return []
        inputs, owners = [], []
        for block in formulas:
            image = cv2.imread(str(output / block.source_path), cv2.IMREAD_COLOR)
            if image is None:
                block.review_reasons.append("formula_refinement_failed")
                continue
            variants = formula_crop_variants(image, [0, 0, image.shape[1], image.shape[0]])
            for variant in variants:
                inputs.append(variant)
                owners.append(block)
        if not inputs:
            return ["formula_refinement_failed"]
        try:
            model = self._formula_model()
            outputs = list(model(inputs))
        except Exception:
            for block in formulas:
                block.review_reasons = sorted(
                    {*block.review_reasons, "formula_refinement_failed"}
                )
            return ["formula_refinement_failed"]
        if len(outputs) != len(inputs):
            return ["formula_refinement_failed"]

        candidates: dict[int, list[str]] = {id(block): [] for block in formulas}
        for owner, result in zip(owners, outputs, strict=True):
            payload = result.json if hasattr(result, "json") else result
            if isinstance(payload, str):
                payload = json.loads(payload)
            payload = payload.get("res", payload)
            value = payload.get("rec_formula")
            if isinstance(value, str) and value.strip():
                candidates[id(owner)].append(value.strip())
        for block in formulas:
            reasons = set(block.review_reasons)
            consensus = formula_consensus(candidates[id(block)])
            if consensus is None:
                reasons.add("formula_variants_disagree")
            elif consensus != (block.latex or "").strip():
                block.latex = consensus
                reasons.add("formula_refined_by_consensus")
            block.review_reasons = sorted(reasons)
        return []

    def extract(self, prepared: PreparedImage) -> Recognition:
        try:
            versions = {name: version(name) for name in ("paddleocr", "paddlex", "paddlepaddle")}
        except PackageNotFoundError:
            return Recognition(warnings=["local_models_unavailable"])
        signature = {
            "image": sha256_file(prepared.path),
            "versions": versions,
            "formula_model": self.settings.formula_model,
            "adapter": "4",
        }
        import hashlib

        key = hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
        cache_file = self.cache / f"{key}.json"
        try:
            if cache_file.is_file():
                result = decode_result(json.loads(cache_file.read_text()), prepared)
                result.engine = "paddleocr/" + versions["paddleocr"]
                return result
        except (ValueError, KeyError, TypeError):
            pass
        if self.failure:
            return Recognition(warnings=[self.failure])
        try:
            if self.pipeline is None:
                self._load()
        except Exception:
            self.failure = "local_models_unavailable"
            return Recognition(warnings=[self.failure])
        try:
            outputs = list(self.pipeline.predict(str(prepared.path)))
            if len(outputs) != 1:
                return Recognition(warnings=["local_models_invalid_output"])
            payload = outputs[0].json
            if isinstance(payload, str):
                payload = json.loads(payload)
            result = decode_result(payload, prepared)
            result.engine = "paddleocr/" + versions["paddleocr"]
            if result.regions:
                atomic_json(cache_file, payload)
            return result
        except Exception:
            return Recognition(warnings=["local_models_failed"])


INLINE_MATH = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\\((.+?)\\\)", re.S)


def split_inline_math(text: str):
    """Only unambiguous delimiters; a pair of currency dollar signs isn't maths."""
    previous = 0
    for match in INLINE_MATH.finditer(text):
        if text[previous : match.start()].strip():
            yield "text", text[previous : match.start()].strip()
        yield "math", next(group for group in match.groups() if group is not None).strip()
        previous = match.end()
    if text[previous:].strip():
        yield "text", text[previous:].strip()
