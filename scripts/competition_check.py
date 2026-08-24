from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.evaluate_sourcechain_v0 import evaluate_sourcebench
from scripts.validate_sourcebench import validate_sourcebench


CHECKS = {
    "NIYET tests": (
        "tests/test_runtime.py",
        "tests/test_reviewed_benchmark_metrics.py",
    ),
    "SOURCECHAIN tests": (
        "tests/sourcechain",
        "tests/test_sourcechain_evaluation.py",
    ),
    "Resolution": ("tests/test_drsk_resolution.py",),
    "Escalation": ("tests/test_drsk_orchestrator.py",),
}


def _pytest(paths: tuple[str, ...]) -> bool:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *paths],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def main() -> None:
    sourcebench_root = ROOT / "data" / "sourcebench_tr"
    dataset_valid = not validate_sourcebench(sourcebench_root)
    evaluation = evaluate_sourcebench(sourcebench_root)
    correct = sum(task["correct"] for task in evaluation["metrics"].values())
    total = evaluation["total_examples"]

    statuses = {name: _pytest(paths) for name, paths in CHECKS.items()}
    statuses["Evidence provenance"] = statuses["SOURCECHAIN tests"]
    all_passed = dataset_valid and all(statuses.values())

    print("DRSK Competition Check")
    for name in ("NIYET tests", "SOURCECHAIN tests"):
        print(f"{name:.<22} {'PASS' if statuses[name] else 'FAIL'}")
    print(f"{'SOURCEBENCH-TR':.<22} {correct}/{total}{'' if dataset_valid else ' INVALID'}")
    for name in ("Resolution", "Escalation", "Evidence provenance"):
        print(f"{name:.<22} {'PASS' if statuses[name] else 'FAIL'}")

    raise SystemExit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
