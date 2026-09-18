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

