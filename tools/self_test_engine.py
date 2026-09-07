#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PYTHON=sys.executable

def run(*args,cwd):
    p=subprocess.run([PYTHON,*args],cwd=cwd,text=True,capture_output=True)
    if p.returncode: print(p.stdout); print(p.stderr); raise SystemExit(p.returncode)
    return p.stdout.strip()

def main():
    with tempfile.TemporaryDirectory() as td:
        t=Path(td); shutil.copytree(ROOT,t/"repo",dirs_exist_ok=True); r=t/"repo"
        # Initialize baseline state without changing production feeds.
        master=json.loads((r/"data/master_snapshot.json").read_text(encoding="utf-8"))
        sys.path.insert(0,str(r/"tools")); from update_engine import init_state
        (r/"data/published_state.json").write_text(json.dumps(init_state(master),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        out=run("tools/update_engine.py","--candidate","data/master_snapshot.json",cwd=r)
        assert "Modificados: 0" in out and "Añadidos: 0" in out and "Ausentes: 0" in out, out
        run("tools/simulate_master_change.py",cwd=r)
        out=run("tools/update_engine.py","--candidate","data/master_candidate_test.json",cwd=r)
        assert "Modificados: 1" in out, out
        run("tools/update_engine.py","--candidate","data/master_candidate_test.json","--apply",cwd=r)
        state=json.loads((r/"data/published_state.json").read_text(encoding="utf-8"))["events"]["NBA2627-0001"]
        assert state["sequence"]==1
        text=(r/"docs/calendars/nba-2026-27-completo.ics").read_text(encoding="utf-8")
        assert "UID:NBA2627-0001@nba-master-calendar.local" in text
        assert "SEQUENCE:1" in text
        assert "DTSTART:20261020T191500Z" in text
        assert "Hora Santiago: 20-10-2026 16:15" in text.replace("\r\n ","").replace("\n ","")
        assert text.count("UID:NBA2627-0001@nba-master-calendar.local")==1
        print("SELF TEST 3.3: OK — baseline 0 cambios; simulación 1 cambio; SEQUENCE 1; sin duplicado; descripción horaria recalculada.")
if __name__=="__main__": main()
