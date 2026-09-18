#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


FIELDS = (
    "Ciudad",
    "Estado_Provincia",
    "Pais",
    "Zona_Horaria_Arena",
)


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def normalize(value):
    if value is None:
        return None

    value = str(value).strip()

    if value == "":
        return None

    return value


def main():
    parser = argparse.ArgumentParser(
        description="Valida coherencia geografica de cambios de Arena."
    )

    parser.add_argument("--candidate", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    candidate_data = load_json(args.candidate)
    report = load_json(args.report)
    registry_data = load_json(args.registry)

    events = candidate_data.get("events")

    if not isinstance(events, list):
        raise SystemExit(
            "ERROR: candidate no contiene una lista 'events'"
        )

    arenas = registry_data.get("arenas", registry_data)

    if not isinstance(arenas, dict):
        raise SystemExit(
            "ERROR: arena registry invalido"
        )

    candidate_by_id = {
        e.get("ID_Partido"): e
        for e in events
        if e.get("ID_Partido")
    }

    checks = []
    blocked = []

    for modified in report.get("modified", []):
        game_id = modified.get("ID_Partido")

        arena_changes = [
            c
            for c in modified.get("changes", [])
            if c.get("field") == "Arena"
        ]

        if not arena_changes:
            continue

        event = candidate_by_id.get(game_id)

        if event is None:
            blocked.append({
                "ID_Partido": game_id,
                "reason": "candidate_event_not_found",
            })
            continue

        arena = normalize(event.get("Arena"))

        registry_entry = arenas.get(arena)

        check = {
            "ID_Partido": game_id,
            "Arena": arena,
            "registry_match": registry_entry is not None,
            "mismatches": [],
        }

        if registry_entry is None:
            check["mismatches"].append({
                "field": "Arena",
                "candidate": arena,
                "registry": None,
                "reason": "arena_not_registered",
            })

        else:
            for field in FIELDS:
                candidate_value = normalize(event.get(field))
                registry_value = normalize(
                    registry_entry.get(field)
                )

                if candidate_value != registry_value:
                    check["mismatches"].append({
                        "field": field,
                        "candidate": candidate_value,
                        "registry": registry_value,
                    })

        checks.append(check)

        if check["mismatches"]:
            blocked.append(check)

    result = {
        "schema_version": "1.0",
        "mode": "READ_ONLY",
        "arena_changes_checked": len(checks),
        "blocked": len(blocked),
        "decision": (
            "BLOCKED"
            if blocked
            else "AUTO_ELIGIBLE"
        ),
        "checks": checks,
    }

    Path(args.output).write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("=== ARENA GEOGRAPHY GUARD ===")
    print("Mode: READ_ONLY")
    print(
        "Arena changes checked:",
        result["arena_changes_checked"],
    )
    print("Blocked:", result["blocked"])

    for check in checks:
        print()
        print(
            check["ID_Partido"],
            "|",
            check["Arena"],
        )

        if not check["mismatches"]:
            print("  GEOGRAPHY: OK")
            continue

        for mismatch in check["mismatches"]:
            print(
                " ",
                mismatch["field"],
                "| candidate:",
                repr(mismatch.get("candidate")),
                "| registry:",
                repr(mismatch.get("registry")),
            )

    print()
    print("Decision:", result["decision"])
    print("JSON:", args.output)

    if blocked:
        print(
            "ARENA GEOGRAPHY GUARD: BLOCKED",
            file=sys.stderr,
        )
        return 2

    print("ARENA GEOGRAPHY GUARD: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
