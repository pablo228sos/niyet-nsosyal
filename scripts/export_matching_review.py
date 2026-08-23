from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "data" / "matching_benchmark_v1_draft.json"
DEFAULT_RESPONDERS = ROOT / "data" / "responder_profiles_v1.json"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--responders", type=Path, default=DEFAULT_RESPONDERS)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    benchmark = json.loads(args.benchmark.read_text(encoding="utf-8"))
    responders = json.loads(args.responders.read_text(encoding="utf-8"))
    responder_by_id = {item["id"]: item for item in responders}

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "pair_id",
                "query_id",
                "intent_type",
                "intent_text",
                "responder_id",
                "responder_name",
                "responder_profile",
                "willing_for_intent",
                "label_a",
                "label_b",
                "final_relevance",
                "notes",
            ]
        )

        pair_index = 0
        for query in benchmark["queries"]:
            for responder_id in query["relevance"]:
                pair_index += 1
                responder = responder_by_id[responder_id]
                profile = (
                    f"{responder['profile_text']} Topics: "
                    + ", ".join(responder["topics"])
                )
                writer.writerow(
                    [
                        f"pair_{pair_index:03d}",
                        query["id"],
                        query["intent"].upper(),
                        query["text"],
                        responder_id,
                        responder["display_name"],
                        profile,
                        "yes"
                        if query["intent"] in responder["willing_intents"]
                        else "no",
                        "",
                        "",
                        "",
                        "",
                    ]
                )

    print(f"wrote {pair_index} blind review pairs to {args.output}")


if __name__ == "__main__":
    main()
