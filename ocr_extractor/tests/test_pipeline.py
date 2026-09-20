import json
import shutil

import pymupdf
import pytest
from conftest import write_pdf

from ocr_extractor import ExtractionResult, ExtractionService, Settings
from ocr_extractor.pdf import ExtractionError


def test_questions_options_answers_and_source_images(service, normal_pdf):
    result = service.extract_file(normal_pdf)
    assert [q.question_number for q in result.questions] == ["1", "2"]
    assert result.questions[0].question_text == "Calculate the sum of 12 and 8. [2]"
    assert result.questions[0].marks == 2
    assert result.questions[0].answer_key.raw_text == "20"
    assert result.questions[1].answer_key.raw_text == "B"
    assert result.questions[1].answer_type == "multiple_choice"
    assert [o.label for o in result.questions[1].options] == ["A", "B"]
    assert all(q.status == "needs_review" for q in result.questions)
    assert all(q.answer_key.verified is False for q in result.questions)
    for question in result.questions:
        assert [a.kind for a in question.assets] == ["question", "solution"]
        assert [a.page_number for a in question.assets] == [1, 2]
        for asset in question.assets:
            image = pymupdf.Pixmap(service.output_dir / asset.path)
            assert (image.width, image.height) == (asset.width, asset.height)
            assert image.width > 800
    exported = ExtractionResult.model_validate_json(service.result_path(result).read_text())
    assert exported == result


def test_continuations_diagrams_number_restarts_and_ambiguous_solutions(service, multipage_pdf):
    result = service.extract_file(multipage_pdf)
    assert [(q.paper, q.question_number) for q in result.questions] == [
        ("Paper 1", "1"),
        ("Paper 1", "2"),
        ("Paper 2", "1"),
    ]
    first = result.questions[0]
    assert [a.page_number for a in first.assets] == [1, 2]
    assert [a.order for a in first.assets] == [0, 1]
    assert [p.label for p in first.subparts] == ["a", "b"]
    assert "area" in first.question_text
    assert first.assets[0].bbox.y1 > 400 / 842  # diagram isn't clipped
    assert len(result.unpaired_solutions) == 1
    assert all(q.answer_key is None for q in result.questions)
    assert "ambiguous_or_unmatched_solution" in result.warnings


def test_cache_idempotency_rename_and_missing_crop_recovery(service, normal_pdf, monkeypatch):
    first = service.extract_file(normal_pdf)
    copy = normal_pdf.with_name("renamed.pdf")
    shutil.copyfile(normal_pdf, copy)
    original_process = service._process

    def must_not_process(*args):
        raise AssertionError("A complete identical input must be cached")

    monkeypatch.setattr(service, "_process", must_not_process)
    assert service.extract_file(copy) == first
    monkeypatch.setattr(service, "_process", original_process)
    crop = service.output_dir / first.questions[0].assets[0].path
    crop.unlink()
    repaired = service.extract_file(normal_pdf)
    assert crop.is_file()
    assert [q.id for q in repaired.questions] == [q.id for q in first.questions]
    assert [q.assets for q in repaired.questions] == [q.assets for q in first.questions]


def test_configuration_changes_create_new_run_preserving_question_identity(tmp_path, normal_pdf):
    first = ExtractionService(tmp_path / "out", Settings(ocr="off", dpi=100)).extract_file(
        normal_pdf
    )
    second = ExtractionService(tmp_path / "out", Settings(ocr="off", dpi=120)).extract_file(
        normal_pdf
    )
    assert first.run_key != second.run_key
    assert first.questions[0].id == second.questions[0].id
    assert first.questions[0].assets[0].path != second.questions[0].assets[0].path


def test_instructions_formula_and_blank_pages_are_not_questions(service, tmp_path):
    pdf = write_pdf(
        tmp_path / "instructions.pdf",
        [
            [
                (60, "Instructions to Candidates"),
                (130, "1. Answer all questions."),
                (170, "2. Write your name clearly."),
            ],
            [(60, "Formula Sheet"), (130, "1. Area = length x width")],
            [],
            [(130, "1. Calculate the sum of 12 and 8. [2]")],
        ],
    )
    result = service.extract_file(pdf)
    assert [p.page_type for p in result.pages] == [
        "instructions",
        "formula_sheet",
        "blank",
        "question",
    ]
    assert len(result.questions) == 1
    assert result.questions[0].assets[0].page_number == 4


