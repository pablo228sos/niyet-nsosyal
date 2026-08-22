from pathlib import Path

from niyet.allocator import allocate
from niyet.baselines import random_capacity, topic_capacity, unconstrained_best_match
from niyet.benchmark import load_benchmark
from niyet.metrics import (
    intent_coverage,
    mean_gold_relevance,
    overload_count,
    responder_load_gini,
)


DATA = Path(__file__).parents[1] / "data" / "toy_benchmark.json"
benchmark = load_benchmark(DATA)
matches = [item.match for item in benchmark.matches]

methods = {
    "random_capacity": random_capacity(matches, benchmark.responders, seed=7),
    "topic_capacity": topic_capacity(matches, benchmark.responders),
    "unconstrained_best": unconstrained_best_match(matches),
    "capacity_pair_score": allocate(matches, benchmark.responders),
}

print("method                 coverage  gold  load_gini  overload")
for name, assignments in methods.items():
    print(
        f"{name:22} "
        f"{intent_coverage(assignments, benchmark.intents):8.2f} "
        f"{mean_gold_relevance(assignments, benchmark.matches):5.2f} "
        f"{responder_load_gini(assignments, benchmark.responders):10.2f} "
        f"{overload_count(assignments, benchmark.responders):8d}"
    )
