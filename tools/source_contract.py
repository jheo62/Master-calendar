#!/usr/bin/env python3

"""
NBA Master Calendar
Fase 3.7.4A - Source Contract

Valida datos provenientes de una fuente externa antes
de que puedan entrar al Candidate Builder.

NO modifica producción.
"""

import json
import sys
from pathlib import Path


REQUIRED_FIELDS = (
    "Visitante",
    "Local",
    "Fecha_Hora_UTC",
)

OPTIONAL_FIELDS = (
    "Arena",
    "Ciudad",
    "Estado_Provincia",
    "Pais",
    "TV_Normalizada",
    "Streaming_Normalizado",
    "URL_NBA",
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_event(event, position):
    errors = []

    for field in REQUIRED_FIELDS:
        value = event.get(field)

        if value is None or str(value).strip() == "":
            errors.append(
                f"Evento {position}: falta {field}"
            )

    return errors


def main():
    if len(sys.argv) != 2:
        raise SystemExit(
            "Uso: python3 tools/source_contract.py SOURCE.json"
        )

    path = Path(sys.argv[1])

    if not path.exists():
        raise SystemExit(
            f"ERROR: no existe {path}"
        )

    data = load_json(path)
    events = data.get("events")

    if not isinstance(events, list):
        raise SystemExit(
            "BLOQUEADO: 'events' no es una lista."
        )

    if not events:
        raise SystemExit(
            "BLOQUEADO: la fuente no contiene eventos."
        )

    errors = []

    for i, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            errors.append(
                f"Evento {i}: no es un objeto."
            )
            continue

        errors.extend(
            validate_event(event, i)
        )

    print("=== SOURCE CONTRACT ===")
    print(f"Eventos recibidos : {len(events)}")
    print(
        "Campos requeridos : "
        + ", ".join(REQUIRED_FIELDS)
    )

    if errors:
        print(f"Errores            : {len(errors)}")

        for error in errors[:20]:
            print("-", error)

        raise SystemExit(
            "SOURCE CONTRACT: BLOQUEADO"
        )

    print("Errores            : 0")
    print("SOURCE CONTRACT: OK")


if __name__ == "__main__":
    main()
