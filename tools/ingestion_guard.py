#!/usr/bin/env python3

"""
NBA Master Calendar - Ingestion Guard
Fase 3.7

Valida un candidato antes de permitir que llegue
al motor de actualización.

Este módulo NO modifica:
- master_snapshot.json
- published_state.json
- calendarios ICS
"""

import json
import sys
from pathlib import Path


EXPECTED_CURRENT_EVENTS = 1200
MAX_ADDED = 10
MAX_MODIFIED = 20
MAX_MISSING = 0


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_events(data):
    events = data.get("events", [])

    index = {}
    duplicates = []

    for event in events:
        event_id = event.get("ID_Partido")

        if not event_id:
            raise SystemExit(
                "BLOQUEADO: existe un evento sin ID_Partido."
            )

        if event_id in index:
            duplicates.append(event_id)

        index[event_id] = event

    if duplicates:
        raise SystemExit(
            "BLOQUEADO: existen ID_Partido duplicados: "
            + ", ".join(sorted(set(duplicates))[:20])
        )

    return index


def compare(master, candidate):
    current = index_events(master)
    incoming = index_events(candidate)

    added = sorted(set(incoming) - set(current))
    missing = sorted(set(current) - set(incoming))

    modified = []

    for event_id in sorted(set(current) & set(incoming)):
        if current[event_id] != incoming[event_id]:
            modified.append(event_id)

    return {
        "current": len(current),
        "candidate": len(incoming),
        "added": added,
        "modified": modified,
        "missing": missing,
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            "Uso: python3 tools/ingestion_guard.py "
            "MASTER.json CANDIDATE.json"
        )

    master_path = Path(sys.argv[1])
    candidate_path = Path(sys.argv[2])

    if not master_path.exists():
        raise SystemExit(f"No existe master: {master_path}")

    if not candidate_path.exists():
        raise SystemExit(f"No existe candidato: {candidate_path}")

    master = load_json(master_path)
    candidate = load_json(candidate_path)

    result = compare(master, candidate)

    print("=== INGESTION GUARD ===")
    print(f"Master actual : {result['current']}")
    print(f"Candidato     : {result['candidate']}")
    print(f"Añadidos      : {len(result['added'])}")
    print(f"Modificados   : {len(result['modified'])}")
    print(f"Ausentes      : {len(result['missing'])}")

    if result["current"] != EXPECTED_CURRENT_EVENTS:
        raise SystemExit(
            f"BLOQUEADO: master actual contiene "
            f"{result['current']} eventos; se esperaban "
            f"{EXPECTED_CURRENT_EVENTS}."
        )

    if len(result["added"]) > MAX_ADDED:
        raise SystemExit(
            f"BLOQUEADO: {len(result['added'])} añadidos "
            f"superan límite {MAX_ADDED}."
        )

    if len(result["modified"]) > MAX_MODIFIED:
        raise SystemExit(
            f"BLOQUEADO: {len(result['modified'])} modificados "
            f"superan límite {MAX_MODIFIED}."
        )

    if len(result["missing"]) > MAX_MISSING:
        raise SystemExit(
            f"BLOQUEADO: existen "
            f"{len(result['missing'])} partidos ausentes."
        )

    print("INGESTION GUARD: OK")


if __name__ == "__main__":
    main()
