import json
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pymupdf
import pytest
from conftest import write_pdf

from ocr_extractor import ExtractionService, Settings
from ocr_extractor.content import make_content
from ocr_extractor.evaluate import evaluate
from ocr_extractor.files import sha256_file
from ocr_extractor.local import Context, LocalExtractor
from ocr_extractor.models import Asset
from ocr_extractor.pdf import analyze_page, read_lines, union_area, words_to_lines
from ocr_extractor.preprocess import prepare_image
from ocr_extractor.recognition import (
    PaddleRecognizer,
    Recognition,
    Region,
    decode_result,
    formula_consensus,
    formula_crop_variants,
)

FIXTURE = Path(__file__).parent / "fixtures" / "beasiswa_aris.json"
SAMPLE = (
    Path(__file__).parents[2] / "backend_resources/sample_papers/Beasiswa_Aris_[2 Oktober 2022].pdf"
)


def test_analysis_detects_images_despite_long_text_overlay(tmp_path):
    path = write_pdf(tmp_path / "mixed.pdf", [[(60, "Running header: " + "text " * 30)]])
    with pymupdf.open(path) as pdf:
        page = pdf[0]
        pix = pymupdf.Pixmap(pymupdf.csRGB, (0, 0, 50, 50), False)
        pix.clear_with(255)
        page.insert_image(pymupdf.Rect(50, 100, 500, 750), pixmap=pix)
        result = analyze_page(page, Settings(dpi=100))
    assert result.embedded_characters > 40
    assert result.image_backed
    assert result.render_dpi == 300
    assert result.image_coverage > result.text_coverage
    assert union_area([(0, 0, 2, 2), (1, 0, 3, 2)]) == 6


def test_preprocessing_preserves_evidence_and_maps_coordinates(tmp_path):
    source = tmp_path / "scan.png"
    img = np.full((800, 800), 240, dtype=np.uint8)
    img[:5] = 0
    for y in range(100, 650, 70):
        cv2.line(img, (80, y), (700, y + 17), 0, 2)
    cv2.imwrite(str(source), img)
    digest = sha256_file(source)
    prepared = prepare_image(source, tmp_path / "prepared.png")
    assert sha256_file(source) == digest
    assert abs(prepared.steps["deskew_degrees"] - 1.57) < 0.4
    assert prepared.steps["removed_border_lines"] == 5
    assert (prepared.width, prepared.height) == (800, 800)
    assert prepared.original_box((0, 0, 800, 800)) == (0, 0, 800, 800)
    clean = cv2.imread(str(prepared.path), cv2.IMREAD_GRAYSCALE)
    assert (clean < 100).sum() > 5000  # Thin rules survive denoising.


