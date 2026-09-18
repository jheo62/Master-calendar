#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
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


def parse_utc(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Fecha_Hora_UTC vacía")

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    ).astimezone(timezone.utc)


def classify_delta(delta_minutes):
    delta = abs(delta_minutes)

    if delta <= 360:
        return "AUTO_ELIGIBLE"

    if delta <= 1440:
        return "REVIEW_REQUIRED"

    return "BLOCKED"


def strongest(decisions):
    if not decisions:
        return "AUTO_ELIGIBLE"

    return max(
        decisions,
        key=lambda value: RANK[value]
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Evalúa cambios de Fecha_Hora_UTC "
            "sin modificar producción."
        )
    )

    parser.add_argument(
        "--report",
        required=True,
        help="Reporte detallado de cambios."
    )

    parser.add_argument(
        "--output",
        help="Archivo JSON de salida."
    )

    args = parser.parse_args()

    report = load_json(args.report)

    modified = report.get("modified", [])

    temporal_changes = []
    decisions = []

    for item in modified:
        event_id = item.get(
            "ID_Partido",
            item.get("SIN_ID")
        )

        for change in item.get("changes", item.get("Changes", [])):
            field = change.get(
                "field",
                change.get("Field")
            )

            if field != "Fecha_Hora_UTC":
                continue

            before_raw = change.get(
                "before",
                change.get("Before")
            )

            after_raw = change.get(
                "after",
                change.get("After")
            )

            try:
                before = parse_utc(before_raw)
                after = parse_utc(after_raw)

                signed_delta = (
                    after - before
                ).total_seconds() / 60

                decision = classify_delta(
                    signed_delta
                )

                error = None

            except Exception as exc:
                signed_delta = None
                decision = "BLOCKED"
                error = str(exc)

            decisions.append(decision)

            temporal_changes.append({
                "ID_Partido": event_id,
                "field": "Fecha_Hora_UTC",
                "before": before_raw,
                "after": after_raw,
                "delta_minutes": signed_delta,
                "decision": decision,
                "error": error,
            })

    final_decision = strongest(decisions)

    result = {
        "schema_version": "1.0",
        "mode": "READ_ONLY",
        "decision": final_decision,
        "thresholds_minutes": {
            "auto_eligible_max": 360,
            "review_required_max": 1440,
            "blocked_above": 1440,
        },
        "counts": {
            "modified_events": len(modified),
            "temporal_changes": len(temporal_changes),
        },
        "changes": temporal_changes,
    }

    text = json.dumps(
        result,
        ensure_ascii=False,
        indent=2
    )

    if args.output:
        Path(args.output).write_text(
            text + "\n",
            encoding="utf-8"
        )

    print(text)


if __name__ == "__main__":
    main()
