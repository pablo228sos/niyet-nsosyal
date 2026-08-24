from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from experiments.evaluate_matching_draft import (
    TOP_K,
    build_batch,
    lexical_similarity_matrix,
    load_data,
    retrieval_metrics,
)
from experiments.evaluate_sourcechain_v0 import evaluate_sourcebench
from niyet.allocator import allocate
from niyet.optimizer import global_allocate


ROOT = Path(__file__).resolve().parents[1]
RESULT_FILENAMES = (
    "sourcechain_v0.json",
    "niyet_retrieval_reviewed.json",
    "niyet_allocation_reviewed.json",
    "test_summary.json",
)


def _metadata() -> dict:
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    }


def _allocation_metrics(queries, responders, similarities, floor: float) -> dict:
    query_by_id = {query.id: query for query in queries}
    aggregate = {
        "greedy": {"covered": 0, "intents": 0, "grades": []},
        "global": {"covered": 0, "intents": 0, "grades": []},
    }
    for start in range(0, len(queries), 8):
        indices = range(start, min(start + 8, len(queries)))
        intents, responder_objects, matches = build_batch(
            queries, responders, similarities, indices, floor
        )
        assignments = {
            "greedy": allocate(matches, responder_objects),
            "global": global_allocate(matches, responder_objects),
        }
        for name, items in assignments.items():
            aggregate[name]["covered"] += len({item.intent_id for item in items})
            aggregate[name]["intents"] += len(intents)
            aggregate[name]["grades"].extend(
                query_by_id[item.intent_id].relevance[item.responder_id] for item in items
            )

    result = {}
    for name, values in aggregate.items():
        grades = values["grades"]
        result[name] = {
            "coverage": round(values["covered"] / values["intents"], 4),
            "mean_reviewed_relevance": round(sum(grades) / len(grades), 4),
            "total_reviewed_relevance": sum(grades),
        }
    return result


def run_tests() -> dict:
    command = [sys.executable, "-m", "pytest", "-q"]
    completed = subprocess.run(
        command, cwd=ROOT, text=True, capture_output=True, check=False
    )
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    passed_match = re.search(r"(\d+) passed", output)
    failed_match = re.search(r"(\d+) failed", output)
    return {
        "command": command,
        "exit_code": completed.returncode,
        "passed": int(passed_match.group(1)) if passed_match else 0,
        "failed": int(failed_match.group(1)) if failed_match else 0,
        "summary": output.splitlines()[-1] if output else "no pytest output",
    }


def build_result_payloads(*, test_summary: dict) -> dict[str, dict]:
    metadata = _metadata()
    benchmark, queries, responders = load_data()
    similarities = lexical_similarity_matrix(queries, responders)
    precision, recall, ndcg = retrieval_metrics(queries, responders, similarities)

    sourcechain = evaluate_sourcebench(ROOT / "data" / "sourcebench_tr")
    sourcechain.update(metadata)
    sourcechain["parameters"] = {
        "statement": "deterministic_rules_v0",
        "alignment": "lexical_structured_v0",
        "distortion": "structured_rules_v0",
    }

    retrieval = {
        **metadata,
        "dataset_version": benchmark["version"],
        "review_status": benchmark["review_status"],
        "parameters": {
            "retriever": "weighted_character_tfidf",
            "topic_weight": 0.8,
            "profile_weight": 0.2,
            "top_k": TOP_K,
        },
        "metrics": {
            "precision_at_3": round(precision, 4),
            "recall_at_3": round(recall, 4),
            "ndcg_at_3": round(ndcg, 4),
        },
    }

    floor = 0.02
    allocation = {
        **metadata,
        "dataset_version": benchmark["version"],
        "review_status": benchmark["review_status"],
        "parameters": {
            "allocator_batch_size": 8,
            "similarity_floor": floor,
            "capacity_per_batch": 1,
        },
        "metrics": _allocation_metrics(queries, responders, similarities, floor),
    }

    tests = {
        **metadata,
        "dataset_version": "repository-test-suite",
        "parameters": {"runner": "pytest", "mode": "quiet"},
        "metrics": test_summary,
    }
    return {
        "sourcechain_v0.json": sourcechain,
        "niyet_retrieval_reviewed.json": retrieval,
        "niyet_allocation_reviewed.json": allocation,
        "test_summary.json": tests,
    }


def write_result_payloads(payloads: dict[str, dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename in RESULT_FILENAMES:
        (output_dir / filename).write_text(
            json.dumps(payloads[filename], ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate measured DRSK result artifacts from executable evaluations."
    )
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    summary = run_tests()
    write_result_payloads(build_result_payloads(test_summary=summary), args.output)
    if summary["exit_code"]:
        raise SystemExit(summary["exit_code"])
    print(f"wrote {len(RESULT_FILENAMES)} artifacts to {args.output}")


if __name__ == "__main__":
    main()
