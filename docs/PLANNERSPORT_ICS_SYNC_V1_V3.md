# PlannerSport — Validación de sincronización ICS V1–V3

Fecha del cierre: 17 de octubre de 2026.

Repositorio: `jheo62/Master-calendar`.
Referencia publicada al cierre: `4dfc3763de8051704c529f54b2f859abab5a4bc5`.

## A. Objetivo

Validar la distribución y recepción automática de cambios de un mismo evento ICS mediante suscripciones existentes en Apple Calendar y Google Calendar, conservando la URL y el UID. El ensayo utiliza un único evento ficticio, sin datos deportivos ni nombres de equipos.

Este cierre documenta exclusivamente el ensayo PlannerSport V1–V3. No sustituye ni modifica los cierres históricos de otros calendarios de laboratorio.

## B. Infraestructura y procedencia de la evidencia

- Hosting: GitHub Pages, rama `main`, carpeta `/docs`, HTTPS.
- Ruta estable: `docs/test/plannersport-refresh-v1.ics`.
- URL estable de suscripción: https://jheo62.github.io/Master-calendar/test/plannersport-refresh-v1.ics
- Clientes: Apple Calendar y Google Calendar.
- Apple Calendar mantuvo activa la suscripción, con actualización automática configurada cada 5 minutos. Esta configuración no acredita un plazo garantizado de recepción.

Las publicaciones controladas de V1, V2 y V3 se verificaron mediante lectura del SHA de main remoto, finalización de Pages y comparación byte por byte y SHA-256 entre el ICS público y el archivo local aprobado. La recepción en los clientes, la ausencia de intervención manual y las observaciones del correo de Google fueron confirmadas por el usuario en el cierre; no se atribuyen a inspección automatizada del agente ni se presentan capturas o correos como archivos adjuntos a este documento.

## C. Historial de versiones

Fecha del evento ficticio: **20 de octubre de 2026**. La hora de Chile indicada corresponde a Santiago, UTC−03:00 para esa fecha. Los archivos expresan las fechas en UTC mediante el sufijo `Z`.

| Versión | Commit publicado | SEQUENCE | Horario UTC | Horario Chile (Santiago) | SUMMARY |
|---|---|---:|---|---|---|
| V1 | `c65392c061a6edba7113a98ec8ace6f5704c6dfd` | 0 | 18:00–18:30 | 15:00–15:30 | PlannerSport - Prueba de sincronizacion V1 |
| V2 | `2db3e094810d1d132ca5ec54c9d4a4bd22351227` | 1 | 19:00–19:30 | 16:00–16:30 | PlannerSport - Actualizacion recibida V2 |
| V3 | `4dfc3763de8051704c529f54b2f859abab5a4bc5` | 2 | 20:00–20:30 | 17:00–17:30 | PlannerSport - Actualizacion recibida V3 |

En cada transición se modificaron exclusivamente `SEQUENCE`, `SUMMARY`, `DTSTART`, `DTEND` y `DTSTAMP`. Se mantuvieron la ruta, la URL, el UID y un único VEVENT. Los calendarios conservaron UTF-8, CRLF, VCALENDAR y VERSION:2.0.

| Versión | DTSTAMP UTC | SHA-256 del ICS publicado |
|---|---|---|
| V1 | `20261017T110748Z` | `8a20ef0bb2597400262e836022786975973d274567cc71f0888a6ff89b191a50` |
| V2 | `20261017T112211Z` | `4454fb4c5bcd5233e2845199cce1b57f70be0fb70cb48fc19650a913a818fbe4` |
| V3 | `20261017T114204Z` | `7b53ce73715c47913499e4030852724dacfb733c67184b42c29fbe99af4c81a3` |

DTSTAMP identifica la preparación de cada versión; no es una medición del instante en que un cliente recibió el cambio.

## D. Identidad persistente

UID conservado exactamente en V1, V2 y V3:

`plannersport-apple-refresh-20261020-v1@plannersport.test`

La denominación `v1` dentro del UID forma parte de la identidad estable y no se cambió al preparar V2 o V3. Las versiones posteriores actualizaron el mismo evento en la misma URL.

## E. Resultado Apple Calendar

**PASS.** El usuario confirmó recepción automática V1→V2 y V2→V3 con la suscripción activa, sin intervención manual para recibir las actualizaciones. Se recibieron los cambios de título y horario; no se observaron eventos duplicados.

El intervalo de 5 minutos corresponde a la configuración elegida en Apple Calendar, no a una garantía de frecuencia efectiva ni de latencia de extremo a extremo.

## F. Resultado Google Calendar

**PASS.** La suscripción inicial se realizó cuando V2 ya estaba publicada. El usuario confirmó la actualización automática V2→V3. Este ensayo no acredita una transición V1→V2 observada en Google Calendar.

Evidencia comunicada por el usuario del **17 de octubre de 2026**, hora de Chile (Santiago, UTC−03:00):

| Hora | Observación |
|---|---|
| 08:52 | Google Calendar mostraba V2. |
| 10:12 | Un correo de Google notificó la modificación e identificó cambios de título y horario. |
| 10:23 | Google Calendar mostraba V3. |

Estos tiempos son observaciones de esta prueba. No permiten determinar el instante exacto de consulta del feed, no establecen una frecuencia garantizada de Google Calendar ni un plazo general de sincronización. La hora del correo tampoco sustituye la observación del evento actualizado en Calendar.

## G. Integridad

Los 33 feeds oficiales NBA permanecieron intactos durante las publicaciones controladas de prueba. Se verificaron los archivos locales frente a la base y los 33 ICS públicos frente a los bytes locales, sin diferencias.

Los commits V1, V2 y V3 afectaron exclusivamente `docs/test/plannersport-refresh-v1.ics`: V1 lo incorporó; V2 y V3 modificaron cinco propiedades del mismo archivo. No cambiaron datos deportivos, página web ni workflows. Main local conservó su HEAD, archivos, índice y cambios preexistentes.

El cierre documental se prepara en una rama y un worktree separados, mediante un único documento y un commit local. No publica cambios ni modifica las evidencias históricas.

## H. Limitaciones

- Prueba realizada con un único evento ficticio; no acredita el comportamiento de todos los clientes, versiones, dispositivos o volúmenes de eventos.
- No valida actualizaciones automáticas de datos NBA ni su vigencia, fuentes, guards, generación o aprobación.
- No garantiza intervalos de sincronización ni recepción inmediata.
- Android todavía no ha sido probado.
- No se ensayaron cancelaciones, eliminación de eventos ni incorporación de nuevos partidos.
- Publish Live permanece bloqueado. Este ensayo no habilita una vía de publicación ni reemplaza guards, L4, revisión humana o autorización del candidato exacto.

## I. Conclusión

**PASS para distribución y recepción automática de cambios ICS en Apple Calendar y Google Calendar**, dentro del alcance y evidencia descritos: Apple V1→V2 y V2→V3; Google V2→V3.

**NO-GO para habilitar automáticamente Publish Live basándose únicamente en esta prueba.** La recepción correcta de cambios por los clientes no demuestra seguridad ni autorización del ciclo de actualización y publicación de datos deportivos.