def test_rotated_pdf_coordinates_match_crops(service, tmp_path):
    path = write_pdf(tmp_path / "rotated.pdf", [[(120, "1. Calculate 12 + 8. [2]")]])
    with pymupdf.open(path) as document:
        document[0].set_rotation(90)
        rotated = tmp_path / "rotated-copy.pdf"
        document.save(rotated)
    result = service.extract_file(rotated)
    assert result.pages[0].width == 842
    # The single-column heuristic need not recognize rotated text. The full source is retained.
    assert (service.output_dir / result.pages[0].image_path).is_file()


@pytest.mark.parametrize("kind,code", [("corrupt", "invalid_pdf"), ("encrypted", "encrypted_pdf")])
def test_invalid_inputs_fail_readably(service, tmp_path, kind, code):
    path = tmp_path / "bad.pdf"
    if kind == "corrupt":
        path.write_bytes(b"not a PDF")
    else:
        with pymupdf.open() as document:
            document.new_page()
            document.save(
                path,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw="owner-password",
                user_pw="user-password",
            )
    with pytest.raises(ExtractionError) as raised:
        service.extract_file(path)
    assert raised.value.code == code


def test_page_and_render_limits(normal_pdf, tmp_path):
    service = ExtractionService(tmp_path, Settings(ocr="off", max_pages=1))
    with pytest.raises(ExtractionError, match="1–1 pages"):
        service.extract_file(normal_pdf)
    service = ExtractionService(tmp_path, Settings(ocr="off", max_page_pixels=100))
    with pytest.raises(ExtractionError) as error:
        service.extract_file(normal_pdf)
    assert error.value.code == "page_too_large"
    statuses = list(tmp_path.rglob("status.json"))
    assert json.loads(statuses[0].read_text())["status"] == "failed"


def test_repeated_main_number_with_later_subpart_is_a_continuation(service, tmp_path):
    pdf = write_pdf(
        tmp_path / "subparts.pdf",
        [
            [(120, "1(a) Calculate the sum of 2 and 3. [2]")],
            [
                (120, "1(b) Calculate the product of 2 and 3. [2]"),
                (350, "2. Find the solutions of the equation x squared = 4. [2]"),
            ],
        ],
    )
    result = service.extract_file(pdf)
    assert len(result.questions) == 2
    assert [p.label for p in result.questions[0].subparts] == ["a", "b"]
    assert [a.page_number for a in result.questions[0].assets] == [1, 2]
    assert result.questions[1].assets[0].kind == "question"


def test_answer_instructions_do_not_become_solution_heading(service, tmp_path):
    pdf = write_pdf(
        tmp_path / "answer-instructions.pdf",
        [
            [
                (60, "Give all answers to 3 significant figures."),
                (130, "1. Find the solutions of x squared = 4. [2]"),
            ]
        ],
    )
    result = service.extract_file(pdf)
    assert len(result.questions) == 1
    assert result.questions[0].assets[0].kind == "question"


def test_ambiguous_decimal_solution_anchor_is_reported(service, tmp_path):
    pdf = write_pdf(
        tmp_path / "merged-number.pdf",
        [
            [(120, "1. Calculate the sum of 12 and 8. [2]")],
            [(60, "Marking Scheme"), (120, "1.20")],
        ],
    )
    result = service.extract_file(pdf)
    assert result.questions[0].answer_key is None
    assert "unrecognized_solution_row" in result.pages[1].warnings


def test_result_contract_rejects_missing_pages_and_wrong_document(service, normal_pdf):
    from pydantic import ValidationError

    result = service.extract_file(normal_pdf)
    payload = result.model_dump(mode="json")
    payload["pages"].pop()
    with pytest.raises(ValidationError, match="entire document"):
        ExtractionResult.model_validate(payload)
    payload = result.model_dump(mode="json")
    payload["questions"][0]["document_id"] = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(ValidationError, match="another source document"):
        ExtractionResult.model_validate(payload)
