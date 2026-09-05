#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parents[1] / "docs"
feeds = list((ROOT/"calendars").rglob("*.ics")) + list((ROOT/"test").glob("*.ics"))
errors = []

def unfold(t):
    return re.sub(r"\r?\n[ \t]", "", t)

for p in feeds:
    t = p.read_text(encoding="utf-8")
    if not t.startswith("BEGIN:VCALENDAR") or not t.rstrip().endswith("END:VCALENDAR"):
        errors.append(f"{p}: VCALENDAR inválido")
    bodies = re.findall(r"BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT", t, flags=re.S)
    uids = []
    for b in bodies:
        u = unfold(b)
        for req in ("UID","DTSTART","DTEND","SUMMARY","SEQUENCE"):
            if not re.search(rf"^{req}:", u, flags=re.M):
                errors.append(f"{p}: falta {req}")
        m = re.search(r"^UID:(.+)$", u, flags=re.M)
        if m: uids.append(m.group(1).strip())
    if len(uids) != len(set(uids)):
        errors.append(f"{p}: UID duplicados")
    print(f"OK {p.relative_to(ROOT)} | eventos={len(bodies)} | UID únicos={len(set(uids))}")

if errors:
    print("\nERRORES:")
    print("\n".join(errors))
    sys.exit(1)
print("\nVALIDACIÓN COMPLETA: OK")
