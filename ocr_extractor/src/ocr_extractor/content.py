"""Assign local layout regions to questions and retain original evidence per block."""

import re
from pathlib import Path
from uuid import uuid5

import pymupdf

from .files import sha256_file
from .local import ANCHOR
from .models import Box, ContentBlock
from .recognition import Recognition, Region, intersection, split_inline_math

MARGIN_LABELS = {"header", "footer", "header_image", "footer_image", "footnote"}
IMAGE_LABELS = {"image", "chart", "figure", "seal"}


def make_content(page, fragment, asset, recognition: Recognition, output: Path, settings):
    clip = tuple(fragment.bbox.model_dump().values())
    regions = []
    for region in recognition.regions:
        overlap = intersection(clip, region.bbox)
        area = (region.bbox[2] - region.bbox[0]) * (region.bbox[3] - region.bbox[1])
        if overlap <= 0 or region.label in MARGIN_LABELS:
            continue
        if re.fullmatch(r"\s*\d+[.)]?\s*", region.text) and region.bbox[0] < 0.25:
            continue
        bbox = (
            max(clip[0], region.bbox[0]),
            max(clip[1], region.bbox[1]),
            min(clip[2], region.bbox[2]),
            min(clip[3], region.bbox[3]),
        )
        if overlap < area * 0.95:
            # A model paragraph spanning two questions is unsafe to duplicate.
            regions.append(Region("image", bbox, warnings=["region_crosses_question_boundary"]))
        else:
            regions.append(region)

    if not regions:
        if fragment.text.strip():
            regions.append(Region("text", clip, fragment.text, warnings=["local_text_unverified"]))
        # Always retain visual fallback when layout recognition failed or was skipped
        # on image-backed/drawn content. Empty OCR becomes a reviewable image block.
        if (
            recognition.warnings
            or not fragment.text.strip()
            or page.get_images()
            or page.get_drawings()
        ):
            regions.append(Region("image", clip, warnings=["layout_requires_review"]))

    blocks = []
    for region in regions:
        label, text = region.label, region.text
        if label == "formula":
            kind = "math"
            text = re.sub(r"^\s*\$\$?|\$\$?\s*$", "", text).strip()
        elif label == "table":
            kind = "table"
        elif label in IMAGE_LABELS:
            kind = "image"
        else:
            kind = "text"
            match = ANCHOR.match(text)
            if (
                match
                and str(int(match[1])) == fragment.question_number
                and (region.bbox[1] < clip[1] + 0.04)
            ):
                text = text[match.end() :].strip()
        pieces = list(split_inline_math(text)) if kind == "text" else [(kind, text)]
        for piece_kind, value in pieces:
            block_id = uuid5(asset.id, f"block:{len(blocks)}")
            box = Box(**dict(zip(("x0", "y0", "x1", "y1"), region.bbox, strict=True)))
            evidence = Path(asset.path).parent.parent / "regions" / f"{block_id}.png"
            destination = output / evidence
            destination.parent.mkdir(parents=True, exist_ok=True)
            crop = pymupdf.Rect(
                box.x0 * page.rect.width,
                box.y0 * page.rect.height,
                box.x1 * page.rect.width,
                box.y1 * page.rect.height,
            )
            if crop.width < 1 or crop.height < 1:
                continue
            page.get_pixmap(dpi=300, clip=crop, colorspace=pymupdf.csRGB, alpha=False).save(
                destination
            )
            reasons = set(region.warnings + recognition.warnings)
            confidence = region.confidence if piece_kind == "text" else None
            if confidence is None:
                reasons.add("recognition_confidence_unknown")
            elif confidence < settings.review_threshold:
                reasons.add("low_recognition_confidence")
            if (
                region.layout_confidence is not None
                and region.layout_confidence < settings.review_threshold
            ):
                reasons.add("low_layout_confidence")
            if piece_kind == "math":
                reasons.add("formula_requires_review")
                if not value or value.count("{") != value.count("}"):
                    reasons.add("invalid_or_empty_latex")
            if piece_kind == "table":
                reasons.add("table_requires_review")
            if piece_kind == "image":
                reasons.add("visual_content_requires_review")
            blocks.append(
                ContentBlock(
                    id=block_id,
                    type=piece_kind,
                    page_number=asset.page_number,
                    bbox=box,
                    source_path=evidence.as_posix(),
                    source_sha256=sha256_file(destination),
                    text=value if piece_kind == "text" else "",
                    latex=value if piece_kind == "math" else None,
                    rows=region.rows if piece_kind == "table" else [],
                    raw_text=region.text,
                    engine=recognition.engine if recognition.regions else "embedded_or_tesseract",
                    model=settings.formula_model if piece_kind == "math" else None,
                    confidence=confidence,
                    layout_confidence=region.layout_confidence,
                    review_reasons=sorted(reasons),
                )
            )
    return blocks


def display_text(blocks):
    return "\n".join(
        block.text
        if block.type == "text"
        else block.latex or ""
        if block.type == "math"
        else "\n".join(" | ".join(row) for row in block.rows)
        if block.type == "table"
        else "[See source diagram]"
        for block in blocks
    )