def test_formula_refinement_requires_variant_consensus(tmp_path):
    image = np.full((100, 300, 3), 255, dtype=np.uint8)
    cv2.putText(image, "x-3", (40, 65), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
    source = tmp_path / "formula.png"
    cv2.imwrite(str(source), image)
    assert len(formula_crop_variants(image, [30, 20, 150, 80])) == 2
    assert formula_consensus(["x-3", "x-3"]) == "x-3"
    assert formula_consensus(["x-3", "x=3"]) is None

    def recognize(inputs):
        assert len(inputs) == 2
        return iter([{"rec_formula": "x-3"}, {"rec_formula": "x-3"}])

    recognizer = PaddleRecognizer(Settings(), tmp_path / "cache")
    recognizer.pipeline = SimpleNamespace(
        paddlex_pipeline=SimpleNamespace(
            formula_recognition_pipeline=SimpleNamespace(formula_recognition_model=recognize)
        )
    )
    block = SimpleNamespace(
        type="math",
        source_path=source.name,
        latex="x=3",
        review_reasons=["formula_requires_review"],
    )
    assert recognizer.refine_blocks([block], tmp_path) == []
    assert block.latex == "x-3"
    assert "formula_refined_by_consensus" in block.review_reasons


def paddle_payload():
    return {
        "res": {
            "overall_ocr_res": {
                "rec_texts": ["Express", "as a fraction"],
                "rec_boxes": [[10, 30, 70, 55], [140, 30, 270, 55]],
                "rec_scores": [0.97, 0.65],
            },
            "layout_det_res": {
                "boxes": [{"label": "text", "coordinate": [10, 20, 280, 80], "score": 0.99}]
            },
            "formula_res_list": [{"rec_formula": "\\frac{x}{2}", "dt_polys": [75, 20, 130, 80]}],
            "parsing_res_list": [
                {"block_label": "header", "block_bbox": [0, 0, 300, 10], "block_content": "Date"},
                {
                    "block_label": "text",
                    "block_bbox": [10, 20, 280, 80],
                    "block_content": "Express $\\frac{x}{2}$ as a fraction",
                },
                {
                    "block_label": "text",
                    "block_bbox": [10, 90, 280, 140],
                    "block_content": "Reduced from $240 to $212.",
                },
                {
                    "block_label": "table",
                    "block_bbox": [10, 150, 280, 200],
                    "block_content": (
                        '<table><tr><td colspan="2">Rate</td></tr>'
                        "<tr><td>POSB</td><td>2%</td></tr></table>"
                    ),
                },
                {
                    "block_label": "image",
                    "block_bbox": [100, 210, 260, 290],
                    "block_content": "A B C",
                },
            ],
        }
    }


def test_paddle_contract_split_formulas_currency_scores_and_tables(tmp_path):
    source = tmp_path / "page.png"
    cv2.imwrite(str(source), np.full((300, 300), 255, dtype=np.uint8))
    prepared = prepare_image(source, tmp_path / "prepared.png", enabled=False)
    result = decode_result(paddle_payload(), prepared)
    assert [r.label for r in result.regions] == [
        "header",
        "text",
        "formula",
        "text",
        "text",
        "table",
        "image",
    ]
    assert result.regions[1].confidence == 0.65
    formula = result.regions[2]
    assert formula.text == "\\frac{x}{2}"
    assert formula.confidence is None  # Layout confidence isn't formula correctness.
    assert result.regions[4].text == "Reduced from $240 to $212."
    table = result.regions[5]
    assert table.rows == [["Rate"], ["POSB", "2%"]]
    assert "table_merged_cells_require_review" in table.warnings


def test_diagram_survives_parser_omission_and_repeated_formulas_keep_their_source(tmp_path):
    source = tmp_path / "page.png"
    cv2.imwrite(str(source), np.full((300, 300), 255, dtype=np.uint8))
    prepared = prepare_image(source, source, enabled=False)
    payload = {
        "parsing_res_list": [
            {
                "block_label": "text",
                "block_bbox": [10, 10, 280, 50],
                "block_content": "Graph $x+1$",
            },
            {"block_label": "formula", "block_bbox": [90, 110, 130, 140], "block_content": "x+1"},
            {
                "block_label": "text",
                "block_bbox": [10, 240, 280, 270],
                "block_content": "Find $x+1$",
            },
        ],
        "layout_det_res": {
            "boxes": [{"label": "image", "coordinate": [50, 80, 200, 200], "score": 0.98}]
        },
        "formula_res_list": [
            {"rec_formula": "x+1", "dt_polys": [60, 10, 110, 50]},
            {"rec_formula": "x+1", "dt_polys": [90, 110, 130, 140]},
            {"rec_formula": "x+1", "dt_polys": [60, 240, 110, 270]},
        ],
    }
    regions = decode_result(payload, prepared).regions
    assert [r.label for r in regions] == ["text", "formula", "image", "text", "formula"]
    assert regions[1].bbox[1] == pytest.approx(10 / 300)
    assert regions[-1].bbox[1] == pytest.approx(240 / 300)
    assert "layout_image_recovered" in regions[2].warnings


def test_failed_models_preserve_crop_and_never_construct_vision(tmp_path, normal_pdf, monkeypatch):
    def no_provider(*args, **kwargs):
        pytest.fail("Local processing must never instantiate a vision provider")

    monkeypatch.setenv("OPENAI_API_KEY", "should-never-be-used")
    monkeypatch.setattr("ocr_extractor.service.VisionExtractor", no_provider)

    class FailedRecognizer:
        def extract(self, prepared):
            return Recognition(warnings=["local_models_failed"])

    result = ExtractionService(
        tmp_path / "out",
        Settings(dpi=100),
        recognizer=FailedRecognizer(),
    ).extract_file(normal_pdf)
    assert not result.ai_runs
    assert all(q.status == "needs_review" for q in result.questions)
    assert "local_models_failed" in result.questions[0].review_reasons
    assert any(b.type == "image" for b in result.questions[0].content)


def test_header_only_prefix_does_not_continue_previous_question(tmp_path):
    path = write_pdf(
        tmp_path / "headers.pdf",
        [
            [(40, "Jum'at 2 Oktober 2020"), (100, "1. First question")],
            [(40, "Jum'at 2 Oktober 2020"), (100, "2. Second question")],
        ],
    )
    result = ExtractionService(tmp_path / "out", Settings(ocr="off", dpi=100)).extract_file(path)
    assert [len(q.assets) for q in result.questions] == [1, 1]
    assert all("Oktober" not in q.question_text for q in result.questions)


@pytest.mark.skipif(not SAMPLE.is_file(), reason="Sample paper is not in this checkout")
def test_beasiswa_boundaries_and_metadata_against_visual_reference(tmp_path):
    fixture = json.loads(FIXTURE.read_text())
    result = ExtractionService(tmp_path / "out", Settings(ocr="off", dpi=100)).extract_file(SAMPLE)
    assert [q.question_number for q in result.questions] == [
        q["number"] for q in fixture["questions"]
    ]
    assert [[a.page_number for a in q.assets] for q in result.questions] == [
        q["pages"] for q in fixture["questions"]
    ]
    assert result.pages[0].page_type == "cover"
    assert all(p.analysis.image_backed and p.analysis.render_dpi == 300 for p in result.pages[1:])
    assert result.document.metadata.year is None
    assert result.document.metadata_evidence["printed_years"] == [2020]
    assert "metadata_year_conflict" in result.document.review_reasons
    assert all(q.answer_key is None for q in result.questions)
    # Merely finding all eight numbers must not pass the transcription evaluation.
    report = evaluate(result, fixture)
    assert report["question_recall"] == report["question_precision"] == 1
    assert not report["passed"]
    assert all(q["source_pages_correct"] for q in report["questions"])


def test_cross_question_model_region_is_retained_for_review(tmp_path, normal_pdf):
    from uuid import uuid4

    with pymupdf.open(normal_pdf) as document:
        page = document[0]
        fragment = (
            LocalExtractor()
            .extract(
                words_to_lines(page.get_text("words")),
                page.rect.width,
                page.rect.height,
                Context(),
                has_visual_content=False,
            )
            .fragments[0]
        )
        asset = Asset(
            id=uuid4(),
            page_number=1,
            kind="question",
            order=0,
            path="doc/run/crops/one.png",
            sha256="source",
            bbox=fragment.bbox,
            width=100,
            height=100,
        )
        recognition = Recognition(
            regions=[Region("text", (0.0, 0.1, 1.0, 0.8), "Two questions merged")]
        )
        blocks = make_content(page, fragment, asset, recognition, tmp_path, Settings())
    assert blocks[0].type == "image"
    assert "region_crosses_question_boundary" in blocks[0].review_reasons


def test_ocr_library_error_is_reviewable(tmp_path, scanned_pdf, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("OCR library failed")

    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", fail)
    with pymupdf.open(scanned_pdf) as pdf:
        _, _, warnings = read_lines(pdf[0], Settings())
    assert warnings == ["ocr_unavailable"]
