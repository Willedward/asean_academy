# Sample papers

Place the source exam PDFs here; nested directories are supported. This checkout
did not include the Canberra or Zhonghua PDFs described in `docs/plan/plan.md`.

From the repository root:

```bash
uv sync --project ocr_extractor --locked
uv run --project ocr_extractor ocr-extract extract backend_resources/sample_papers
```

See [the extractor guide](../../ocr_extractor/README.md) for scanned-paper OCR,
vision extraction, database setup and synthetic examples.
