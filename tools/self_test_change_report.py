#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

MASTER = ROOT / "data/master_snapshot.json"
STATE = ROOT / "data/published_state.json"
REPORTER = ROOT / "tools/change_report.py"

TARGET_ID = "NBA2627-0001"
NEW_ID = "NBA2627-TEST-ADD-0001"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_report(candidate, output):
    subprocess.run(
        [
            PYTHON,
            str(REPORTER),
            "--candidate", str(candidate),
            "--state", str(STATE),
            "--output", str(output),
        ],
        check=True,
        cwd=ROOT,
    )
    return load(output)


def assert_counts(report, added, modified, unchanged, missing):
    expected = {
        "added": added,
        "modified": modified,
        "unchanged": unchanged,
        "missing": missing,
    }

    if report["counts"] != expected:
        raise AssertionError(
            f"Conteo inesperado.\n"
            f"Esperado: {expected}\n"
            f"Obtenido: {report['counts']}"
        )


def main():
    master = load(MASTER)

    if len(master["events"]) != 1200:
        raise AssertionError("La Base Maestra debe contener 1200 eventos")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)

        print("=== TEST 1: BASELINE ===")
        report = run_report(
            MASTER,
            tmp / "baseline.json",
        )
        assert_counts(report, 0, 0, 1200, 0)
        print("BASELINE: OK")

        print("\n=== TEST 2: MODIFICACION ===")
        modified_master = deepcopy(master)

        target = next(
            e for e in modified_master["events"]
            if e["ID_Partido"] == TARGET_ID
        )

        old_dt = datetime.fromisoformat(
            target["Fecha_Hora_UTC"].replace("Z", "+00:00")
        )

        target["Fecha_Hora_UTC"] = (
            old_dt + timedelta(minutes=15)
        ).isoformat().replace("+00:00", "Z")

        modified_path = tmp / "modified.json"
        save(modified_path, modified_master)

        report = run_report(
            modified_path,
            tmp / "modified_report.json",
        )

        assert_counts(report, 0, 1, 1199, 0)

        change = report["modified"][0]

        assert change["id"] == TARGET_ID
        assert change["uid"] == (
            "NBA2627-0001@nba-master-calendar.local"
        )
        assert change["sequence_actual"] == 0
        assert change["sequence_propuesto"] == 1

        print("MODIFICACION + UID + SEQUENCE: OK")

        print("\n=== TEST 3: EVENTO AUSENTE ===")
        missing_master = deepcopy(master)

        missing_master["events"] = [
            e for e in missing_master["events"]
            if e["ID_Partido"] != TARGET_ID
        ]

        missing_path = tmp / "missing.json"
        save(missing_path, missing_master)

        report = run_report(
            missing_path,
            tmp / "missing_report.json",
        )

        assert_counts(report, 0, 0, 1199, 1)

        missing = report["missing"][0]

        assert missing["id"] == TARGET_ID
        assert missing["accion_automatica"] == "NINGUNA"
        assert missing["requiere_revision"] is True
        assert report["safety"]["auto_cancel_missing"] is False
        assert report["safety"]["requires_review_if_missing"] is True

        print("PROTECCION DE AUSENCIAS: OK")

        print("\n=== TEST 4: EVENTO NUEVO ===")
        added_master = deepcopy(master)

        new_event = deepcopy(master["events"][0])
        new_event["ID_Partido"] = NEW_ID
        new_event["Visitante"] = "TEST VISITANTE"
        new_event["Local"] = "TEST LOCAL"
        new_event["Evento_Especial"] = "Prueba controlada"
        new_event["Fecha_Hora_UTC"] = "2027-04-12T00:00:00Z"

        added_master["events"].append(new_event)

        added_path = tmp / "added.json"
        save(added_path, added_master)

        report = run_report(
            added_path,
            tmp / "added_report.json",
        )

        assert_counts(report, 1, 0, 1200, 0)

        added = report["added"][0]

        assert added["id"] == NEW_ID
        assert added["uid"] == (
            "NBA2627-TEST-ADD-0001@nba-master-calendar.local"
        )
        assert added["sequence_propuesto"] == 0

        print("EVENTO NUEVO + UID + SEQUENCE: OK")

    print()
    print("======================================")
    print("SELF TEST CHANGE REPORT: OK")
    print("4/4 ESCENARIOS SUPERADOS")
    print("======================================")


if __name__ == "__main__":
    main()
