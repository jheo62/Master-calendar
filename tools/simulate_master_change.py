#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import timedelta
from common import load_json, save_json, parse_utc

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--source",default="data/master_snapshot.json"); ap.add_argument("--output",default="data/master_candidate_test.json"); ap.add_argument("--id",default="NBA2627-0001"); ap.add_argument("--minutes",type=int,default=15)
    a=ap.parse_args(); obj=load_json(a.source); found=False
    for e in obj["events"]:
        if e["ID_Partido"]==a.id:
            e["Fecha_Hora_UTC"]=(parse_utc(e["Fecha_Hora_UTC"])+timedelta(minutes=a.minutes)).strftime("%Y-%m-%dT%H:%M:%SZ"); found=True; break
    if not found: raise SystemExit(f"ID no encontrado: {a.id}")
    obj["simulation"]={"event_id":a.id,"offset_minutes":a.minutes,"not_real_nba_change":True}; save_json(a.output,obj); print(a.output)
if __name__=="__main__": main()
