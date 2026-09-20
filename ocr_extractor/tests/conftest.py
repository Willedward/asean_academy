from pathlib import Path

import pymupdf
import pytest


def write_pdf(path: Path, pages: list[list[tuple[float, str]]], *, diagram_page=None) -> Path:
    with pymupdf.open() as document:
        for index, lines in enumerate(pages):
            page = document.new_page(width=595, height=842)
            for y, text in lines:
                page.insert_text((45, y), text, fontsize=12)
            if index == diagram_page:
                page.draw_rect(pymupdf.Rect(100, 280, 260, 400))
                page.insert_text((130, 340), "diagram", fontsize=12)
        document.save(path)
    return path


@pytest.fixture
def normal_pdf(tmp_path):
    return write_pdf(
        tmp_path / "ordinary.pdf",
        [
            [
                (45, "Paper 1"),
                (100, "1. Calculate the sum of 12 and 8. [2]"),
                (240, "2. Choose the even number."),
                (270, "A) 3"),
                (295, "B) 4"),
            ],
            [(45, "Paper 1 - Marking Scheme"), (100, "1. 20"), (240, "2. B")],
        ],
    )


@pytest.fixture
def multipage_pdf(tmp_path):
    return write_pdf(
        tmp_path / "multipage.pdf",
        [
            [
                (45, "Paper 1"),
                (70, "Section A"),
                (120, "1. Study the diagram below."),
                (160, "(a) Find its perimeter. [2]"),
            ],
            [
                (45, "Paper 1"),
                (70, "Section A"),
                (130, "(b) Find its area. [3]"),
                (470, "2. Calculate the product of 6 and 7. [1]"),
            ],
            [(45, "Paper 2"), (100, "1. Simplify the fraction 4/8. [1]")],
            [(45, "Answers"), (100, "1. The answer belongs to an unspecified paper.")],
        ],
        diagram_page=0,
    )


@pytest.fixture
def service(tmp_path):
    from ocr_extractor import ExtractionService, Settings

    return ExtractionService(tmp_path / "output", Settings(ocr="off", dpi=100))


@pytest.fixture
def scanned_pdf(tmp_path):
    digital = write_pdf(
        tmp_path / "digital.pdf",
        [
            [
                (60, "Paper 1"),
                (130, "1. Calculate the sum of twelve and eight. [2]"),
                (350, "2. Calculate the product of six and seven. [2]"),
            ]
        ],
    )
    path = tmp_path / "scan.pdf"
    with pymupdf.open(digital) as source, pymupdf.open() as scan:
        image = source[0].get_pixmap(dpi=200).tobytes("png")
        page = scan.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=image)
        scan.save(path)
    return path
