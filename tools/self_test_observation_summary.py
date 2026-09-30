#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
from pathlib import Path


PYTHON = sys.executable
ROOT = Path(__file__).resolve().parent.parent
SUMMARY_TOOL = ROOT / "tools/observation_summary.py"


def save(path, data):
    Path(path).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def run_summary(
    directory,
    report,
    change,
    arena,
    temporal,
    promotion,
):
    output = directory / "summary.md"

    subprocess.run(
        [
            PYTHON,
            str(SUMMARY_TOOL),
            "--report",
            str(report),
            "--change-decision",
            str(change),
            "--arena-guard",
            str(arena),
            "--temporal-guard",
            str(temporal),
            "--promotion-gate",
            str(promotion),
            "--output",
            str(output),
        ],
        check=True,
    )

    return output.read_text(encoding="utf-8")


def assert_contains(text, expected):
    if expected not in text:
        raise AssertionError(
            f"Texto esperado no encontrado: {expected}"
        )


def main():
    if not SUMMARY_TOOL.is_file():
        raise AssertionError(
            f"No existe la herramienta: {SUMMARY_TOOL}"
        )

    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)

        missing = tmp / "missing.json"

        print("=== TEST 1: EVIDENCIA AUSENTE ===")

        summary = run_summary(
            tmp,
            missing,
            missing,
            missing,
            missing,
            missing,
        )

        assert_contains(
            summary,
            "| Added | NOT_AVAILABLE |",
        )
        assert_contains(
            summary,
            "| Promotion Gate | NOT_AVAILABLE |",
        )
        assert_contains(
            summary,
            "**PUBLICACION AUTOMATICA: NO**",
        )

        print("EVIDENCIA AUSENTE: OK")

        print("\n=== TEST 2: EVIDENCIA COMPLETA ===")

        report = tmp / "report.json"
        change = tmp / "change_decision.json"
        arena = tmp / "arena_guard.json"
        temporal = tmp / "temporal_guard.json"
        promotion = tmp / "promotion_gate.json"

        save(
            report,
            {
                "counts": {
                    "baseline": 1200,
                    "candidate": 1200,
                    "added": 11,
                    "modified": 22,
                    "unchanged": 33,
                    "missing": 44,
                }
            },
        )

        save(
            change,
            {
                "mode": "READ-ONLY",
                "decision": "REVIEW",
                "counts": {
                    "added": 11,
                    "modified": 22,
                    "missing": 44,
                    "classified_changes": 55,
                },
            },
        )

        save(
            arena,
            {
                "mode": "READ_ONLY",
                "arena_changes_checked": 66,
                "blocked": 77,
                "decision": "BLOCKED",
            },
        )

        save(
            temporal,
            {
                "mode": "READ_ONLY",
                "decision": "AUTO_ELIGIBLE",
                "counts": {
                    "modified_events": 22,
                    "temporal_changes": 88,
                },
            },
        )

        save(
            promotion,
            {
                "mode": "READ_ONLY",
                "decision": "BLOCKED",
                "guards": {
                    "change_decision": "REVIEW",
                    "arena_geography_guard": "BLOCKED",
                    "temporal_guard": "AUTO_ELIGIBLE",
                },
            },
        )

        summary = run_summary(
            tmp,
            report,
            change,
            arena,
            temporal,
            promotion,
        )

        expected_values = [
            "| Added | 11 |",
            "| Modified | 22 |",
            "| Unchanged | 33 |",
            "| Missing | 44 |",
            "| Change Decision | REVIEW |",
            "| Arena Geography Guard | BLOCKED |",
            "| Temporal Guard | AUTO_ELIGIBLE |",
            "| Promotion Gate | BLOCKED |",
            "- Classified field changes: 55",
            "- Arena changes checked: 66",
            "- Arena changes blocked: 77",
            "- Temporal changes: 88",
            "**PUBLICACION AUTOMATICA: NO**",
        ]

        for expected in expected_values:
            assert_contains(summary, expected)

        print("EVIDENCIA COMPLETA: OK")

        print("\n=== TEST 3: EVIDENCIA PARCIAL ===")

        arena.unlink()
        temporal.unlink()
        promotion.unlink()

        summary = run_summary(
            tmp,
            report,
            change,
            arena,
            temporal,
            promotion,
        )

        assert_contains(summary, "| Added | 11 |")
        assert_contains(
            summary,
            "| Change Decision | REVIEW |",
        )
        assert_contains(
            summary,
            "| Arena Geography Guard | NOT_AVAILABLE |",
        )
        assert_contains(
            summary,
            "| Temporal Guard | NOT_AVAILABLE |",
        )
        assert_contains(
            summary,
            "| Promotion Gate | NOT_AVAILABLE |",
        )
        assert_contains(
            summary,
            "- Classified field changes: 55",
        )
        assert_contains(
            summary,
            "**PUBLICACION AUTOMATICA: NO**",
        )

        print("EVIDENCIA PARCIAL: OK")

    print()
    print("==========================================")
    print("SELF TEST OBSERVATION SUMMARY: OK")
    print("3/3 ESCENARIOS SUPERADOS")
    print("==========================================")


if __name__ == "__main__":
    main()
