"""The English diagnostic v2 generator must not undo the hand edits made after generation."""

import importlib.util
import shutil
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "generate_english_diagnostic_v2.py"
REPOSITORY_ENGLISH = Path(__file__).resolve().parents[2] / "backend_resources/english/v1"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_english_diagnostic_v2", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.fixture
def generator(tmp_path, monkeypatch):
    module = _load_generator()
    english = tmp_path / "english"
    for folder in ("banks", "forms"):
        shutil.copytree(REPOSITORY_ENGLISH / folder, english / folder)
    monkeypatch.setattr(module, "ENGLISH", english)
    return module, english


def test_committed_diagnostic_v2_records_are_all_protected():
    module = _load_generator()
    module.ENGLISH = REPOSITORY_ENGLISH
    questions = {key: {} for keys in module.FORM_KEYS.values() for key in keys.values()}
    targets = module.target_paths(questions, {})
    # Every generated question and batch is committed, so a plain re-run refuses.
    assert all(path.exists() for path in targets), [p for p in targets if not p.exists()]


def test_rerun_refuses_to_overwrite_hand_edited_content(generator):
    module, english = generator
    edited = english / "questions" / f"{module.FORM_KEYS['baseline']['vocab']}.json"
    edited.parent.mkdir(parents=True)
    edited.write_text('{"hand_edited": true}\n')
    before = _snapshot(english)

    with pytest.raises(SystemExit) as raised:
        module.main([])

    message = str(raised.value)
    assert "Refusing to overwrite" in message
    assert "edited by hand" in message
    assert "--overwrite-hand-edited" in message
    assert "Nothing was written" in message
    assert _snapshot(english) == before


def test_explicit_flag_allows_a_deliberate_overwrite(generator):
    module, english = generator
    edited = english / "questions" / f"{module.FORM_KEYS['baseline']['vocab']}.json"
    edited.parent.mkdir(parents=True)
    edited.write_text('{"hand_edited": true}\n')

    module.main(["--overwrite-hand-edited"])

    assert "hand_edited" not in edited.read_text()


def test_first_run_on_an_empty_tree_needs_no_flag(generator):
    module, english = generator
    module.main([])
    assert (english / "authoring/batches/english-er-b015.json").is_file()
