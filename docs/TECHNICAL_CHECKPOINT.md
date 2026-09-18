# NBA Calendar — Technical Checkpoint

CURRENT_PHASE: 3.7.10K.31
LAST_APPROVED_PHASE: 3.7.10K.30

SEASON: 2026-27

MASTER_DEFINED_EVENTS: 1200
NBA_TEAMS: 30
DEFINED_EVENTS_PER_TEAM: 80
NBA_CUP_PENDING_EVENTS: 30
EXPECTED_FINAL_REGULAR_SEASON_EVENTS: 1230

SOURCE: Official NBA web schedule sources

IDENTITY_BRIDGE:
NBA gameId -> nba_game_identity_map -> ID_Partido -> stable ICS UID

MASTER_FILE:
data/master_snapshot.json

PUBLISHED_STATE:
data/published_state.json

ARENA_REGISTRY:
data/reference/arena_registry.json

CHANGE_POLICY:
data/reference/change_decision_policy.json

PRODUCTION_FEEDS:
docs/calendars

CORE_TOOLS:
tools/update_engine.py
tools/detailed_change_report.py
tools/change_decision.py
tools/arena_geography_guard.py
tools/temporal_guard.py
tools/promotion_gate.py
tools/validate_feeds.py

E2E_SANDBOX: PASS
PROMOTION_GATE: PASS
FAIL_CLOSED: PASS
WRITE_BARRIER: PASS
IDEMPOTENCE: PASS
PRODUCTION_MODIFIED: NO

LAST_IDEMPOTENCE_RESULT:
added=0
modified=0
unchanged=1200
missing=0
applied=false

TEST_EVENT:
ID_Partido=NBA2627-0001
change=Fecha_Hora_UTC +30 minutes

NEXT_STEP:
Controlled test of the valid-change path without altering real NBA production data.

EXPECTED_K22:
UID stable
DTSTART +30m
DTEND coherent
SEQUENCE incremented
3 alarms preserved
0 duplicate UID
affected feeds correct
production unchanged

CRITICAL_RULE:
Never fabricate the 30 NBA Cup dependent TBD games.

PUBLICATION_RULE:
No production write before Promotion Gate approval.

MISSING_EVENT_RULE:
Missing source event must never automatically cancel a published game.

STATUS_VALUES:
PASS
REVIEW
BLOCKED


## FASE 3.7.10K.31 — CLOSED / PASS

Prueba controlada completa del camino AUTO_ELIGIBLE.

Resultados:
- Rama temporal de laboratorio creada desde main y posteriormente eliminada.
- Sandbox aislado: /tmp/nba-k31.
- Producción permaneció intacta durante todo el ensayo.
- Cambio controlado: NBA2627-0001, +30 minutos.
- Change Decision: AUTO_ELIGIBLE.
- Arena Geography Guard: AUTO_ELIGIBLE.
- Temporal Guard: AUTO_ELIGIBLE.
- Promotion Gate: AUTO_ELIGIBLE.
- Apply sandbox: 0 added / 1 modified / 1199 unchanged / 0 missing.
- Feeds regenerados y validados correctamente.
- Master sandbox promovido correctamente.
- UID estable.
- SEQUENCE incrementado a 1.
- Estado post-publicación: 0 added / 0 modified / 1200 unchanged / 0 missing.
- Segundo apply: NO-OP.
- State no reescrito en segundo apply.
- Feeds no reescritos en segundo apply.
- Rama lab eliminada.
- Sandbox eliminado.
- main sincronizada con origin/main.

LAST_APPROVED_PHASE: 3.7.10K.31
NEXT_PHASE: 3.7.10K.32

## FASE 3.7.10K.32 — CLOSED / PASS

Observación automática de la fuente oficial NBA integrada y validada en entorno real.

Resultados:
- Workflow NBA Calendar Update ejecutado correctamente en GitHub Actions.
- Fuente oficial NBA descargada para 30 equipos.
- Extracción validada: 2400 apariciones / 1200 partidos únicos.
- Cada gameId regular aparece exactamente 2 veces.
- Identity map mantiene correspondencia con los 1200 partidos del Master.
- Ingestion Guard: 0 added / 3 modified / 0 missing.
- Cambios reales detectados: NBA2627-0027, NBA2627-0864 y NBA2627-0873.
- Los 3 cambios corresponden a Moody Center, Austin.
- Change Decision: AUTO_ELIGIBLE.
- Arena Geography Guard: 3 checked / 0 blocked / AUTO_ELIGIBLE.
- Temporal Guard: AUTO_ELIGIBLE, 0 cambios temporales.
- Promotion Gate: AUTO_ELIGIBLE.
- PUBLICACION AUTOMATICA: NO.
- Workflow de observación permanece READ_ONLY.
- Producción no fue modificada por K.32.
- Esquema canónico normalizado a "País".
- arena_registry.json conserva "Pais" como clave de frontera externa.
- source_adapter.py traduce Registry "Pais" -> Candidate "País".
- arena_geography_guard.py usa mapeo explícito Candidate "País" <-> Registry "Pais".
- source_contract.py quedó alineado con el Candidate canónico usando "País".
- Commit operativo validado: f28d7518fcf21492a9a4ff688a91cf5934fd0e4a.
- GitHub Actions validó el commit f28d751 en main.
- Los 3 cambios Moody Center permanecen detectados; no fueron publicados automáticamente.

LAST_APPROVED_PHASE: 3.7.10K.32
NEXT_PHASE: 3.7.10K.33
