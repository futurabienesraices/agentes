# Memoria Persistente — Claude Code

Este archivo es la memoria de largo plazo de Claude Code para este proyecto.
Se actualiza conforme avanzamos y se lee al inicio de cada sesión.

## Usuario y contexto

- **Nombre:** Ever Quiñonez
- **Máquina:** iMac (`everquinonezmorales@iMac-de-Ever`)
- **Directorio del proyecto:** `~/Documents/agentes`
- **Python venv:** `.venv` (activar con `source .venv/bin/activate`)
- **Rama activa:** `claude/setup-business-environment-Ipc5k`

## Negocios

| Negocio | Tipo | Tel/WA |
|---------|------|--------|
| Futura Bienes Raíces | Inmobiliaria, Santa Ana, El Salvador | 6027-2418 |
| Futura Cleaning | Limpieza profunda de muebles a domicilio | 6027-2418 |

## Reglas críticas para Claude Code

1. **SIEMPRE incluir `cd ~/Documents/agentes &&` antes de cualquier comando git**
   - Correcto: `cd ~/Documents/agentes && git pull origin claude/setup-business-environment-Ipc5k`
   - Incorrecto: `git pull origin ...` (el usuario está en `~` por defecto)

2. **Rama de desarrollo:** `claude/setup-business-environment-Ipc5k` — no tocar `main`

3. **Videos del iPhone** son HEVC/H.265 + Dolby Vision — `_transcodar_si_hevc()` los convierte automáticamente en `_video_crear_profesional`

4. **Nunca re-analizar videos ya indexados** — `media_indexados` primero, `video_analizar` solo para videos nuevos

## Estado actual del sistema (2026-04-22)

### Implementado y funcionando
- ✅ 12 agentes: investigador, estratega, desarrollador, marketing, analista, trader, media, leads, contenido, clientes, **analista_propiedades** + orquestador
- ✅ Memoria persistente: sesiones, errores, aprendizajes, notas curadas, patrones estructurados
- ✅ `src/patron_db.py` — prohibiciones y reglas aprendidas, se inyectan en todos los prompts
- ✅ `src/cache.py` — caché de herramientas (video_analizar: 24h, web_buscar: 6h, etc.)
- ✅ `src/video_db.py` — índice permanente de videos, keyed por MD5(64KB)+size
- ✅ `src/tools/media_tools.py` — MoviePy + edge-tts + subtítulos + HEVC auto-transcode
- ✅ `src/tools/design_tools.py` — Generador de flyers PNG (1080×1350) y carousels (1080×1080) con Pillow
- ✅ `AgenteAnalistaPropiedades` — lee Airtable, analiza propiedad y genera flyer+carousel+copies automáticamente
- ✅ `AgenteContenido` — ahora tiene acceso a design_flyer y design_carousel
- ✅ Pipeline `analisis-propiedad`: Investigador → AnalistaPropiedades (tendencias + flyer completo)
- ✅ `app.py` + `templates/index.html` — interfaz web tipo WhatsApp (Flask, puerto 5000)
- ✅ `scheduler.py` — publicaciones diarias automáticas (08:00)
- ✅ `reporte_diario.py` — reporte de tendencias + plan de contenido
- ✅ `memoria_cli.py` — gestión completa de memoria y patrones desde terminal

### Pendiente / En progreso
- ⏳ Lead generation via Facebook Lead Ads API (sin implementar)
- ⏳ WhatsApp Business auto-respuestas (sin implementar)
- ⏳ Remotion para videos más profesionales (evaluando, requiere Node.js)
- ⏳ Probar `app.py` en producción (Ever aún no lo ha probado)

## Arquitectura de archivos importantes

```
app.py                    ← Interfaz web Flask
main.py                   ← CLI original
scheduler.py              ← Publicaciones automáticas diarias
reporte_diario.py         ← Reporte + auto-publicación
memoria_cli.py            ← Gestión de memoria desde terminal
src/
  patron_db.py            ← Patrones aprendidos
  cache.py                ← Caché de herramientas
  video_db.py             ← Índice permanente de videos
  config.py               ← Variables de entorno
  agents/
    orchestrator.py       ← Enrutador + pipelines (incl. analisis-propiedad)
    analista_propiedades.py ← NUEVO: analiza propiedad → flyer + carousel + copies
    media.py              ← Editor profesional de video
    base.py               ← Loop de tool-use + memoria
    content_creator.py    ← Contenido + redes + design_tools
  tools/
    media_tools.py        ← Video/audio/ebook tools
    design_tools.py       ← NUEVO conectado: flyer y carousel con Pillow
    social_media_tools.py ← Facebook/Instagram API
    drive_tools.py        ← Google Drive
    airtable_tools.py     ← CRM
    notion_tools.py       ← Propiedades y tareas
memoria/
  patrones.json           ← Prohibiciones y reglas aprendidas
  historial/              ← Historial de chats por agente (app.py)
  [agente]_notas.json     ← Notas curadas por el usuario
  [agente]_sesiones.json  ← Sesiones automáticas
media/
  input/                  ← Videos/imágenes originales
  output/
    futura_cleaning/reels/
    futura_cleaning/facebook/
    futura_bienes_raices/reels/
    futura_bienes_raices/facebook/
    futura_bienes_raices/flyers/    ← NUEVO: flyers PNG generados
    futura_bienes_raices/carousel/  ← NUEVO: slides de carousel
  video_index.json        ← Índice permanente de videos analizados
```

## Lo que Ever quiere lograr

1. **Automatización diaria** de redes sociales (contenido + publicación)
2. **Lead generation** automático para propiedades en venta
3. **Videos profesionales** tipo TikTok/Instagram Reels para ambos negocios
4. **Interfaz visual** (web/WhatsApp) para dar órdenes a los agentes
5. **Equipo que mejore solo** con el tiempo, sin repetir errores

## Historial de problemas resueltos

| Problema | Solución |
|----------|----------|
| HEVC iPhone no procesa MoviePy | `_transcodar_si_hevc()` convierte a H.264 automáticamente |
| Agent re-analiza videos (gasta tokens) | video_db índice permanente + cache 24h |
| FFmpeg se colgaba en videos grandes | `timeout=120` en `_ffmpeg()` |
| MP4 cortado no se podía abrir | `-c copy` → `libx264 + AAC + faststart` |
| Duplicados en output/ | `_subcarpeta_por_nombre()` + limpiar elimina duplicado de raíz |
| git pull sin estar en el directorio | Siempre `cd ~/Documents/agentes &&` antes |
