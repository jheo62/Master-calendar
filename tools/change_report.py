#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from common import fingerprint, uid_for


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def index_events(master):
    events = master.get("events", [])
    return {
        str(event["ID_Partido"]): event
        for event in events
    }


def main():
    parser = argparse.ArgumentParser(
        description="Genera informe seguro de diferencias entre candidato y estado publicado."
    )
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    candidate = load_json(args.candidate)
    state = load_json(args.state)

    candidate_events = index_events(candidate)
    published_events = state.get("events", {})

    candidate_ids = set(candidate_events)
    published_ids = set(published_events)

    added_ids = sorted(candidate_ids - published_ids)
    missing_ids = sorted(published_ids - candidate_ids)
    common_ids = sorted(candidate_ids & published_ids)

    modified = []
    unchanged = []

    for event_id in common_ids:
        event = candidate_events[event_id]
        current = published_events[event_id]

        new_fingerprint = fingerprint(event)
        old_fingerprint = current.get("fingerprint")

        if new_fingerprint == old_fingerprint:
            unchanged.append(event_id)
        else:
            modified.append({
                "id": event_id,
                "uid": current.get("uid") or uid_for(event_id),
                "sequence_actual": int(current.get("sequence", 0)),
                "sequence_propuesto": int(current.get("sequence", 0)) + 1,
                "fingerprint_actual": old_fingerprint,
                "fingerprint_nuevo": new_fingerprint,
                "evento_candidato": event,
            })

    added = []
    for event_id in added_ids:
        event = candidate_events[event_id]
        added.append({
            "id": event_id,
            "uid": uid_for(event_id),
            "sequence_propuesto": 0,
            "fingerprint_nuevo": fingerprint(event),
            "evento_candidato": event,
        })

    missing = []
    for event_id in missing_ids:
        current = published_events[event_id]
        missing.append({
            "id": event_id,
            "uid": current.get("uid") or uid_for(event_id),
            "sequence_actual": int(current.get("sequence", 0)),
            "status_actual": current.get("status"),
            "accion_automatica": "NINGUNA",
            "requiere_revision": True,
        })

    counts = {
        "added": len(added),
        "modified": len(modified),
        "unchanged": len(unchanged),
        "missing": len(missing),
    }

    report = {
        "schema_version": "1.0",
        "season": candidate.get("season"),
        "counts": counts,
        "added": added,
        "modified": modified,
        "missing": missing,
        "safety": {
            "auto_cancel_missing": False,
            "requires_review_if_missing": bool(missing),
        },
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== INFORME DE CAMBIOS ===")
    print("Añadidos:", counts["added"])
    print("Modificados:", counts["modified"])
    print("Sin cambio:", counts["unchanged"])
    print("Ausentes:", counts["missing"])
    print("Salida:", output)

    if missing:
        print("SEGURIDAD: existen eventos ausentes; NO se propone cancelación automática.")
    else:
        print("SEGURIDAD: sin eventos ausentes.")


if __name__ == "__main__":
    main()
