from __future__ import annotations

import argparse
from collections.abc import Callable

from niyet.allocator import Assignment, allocate
from niyet.baselines import random_capacity, topic_capacity, unconstrained_best_match
from niyet.benchmark import Benchmark, load_benchmark
from niyet.metrics import (
    intent_coverage,
    mean_gold_relevance,
    overload_count,
    responder_load_gini,
)
from niyet.optimizer import global_allocate


Allocator = Callable[[Benchmark], list[Assignment]]


def methods() -> dict[str, Allocator]:
    return {
        "random_capacity": lambda benchmark: random_capacity(
            [item.match for item in benchmark.matches], benchmark.responders
        ),
        "topic_capacity": lambda benchmark: topic_capacity(
            [item.match for item in benchmark.matches], benchmark.responders
        ),
        "unconstrained_best": lambda benchmark: unconstrained_best_match(
            [item.match for item in benchmark.matches]
        ),
        "greedy_pair_score": lambda benchmark: allocate(
            [item.match for item in benchmark.matches], benchmark.responders
        ),
        "global_allocation": lambda benchmark: global_allocate(
            [item.match for item in benchmark.matches], benchmark.responders
        ),
    }


def evaluate(name: str, assignments: list[Assignment], benchmark: Benchmark) -> None:
    print(
        f"{name:20s} "
        f"coverage={intent_coverage(assignments, benchmark.intents):.3f} "
        f"gold={mean_gold_relevance(assignments, benchmark.matches):.3f} "
        f"load_gini={responder_load_gini(assignments, benchmark.responders):.3f} "
        f"overload={overload_count(assignments, benchmark.responders)}"
    )


parser = argparse.ArgumentParser()
parser.add_argument("path", nargs="?", default="data/toy_benchmark.json")
args = parser.parse_args()

benchmark = load_benchmark(args.path)
for name, method in methods().items():
    evaluate(name, method(benchmark), benchmark)
