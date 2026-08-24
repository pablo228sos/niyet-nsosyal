from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ALLOWED_LABELS = {
    "ASK",
    "FEEDBACK",
    "COLLABORATE",
    "DISCUSS",
    "RESPONSE",
    "NONE",
}
ALLOWED_SOURCE_TYPES = {"public", "team_written", "controlled_seed"}
REQUIRED_COLUMNS = (
    "example_id",
    "text",
    "source_type",
    "source_group",
    "label_a",
    "label_b",
    "final_label",
    "notes",
)


@dataclass(frozen=True)
class AnnotationProblem:
    row: int
    message: str


def _normalize_label(value: str) -> str:
    return value.strip().upper()


def validate_annotation_file(path: str | Path) -> list[AnnotationProblem]:
    problems: list[AnnotationProblem] = []
    seen_ids: set[str] = set()

    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
            return [AnnotationProblem(1, "unexpected CSV columns")]

        for row_number, row in enumerate(reader, start=2):
            if None in row:
                problems.append(AnnotationProblem(row_number, "malformed CSV row"))
                continue
            example_id = row["example_id"].strip()
            text = row["text"].strip()
            source_type = row["source_type"].strip()
            source_group = row["source_group"].strip()
            label_a = _normalize_label(row["label_a"])
            label_b = _normalize_label(row["label_b"])
            final_label = _normalize_label(row["final_label"])

            if not example_id:
                problems.append(AnnotationProblem(row_number, "missing example_id"))
            elif example_id in seen_ids:
                problems.append(AnnotationProblem(row_number, "duplicate example_id"))
            else:
                seen_ids.add(example_id)

            if not text:
                problems.append(AnnotationProblem(row_number, "missing text"))
            if source_type not in ALLOWED_SOURCE_TYPES:
                problems.append(AnnotationProblem(row_number, "invalid source_type"))
            if not source_group:
                problems.append(AnnotationProblem(row_number, "missing source_group"))

            for field_name, value in (
                ("label_a", label_a),
                ("label_b", label_b),
                ("final_label", final_label),
            ):
                if value and value not in ALLOWED_LABELS:
                    problems.append(
                        AnnotationProblem(row_number, f"invalid {field_name}: {value}")
                    )

            if not final_label:
                problems.append(AnnotationProblem(row_number, "missing final_label"))

            if label_a and label_b and label_a == label_b and final_label != label_a:
                problems.append(
                    AnnotationProblem(
                        row_number,
                        "final_label differs from two agreeing annotators",
                    )
                )

    return problems
