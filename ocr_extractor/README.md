# OCR extractor

Local PDF ingestion for ASEAN Academy: source analysis, 300 DPI images, image
preparation, question segmentation, layout-aware transcription, JSON/database
staging, and a browser workbench for human review.

**Failed and uncertain regions go to human review. There is no automatic vision
API fallback.** Every extracted question stays `needs_review`. A reviewer can
check the transcription, but publication still requires the application's
academic verification and curriculum gates.

## Install and extract

Run from the repository root with Python 3.12+ and `uv`:

```bash
uv sync --project ocr_extractor --locked --extra paddle --extra postgres
uv run --project ocr_extractor --extra paddle ocr-extract extract \
  'backend_resources/sample_papers/Beasiswa_Aris_[2 Oktober 2022].pdf'
```

The first hybrid run downloads local Paddle model weights. Subsequent inference
runs locally; no API key is needed. Models require substantial disk/RAM and CPU
runs can take minutes per page. The default device is `cpu`; configure a compatible
Paddle GPU installation before selecting `--paddle-device gpu:0`.

Process all sample PDFs by passing `backend_resources/sample_papers` instead of one
file. JSON, source images, and SQLite records go to `ocr_extractor/output` by default.
Use `--output DIRECTORY` for an isolated batch or `--json-only` to skip persistence.

The latest implementation test output for Beasiswa is in
`ocr_extractor/output/hybrid-refined`. The crop-consensus pass improved the
provisional fixture's matched formulas from 14/22 to 17/22; all questions still
require human review.
To view that run:

```bash
uv run --project ocr_extractor ocr-extract review \
  --output ocr_extractor/output/hybrid-refined
```

Open **http://localhost:8765**. For new extractions in the default output folder:

```bash
uv run --project ocr_extractor ocr-extract review
```

The workbench shows original crops beside text, rendered LaTeX, diagrams, and tables.
You can edit/reorder/split blocks, save drafts, check transcriptions, or reject a
candidate. Tables use editable JSON arrays of cell strings. All source pages and
page warnings remain accessible even when segmentation finds no questions.
KaTeX and its fonts are bundled locally; previews need no CDN or paid API.

The workbench binds only to `127.0.0.1`, uses a per-session token and same-origin
checks, and serves only known source assets. It is a local founder tool, not the
future deployed admin application. Use `--port 8766` if the default port is occupied.

## How the hybrid pipeline works

1. **Analyze:** measure the union of embedded text/image rectangles and text density.
   A page with a text header and image question bodies is recognized as image-backed.
   Preserve filename, printed, supplied, and PDF creation years separately; flag
   conflicting years without silently choosing metadata.
2. **Render:** image-backed pages use 300 DPI; other pages use `--dpi` (default 220).
   The pixel budget applies to the actual rendering resolution.
3. **Prepare:** normalize the grayscale background, reduce noise, remove solid dark
   edge strips, and deskew when multiple near-horizontal lines agree. Coordinate
   transforms map recognition regions back to the original page. `--no-preprocess`
   allows comparison with the original render. Crops always use the original PDF.
4. **Segment:** use embedded question-number anchors when the body is rasterized;
   otherwise use embedded/Tesseract/Paddle text coordinates. Exclude repeated
   margins, dates, numbered instructions, and covers. Continuations need a later
   subpart, an explicit continuation marker, or bottom-of-page continuation evidence.
   Nearby raster bodies extend crops above their number to retain superscripts.
5. **Recognize locally:** PaddleOCR PP-StructureV3 runs PP-DocLayout_plus-L, ordinary
   English OCR, PP-FormulaNet_plus-M, and wired/wireless table recognition. It preserves
   reading order and splits model-derived inline formulas into math blocks. Dollar
   amounts remain text. Each detected formula is also rerun as padded grayscale and
   binarized formula-only crops. The initial transcription is replaced only when both
   local reruns agree; disagreement is retained as a human-review reason. Diagram
   detections survive omissions by the reading-order parser; graphs and geometry
   remain original images. Select
   `--formula-model PP-FormulaNet_plus-L` or `--formula-model UniMERNet` to compare
   another supported formula model (additional downloads and compute).
6. **Queue review:** low/unknown recognition confidence, failed models, partial
   regions, missing boundaries, metadata conflicts, and formulas/tables generate
   review reasons. `--review-threshold 0.9` controls score warnings. Formula/table
   models without usable transcription scores retain `confidence: null`; a layout
   score is never substituted for transcription correctness.
