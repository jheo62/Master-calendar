#!/usr/bin/env python3
from pathlib import Path
import shutil, sys

ROOT = Path(__file__).resolve().parents[1] / "docs" / "test"
version = (sys.argv[1] if len(sys.argv) > 1 else "").lower()
source = {"v1":"feed-v1.ics", "v2":"feed-v2.ics"}.get(version)
if not source:
    raise SystemExit("Uso: python3 tools/simulate_test_update.py v1|v2")
shutil.copy2(ROOT/source, ROOT/"nba-test-current.ics")
print(f"Feed de prueba actualizado a {version.upper()}. Haz commit + push.")
