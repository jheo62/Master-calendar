#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


RANK = {
    "AUTO_ELIGIBLE": 1,
    "REVIEW_REQUIRED": 2,
    "BLOCKED": 3,
}


def load_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def read_decision(name, path):
    data = load_json(path)
    decision = data.get("decision")

    if decision not in RANK:
        raise ValueError(
            f"{name}: decision invalida o ausente: {decision!r}"
        )

    return decision


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Combina los guards de promocion NBA. "
            "No modifica produccion."
        )
    )

    parser.add_argument("--change-decision", required=True)
    parser.add_argument("--arena-guard", required=True)
    parser.add_argument("--temporal-guard", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    try:
        decisions = {
            "change_decision": read_decision(
                "change_decision",
                args.change_decision,
            ),
            "arena_geography_guard": read_decision(
                "arena_geography_guard",
                args.arena_guard,
            ),
            "temporal_guard": read_decision(
                "temporal_guard",
                args.temporal_guard,
            ),
        }

        final_decision = max(
            decisions.values(),
            key=lambda value: RANK[value],
        )

        result = {
            "schema_version": "1.0",
            "mode": "READ_ONLY",
            "decision": final_decision,
            "guards": decisions,
        }

    except Exception as exc:
        result = {
            "schema_version": "1.0",
            "mode": "READ_ONLY",
            "decision": "BLOCKED",
            "guards": {},
            "error": str(exc),
        }

    Path(args.output).write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("=== NBA PROMOTION GATE ===")
    print("Decision:", result["decision"])

    for name, decision in result.get("guards", {}).items():
        print(f"{name}: {decision}")

    if result.get("error"):
        print("Error:", result["error"])

    if result["decision"] != "AUTO_ELIGIBLE":
        raise SystemExit(2)

    print("PROMOTION GATE: AUTO_ELIGIBLE")
    print("PUBLICACION AUTOMATICA: NO")


if __name__ == "__main__":
    main()
