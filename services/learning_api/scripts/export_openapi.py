"""Export a stable OpenAPI document consumed by the web client."""

from __future__ import annotations

import json
from pathlib import Path

from learning_api.config import Settings
from learning_api.main import create_app


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = create_app(
        Settings(environment="test", cors_origins=("http://localhost:3000",), log_level="INFO")
    )
    destination = project_root / "openapi.json"
    destination.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
