"""Create original synthetic fixtures, including an image-only copy (no OCR layer)."""

import argparse
from pathlib import Path

import pymupdf


def create_demo(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    with pymupdf.open() as document:
        pages = [
            [
                (45, "Paper 1"),
                (70, "Section A"),
                (120, "1. Calculate the sum of twelve and eight. [2]"),
                (260, "2. A rectangle has length 8 cm and width 3 cm."),
                (295, "(a) Find its perimeter. [2]"),
            ],
            [
                (45, "Paper 1"),
                (70, "Section A"),
                (120, "2(b) Find the area of the rectangle. [2]"),
                (350, "3. Choose the even number. [1]"),
                (385, "A) 3"),
                (415, "B) 4"),
            ],
            [
                (45, "Paper 1 - Marking Scheme"),
                (70, "Section A"),
                (120, "1. 20"),
                (260, "2. (a) 22 cm; (b) 24 square cm"),
                (400, "3. B"),
            ],
        ]
        for index, lines in enumerate(pages):
            page = document.new_page(width=595, height=842)
            for y, text in lines:
                page.insert_text((45, y), text, fontsize=12)
            if index == 0:
                page.draw_rect(pymupdf.Rect(120, 340, 360, 430))
                page.insert_text((220, 450), "8 cm")
                page.insert_text((370, 390), "3 cm")
        document.save(directory / "synthetic-paper.pdf", deflate=True)
        with pymupdf.open() as scanned:
            for source in document:
                page = scanned.new_page(width=source.rect.width, height=source.rect.height)
                page.insert_image(page.rect, stream=source.get_pixmap(dpi=200).tobytes("png"))
            scanned.save(directory / "synthetic-scan.pdf", deflate=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "output", type=Path, nargs="?", default=Path("ocr_extractor/output/demo-input")
    )
    create_demo(parser.parse_args().output)
