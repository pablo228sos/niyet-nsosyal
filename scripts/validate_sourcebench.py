from __future__ import annotations

import argparse
import json
from pathlib import Path


LABELS = {
    "statement_types.jsonl": {"FACTUAL_CLAIM", "OPINION", "PERSONAL_EXPERIENCE", "PREDICTION", "QUESTION", "MIXED"},
    "alignment.jsonl": {"SUPPORTED", "PARTIALLY_SUPPORTED", "CONFLICTING", "INSUFFICIENT"},
    "distortion.jsonl": {"NONE", "CERTAINTY_SHIFT", "CAUSALITY_SHIFT", "NUMERIC_DISTORTION", "SCOPE_SHIFT", "ATTRIBUTION_SHIFT", "TEMPORAL_SHIFT"},
}


def validate_sourcebench(root: str | Path) -> list[str]:
    root = Path(root)
    problems: list[str] = []
    seen: set[str] = set()
    for filename, labels in LABELS.items():
        path = root / filename
        if not path.exists():
            problems.append(f"{filename}: missing file")
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"{filename}:{line_number}: invalid JSON")
                continue
            item_id = str(item.get("id", "")).strip()
            label = str(item.get("label", "")).strip()
            if not item_id:
                problems.append(f"{filename}:{line_number}: missing id")
            elif item_id in seen:
                problems.append(f"{filename}:{line_number}: duplicate id {item_id}")
            else:
                seen.add(item_id)
            if label not in labels:
                problems.append(f"{filename}:{line_number}: unknown label {label}")
            if not any(str(item.get(field, "")).strip() for field in ("text", "claim", "child_text")):
                problems.append(f"{filename}:{line_number}: missing text")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="data/sourcebench_tr")
    args = parser.parse_args()
    problems = validate_sourcebench(args.path)
    if problems:
        print("\n".join(problems))
        raise SystemExit(1)
    print("SOURCEBENCH-TR v0 looks valid")


if __name__ == "__main__":
    main()
