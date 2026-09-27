"""Start the local API with repository-scoped development configuration."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").lstrip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def _configure_environment() -> None:
    api_values = _read_env(REPOSITORY_ROOT / "services/learning_api/.env.local")
    web_values = _read_env(REPOSITORY_ROOT / "apps/web/.env.local")
    for key, value in api_values.items():
        os.environ.setdefault(key, value)

    public_auth_mapping = {
        "SUPABASE_URL": "NEXT_PUBLIC_SUPABASE_URL",
        "SUPABASE_ANON_KEY": "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
    }
    for server_key, public_key in public_auth_mapping.items():
        if value := web_values.get(public_key):
            os.environ.setdefault(server_key, value)

    os.environ.setdefault("ASEAN_ACADEMY_REPOSITORY_ROOT", str(REPOSITORY_ROOT))
    os.environ.setdefault("ASEAN_ACADEMY_ALLOW_DRAFT_CONTENT", "true")

    if os.getenv("SUPABASE_URL") and not os.getenv("ASEAN_ACADEMY_DATABASE_URL"):
        print(
            "Local API has Supabase token verification, but hosted onboarding and admin "
            "features still need PostgreSQL. Run corepack pnpm setup:api once."
        )


if __name__ == "__main__":
    _configure_environment()
    uvicorn.run(
        "learning_api.main:app",
        host=os.getenv("ASEAN_ACADEMY_API_HOST", "127.0.0.1"),
        port=int(os.getenv("ASEAN_ACADEMY_API_PORT", "8000")),
        reload=True,
        reload_dirs=[
            str(REPOSITORY_ROOT / "services/learning_api/src"),
            str(REPOSITORY_ROOT / "question_bank/src"),
        ],
    )
