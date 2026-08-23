from __future__ import annotations

import argparse
import csv
from pathlib import Path
from statistics import mean, median


TASKS = range(1, 7)
RATING_COLUMNS = (
    "activation_clarity_1_5",
    "control_clarity_1_5",
    "match_reason_clarity_1_5",
)


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: str) -> float:
    return float(value.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    args = parser.parse_args()

    with args.results.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("no usability rows")

    print(f"participants: {len(rows)}")

    all_success = []
    all_times = []
    all_hints = []
    for task in TASKS:
        success_col = f"task_{task}_success_without_hint"
        time_col = f"task_{task}_seconds"
        successes = [as_bool(row[success_col]) for row in rows]
        times = [as_float(row[time_col]) for row in rows if row[time_col].strip()]
        all_success.extend(successes)
        all_times.extend(times)
        success_rate = sum(successes) / len(successes)
        task_median = median(times) if times else float("nan")
        print(
            f"task_{task}: success_without_hint={success_rate:.4f}, "
            f"median_seconds={task_median:.2f}"
        )

    for row in rows:
        raw = row.get("total_hints", "").strip()
        if raw:
            all_hints.append(int(raw))

    print(f"overall_task_success_without_hint: {sum(all_success)/len(all_success):.4f}")
    if all_times:
        print(f"median_task_time_seconds: {median(all_times):.2f}")
    if all_hints:
        print(f"median_hints_per_participant: {median(all_hints):.2f}")

    for column in RATING_COLUMNS:
        values = [as_float(row[column]) for row in rows if row[column].strip()]
        if values:
            print(f"{column}: mean={mean(values):.3f}, median={median(values):.3f}")

    confusions: dict[str, int] = {}
    for row in rows:
        value = row.get("main_confusion", "").strip()
        if value:
            confusions[value] = confusions.get(value, 0) + 1
    if confusions:
        print("main_confusions:")
        for text, count in sorted(confusions.items(), key=lambda item: (-item[1], item[0])):
            print(f"  {count}x {text}")


if __name__ == "__main__":
    main()
