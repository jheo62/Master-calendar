#!/usr/bin/env python3

"""
NBA Master Calendar
Fase 3.7.5I - Detailed Change Report

Compara un baseline completo con un candidato normalizado y genera
un informe campo por campo limitado a SIGNIFICANT_FIELDS.

READ-ONLY:
- No modifica master_snapshot.
- No modifica published_state.
- No modifica feeds.
"""

import argparse
import json
from pathlib import Path

from common import SIGNIFICANT_FIELDS, canonical_event


def load_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def index_events(data, label):
    events = data.get("events")

    if not isinstance(events, list):
        raise SystemExit(
            f"ERROR: {label} no contiene una lista 'events'"
        )

    indexed = {}

    for position, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise SystemExit(
                f"ERROR: {label} evento {position} no es un objeto"
            )

        event_id = event.get("ID_Partido")

        if not event_id:
            raise SystemExit(
                f"ERROR: {label} evento {position} sin ID_Partido"
            )

        if event_id in indexed:
            raise SystemExit(
                f"ERROR: {label} ID duplicado: {event_id}"
            )

        indexed[event_id] = event

    return indexed


def field_differences(base_event, candidate_event):
    base = canonical_event(base_event)
    candidate = canonical_event(candidate_event)

    differences = []

    for field in SIGNIFICANT_FIELDS:
        before = base.get(field)
        after = candidate.get(field)

        if before != after:
            differences.append({
                "field": field,
                "before": before,
                "after": after,
            })

    return differences


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Genera un informe detallado read-only entre "
            "baseline y candidato NBA."
        )
    )

    parser.add_argument(
        "--baseline",
        required=True,
        help="JSON baseline completo"
    )

    parser.add_argument(
        "--candidate",
        required=True,
        help="JSON candidato normalizado"
    )

    parser.add_argument(
        "--output",
        help="Salida JSON opcional"
    )

    args = parser.parse_args()

    baseline_data = load_json(args.baseline)
    candidate_data = load_json(args.candidate)

    baseline = index_events(
        baseline_data,
        "baseline"
    )

    candidate = index_events(
        candidate_data,
        "candidate"
    )

    baseline_ids = set(baseline)
    candidate_ids = set(candidate)

    added = sorted(candidate_ids - baseline_ids)
    missing = sorted(baseline_ids - candidate_ids)

    modified = []
    unchanged = 0

    for event_id in sorted(
        baseline_ids & candidate_ids
    ):
        changes = field_differences(
            baseline[event_id],
            candidate[event_id]
        )

        if changes:
            event = candidate[event_id]

            modified.append({
                "ID_Partido": event_id,
                "Visitante": event.get("Visitante"),
                "Local": event.get("Local"),
                "changes": changes,
            })
        else:
            unchanged += 1

    report = {
        "mode": "read-only",
        "significant_fields": list(
            SIGNIFICANT_FIELDS
        ),
        "counts": {
            "baseline": len(baseline),
            "candidate": len(candidate),
            "added": len(added),
            "modified": len(modified),
            "unchanged": unchanged,
            "missing": len(missing),
        },
        "added": added,
        "missing": missing,
        "modified": modified,
    }

    print("=== DETAILED CHANGE REPORT ===")
    print("Mode: READ-ONLY")
    print("Baseline:", len(baseline))
    print("Candidate:", len(candidate))
    print("Added:", len(added))
    print("Modified:", len(modified))
    print("Unchanged:", unchanged)
    print("Missing:", len(missing))

    for item in modified:
        print()
        print(
            f"{item['ID_Partido']} — "
            f"{item['Visitante']} @ {item['Local']}"
        )

        for change in item["changes"]:
            print()
            print(change["field"])
            print(
                "  BASE:",
                json.dumps(
                    change["before"],
                    ensure_ascii=False
                )
            )
            print(
                "  LIVE:",
                json.dumps(
                    change["after"],
                    ensure_ascii=False
                )
            )

    if added:
        print()
        print("Added IDs:")
        for event_id in added:
            print(" -", event_id)

    if missing:
        print()
        print("Missing IDs:")
        for event_id in missing:
            print(" -", event_id)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        output.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2
            )
            + "\n",
            encoding="utf-8"
        )

        print()
        print("JSON:", output)

    print()
    print("DETAILED REPORT: OK")


if __name__ == "__main__":
    main()
