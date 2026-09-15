#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone


REQUIRED = (
    "Visitante",
    "Local",
    "Fecha_Hora_UTC",
)


def load_json(path):
    return json.loads(
        Path(path).read_text(encoding="utf-8")
    )


def validate_event(event, index):
    errors = []

    for field in REQUIRED:
        if not event.get(field):
            errors.append(
                f"Evento {index}: falta {field}"
            )

    return errors


def matching_key(event):
    return (
        event.get("Visitante"),
        event.get("Local"),
        event.get("Fecha_Hora_UTC"),
    )


def main():
    parser = argparse.ArgumentParser(
        description="NBA Source Adapter - modo observación"
    )

    parser.add_argument(
        "--source",
        required=True,
        help="JSON de fuente normalizada"
    )

    parser.add_argument(
        "--master",
        default="data/master_snapshot.json",
        help="Snapshot maestro actual"
    )

    parser.add_argument(
        "--output",
        default="data/incoming/nba_adapter_candidate.json",
        help="Candidate de salida"
    )

    args = parser.parse_args()

    source = load_json(args.source)
    master = load_json(args.master)

    source_events = source.get("events", [])
    master_events = master.get("events", [])

    errors = []

    for i, event in enumerate(source_events, 1):
        errors.extend(
            validate_event(event, i)
        )

    if errors:
        print("SOURCE ADAPTER: BLOQUEADO")

        for error in errors[:20]:
            print("-", error)

        raise SystemExit(1)

    master_index = {}

    for event in master_events:
        key = matching_key(event)

        if key in master_index:
            raise SystemExit(
                "MASTER INVALIDO: clave duplicada"
            )

        master_index[key] = event

    matched = []
    unmatched = []

    for source_event in source_events:
        key = matching_key(source_event)

        master_event = master_index.get(key)

        if master_event is None:
            unmatched.append(source_event)
            continue

        candidate = dict(master_event)

        # En v0.1 todavía no sobrescribimos campos.
        # Sólo demostramos matching seguro.
        matched.append(candidate)

    result = {
        "schema_version": "source-adapter-0.1",
        "season": master.get("season"),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "mode": "observation",
        "source_count": len(source_events),
        "master_count": len(master_events),
        "matched_count": len(matched),
        "unmatched_count": len(unmatched),
        "events": matched,
    }

    output = Path(args.output)
    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        ) + "\n",
        encoding="utf-8"
    )

    print("SOURCE ADAPTER: OK")
    print("Fuente:", len(source_events))
    print("Master:", len(master_events))
    print("Matched:", len(matched))
    print("Unmatched:", len(unmatched))
    print("Salida:", output)


if __name__ == "__main__":
    main()
