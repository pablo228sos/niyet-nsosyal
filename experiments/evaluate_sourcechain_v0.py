from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from sourcechain.alignment import align_claim
from sourcechain.statement_classifier import classify_statement
from sourcechain.structured_checks import detect_distortions


ROOT = Path(__file__).resolve().parents[1]
FILES = ("statement_types.jsonl", "alignment.jsonl", "distortion.jsonl")


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _task_result(cases: list[dict]) -> dict:
    correct = sum(item["correct"] for item in cases)
    return {
        "total": len(cases),
        "correct": correct,
        "accuracy": round(correct / len(cases), 6) if cases else None,
    }


def _dataset_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for filename in FILES:
        digest.update(filename.encode("utf-8"))
        digest.update((root / filename).read_bytes())
    return digest.hexdigest()


def evaluate_sourcebench(root: str | Path) -> dict:
    root = Path(root)
    cases: list[dict] = []
    by_task: dict[str, list[dict]] = {"statement_type": [], "alignment": [], "distortion": []}

    for row in _rows(root / "statement_types.jsonl"):
        predicted = classify_statement(row["text"]).value
        case = {"id": row["id"], "task": "statement_type", "gold": row["label"], "predicted": predicted, "correct": predicted == row["label"]}
        cases.append(case)
        by_task["statement_type"].append(case)

    for row in _rows(root / "alignment.jsonl"):
        predicted = align_claim(row["claim"], row["passage"]).value
        gold = "PARTIALLY_SUPPORTED" if row["label"] == "PARTIALLY_SUPPORTED" else row["label"]
        case = {"id": row["id"], "task": "alignment", "gold": gold, "predicted": predicted, "correct": predicted == gold}
        cases.append(case)
        by_task["alignment"].append(case)

    for row in _rows(root / "distortion.jsonl"):
        predicted_values = [item.value for item in detect_distortions(row["child_text"], row["parent_text"])]
        case = {"id": row["id"], "task": "distortion", "gold": row["label"], "predicted": predicted_values, "correct": row["label"] in predicted_values}
        cases.append(case)
        by_task["distortion"].append(case)

    task_metrics = {name: _task_result(task_cases) for name, task_cases in by_task.items()}
    return {
        "dataset_version": "SOURCEBENCH-TR-v0-development",
        "development_only": True,
        "dataset_sha256": _dataset_hash(root),
        "total_examples": len(cases),
        "tasks": task_metrics,
        "metrics": task_metrics,
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "sourcebench_tr")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate_sourcebench(args.dataset)
    result["generated_at"] = datetime.now(UTC).isoformat()
    result["git_commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    result["parameters"] = {"statement": "deterministic_rules_v0", "alignment": "lexical_structured_v0", "distortion": "structured_rules_v0"}
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
