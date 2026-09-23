# ASEAN Academy

An ASEAN scholarship preparation platform in early development.

- [PLAN V2](docs/plan/PLAN_V2.md) consolidates the course-based product, service
  boundaries, integration sequence, and delivery plan. The earlier [product plan](docs/plan/plan.md),
  [architecture](docs/plan/ARCHI.md), and [build stages](docs/plan/STAGES.md) remain useful background.
- [OCR extractor](ocr_extractor/README.md) is a Python worker that converts exam
  PDFs into question JSON, source crops and SQLite/PostgreSQL staging records.
- [Question categorizer](question_categorizer/README.md) maps reviewed question
  parts into the fixed Mathematics syllabus using local, explainable rules.
- [N1 practice application](docs/plan/PRACTICE_APPLICATION.md) provides a persistent
  local session API and replaceable student placeholder while the final frontend is designed.
- [N1 course foundation](docs/plan/N1_COURSE_FOUNDATION.md) documents the versioned course map,
  seven draft lesson shells, question-pool allocation, local preview, and PostgreSQL import.
- [Milestone 1 foundation](docs/plan/MILESTONE_1_FOUNDATION.md) documents the production API and
  replaceable Next.js shell, local setup, CI gates, and deliberate blank-lesson workflow.
- [Tutor interaction design](docs/plan/TUTOR_INTERACTION_DESIGN.md) specifies the later grounded,
  multi-turn student-teacher experience and answer-lock rules.
- [Milestone 2 pilot shell](docs/plan/MILESTONE_2_PILOT_SHELL.md) tracks the course-map and blank
  lesson slice, remaining practice/progress work, and content dependencies.
- [Lesson video handoff](docs/plan/LESSON_VIDEO_HANDOFF.md) lets lesson production continue without
  committing large media files or choosing a playback provider prematurely.
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

Run the Milestone 1 applications in two terminals:

```bash
corepack pnpm install
uv sync --project services/learning_api --locked
corepack pnpm dev:api
```

```bash
corepack pnpm dev:web
```

Open <http://localhost:3000>. The temporary foundation screen calls the API at
`http://127.0.0.1:8000/api/v1/health` through a same-origin Next.js rewrite.
