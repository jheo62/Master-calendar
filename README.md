# NBA Master Calendar 2026-27 — Fase 3.2

Este repositorio está preparado para un piloto de **GitHub Pages**.

## Publicación recomendada
1. Crea un repositorio en GitHub.
2. Sube **todo el contenido de esta carpeta** conservando la estructura.
3. En `Settings > Pages`, elige `Deploy from a branch`.
4. Selecciona la rama `main` y la carpeta `/docs`.
5. Guarda la configuración.
6. GitHub publicará `docs/index.html` y los `.ics` bajo URLs estables.

Ejemplo, si tu usuario es `USUARIO` y el repositorio se llama `nba-master-calendar`:
`https://USUARIO.github.io/nba-master-calendar/calendars/nba-2026-27-completo.ics`

## Suscripción Apple Calendar en Mac
En Calendar: `Archivo > Nueva suscripción a calendario`, pega la URL HTTPS del `.ics`
y configura la frecuencia de actualización.

## Prueba controlada
El feed `docs/test/nba-test-current.ics` empieza en V1.

Después de suscribir Apple Calendar a esa URL:
```bash
python3 tools/simulate_test_update.py v2
python3 tools/validate_feeds.py
```
Haz commit y push. La URL no cambia, el UID no cambia y `SEQUENCE` aumenta.
La actualización puede no aparecer de inmediato: depende del refresco configurado por Apple Calendar.

Para volver al estado inicial:
```bash
python3 tools/simulate_test_update.py v1
```

## Producción
- `docs/calendars/nba-2026-27-completo.ics`
- `docs/calendars/nba-2026-27-cup-group-play.ics`
- `docs/calendars/nba-2026-27-eventos-especiales.ics`
- `docs/calendars/teams/*.ics`

## Importante
- Estos feeds contienen los 1.200 partidos actualmente definidos.
- Los 30 partidos dependientes de los resultados de NBA Cup siguen pendientes.
- GitHub Pages es un piloto de hosting estático, no el backend final.
- La siguiente evolución será automatizar la comparación Base Maestra → feed y publicar cambios.
