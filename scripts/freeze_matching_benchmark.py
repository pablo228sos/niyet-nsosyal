from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


VALID_GRADES = {0, 1, 2, 3}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))

    final_by_pair: dict[tuple[str, str], int] = {}
    with args.adjudication.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            query_id = row["query_id"].strip()
            responder_id = row["responder_id"].strip()
            raw = row.get("final_relevance", "").strip()
            if not query_id or not responder_id:
                continue
            if raw == "":
                raise ValueError(
                    f"missing final_relevance for {query_id}/{responder_id}"
                )
            grade = int(raw)
            if grade not in VALID_GRADES:
                raise ValueError(
                    f"invalid final_relevance {grade} for {query_id}/{responder_id}"
                )
            final_by_pair[(query_id, responder_id)] = grade

    expected_pairs = 0
    for query in benchmark["queries"]:
        for responder_id in query["relevance"]:
            expected_pairs += 1
            key = (query["id"], responder_id)
            if key not in final_by_pair:
                raise ValueError(f"adjudication is missing pair {key[0]}/{key[1]}")
            query["relevance"][responder_id] = final_by_pair[key]

    if len(final_by_pair) != expected_pairs:
        extras = len(final_by_pair) - expected_pairs
        raise ValueError(f"adjudication pair count mismatch: extras={extras}")

    old_version = str(benchmark.get("version", "v1-draft"))
    base = old_version.removesuffix("-draft")
    benchmark["version"] = f"{base}-reviewed"
    benchmark["review_status"] = "reviewed"
    benchmark["review_metadata"] = {
        "pairs": expected_pairs,
        "process": "two independent team reviewers followed by third-member adjudication",
        "frozen_on": date.today().isoformat(),
        "source": args.adjudication.name,
    }

    notes = [
        note
        for note in benchmark.get("notes", [])
        if "Draft labels" not in str(note)
    ]
    notes.append(
        "Relevance labels were frozen after two independent team reviews and adjudication."
    )
    benchmark["notes"] = notes

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"frozen_pairs: {expected_pairs}")
    print(f"benchmark_version: {benchmark['version']}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
