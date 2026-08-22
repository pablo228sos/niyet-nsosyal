from pathlib import Path

from niyet.annotations import validate_annotation_file


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
