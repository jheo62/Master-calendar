#!/usr/bin/env python3
from __future__ import annotations
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from common import load_json, parse_utc, fmt_ics_utc, fmt_local, slugify, uid_for, status_for

CRLF = "\r\n"

def esc(s):
    s = "" if s is None else str(s)
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def fold_line(line: str, limit: int = 73):
    # Byte-safe UTF-8 folding, continuation line starts with one space.
    out=[]; current=""; current_bytes=0
    for ch in line:
        b=len(ch.encode("utf-8"))
        if current and current_bytes+b > limit:
            out.append(current); current=" " + ch; current_bytes=1+b
        else:
            current += ch; current_bytes += b
    out.append(current)
    return CRLF.join(out)

def event_summary(e):
    base=f"{e['Visitante']} @ {e['Local']}"
    if e.get("Evento_Especial"):
        return f"[{str(e['Evento_Especial']).upper()}] {base}"
    if e.get("Es_NBA_Cup"):
        return f"[NBA CUP] {base}"
    return base

def event_lines(e, state, stamp):
    start=parse_utc(e["Fecha_Hora_UTC"]); end=start+timedelta(hours=3)
    seq=int(state.get(e["ID_Partido"],{}).get("sequence",0))
    uid=uid_for(e["ID_Partido"])
    loc=", ".join(x for x in [e.get("Arena"),e.get("Ciudad"),e.get("Estado_Provincia"),e.get("País")] if x)
    desc=[
        f"NBA {e.get('Temporada','2026-27')} — {e.get('Fase') or 'Temporada Regular'}",
        f"Hora Santiago: {fmt_local(start,'America/Santiago')}",
        f"Hora Punta Arenas/Magallanes: {fmt_local(start,'America/Punta_Arenas')}",
        f"TV nacional EE.UU.: {e.get('TV_Normalizada') or 'No indicado'}",
        f"Streaming: {e.get('Streaming_Normalizado') or 'No indicado'}",
    ]
    if e.get("Grupo_NBA_Cup"): desc.append(f"Grupo NBA Cup: {e['Grupo_NBA_Cup']}")
    if e.get("Evento_Especial"): desc.append(f"Evento especial: {e['Evento_Especial']}")
    desc += [f"ID maestro: {e['ID_Partido']}", "Fuente base: NBA.com", "Duración del calendario: 3 h estimadas; el término real del partido puede variar."]
    base=f"{e['Visitante']} @ {e['Local']}"
    lines=[
        "BEGIN:VEVENT", f"UID:{uid}", f"DTSTAMP:{stamp}", f"DTSTART:{fmt_ics_utc(start)}", f"DTEND:{fmt_ics_utc(end)}",
        f"SUMMARY:{esc(event_summary(e))}", f"LOCATION:{esc(loc)}", f"DESCRIPTION:{esc(chr(10).join(desc))}",
        f"STATUS:{status_for(e)}", "TRANSP:TRANSPARENT", "CATEGORIES:NBA 2026-27", f"SEQUENCE:{seq}"
    ]
    last=state.get(e["ID_Partido"],{}).get("last_modified")
    if last: lines.append(f"LAST-MODIFIED:{last}")
    for trigger, text in [("-P1D","partido mañana"),("-PT2H","partido en 2 horas"),("-PT30M","partido en 30 minutos")]:
        lines += ["BEGIN:VALARM","ACTION:DISPLAY",f"DESCRIPTION:{esc('NBA: '+text+' — '+base)}",f"TRIGGER:{trigger}","END:VALARM"]
    lines += ["END:VEVENT"]
    return lines

def write_calendar(path, name, events, state, stamp):
    lines=["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//NBA Master Calendar//2026-27 Feed Engine 3.3//ES","CALSCALE:GREGORIAN","METHOD:PUBLISH",f"X-WR-CALNAME:{esc(name)}","X-WR-TIMEZONE:UTC"]
    for e in sorted(events, key=lambda x:(x["Fecha_Hora_UTC"],x["ID_Partido"])):
        lines += event_lines(e,state,stamp)
    lines += ["END:VCALENDAR"]
    text=CRLF.join(fold_line(x) for x in lines)+CRLF
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(text.encode("utf-8"))

def build_all(master_path, state_path, docs_dir):
    master=load_json(master_path); state=load_json(state_path).get("events",{})
    events=master["events"]; docs=Path(docs_dir); stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cal=docs/"calendars"; teams=cal/"teams"; teams.mkdir(parents=True,exist_ok=True)
    write_calendar(cal/"nba-2026-27-completo.ics","NBA 2026-27 — Completo",events,state,stamp)
    write_calendar(cal/"nba-2026-27-cup-group-play.ics","NBA Cup 2026 — Group Play",[e for e in events if e.get("Es_NBA_Cup")],state,stamp)
    write_calendar(cal/"nba-2026-27-eventos-especiales.ics","NBA 2026-27 — Eventos especiales",[e for e in events if e.get("Es_Partido_Especial")],state,stamp)
    team_names=sorted({e["Visitante"] for e in events}|{e["Local"] for e in events})
    for team in team_names:
        write_calendar(teams/f"{slugify(team)}.ics",f"NBA 2026-27 — {team}",[e for e in events if team in (e["Visitante"],e["Local"])],state,stamp)
    return {"events":len(events),"teams":len(team_names),"cup":sum(bool(e.get("Es_NBA_Cup")) for e in events),"special":sum(bool(e.get("Es_Partido_Especial")) for e in events)}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--master",default="data/master_snapshot.json"); ap.add_argument("--state",default="data/published_state.json"); ap.add_argument("--docs",default="docs")
    a=ap.parse_args(); print(build_all(a.master,a.state,a.docs))
if __name__=="__main__": main()