7. **Persist:** store raw OCR, source evidence, structured content, and diagnostics.
   Human corrections create separate review revisions. Re-extraction preserves
   review history and marks a review outdated if its source fingerprint changes.

PaddleOCR's [pipeline documentation](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PP-StructureV3.html)
and [formula documentation](https://www.paddleocr.ai/main/en/version3.x/module_usage/formula_recognition.html)
describe the model APIs. Image preparation follows
[Tesseract's quality guidance](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html).

### Backend and OCR options

| Option | Behavior |
| --- | --- |
| `--backend hybrid` (default) | Local layout, prose, formula, and table recognition; requires the `paddle` extra for model recognition |
| `--backend local` | Lightweight embedded text/Tesseract baseline, source crops, and reviewable content blocks |
| `--backend vision` | Existing explicit opt-in paid backend; never selected by hybrid failures |
| `--ocr auto` | OCR missing, sparse, or image-backed text layers; hybrid also runs structured local recognition |
| `--ocr required` | Require Tesseract on every page; unavailable OCR fails with an actionable error |
| `--ocr off` | Embedded text and evidence only; disable local recognition (explicit vision still reads images) |

Without the Paddle extra, hybrid preserves evidence and returns
`local_models_unavailable` for review. If only Tesseract is missing, Paddle can supply
ordinary text; pages record `tesseract_unavailable_using_paddle`.

Optional Tesseract language data on Ubuntu:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng
uv run --project ocr_extractor --extra paddle ocr-extract extract path/to/paper.pdf \
  --tessdata /usr/share/tesseract-ocr/5/tessdata
```

`TESSDATA_PREFIX` is also supported. The tested Paddle prose model is English;
`--language` selects the Tesseract language and does not change that Paddle model.

Models are cached under `OUTPUT/model-cache`. To share weights across output roots,
set `PADDLE_PDX_CACHE_HOME` and `HF_HOME` before starting the worker. After weights
have downloaded, `PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True` avoids startup probes
and `HF_HUB_OFFLINE=1` disables Hugging Face lookups. Paddle may attempt alternate
hosts if a weight is missing; enforce network isolation externally when required.
No local pipeline path uploads source PDFs or invokes a hosted inference service.

The older vision backend still requires an explicitly supplied `--backend vision`,
`--extra vision`, and `OPENAI_API_KEY`. Its implementation is in `vision.py`; it is
independent of the default human-review workflow.

## Output and display contract

```text
output/
  questions.sqlite3
  batch-report.json
  model-cache/
  cache/paddle/<input-and-model-hash>.json
  <document-uuid>/
    original.pdf
    <run-key>/
      questions.json
      status.json
      pages/page-0001.png
      prepared/page-0001.png
      crops/<asset-uuid>.png
      regions/<block-uuid>.png
  reviews/<document-uuid>/<run-key>/<question-uuid>/<review-uuid>.json
```

Schema **1.1.0** adds `pages[].analysis`, preprocessing/layout diagnostics,
`document.metadata_evidence`, `questions[].raw_ocr_text`, and ordered
`questions[].content`. Earlier 1.0 exports remain readable.

A display block has `type: text | math | table | image`, a stable ID, page/bounding
box, original `source_path`/checksum, engine/model provenance, recognition and
layout confidence, and review reasons. Its display value is `text`, `latex`,
`rows`, or the source image respectively. All paths are relative to the output
root. Only mathematical fragments need LaTeX; ordinary prose and diagrams stay
separate. Legacy `question_text` and `question_latex` are convenience summaries;
new clients should render ordered `content`.

`status: complete` in the batch report describes execution only. It is accompanied
by `review_status: needs_review` and `questions_needing_review`. It never means a
question is ready to publish. Missing printed answers and marks stay null.

Generate the schema:

```bash
uv run --project ocr_extractor ocr-extract schema > ocr_extractor/output/schema.json
```

## PostgreSQL and SQLite

For PostgreSQL, load your private `.env` and apply both idempotent migrations. This
upgrades an existing extractor schema without deleting rows:

```bash
uv run --project ocr_extractor --env-file ocr_extractor/.env --extra postgres \
  ocr-extract init-db --postgres
uv run --project ocr_extractor --env-file ocr_extractor/.env \
  --extra postgres --extra paddle ocr-extract extract \
  'backend_resources/sample_papers/Beasiswa_Aris_[2 Oktober 2022].pdf' --postgres
uv run --project ocr_extractor --env-file ocr_extractor/.env --extra postgres \
  ocr-extract review --postgres
```

Tables live in the private `ocr_extractor` schema. Use the trusted worker/schema
owner role. Existing tables retain their raw extraction payloads. New tables:

- `question_blocks`: queryable block type, order, text, LaTeX, confidence, source,
  and full payload including table rows and review reasons.
- `question_reviews`: immutable reviewer revisions, decision, notes, corrected
  content, run key, and source fingerprint. Reviews survive staging re-ingestion.
- `question_display` view: exposes the legacy summary LaTeX and review reasons
  alongside question columns for database viewers.

```sql
SELECT question_number, question_text, question_latex, review_reasons
FROM ocr_extractor.question_display;

SELECT q.question_number, b.block_order, b.type, b.text, b.latex,
       b.confidence, b.payload->'rows' AS table_rows
FROM ocr_extractor.questions q
JOIN ocr_extractor.question_blocks b ON b.question_id = q.id
ORDER BY q.question_number::int, b.block_order;

SELECT reviewer, decision, payload->'content' AS corrected_content
FROM ocr_extractor.question_reviews
ORDER BY created_at DESC;
```

Some source numbers may be unlabelled strings; omit the `::int` cast for those
papers. SQLite uses the same table names without `ocr_extractor.` and stores
payloads as JSON text. Select another file with `--database PATH`.

Saving a review writes its JSON revision and, when started through the CLI, a
`question_reviews` database row. It never overwrites machine output or changes
`questions.status`. For application integration, use the latest checked revision
matching the current question/run/source fingerprint, then apply independent
academic verification, answer-key, curriculum, and publication checks. A checked
transcription alone is not a publishable, automatically markable question.

## Evaluation and tests

`tests/fixtures/beasiswa_aris.json` contains independent visual transcriptions of
all eight questions, formulas, table cells, expected pages and diagram requirements.
The coding agent transcribed the rendered source; **founder confirmation is still
pending**, recorded as `human_verified: false`. The fixture never supplies content
to the extractor and is not used to patch OCR outputs.

```bash
uv run --project ocr_extractor ocr-extract evaluate \
  path/to/questions.json ocr_extractor/tests/fixtures/beasiswa_aris.json \
  --output ocr_extractor/output/evaluation.json
uv run --project ocr_extractor --extra vision --group dev pytest ocr_extractor/tests
uv run --project ocr_extractor --group dev ruff check ocr_extractor/src ocr_extractor/tests
```

Evaluation reports boundary precision/recall, crop coverage, prose character error,
reference-formula matches, table cell accuracy, and diagram retention. It exits 1
when accuracy requirements fail. Successful execution or 8/8 question numbers is
not a passing transcription result. Formula matching normalizes cosmetic notation,
not algebraic errors. Metrics are diagnostics, not proof of academic correctness.

The default tests use synthetic PDFs and controlled model results, plus the real
Beasiswa PDF when present. No tests call a paid API. Set `TESSDATA_PREFIX` for the
optional real Tesseract test and `TEST_DATABASE_URL` for PostgreSQL integration.

## Reliability limits and operations

This remains a candidate-ingestion service. Low-resolution source images cannot
regain missing detail through upscaling. Formula recognition can confuse minus
and equals signs; labels and symbols can still be wrong. Multiple columns, shared
passages, badly damaged pages, and unnumbered questions can need manual segmentation.
The workbench exposes the full pages for those cases; it does not invent missing
questions or answers. Compare several papers before using any automation gate.

Use one extractor process per output directory. Reruns reuse completed outputs
only while evidence hashes match; missing models/failed recognition retry.
Changed engine versions, settings, or source produce new run directories. `--force`
rebuilds candidate assembly while retaining successful local recognition caches.
Delete only the relevant cache entry when deliberately rerunning model inference.
Review revisions refer to their source run and fingerprint, preventing silent reuse
of outdated corrections. Review JSON/database writes are not a distributed
transaction; a database success followed by disk failure requires local recovery.

CLI exit codes: 0 for successful extraction/persistence, 1 for a failed/no-question
input (or failed evaluation), 2 for configuration/initialization errors. Inspect
page warnings and review status even when exit code is 0. Production storage,
deployed authentication, answer normalization and publication remain later backend
integration work described in `docs/plan`.
