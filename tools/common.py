#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

UTC = timezone.utc
SIGNIFICANT_FIELDS = [
    "Fecha_Hora_UTC", "Visitante", "Local", "Arena", "Ciudad", "Estado_Provincia", "País",
    "Fase", "TV_Normalizada", "Streaming_Normalizado", "Grupo_NBA_Cup", "Evento_Especial",
    "Estado", "Es_NBA_Cup", "Es_Partido_Especial", "Zona_Horaria_Arena", "URL_NBA"
]

def load_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save_json(path: str | Path, obj):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def canonical_event(event: dict) -> dict:
    return {k: event.get(k) for k in SIGNIFICANT_FIELDS}

def fingerprint(event: dict) -> str:
    raw = json.dumps(canonical_event(event), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def parse_utc(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC)

def fmt_ics_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")

def fmt_local(dt: datetime, zone: str) -> str:
    z = ZoneInfo(zone)
    return dt.astimezone(z).strftime("%d-%m-%Y %H:%M")

def slugify(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

def uid_for(event_id: str) -> str:
    return f"{event_id}@nba-master-calendar.local"

def status_for(event: dict) -> str:
    s = str(event.get("Estado") or "").strip().lower()
    if "cancel" in s:
        return "CANCELLED"
    return "CONFIRMED"
