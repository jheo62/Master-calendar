#!/usr/bin/env python3

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


NEXT_DATA_RE = re.compile(
    r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>'
    r'(.*?)</script>',
    re.S,
)


def load_teams(path):
    teams = []

    for line in Path(path).read_text(
        encoding="utf-8"
    ).splitlines():

        if not line.strip():
            continue

        parts = line.split()

        if len(parts) != 2:
            raise SystemExit(
                f"TEAMS TSV INVALIDO: {line!r}"
            )

        teams.append(
            {
                "tricode": parts[0],
                "team_id": parts[1],
            }
        )

    if len(teams) != 30:
        raise SystemExit(
            f"SE ESPERABAN 30 EQUIPOS; HAY {len(teams)}"
        )

    return teams


def extract_schedule(html_path):
    text = Path(html_path).read_text(
        encoding="utf-8",
        errors="replace",
    )

    match = NEXT_DATA_RE.search(text)

    if not match:
        raise ValueError("sin __NEXT_DATA__")

    data = json.loads(match.group(1))

    schedule = (
        data["props"]
            ["pageProps"]
            ["team"]
            ["schedule"]
    )

    if not isinstance(schedule, list):
        raise ValueError("schedule no es lista")

    return schedule


def normalize_event(event):
    return {
        "gameId": str(
            event.get("gameId") or ""
        ).strip(),
        "gameDateTimeUTC": str(
            event.get("gameDateTimeUTC") or ""
        ).strip(),
        "home": str(
            (event.get("homeTeam") or {}).get(
                "teamTricode"
            ) or ""
        ).strip(),
        "away": str(
            (event.get("awayTeam") or {}).get(
                "teamTricode"
            ) or ""
        ).strip(),
        "arenaName": str(
            event.get("arenaName") or ""
        ).strip(),
        "gameLabel": str(
            event.get("gameLabel") or ""
        ).strip(),
        "gameSubtype": str(
            event.get("gameSubtype") or ""
        ).strip(),
    }


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Extrae calendario NBA desde HTML "
            "__NEXT_DATA__ de páginas oficiales."
        )
    )

    parser.add_argument(
        "--html-dir",
        required=True,
    )

    parser.add_argument(
        "--teams",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    html_dir = Path(args.html_dir)
    teams = load_teams(args.teams)

    unique = {}
    appearances = Counter()
    errors = []

    for team in teams:
        tricode = team["tricode"]
        html = html_dir / f"{tricode}.html"

        if not html.exists():
            errors.append(
                f"{tricode}: HTML ausente"
            )
            continue

        try:
            schedule = extract_schedule(html)
        except Exception as exc:
            errors.append(
                f"{tricode}: {exc}"
            )
            continue

        regular = [
            event
            for event in schedule
            if isinstance(event, dict)
            and str(
                event.get("gameId") or ""
            ).startswith("002")
        ]

        if len(regular) != 80:
            errors.append(
                f"{tricode}: "
                f"se esperaban 80 juegos 002; "
                f"hay {len(regular)}"
            )

        for raw_event in regular:
            event = normalize_event(raw_event)
            gid = event["gameId"]

            appearances[gid] += 1

            if gid in unique:
                if unique[gid] != event:
                    errors.append(
                        f"{gid}: datos inconsistentes "
                        "entre equipos"
                    )
            else:
                unique[gid] = event

    bad_appearances = {
        gid: count
        for gid, count in appearances.items()
        if count != 2
    }

    if bad_appearances:
        errors.append(
            f"{len(bad_appearances)} gameId "
            "no aparecen exactamente 2 veces"
        )

    if len(unique) != 1200:
        errors.append(
            f"se esperaban 1200 juegos únicos; "
            f"hay {len(unique)}"
        )

    if errors:
        print("NBA SOURCE EXTRACTOR: BLOQUEADO")

        for error in errors[:30]:
            print(" -", error)

        raise SystemExit(1)

    events = sorted(
        unique.values(),
        key=lambda x: (
            x["gameDateTimeUTC"],
            x["gameId"],
        ),
    )

    result = {
        "schema_version": "nba-source-0.1",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "source": "NBA.com team schedules",
        "mode": "observation",
        "extraction": {
            "method": "__NEXT_DATA__",
            "path": "$.props.pageProps.team.schedule[]",
            "regular_season_gameId_prefix": "002",
            "teams": 30,
        },
        "appearance_count": sum(
            appearances.values()
        ),
        "unique_game_count": len(events),
        "events": events,
    }

    output = Path(args.output)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print("NBA SOURCE EXTRACTOR: OK")
    print("Equipos:", len(teams))
    print(
        "Apariciones:",
        sum(appearances.values()),
    )
    print("Partidos únicos:", len(events))
    print(
        "Apariciones por gameId:",
        dict(sorted(
            Counter(
                appearances.values()
            ).items()
        )),
    )
    print("Salida:", output)


if __name__ == "__main__":
    main()
