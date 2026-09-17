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
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def strongest(decisions):
    if not decisions:
        return "AUTO_ELIGIBLE"
    return max(decisions, key=lambda x: RANK[x])


def main():
    parser = argparse.ArgumentParser(
        description="Clasifica cambios NBA sin modificar producción."
    )
    parser.add_argument("--report", required=True)
    parser.add_argument(
        "--policy",
        default="data/reference/change_decision_policy.json",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    report = load_json(args.report)
    policy = load_json(args.policy)

    field_policy = policy["field_policy"]
    event_policy = policy["event_policy"]
    thresholds = policy["thresholds"]

    added = report.get("added", [])
    modified = report.get("modified", [])
    missing = report.get("missing", [])

    decisions = []
    reasons = []

    if len(added) > thresholds["max_added"]:
        decisions.append("BLOCKED")
        reasons.append(
            f"{len(added)} añadidos superan "
            f"límite {thresholds['max_added']}"
        )

    if len(modified) > thresholds["max_modified"]:
        decisions.append("BLOCKED")
        reasons.append(
            f"{len(modified)} modificados superan "
            f"límite {thresholds['max_modified']}"
        )

    if len(missing) > thresholds["max_missing"]:
        decisions.append("BLOCKED")
        reasons.append(
            f"{len(missing)} ausentes superan "
            f"límite {thresholds['max_missing']}"
        )

    if added:
        d = event_policy["added"]
        decisions.append(d)
        reasons.append(f"{len(added)} evento(s) añadido(s): {d}")

    if missing:
        d = event_policy["missing"]
        decisions.append(d)
        reasons.append(f"{len(missing)} evento(s) ausente(s): {d}")

    classified_changes = []

    for item in modified:
        event_id = item.get("ID_Partido", "SIN_ID")

        for change in item.get("changes", []):
            field = change.get("field")

            decision = field_policy.get(
                field,
                "BLOCKED",
            )

            decisions.append(decision)

            classified_changes.append({
                "ID_Partido": event_id,
                "field": field,
                "before": change.get("before"),
                "after": change.get("after"),
                "decision": decision,
            })

    final_decision = strongest(decisions)

    result = {
        "schema_version": "1.0",
        "mode": "READ-ONLY",
        "decision": final_decision,
        "counts": {
            "added": len(added),
            "modified": len(modified),
            "missing": len(missing),
            "classified_changes": len(classified_changes),
        },
        "reasons": reasons,
        "changes": classified_changes,
    }

    print("=== CHANGE DECISION ===")
    print("Mode: READ-ONLY")
    print("Decision:", final_decision)
    print("Added:", len(added))
    print("Modified:", len(modified))
    print("Missing:", len(missing))
    print("Field changes:", len(classified_changes))

    for change in classified_changes:
        print(
            f"{change['ID_Partido']} | "
            f"{change['field']} | "
            f"{change['decision']}"
        )

    if reasons:
        print()
        print("Reasons:")
        for reason in reasons:
            print("-", reason)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(
                result,
                f,
                ensure_ascii=False,
                indent=2,
            )
            f.write("\n")

        print()
        print("JSON:", output)

    print()
    print("CHANGE DECISION: OK")


if __name__ == "__main__":
    main()
