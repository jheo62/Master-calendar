#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def load_teams(path):
    rows = []

    for line in Path(path).read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        parts = line.split()

        if len(parts) != 2:
            raise SystemExit(
                f"TEAMS TSV INVALIDO: {line!r}"
            )

        tricode, team_id = parts

        if (
            len(tricode) != 3
            or not tricode.isalpha()
            or not team_id.isdigit()
        ):
            raise SystemExit(
                f"TEAMS TSV INVALIDO: {line!r}"
            )

        rows.append(
            (tricode.upper(), team_id)
        )

    if len(rows) != 30:
        raise SystemExit(
            f"SE ESPERABAN 30 EQUIPOS; HAY {len(rows)}"
        )

    if len({x[0] for x in rows}) != 30:
        raise SystemExit(
            "TRICODES DUPLICADOS"
        )

    if len({x[1] for x in rows}) != 30:
        raise SystemExit(
            "TEAM IDs DUPLICADOS"
        )

    return rows


def download(url, output, timeout):
    cmd = [
        "curl",
        "--fail",
        "--location",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "--retry",
        "2",
        "--retry-delay",
        "2",
        "--user-agent",
        "Mozilla/5.0",
        "--output",
        str(output),
        url,
    ]

    result = subprocess.run(cmd)

    if result.returncode != 0:
        raise SystemExit(
            f"DESCARGA FALLIDA: {url}"
        )


def validate_html(path):
    text = Path(path).read_text(
        encoding="utf-8",
        errors="replace",
    )

    if "__NEXT_DATA__" not in text:
        raise SystemExit(
            f"HTML INVALIDO: {path} sin __NEXT_DATA__"
        )

    if "gameId" not in text:
        raise SystemExit(
            f"HTML INVALIDO: {path} sin gameId"
        )

    return len(text.encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Descarga páginas oficiales NBA "
            "para extracción segura de calendario."
        )
    )

    parser.add_argument(
        "--teams",
        default="data/reference/nba_teams_2026_27.tsv",
    )

    parser.add_argument(
        "--output-dir",
        required=True,
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
    )

    args = parser.parse_args()

    teams = load_teams(args.teams)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    downloaded = []

    for tricode, team_id in teams:

        url = (
            "https://www.nba.com/team/"
            f"{team_id}/schedule"
        )

        target = output_dir / f"{tricode}.html"

        print(
            f"Descargando {tricode} "
            f"({team_id})..."
        )

        download(
            url,
            target,
            args.timeout,
        )

        size = validate_html(target)

        downloaded.append(
            (tricode, size)
        )

    if len(downloaded) != 30:
        raise SystemExit(
            "DESCARGA INCOMPLETA"
        )

    print()
    print("NBA SOURCE DOWNLOAD: OK")
    print("Equipos:", len(downloaded))

    for tricode, size in downloaded:
        print(
            f"{tricode}: {size} bytes"
        )


if __name__ == "__main__":
    main()
