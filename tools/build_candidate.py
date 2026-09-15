#!/usr/bin/env python3

"""
NBA Master Calendar
Fase 3.7.3 - Candidate Builder

Construye un candidato independiente para la capa de ingesta.

NO modifica:
- data/master_snapshot.json
- data/published_state.json
- docs/calendars/
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")


def validate_events(data):
    events = data.get("events")

    if not isinstance(events, list):
        raise SystemExit(
            "ERROR: el archivo fuente no contiene una lista 'events'."
        )

    ids = []
    for event in events:
        event_id = event.get("ID_Partido")

        if not event_id:
            raise SystemExit(
                "ERROR: existe un evento sin ID_Partido."
            )

        ids.append(event_id)

    duplicates = sorted({
        event_id
        for event_id in ids
        if ids.count(event_id) > 1
    })

    if duplicates:
        raise SystemExit(
            "ERROR: ID_Partido duplicados: "
            + ", ".join(duplicates[:20])
        )

    return events


def main():
    parser = argparse.ArgumentParser(
        description="Construir candidato NBA para ingesta."
    )

    parser.add_argument(
        "--source",
        required=True,
        help="JSON normalizado de origen."
    )

    parser.add_argument(
        "--output",
        default="data/incoming/nba_candidate.json",
        help="Archivo candidato de salida."
    )

    args = parser.parse_args()

    source = Path(args.source)
    output = Path(args.output)

    if not source.exists():
        raise SystemExit(
            f"ERROR: no existe la fuente: {source}"
        )

    data = load_json(source)
    events = validate_events(data)

    candidate = dict(data)

    candidate["ingestion"] = {
        "generated_at": datetime.now(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%SZ"),
        "source_file": str(source),
        "event_count": len(events),
        "mode": "observation"
    }

    save_json(output, candidate)

    print("=== CANDIDATE BUILDER ===")
    print(f"Fuente    : {source}")
    print(f"Salida    : {output}")
    print(f"Eventos   : {len(events)}")
    print("Modo      : observation")
    print("CANDIDATE BUILDER: OK")


if __name__ == "__main__":
    main()
