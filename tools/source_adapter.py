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


def normalize_nba_event(
    source_event,
    master_event,
    relation,
    arena_registry,
):
    """
    Normaliza un evento oficial NBA al esquema interno.

    Identidad:
        gameId NBA -> Identity Map -> ID_Partido

    Política inicial:
    - El Master sigue siendo la base del candidato.
    - Fecha_Hora_UTC puede actualizarse desde NBA.
    - Arena puede actualizarse si NBA entrega un valor no vacío.
    - Visitante y Local se validan contra el Identity Map.
    - No se infieren ciudad, estado, país ni zona horaria.
    - No se modifican todavía TV, streaming ni clasificaciones internas.
    """

    candidate = dict(master_event)

    game_id = str(source_event.get("gameId") or "")
    away = str(source_event.get("away") or "").strip()
    home = str(source_event.get("home") or "").strip()
    utc = str(source_event.get("gameDateTimeUTC") or "").strip()
    arena = str(source_event.get("arenaName") or "").strip()

    expected_away = str(
        relation.get("Visitante_Tricode") or ""
    ).strip()

    expected_home = str(
        relation.get("Local_Tricode") or ""
    ).strip()

    if not game_id:
        raise SystemExit(
            "SOURCE ADAPTER: gameId vacío"
        )

    if away != expected_away:
        raise SystemExit(
            f"SOURCE ADAPTER: visitante inconsistente para {game_id}: "
            f"NBA={away!r} IDENTITY_MAP={expected_away!r}"
        )

    if home != expected_home:
        raise SystemExit(
            f"SOURCE ADAPTER: local inconsistente para {game_id}: "
            f"NBA={home!r} IDENTITY_MAP={expected_home!r}"
        )

    if not utc:
        raise SystemExit(
            f"SOURCE ADAPTER: gameDateTimeUTC vacío para {game_id}"
        )

    candidate["Fecha_Hora_UTC"] = utc

    if arena:
        master_arena = str(
            master_event.get("Arena") or ""
        ).strip()

        if arena != master_arena:
            geo = arena_registry.get(arena)

            if geo is None:
                raise SystemExit(
                    "SOURCE ADAPTER: ARENA NO REGISTRADA: "
                    f"{arena!r} (gameId {game_id})"
                )

            candidate["Arena"] = arena
            candidate["Ciudad"] = geo.get("Ciudad")
            candidate["Estado_Provincia"] = (
                geo.get("Estado_Provincia")
            )
            candidate["Pais"] = geo.get("Pais")
            candidate["Zona_Horaria_Arena"] = (
                geo.get("Zona_Horaria_Arena")
            )

    return candidate


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
        "--identity-map",
        default="data/nba_game_identity_map.json",
        help="Mapa persistente gameId NBA -> ID_Partido",
    )

    parser.add_argument(
        "--arena-registry",
        default="data/reference/arena_registry.json",
        help="Registro controlado de sedes NBA",
    )

    parser.add_argument(
        "--output",
        default="data/incoming/nba_adapter_candidate.json",
        help="Candidate de salida"
    )

    args = parser.parse_args()

    source = load_json(args.source)
    master = load_json(args.master)
    identity = load_json(args.identity_map)
    arena_registry_data = load_json(args.arena_registry)

    arena_registry = arena_registry_data.get(
        "arenas", {}
    )

    if not isinstance(arena_registry, dict):
        raise SystemExit(
            "ARENA REGISTRY INVALIDO: 'arenas' debe ser objeto"
        )

    source_events = source.get("events", [])
    master_events = master.get("events", [])
    identity_events = identity.get("events", [])

    errors = []

    master_by_id = {}

    for event in master_events:
        internal_id = event.get("ID_Partido")

        if not internal_id:
            raise SystemExit("MASTER INVALIDO: falta ID_Partido")

        if internal_id in master_by_id:
            raise SystemExit(
                f"MASTER INVALIDO: ID_Partido duplicado {internal_id}"
            )

        master_by_id[internal_id] = event

    identity_by_gameid = {}

    for relation in identity_events:
        game_id = str(relation.get("gameId") or "")
        internal_id = relation.get("ID_Partido")

        if not game_id or not internal_id:
            raise SystemExit(
                "IDENTITY MAP INVALIDO: falta gameId o ID_Partido"
            )

        if game_id in identity_by_gameid:
            raise SystemExit(
                f"IDENTITY MAP INVALIDO: gameId duplicado {game_id}"
            )

        identity_by_gameid[game_id] = relation

    matched = []
    unmatched = []

    for source_event in source_events:
        game_id = str(source_event.get("gameId") or "")

        relation = identity_by_gameid.get(game_id)

        if relation is None:
            raise SystemExit(
                "SOURCE ADAPTER: GAMEID NO REGISTRADO: "
                f"{game_id!r}"
            )

        internal_id = relation["ID_Partido"]
        master_event = master_by_id.get(internal_id)

        if master_event is None:
            raise SystemExit(
                f"IDENTITY MAP INVALIDO: {internal_id} no existe en Master"
            )

        # Validación defensiva:
        # la identidad proviene exclusivamente de gameId -> ID_Partido.
        # En esta versión todavía NO sobrescribimos campos del Master.
        candidate = normalize_nba_event(
            source_event,
            master_event,
            relation,
            arena_registry,
        )
        candidate_errors = validate_event(
            candidate,
            len(matched) + 1,
        )

        if candidate_errors:
            print("SOURCE ADAPTER: BLOQUEADO")
            print(
                f"gameId {game_id} -> ID_Partido {internal_id}"
            )

            for error in candidate_errors:
                print(" -", error)

            raise SystemExit(1)

        matched.append(candidate)

    result = {
        "schema_version": "source-adapter-0.1",
        "season": master.get("season"),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "mode": "observation",
        "identity_mode": "nba_gameId",
        "identity_map": args.identity_map,
        "identity_count": len(identity_events),
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
