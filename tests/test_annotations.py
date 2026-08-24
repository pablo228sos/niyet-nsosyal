from pathlib import Path

import pytest

from niyet.annotations import validate_annotation_file
from niyet.classifier import load_labeled_texts


HEADER = "example_id,text,source_type,source_group,label_a,label_b,final_label,notes\n"


def test_valid_annotation_file(tmp_path: Path):
    path = tmp_path / "annotations.csv"
    path.write_text(
        HEADER
        + "ex1,Python hatasını nasıl çözebilirim?,team_written,g1,ask,ask,ask,\n",
        encoding="utf-8",
    )

    assert validate_annotation_file(path) == []


def test_duplicate_id_is_rejected(tmp_path: Path):
    path = tmp_path / "annotations.csv"
    path.write_text(
        HEADER
        + "ex1,İlk metin,team_written,g1,ask,ask,ask,\n"
        + "ex1,İkinci metin,team_written,g2,discuss,discuss,discuss,\n",
        encoding="utf-8",
    )

    problems = validate_annotation_file(path)

    assert any(problem.message == "duplicate example_id" for problem in problems)


def test_agreeing_labels_cannot_be_silently_changed(tmp_path: Path):
    path = tmp_path / "annotations.csv"
    path.write_text(
        HEADER
        + "ex1,Tasarımıma yorum yapar mısınız?,public,g1,feedback,feedback,ask,\n",
        encoding="utf-8",
    )

    problems = validate_annotation_file(path)

    assert any("agreeing annotators" in problem.message for problem in problems)


def test_response_gate_labels_are_supported(tmp_path: Path):
    path = tmp_path / "gate.csv"
    path.write_text(
        HEADER
        + "ex1,Yardım eder misiniz?,controlled_seed,g1,response,,response,\n"
        + "ex2,Bugün güneşliydi.,controlled_seed,g2,none,,none,\n",
        encoding="utf-8",
    )

    assert validate_annotation_file(path) == []


def test_malformed_extra_csv_columns_fail_loudly(tmp_path: Path):
    path = tmp_path / "broken.csv"
    path.write_text(
        HEADER
        + "ex1,Virgül, tırnaksız,controlled_seed,g1,ask,,ask,note\n",
        encoding="utf-8",
    )

    problems = validate_annotation_file(path)
    assert any(problem.message == "malformed CSV row" for problem in problems)
    with pytest.raises(ValueError, match="invalid annotation CSV"):
        load_labeled_texts(path)


def test_committed_seed_files_have_all_96_rows():
    root = Path(__file__).resolve().parents[1]
    for name in ("intent_seed_v1.csv", "response_gate_seed_v1.csv"):
        path = root / "data" / name
        assert validate_annotation_file(path) == []
        assert len(load_labeled_texts(path)) == 96
