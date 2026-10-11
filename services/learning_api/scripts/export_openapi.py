"""Export a stable OpenAPI document consumed by the web client."""

from __future__ import annotations

import json
from pathlib import Path

from learning_api.config import Settings
from learning_api.main import create_app


def normalize_response_descriptions(document: dict) -> dict:
    """Keep generated contracts stable across Python HTTPStatus wording changes."""
    canonical = {
        "413": "Request Entity Too Large",
        "422": "Unprocessable Entity",
    }
    for path_item in document.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses", {})
            for status, description in canonical.items():
                if status in responses:
                    responses[status]["description"] = description
    return document


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = create_app(
        Settings(environment="test", cors_origins=("http://localhost:3000",), log_level="INFO")
    )
    destination = project_root / "openapi.json"
    document = normalize_response_descriptions(app.openapi())
    destination.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
    print(destination)


if __name__ == "__main__":
    main()
