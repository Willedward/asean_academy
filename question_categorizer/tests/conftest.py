import json
from uuid import uuid4

import pytest


def question(number, text, *, content=None):
    return {
        "id": str(uuid4()),
        "question_number": str(number),
        "question_text": text,
        "question_latex": None,
        "subparts": [],
        "content": content
        if content is not None
        else [{"type": "text", "text": text, "latex": None, "rows": []}],
    }


@pytest.fixture
def export_factory(tmp_path):
    def make(questions, *, source_level=None):
        document_id = uuid4()
        run_key = "a" * 24
        directory = tmp_path / "output" / str(document_id) / run_key
        directory.mkdir(parents=True)
        path = directory / "questions.json"
        path.write_text(
            json.dumps(
                {
                    "run_key": run_key,
                    "document": {
                        "id": str(document_id),
                        "metadata": {"source_level": source_level},
                    },
                    "questions": questions,
                }
            )
        )
        return path, document_id, run_key

    return make
