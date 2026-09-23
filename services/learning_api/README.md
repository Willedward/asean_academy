# Core learning API

This FastAPI service owns the versioned `/api/v1` HTTP boundary. Mathematics
checking and course-domain rules remain in reusable Python packages such as
`question_bank`; HTTP handlers must not duplicate those rules.

Run it from the repository root:

```bash
uv sync --project services/learning_api --locked
uv run --project services/learning_api uvicorn learning_api.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> or request
`http://127.0.0.1:8000/api/v1/health`.

Authentication is intentionally only a documented boundary in Milestone 1.
Private endpoints must use verified Supabase JWTs when identity is implemented
in Stage 4. No endpoint may trust a browser-provided student ID or role.
