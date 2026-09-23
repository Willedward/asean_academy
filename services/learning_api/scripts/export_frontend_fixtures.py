"""Export typed frontend fixtures from the validated course source."""

from __future__ import annotations

import json
from pathlib import Path

from learning_api.course_catalogue import CourseCatalogue


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload.model_dump(mode="json"), indent=2) + "\n")
    print(path)


def main() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    fixture_root = repository_root / "apps/web/src/fixtures"
    catalogue = CourseCatalogue(repository_root, allow_drafts=True)
    _write(fixture_root / "course-map.json", catalogue.course_map("g3-sec1-math"))
    _write(fixture_root / "lesson-01.json", catalogue.lesson("n1-lesson-01"))


if __name__ == "__main__":
    main()
