#!/usr/bin/env python3
"""Audit script for verifying Technical Report Evidence against repository artifacts.

Resolves issue #3 (Track the technical report evidence).
Validates that every claim across the 14 mandatory report criteria is backed
by existing, non-empty, and consistent repository files, datasets, metrics, and citations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]

CRITERIA_DEFINITIONS: dict[str, dict[str, Any]] = {
    "problem_and_prior_work": {
        "title": "Problem Statement and Prior Work",
        "description": "Evidence for the social disinformation/intent routing problem and scholarly prior art.",
        "required_files": [
            "docs/problem_evidence.md",
            "docs/prior_art.md",
        ],
        "key_checks": [
            {"file": "docs/problem_evidence.md", "contains": ["NSosyal", "Joyce and Kraut", "Popularity bias"]},
            {"file": "docs/prior_art.md", "contains": ["CrowdSTAR", "Reciprocal recommender systems", "NSosyal"]},
        ],
    },
    "novelty_and_competitor_comparison": {
        "title": "Novelty Claim and Competitor Comparison",
        "description": "Comparison matrix and product thesis contrasting DRSK against existing fact-checking systems.",
        "required_files": [
            "docs/comparison_matrix.md",
            "docs/PRODUCT_THESIS.md",
        ],
        "key_checks": [
            {"file": "docs/comparison_matrix.md", "contains": ["Standard social feed", "CrowdSTAR", "Reciprocal recommender systems", "NIYET prototype"]},
            {"file": "docs/PRODUCT_THESIS.md", "contains": ["Distribution is not resolution", "SOURCECHAIN", "NIYET", "author", "reader"]},
        ],
    },
    "repository_history_and_architecture": {
        "title": "Repository History and Architecture",
        "description": "Architectural documentation, system contracts, and engineering journey log.",
        "required_files": [
            "docs/DRSK_ARCHITECTURE.md",
            "docs/architecture.md",
            "docs/ENGINEERING_JOURNEY.md",
        ],
        "key_checks": [
            {"file": "docs/DRSK_ARCHITECTURE.md", "contains": ["DRSK Architecture", "SOURCECHAIN", "NIYET", "Ownership"]},
            {"file": "docs/ENGINEERING_JOURNEY.md", "contains": ["two-device", "browser", "failures"]},
        ],
    },
    "data_provenance_and_split_rules": {
        "title": "Data Provenance and Split Rules",
        "description": "Dataset cards, provenance documentation, annotation protocols, and baseline data files.",
        "required_files": [
            "docs/data_card.md",
            "docs/dataset_card.md",
            "docs/SOURCEBENCH_TR_DATASET_CARD.md",
            "docs/annotation.md",
            "data/intent_seed_v1.csv",
            "data/response_gate_seed_v1.csv",
            "data/sourcebench_tr/alignment.jsonl",
            "data/sourcebench_tr/distortion.jsonl",
            "data/sourcebench_tr/statement_types.jsonl",
            "data/matching_benchmark_v1_reviewed.json",
            "data/toy_benchmark.json",
        ],
        "key_checks": [
            {"file": "data/sourcebench_tr/alignment.jsonl", "min_lines": 4},
            {"file": "data/intent_seed_v1.csv", "min_lines": 50},
            {"file": "data/response_gate_seed_v1.csv", "min_lines": 50},
        ],
    },
    "classifier_metrics": {
        "title": "Classifier Metrics and Baselines",
        "description": "Model cards, seed experiment logs, and frozen baseline evaluation metrics.",
        "required_files": [
            "docs/model_choice.md",
            "docs/SOURCECHAIN_MODEL_CARD.md",
            "experiments/intent_seed_v1.md",
            "experiments/response_gate_seed_v1.md",
            "results/sourcechain_v0.json",
        ],
        "key_checks": [
            {
                "file": "results/sourcechain_v0.json",
                "json_eval": lambda d: "metrics" in d and "dataset_version" in d,
                "description": "Contains valid metrics and dataset_version",
            },
        ],
    },
    "matching_and_allocation_baselines": {
        "title": "Matching and Allocation Baselines",
        "description": "Mathematical formulation, allocator implementation, and reviewed allocation metrics.",
        "required_files": [
            "docs/allocation_formulation.md",
            "results/niyet_allocation_reviewed.json",
            "results/niyet_retrieval_reviewed.json",
            "src/niyet/allocator.py",
            "src/niyet/optimizer.py",
            "src/niyet/scoring.py",
        ],
        "key_checks": [
            {
                "file": "results/niyet_allocation_reviewed.json",
                "json_eval": lambda d: d["metrics"]["global"]["coverage"] == 0.7812
                and d["metrics"]["greedy"]["coverage"] == 0.6562
                and d["parameters"]["allocator_batch_size"] == 8,
                "description": "Matches exact frozen reviewed allocation metrics (global coverage 0.7812, greedy 0.6562)",
            },
            {
                "file": "results/niyet_retrieval_reviewed.json",
                "json_eval": lambda d: d["metrics"]["precision_at_3"] == 0.4688
                and d["metrics"]["recall_at_3"] == 0.8438
                and d["metrics"]["ndcg_at_3"] == 0.845,
                "description": "Matches exact frozen reviewed retrieval metrics (prec@3 0.4688, rec@3 0.8438, ndcg@3 0.845)",
            },
        ],
    },
    "efficiency_and_fairness_metrics": {
        "title": "Efficiency and Fairness Metrics",
        "description": "Benchmarking scripts, fairness/capacity constraints, and evaluation reports.",
        "required_files": [
            "docs/impact_and_metrics.md",
            "experiments/evaluate_matching_draft.py",
            "experiments/global_vs_greedy.py",
            "results/niyet_allocation_reviewed.json",
        ],
        "key_checks": [
            {"file": "docs/impact_and_metrics.md", "contains": ["Intent coverage", "Relevant match rate", "Responder load", "Overload count", "Load Gini"]},
        ],
    },
    "target_users_and_user_flow": {
        "title": "Target Users and User Flow",
        "description": "User persona flows, interactive prototype scripts, visual screenshots, and demo guide.",
        "required_files": [
            "docs/product_flow.md",
            "docs/DRSK_DEMO.md",
            "docs/screenshots/01_live_coffee_conflict.png",
            "web/index.html",
            "web/app.js",
        ],
        "key_checks": [
            {"file": "docs/product_flow.md", "contains": ["author", "SOURCECHAIN", "NIYET", "responder"]},
            {"file": "web/index.html", "contains": ["product-nav", "product-wordmark"]},
            {"file": "web/app.js", "contains": ["applyLanguage", "distortion-lens"]},
        ],
    },
    "accessibility_decisions": {
        "title": "Accessibility Decisions and WCAG Contracts",
        "description": "Design system tokens, focus-visible requirements, reduced motion, and UI rationale.",
        "required_files": [
            "docs/ui_design_rationale.md",
            "web/design-system.css",
            "tests/test_web_ui_contract.py",
        ],
        "key_checks": [
            {
                "file": "web/design-system.css",
                "contains": [
                    "--color-bg-canvas",
                    "--color-sourcechain-accent",
                    "--color-niyet-accent",
                    "--color-drsk-accent",
                    ":focus-visible",
                    "@media (prefers-reduced-motion: reduce)",
                ],
            },
        ],
    },
    "usability_test_plan_and_results": {
        "title": "Usability Test Plan and Results",
        "description": "Usability testing protocol, participant evaluations, and results templates.",
        "required_files": [
            "docs/usability_test_protocol.md",
            "docs/usability_evaluation.md",
            "data/usability_results_template.csv",
        ],
        "key_checks": [
            {"file": "docs/usability_test_protocol.md", "contains": ["participant", "tasks", "protocol"]},
            {"file": "docs/usability_evaluation.md", "contains": ["usability", "tasks"]},
        ],
    },
    "scalability_assumptions": {
        "title": "Scalability Assumptions and Production Boundaries",
        "description": "Infrastructure scaling scripts, external provider boundaries, and live acceptance logs.",
        "required_files": [
            "docs/runtime_provider_setup.md",
            "docs/FINAL_ACCEPTANCE.md",
            "docs/REAL_NSOSYAL_ACCEPTANCE.md",
            "experiments/benchmark_scaling.py",
            "experiments/scaling_results_v1.md",
        ],
        "key_checks": [
            {"file": "docs/FINAL_ACCEPTANCE.md", "contains": ["286 passed", "GitHub Actions"]},
            {"file": "docs/runtime_provider_setup.md", "contains": ["Tavily", "BRAVE_SEARCH_API_KEY", "UPSTASH_REDIS_REST_URL"]},
        ],
    },
    "sustainability_and_cost_assumptions": {
        "title": "Sustainability and Cost Assumptions",
        "description": "Economic feasibility, operational unit economics, and business model.",
        "required_files": [
            "docs/business_model.md",
        ],
        "key_checks": [
            {"file": "docs/business_model.md", "contains": ["Platform value", "Cost structure", "sustainability"]},
        ],
    },
    "project_timeline_and_team_roles": {
        "title": "Project Timeline and Team Roles",
        "description": "Engineering team ownership matrix and development timeline roadmap.",
        "required_files": [
            "docs/team_roles.md",
            "docs/roadmap.md",
        ],
        "key_checks": [
            {"file": "docs/team_roles.md", "contains": ["Developer A", "Developer B", "Product and UI/UX Designer"]},
            {"file": "docs/roadmap.md", "contains": ["Milestone", "technical report stage"]},
        ],
    },
    "references": {
        "title": "Academic and Technical References",
        "description": "Formal citations, standards, and published literature referenced across the technical report.",
        "required_files": [
            "docs/prior_art.md",
            "docs/allocation_formulation.md",
            "docs/SOURCECHAIN_MODEL_CARD.md",
            "docs/safety_and_failure_modes.md",
        ],
        "key_checks": [
            {"file": "docs/prior_art.md", "contains": ["CrowdSTAR", "Palomares", "Klimashevskaia"]},
            {"file": "docs/allocation_formulation.md", "contains": ["linear assignment", "capacity"]},
        ],
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_technical_report_evidence(root: Path = ROOT) -> dict[str, Any]:
    audit_results: dict[str, Any] = {
        "audit_version": "TECHNICAL-REPORT-EVIDENCE-V1",
        "audited_at": datetime.now(UTC).isoformat(),
        "total_criteria": len(CRITERIA_DEFINITIONS),
        "compliant_criteria": 0,
        "criteria": {},
        "overall_status": "PENDING",
    }

    all_passed = True
    total_files_checked = 0
    missing_files: list[str] = []

    for criterion_key, defn in CRITERIA_DEFINITIONS.items():
        criterion_result: dict[str, Any] = {
            "title": defn["title"],
            "description": defn["description"],
            "status": "PASS",
            "checked_files": [],
            "checks": [],
            "failures": [],
        }

        # Check required files
        for rel_path in defn["required_files"]:
            p = root / rel_path
            total_files_checked += 1
            if not p.exists():
                criterion_result["status"] = "FAIL"
                criterion_result["failures"].append(f"Missing file: {rel_path}")
                missing_files.append(rel_path)
                all_passed = False
                continue

            size = p.stat().st_size
            if size == 0:
                criterion_result["status"] = "FAIL"
                criterion_result["failures"].append(f"Empty file: {rel_path}")
                all_passed = False
                continue

            criterion_result["checked_files"].append({
                "path": rel_path,
                "size_bytes": size,
                "sha256": _sha256(p)[:16],
            })

        # Run specific semantic / metric checks
        for chk in defn.get("key_checks", []):
            rel_path = chk["file"]
            p = root / rel_path
            if not p.exists():
                continue

            # Text contains check
            if "contains" in chk:
                content = p.read_text(encoding="utf-8", errors="replace")
                missing_substrings = [s for s in chk["contains"] if s not in content]
                if missing_substrings:
                    criterion_result["status"] = "FAIL"
                    msg = f"{rel_path} missing required text: {missing_substrings}"
                    criterion_result["failures"].append(msg)
                    all_passed = False
                else:
                    criterion_result["checks"].append({
                        "file": rel_path,
                        "check": f"Contains required text tokens: {chk['contains']}",
                        "passed": True,
                    })

            # Min lines check
            if "min_lines" in chk:
                lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
                if len(lines) < chk["min_lines"]:
                    criterion_result["status"] = "FAIL"
                    msg = f"{rel_path} has {len(lines)} lines, expected >= {chk['min_lines']}"
                    criterion_result["failures"].append(msg)
                    all_passed = False
                else:
                    criterion_result["checks"].append({
                        "file": rel_path,
                        "check": f"Line count {len(lines)} >= {chk['min_lines']}",
                        "passed": True,
                    })

            # JSON eval check
            if "json_eval" in chk:
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    eval_fn = chk["json_eval"]
                    if not eval_fn(data):
                        criterion_result["status"] = "FAIL"
                        msg = f"{rel_path} failed assertion: {chk.get('description', 'json_eval')}"
                        criterion_result["failures"].append(msg)
                        all_passed = False
                    else:
                        criterion_result["checks"].append({
                            "file": rel_path,
                            "check": chk.get("description", "json_eval"),
                            "passed": True,
                        })
                except Exception as ex:
                    criterion_result["status"] = "FAIL"
                    criterion_result["failures"].append(f"{rel_path} json error: {ex}")
                    all_passed = False

        if criterion_result["status"] == "PASS":
            audit_results["compliant_criteria"] += 1

        audit_results["criteria"][criterion_key] = criterion_result

    audit_results["total_files_checked"] = total_files_checked
    audit_results["missing_files"] = missing_files
    audit_results["overall_status"] = "PASS" if all_passed else "FAIL"

    return audit_results


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit Technical Report Evidence against repository artifacts.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root path")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "technical_report_evidence_audit.json", help="Output JSON path")
    args = parser.parse_args()

    results = audit_technical_report_evidence(args.root)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Audit results written to {args.output}")

    print("\n" + "=" * 80)
    print("TECHNICAL REPORT EVIDENCE AUDIT REPORT")
    print("=" * 80)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Compliant Criteria: {results['compliant_criteria']} / {results['total_criteria']}")
    print(f"Total Files Checked: {results['total_files_checked']}")
    print("-" * 80)

    for idx, (k, c) in enumerate(results["criteria"].items(), 1):
        status_symbol = "[PASS]" if c["status"] == "PASS" else "[FAIL]"
        print(f"{idx:2d}. {status_symbol} {c['title']} ({k})")
        if c["failures"]:
            for f in c["failures"]:
                print(f"     ! {f}")

    print("=" * 80)
    if results["overall_status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
