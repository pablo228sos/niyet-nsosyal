from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .mismatch import source_mismatch
from .schemas import DistortionType
from .structured_checks import detect_distortions


@dataclass(frozen=True)
class ClaimTransformationHop:
    """A single hop in a multi-hop claim transformation chain."""

    hop_index: int
    parent_text: str
    child_text: str
    distortions: tuple[DistortionType, ...]
    notes: str | None = None

    @property
    def has_distortion(self) -> bool:
        return any(d != DistortionType.NONE for d in self.distortions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hop_index": self.hop_index,
            "parent_text": self.parent_text,
            "child_text": self.child_text,
            "distortions": [d.value for d in self.distortions],
            "notes": self.notes,
        }


@dataclass(frozen=True)
class ClaimEvolutionChain:
    """A multi-hop lineage of claim transformations from primary root evidence to terminal post."""

    chain_id: str
    scenario: str
    hops: tuple[ClaimTransformationHop, ...]
    root_text: str
    terminal_text: str
    cumulative_distortions: tuple[DistortionType, ...]

    @property
    def is_distorted(self) -> bool:
        return len(self.cumulative_distortions) > 0 and DistortionType.NONE not in self.cumulative_distortions

    @property
    def hop_count(self) -> int:
        return len(self.hops)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "scenario": self.scenario,
            "hops": [hop.to_dict() for hop in self.hops],
            "root_text": self.root_text,
            "terminal_text": self.terminal_text,
            "cumulative_distortions": [d.value for d in self.cumulative_distortions],
            "is_distorted": self.is_distorted,
        }


def trace_claim_evolution(
    chain_id: str,
    scenario: str,
    statements: list[str] | tuple[str, ...],
    notes: list[str] | tuple[str, ...] | None = None,
    publishers: list[str | None] | tuple[str | None, ...] | None = None,
) -> ClaimEvolutionChain:
    """Analyze a multi-hop lineage of statements and track distortion accumulation across hops."""
    if len(statements) < 2:
        raise ValueError("Claim evolution chain must contain at least 2 statements")

    hops: list[ClaimTransformationHop] = []
    accumulated_distortions: set[DistortionType] = set()

    for idx in range(len(statements) - 1):
        parent = statements[idx]
        child = statements[idx + 1]
        note = notes[idx] if notes and idx < len(notes) else None

        # Detect semantic distortions between consecutive statements (child relative to parent)
        step_distortions = list(detect_distortions(child, parent))

        # Check for attribution shifts if publisher metadata is provided
        if publishers and idx + 1 < len(publishers) and publishers[idx + 1]:
            if source_mismatch(child, publisher=publishers[idx + 1]) is True:
                if DistortionType.ATTRIBUTION_SHIFT not in step_distortions:
                    step_distortions.append(DistortionType.ATTRIBUTION_SHIFT)

        if len(step_distortions) > 1 and DistortionType.NONE in step_distortions:
            step_distortions.remove(DistortionType.NONE)

        for d in step_distortions:
            if d != DistortionType.NONE:
                accumulated_distortions.add(d)

        hops.append(
            ClaimTransformationHop(
                hop_index=idx + 1,
                parent_text=parent,
                child_text=child,
                distortions=tuple(step_distortions),
                notes=note,
            )
        )

    cumulative = (
        tuple(sorted(accumulated_distortions, key=lambda x: x.value))
        if accumulated_distortions
        else (DistortionType.NONE,)
    )

    return ClaimEvolutionChain(
        chain_id=chain_id,
        scenario=scenario,
        hops=tuple(hops),
        root_text=statements[0],
        terminal_text=statements[-1],
        cumulative_distortions=cumulative,
    )


def evaluate_claim_evolution_benchmark(
    benchmark_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate distortion detection accuracy on the multi-hop Claim Evolution benchmark."""
    if benchmark_path is None:
        benchmark_path = Path(__file__).resolve().parents[2] / "data" / "sourcebench_tr" / "claim_evolution.jsonl"
    else:
        benchmark_path = Path(benchmark_path)

    if not benchmark_path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {benchmark_path}")

    total_chains = 0
    total_hops = 0
    correct_hops = 0
    correct_chains = 0
    metrics_by_distortion: dict[str, dict[str, int]] = {
        d.value: {"tp": 0, "fp": 0, "fn": 0}
        for d in DistortionType
        if d != DistortionType.NONE
    }

    with open(benchmark_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            total_chains += 1

            chain_id = item["id"]
            scenario = item.get("scenario", "")
            statements = item["statements"]
            expected_hops = item.get("expected_hops", [])
            expected_cumulative = {d for d in item.get("expected_cumulative", []) if d != "NONE"}

            traced = trace_claim_evolution(chain_id, scenario, statements)
            detected_cumulative = {d.value for d in traced.cumulative_distortions if d != DistortionType.NONE}

            if detected_cumulative == expected_cumulative:
                correct_chains += 1

            for h_idx, hop in enumerate(traced.hops):
                total_hops += 1
                detected_hop_distortions = {d.value for d in hop.distortions if d != DistortionType.NONE}
                expected_hop_distortions = (
                    {d for d in expected_hops[h_idx] if d != "NONE"}
                    if h_idx < len(expected_hops)
                    else set()
                )

                if detected_hop_distortions == expected_hop_distortions:
                    correct_hops += 1

                for d_val in metrics_by_distortion:
                    in_det = d_val in detected_hop_distortions
                    in_exp = d_val in expected_hop_distortions
                    if in_det and in_exp:
                        metrics_by_distortion[d_val]["tp"] += 1
                    elif in_det and not in_exp:
                        metrics_by_distortion[d_val]["fp"] += 1
                    elif not in_det and in_exp:
                        metrics_by_distortion[d_val]["fn"] += 1

    hop_accuracy = correct_hops / total_hops if total_hops > 0 else 0.0
    chain_accuracy = correct_chains / total_chains if total_chains > 0 else 0.0

    distortion_f1: dict[str, float] = {}
    for d_val, counts in metrics_by_distortion.items():
        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        distortion_f1[d_val] = round(f1, 4)

    return {
        "total_chains": total_chains,
        "total_hops": total_hops,
        "hop_accuracy": round(hop_accuracy, 4),
        "chain_accuracy": round(chain_accuracy, 4),
        "distortion_f1": distortion_f1,
    }
