# ASEAN Academy

An ASEAN scholarship preparation platform in early development.

- [Product plan](docs/plan/plan.md), [architecture](docs/plan/ARCHI.md), and
  [build stages](docs/plan/STAGES.md) describe the planned application.
- [OCR extractor](ocr_extractor/README.md) is a Python worker that converts exam
  PDFs into question JSON, source crops and SQLite/PostgreSQL staging records.
- [Question categorizer](question_categorizer/README.md) maps reviewed question
  parts into the fixed Mathematics syllabus using local, explainable rules.
- `backend_resources/sample_papers` is the input location for source PDFs.
- `frontend_resources` contains branding assets; `main.py` is an initial placeholder.

Run the extractor from the repository root:

```bash
uv sync --project ocr_extractor --locked --extra paddle
uv run --project ocr_extractor --extra paddle ocr-extract extract backend_resources/sample_papers
uv run --project ocr_extractor ocr-extract review
```

Open http://localhost:8765 to compare source crops with editable text, LaTeX,
tables and diagrams. The default pipeline runs local models; failed or uncertain
regions go to human review without automatic vision API calls. Extracted content
remains `needs_review` until academic verification and publication are implemented.
