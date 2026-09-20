import json
import os
from pathlib import Path

import httpx
import pymupdf
import pytest
from openai import OpenAI
from pydantic import ValidationError

from ocr_extractor import ExtractionService, Settings
from ocr_extractor.models import Box, PageExtraction
from ocr_extractor.pdf import ExtractionError
from ocr_extractor.vision import VisionExtractor


def page_output():
    return {
        "page_type": "question",
        "paper": "Paper 1",
        "section": None,
        "warnings": [],
        "fragments": [
            {
                "kind": "question",
                "question_number": "1",
                "paper": "Paper 1",
                "section": None,
                "continues_previous": False,
                "bbox": {"x0": 0.02, "y0": 0.08, "x1": 0.95, "y1": 0.7},
                "text": "Calculate twelve plus eight.",
                "latex": "12 + 8",
                "subparts": [],
                "options": [],
                "marks": 2,
                "answer_type": "integer",
                "official_answer_raw": None,
                "solution_steps": [],
                "diagram_present": False,
                "confidence": 0.95,
                "warnings": [],
            }
        ],
    }


def response_body(payload=None, *, refused=False):
    content = (
        [{"type": "refusal", "refusal": "Unable to transcribe"}]
        if refused
        else [
            {
                "type": "output_text",
                "text": json.dumps(payload or page_output()),
                "annotations": [],
            }
        ]
    )
    return {
        "id": "resp_test",
        "object": "response",
        "created_at": 1,
        "status": "completed",
        "model": "test-snapshot",
        "output": [
            {
                "id": "msg_test",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": content,
            }
        ],
        "usage": {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150},
    }


def mock_client(handler):
    return OpenAI(
        api_key="test-key",
        max_retries=0,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_vision_sdk_contract_scanned_page_and_cache(tmp_path, scanned_pdf):
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json=response_body())

    settings = Settings(backend="vision", ocr="off", dpi=100)
    vision = VisionExtractor(settings, tmp_path / "cache", client=mock_client(handle))
    service = ExtractionService(tmp_path / "output", settings, vision=vision)
    result = service.extract_file(scanned_pdf)
    assert result.pages[0].text_method == "none"
    assert result.questions[0].question_latex == "12 + 8"
    assert result.questions[0].answer_key is None
    assert result.questions[0].status == "needs_review"
    assert result.ai_runs[0].input_tokens == 100
    assert requests[0]["store"] is False
    assert requests[0]["text"]["format"]["strict"] is True
    assert requests[0]["input"][1]["content"][1]["image_url"].startswith("data:image/png;base64,")
    service.extract_file(scanned_pdf, force=True)
    assert len(requests) == 1  # page cache prevents another paid request


@pytest.mark.parametrize("failure", ["refusal", "bad_schema", "network"])
def test_vision_failures_do_not_create_success_manifest(tmp_path, scanned_pdf, failure):
    def handle(request):
        if failure == "network":
            raise httpx.ConnectError("test secret must not be logged", request=request)
        payload = page_output()
        if failure == "bad_schema":
            payload["fragments"][0]["confidence"] = 12
        return httpx.Response(200, json=response_body(payload, refused=failure == "refusal"))

    settings = Settings(backend="vision", ocr="off", dpi=100)
    service = ExtractionService(
        tmp_path / "out",
        settings,
        vision=VisionExtractor(
            settings,
            tmp_path / "cache",
            client=mock_client(handle),
        ),
    )
    with pytest.raises(ExtractionError) as raised:
        service.extract_file(scanned_pdf)
    assert "secret" not in str(raised.value)
    assert not list((tmp_path / "out").rglob("questions.json"))
    assert not list((tmp_path / "cache").glob("*.json"))
    status = json.loads(next((tmp_path / "out").rglob("status.json")).read_text())
    assert status["status"] == "failed"


def test_missing_key_is_actionable(tmp_path, scanned_pdf, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    service = ExtractionService(tmp_path / "out", Settings(backend="vision", ocr="off", dpi=100))
    with pytest.raises(ExtractionError, match="OPENAI_API_KEY"):
        service.extract_file(scanned_pdf)


def test_scan_without_ocr_retains_page_and_signals_no_questions(tmp_path, scanned_pdf):
    service = ExtractionService(tmp_path / "out", Settings(ocr="off", dpi=100))
    result = service.extract_file(scanned_pdf)
    assert not result.questions
    assert result.pages[0].page_type == "unknown"
    assert "no_questions_extracted" in result.warnings
    assert (service.output_dir / result.pages[0].image_path).is_file()


def test_required_ocr_failure_is_actionable(tmp_path, scanned_pdf, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("missing language data")

    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", fail)
    service = ExtractionService(tmp_path / "out", Settings(ocr="required", dpi=100))
    with pytest.raises(ExtractionError, match="Tesseract"):
        service.extract_file(scanned_pdf)


@pytest.mark.ocr
def test_real_image_only_ocr(tmp_path, scanned_pdf):
    tessdata = os.environ.get("TESSDATA_PREFIX")
    if not tessdata or not (Path(tessdata) / "eng.traineddata").is_file():
        pytest.skip("Set TESSDATA_PREFIX to test the real OCR engine")
    settings = Settings(ocr="required", tessdata=tessdata, dpi=200)
    result = ExtractionService(tmp_path / "out", settings).extract_file(scanned_pdf)
    assert result.pages[0].text_method == "tesseract"
    assert [q.question_number for q in result.questions] == ["1", "2"]
    assert "twelve" in result.questions[0].question_text.lower()
    assert "seven" in result.questions[1].question_text.lower()


def test_crop_schema_rejects_invalid_and_nonfinite_coordinates():
    for values in [(0.5, 0, 0.1, 1), (0, 0, 2, 1), (0, 0, float("nan"), 1)]:
        with pytest.raises(ValidationError):
            Box(x0=values[0], y0=values[1], x1=values[2], y1=values[3])
    invalid = page_output()
    invalid["fragments"][0]["invented_field"] = True
    with pytest.raises(ValidationError):
        PageExtraction.model_validate(invalid)
