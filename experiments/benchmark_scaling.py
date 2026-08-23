from __future__ import annotations

import argparse
import random
import time

import numpy as np
from scipy.optimize import linear_sum_assignment


def build_problem(
    n_intents: int,
    n_responders: int,
    *,
    candidates_per_intent: int = 8,
    attention_budget: int = 2,
    seed: int = 42,
):
    rng = random.Random(seed + n_intents)
    candidate_scores: dict[tuple[int, int], float] = {}

    for intent_id in range(n_intents):
        responder_ids = rng.sample(
            range(n_responders), min(candidates_per_intent, n_responders)
        )
        for responder_id in responder_ids:
            candidate_scores[(intent_id, responder_id)] = rng.random()

    return candidate_scores, attention_budget


def run_once(
    n_intents: int,
    n_responders: int,
    *,
    candidates_per_intent: int = 8,
    attention_budget: int = 2,
):
    candidate_scores, budget = build_problem(
        n_intents,
        n_responders,
        candidates_per_intent=candidates_per_intent,
        attention_budget=attention_budget,
    )

    real_slots = n_responders * budget
    start = time.perf_counter()

    utility = np.full(
        (n_intents, real_slots + n_intents),
        -1_000_000.0,
        dtype=float,
    )

    for (intent_id, responder_id), score in candidate_scores.items():
        first_slot = responder_id * budget
        utility[intent_id, first_slot : first_slot + budget] = score

    utility[:, real_slots:] = 0.0
    linear_sum_assignment(utility, maximize=True)

    elapsed_ms = (time.perf_counter() - start) * 1000
    return elapsed_ms, utility.nbytes / 1024 / 1024, len(candidate_scores)


def median_runtime(
    n_intents: int,
    n_responders: int,
    *,
    repeats: int,
):
    samples = [
        run_once(n_intents, n_responders)[0]
        for _ in range(repeats)
    ]
    return float(np.median(samples))


parser = argparse.ArgumentParser()
parser.add_argument("--sizes", nargs="+", type=int, default=[25, 50, 100, 200, 400])
parser.add_argument("--repeats", type=int, default=7)
args = parser.parse_args()

print("intents,responders,candidates,matrix_mb,median_ms")
for n_intents in args.sizes:
    n_responders = max(10, n_intents // 2)
    elapsed_ms, matrix_mb, candidate_count = run_once(n_intents, n_responders)
    median_ms = median_runtime(n_intents, n_responders, repeats=args.repeats)
    print(
        f"{n_intents},{n_responders},{candidate_count},"
        f"{matrix_mb:.3f},{median_ms:.3f}"
    )
