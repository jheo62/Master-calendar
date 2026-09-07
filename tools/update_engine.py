#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy
from datetime import datetime, timezone
from pathlib import Path
from common import load_json, save_json, fingerprint, uid_for
from feed_builder import build_all

def init_state(master):
    return {"schema_version":"3.3.0","season":master.get("season"),"events":{
        e["ID_Partido"]:{"uid":uid_for(e["ID_Partido"]),"sequence":0,"fingerprint":fingerprint(e),"status":"ACTIVE","last_modified":None}
        for e in master["events"]
    }}

def compare(master, state):
    current=state.get("events",{}); candidate={e["ID_Partido"]:e for e in master["events"]}
    added=[]; modified=[]; unchanged=[]; missing=[]
    for eid,e in candidate.items():
        if eid not in current: added.append(eid)
        elif fingerprint(e)!=current[eid].get("fingerprint"): modified.append(eid)
        else: unchanged.append(eid)
    for eid in current:
        if eid not in candidate and current[eid].get("status")!="CANCELLED": missing.append(eid)
    return added, modified, unchanged, missing

def main():
    ap=argparse.ArgumentParser(description="NBA Master Calendar update engine 3.3")
    ap.add_argument("--candidate",required=True); ap.add_argument("--state",default="data/published_state.json"); ap.add_argument("--report",default="reports/update_report.json")
    ap.add_argument("--apply",action="store_true"); ap.add_argument("--docs",default="docs"); ap.add_argument("--cancel-missing",action="store_true")
    a=ap.parse_args(); master=load_json(a.candidate)
    sp=Path(a.state)
    state=load_json(sp) if sp.exists() else init_state(master)
    added,modified,unchanged,missing=compare(master,state)
    now=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report={"engine":"3.3.0","generated_at":now,"candidate":a.candidate,"counts":{"added":len(added),"modified":len(modified),"unchanged":len(unchanged),"missing":len(missing)},"added":added,"modified":modified,"missing":missing,"applied":False}
    if a.apply:
        byid={e["ID_Partido"]:e for e in master["events"]}
        for eid in added:
            state["events"][eid]={"uid":uid_for(eid),"sequence":0,"fingerprint":fingerprint(byid[eid]),"status":"ACTIVE","last_modified":now}
        for eid in modified:
            rec=state["events"][eid]; rec["sequence"]=int(rec.get("sequence",0))+1; rec["fingerprint"]=fingerprint(byid[eid]); rec["status"]="ACTIVE"; rec["last_modified"]=now
        if missing and not a.cancel_missing:
            raise SystemExit("Hay eventos ausentes. Reejecute con --cancel-missing solo si desea publicar cancelaciones explícitas.")
        if a.cancel_missing:
            for eid in missing:
                rec=state["events"][eid]; rec["sequence"]=int(rec.get("sequence",0))+1; rec["status"]="CANCELLED"; rec["last_modified"]=now
        save_json(sp,state)
        stats=build_all(a.candidate,a.state,a.docs); report["feed_stats"]=stats; report["applied"]=True
    save_json(a.report,report)
    print(f"Añadidos: {len(added)} | Modificados: {len(modified)} | Sin cambio: {len(unchanged)} | Ausentes: {len(missing)} | Aplicado: {report['applied']}")
    if modified: print("Modificados:", ", ".join(modified[:20]), "..." if len(modified)>20 else "")
if __name__=="__main__": main()
