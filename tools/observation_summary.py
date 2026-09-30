#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


NOT_AVAILABLE = "NOT_AVAILABLE"


def load_json(path):
    path = Path(path)

    if not path.is_file():
        return None

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def value(data, *keys):
    current = data

    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return NOT_AVAILABLE
        current = current[key]

    return current


def decision(data):
    return value(data, "decision")


def build_summary(args):
    report = load_json(args.report)
    change = load_json(args.change_decision)
    arena = load_json(args.arena_guard)
    temporal = load_json(args.temporal_guard)
    promotion = load_json(args.promotion_gate)

    lines = [
        "## NBA Live Observation Summary",
        "",
        "**Mode:** READ_ONLY",
        "",
        "### Change counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Added | {value(report, 'counts', 'added')} |",
        f"| Modified | {value(report, 'counts', 'modified')} |",
        f"| Unchanged | {value(report, 'counts', 'unchanged')} |",
        f"| Missing | {value(report, 'counts', 'missing')} |",
        "",
        "### Decision chain",
        "",
        "| Stage | Decision |",
        "| --- | --- |",
        f"| Change Decision | {decision(change)} |",
        f"| Arena Geography Guard | {decision(arena)} |",
        f"| Temporal Guard | {decision(temporal)} |",
        f"| Promotion Gate | {decision(promotion)} |",
        "",
        "### Guard details",
        "",
        (
            "- Classified field changes: "
            f"{value(change, 'counts', 'classified_changes')}"
        ),
        (
            "- Arena changes checked: "
            f"{value(arena, 'arena_changes_checked')}"
        ),
        f"- Arena changes blocked: {value(arena, 'blocked')}",
        (
            "- Temporal changes: "
            f"{value(temporal, 'counts', 'temporal_changes')}"
        ),
        "",
        "### Publication safety",
        "",
        "**PUBLICACION AUTOMATICA: NO**",
        "",
        "Evidence artifact: `nba-live-observation-evidence`",
    ]

    promotion_error = value(promotion, "error")

    if promotion_error != NOT_AVAILABLE:
        lines.extend(
            [
                "",
                "### Promotion Gate error",
                "",
                f"`{promotion_error}`",
            ]
        )

    return "\n".join(str(line) for line in lines) + "\n"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Genera un resumen Markdown read-only de la "
            "observacion automatica NBA."
        )
    )
    parser.add_argument("--report", required=True)
    parser.add_argument("--change-decision", required=True)
    parser.add_argument("--arena-guard", required=True)
    parser.add_argument("--temporal-guard", required=True)
    parser.add_argument("--promotion-gate", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    summary = build_summary(args)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(summary, encoding="utf-8")

    print("=== OBSERVATION SUMMARY ===")
    print("Mode: READ_ONLY")
    print("Output:", output)
    print("OBSERVATION SUMMARY: OK")


if __name__ == "__main__":
    main()
