# NBA Master Calendar 2026-27 — Project State

## Estado general

Proyecto: NBA Master Calendar 2026-27
Repositorio: Master-calendar
Rama principal: main

Objetivo:
Mantener un calendario NBA 2026-27 confiable y actualizable mediante una cadena controlada:

NBA oficial
→ extracción
→ normalización
→ comparación
→ controles de seguridad
→ Promotion Gate
→ actualización del master
→ regeneración selectiva de feeds ICS
→ GitHub Pages
→ Apple Calendar

## Datos de temporada

- Partidos actualmente definidos: 1200
- Equipos NBA: 30
- Partidos definidos por equipo: 80
- Partidos pendientes dependientes de NBA Cup: 30
- Total final esperado de temporada regular: 1230

Los 30 partidos pendientes NO deben inventarse.
Solo pueden incorporarse cuando exista información oficial NBA.

## Componentes completados

- Base Maestra 2026-27
- Auditoría final de Base Maestra
- Conversión horaria UTC / arena / Santiago / Magallanes
- Clasificación NBA Cup
- Eventos especiales
- Carga de calendario y back-to-backs
- Generador ICS
- Calendario completo
- Calendario NBA Cup
- Calendario eventos especiales
- 30 calendarios por equipo
- UIDs estables
- Alarmas
- GitHub Pages
- Feed de suscripción
- Prueba de actualización en Apple Calendar
- Motor de actualización
- SEQUENCE y LAST-MODIFIED
- Idempotencia del motor
- Regeneración selectiva de feeds
- Workflow de validación
- Workflow de publicación protegida
- Ingestion Guard
- Source Contract
- Candidate Builder
- Extracción desde fuente oficial NBA
- Matching oficial NBA ↔ Master 1200/1200
- NBA game identity map
- Source Adapter
- Arena Registry
- Detailed Change Report
- Change Decision
- Arena Geography Guard
- Temporal Guard
- Promotion Gate
- Sandbox E2E aislado

## Principios de seguridad

1. No inventar datos NBA.
2. No crear los 30 partidos Cup TBD hasta confirmación oficial.
3. gameId NBA es el puente de identidad oficial.
4. Mantener ID_Partido y UID estables.
5. Un partido ausente nunca se cancela automáticamente.
6. Diferencias entre copias oficiales deben bloquear la ingesta.
7. Arena desconocida no debe generar geografía inventada.
8. Arena vacía no debe borrar datos válidos existentes.
9. Toda escritura de producción debe ocurrir después del Promotion Gate.
10. AUTO_ELIGIBLE permite continuar.
11. REVIEW_REQUIRED requiere revisión.
12. BLOCKED detiene el proceso.
13. Las pruebas deben ejecutarse primero en sandbox.
14. Un segundo apply del mismo candidato debe ser un no-op.

## Estado E2E actual

Última fase aprobada:

FASE 3.7.10K.30

Resultado:

- added: 0
- modified: 0
- unchanged: 1200
- missing: 0
- applied: false

IDEMPOTENCIA LOGICA: APROBADA 1200/1200
SEGUNDO APPLY: NO-OP CONFIRMADO

El sandbox demostró:

candidato +30 min
→ detailed report
→ change decision
→ arena guard
→ temporal guard
→ promotion gate
→ apply
→ regeneración de feeds
→ validación
→ segundo apply
→ no-op

Producción permaneció intacta.

## Próximo paso

FASE 3.7.10K.31

Objetivo:
Auditoría semántica del evento NBA2627-0001 después del apply en sandbox.

Debe comprobar:

- UID estable
- DTSTART actualizado +30 minutos
- DTEND coherente
- SEQUENCE incrementado correctamente
- alarmas conservadas
- ausencia de duplicados
- feeds afectados correctos
- producción intacta

## Política de trabajo

Las capturas de pantalla dejan de ser obligatorias.

Resultados normales:
copiar y pegar únicamente el resumen de Terminal.

Usar capturas solo para:
- errores visuales
- GitHub Actions cuando sea necesario
- Apple Calendar
- interfaces gráficas
- resultados imposibles de representar correctamente como texto

Estados estándar:

PASS
REVIEW
BLOCKED


## Último hito validado — K.31

FASE 3.7.10K.31: APROBADA.

Se certificó de extremo a extremo, en aislamiento, el camino de un cambio AUTO_ELIGIBLE:
guards -> promotion gate -> apply -> feeds -> master promotion -> post-publish -> idempotencia.

Producción no fue modificada.

Estado al cierre:
- branch: main
- local/remote sincronizados
- rama de laboratorio eliminada
- sandbox eliminado

Próxima fase: K.32.

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

## FASE 3.7.10K.33 — CLOSED / PASS

Publicación manual NBA Live integrada, publicada y validada de extremo a extremo en producción.

Resultados:
- Nuevo workflow NBA Calendar Publish Live incorporado a GitHub Actions.
- Ejecución exclusivamente manual mediante workflow_dispatch.
- Autorización humana obligatoria mediante confirm_publish = PUBLICAR.
- Publicación restringida a branch main.
- contents: write y concurrency compartida nba-calendar-publish.
- Checkout endurecido con fetch-depth: 0.
- Pipeline Live: fuente oficial NBA -> extracción -> adaptación -> contrato -> Ingestion Guard -> State Safety Gate -> Change Decision -> Arena Geography Guard -> Temporal Guard -> Promotion Gate -> autorización humana -> update engine -> regeneración selectiva -> validación -> master/state -> commit/push.
- No existe publicación automática programada en este workflow.
- No se utiliza --cancel-missing; eventos ausentes continúan bloqueando publicación automática.
- Commit de incorporación del workflow: a102d2075caa1c7e1d490e80a15bbaf8d7a434a4.
- Primera publicación NBA Live real ejecutada correctamente en GitHub Actions.
- Commit de publicación real: b2edae1fdc153035b6e27ef60748b012e273ff0c.
- Cambios publicados: 0 added / 3 modified / 0 missing.
- IDs modificados: NBA2627-0027, NBA2627-0864 y NBA2627-0873.
- Delta semántico exacto: 6 campos.
- Arena: Frost Bank Center -> Moody Center en los 3 partidos.
- Ciudad: San Antonio -> Austin en los 3 partidos.
- UID estable conservado para los 3 eventos.
- SEQUENCE incrementado de 0 a 1 para los 3 eventos.
- STATUS permanece ACTIVE.
- Regeneración selectiva confirmada: calendario completo y feeds Denver Nuggets, Houston Rockets, Memphis Grizzlies y San Antonio Spurs.
- Sólo 7 archivos fueron modificados por la primera publicación: master, state y 5 feeds.
- Validación completa de feeds: OK.
- Calendario completo: 1200 eventos / 1200 UID únicos.
- Cada calendario de equipo: 80 eventos / 80 UID únicos.
- Estado post-publicación: 0 added / 0 modified / 1200 unchanged / 0 missing.
- Segunda ejecución real NBA Calendar Publish Live completada correctamente sin cambios en la fuente.
- Segunda ejecución no generó nuevo commit.
- SEQUENCE de los 3 eventos permaneció en 1.
- Segunda ejecución confirmó idempotencia real en producción.
- Detección automática y publicación manual permanecen separadas.
- main y origin/main sincronizados al cierre operativo de K.33.

LAST_APPROVED_PHASE: 3.7.10K.33
NEXT_PHASE: 3.7.10K.34
