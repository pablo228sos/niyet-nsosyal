import json
from pathlib import Path

from scripts.validate_sourcebench import validate_sourcebench


def test_committed_sourcebench_v0_is_valid():
    root = Path(__file__).resolve().parents[1]
    problems = validate_sourcebench(root / "data" / "sourcebench_tr")
    assert problems == []


def test_sourcebench_rejects_duplicate_ids_and_unknown_labels(tmp_path: Path):
    (tmp_path / "statement_types.jsonl").write_text(
        json.dumps({"id": "s1", "text": "x", "label": "UNKNOWN"}) + "\n"
        + json.dumps({"id": "s1", "text": "y", "label": "OPINION"}) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "alignment.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "distortion.jsonl").write_text("", encoding="utf-8")

    problems = validate_sourcebench(tmp_path)
    assert any("unknown label" in item for item in problems)
    assert any("duplicate id" in item for item in problems)
