# Equipo de Agentes IA — Futura Bienes Raíces

> **IMPORTANTE para Claude Code:** Lee `CLAUDE_MEMORY.md` al inicio de cada sesión.
> Contiene el estado actual del proyecto, reglas críticas y contexto del usuario.

Sistema multi-agente construido con Claude para automatizar operaciones del negocio inmobiliario.

## Arquitectura

```
main.py                         ← Punto de entrada CLI
src/
  config.py                     ← Variables de entorno y configuración
  agents/
    base.py                     ← Clase base con loop de tool-use de Claude
    orchestrator.py             ← Enruta tareas al agente correcto
    lead_manager.py             ← Gestión de prospectos (Airtable + Notion)
    content_creator.py          ← Marketing y redes sociales
    reports_agent.py            ← Reportes y análisis
    client_service.py           ← Atención al cliente
  tools/
    airtable_tools.py           ← CRUD de leads y propiedades en Airtable
    notion_tools.py             ← Propiedades y tareas en Notion
    drive_tools.py              ← Archivos y documentos en Google Drive
    social_media_tools.py       ← Publicaciones en Facebook e Instagram
```

## Modelos usados

- **Orquestador (enrutamiento)**: `claude-haiku-4-5-20251001` — rápido y económico
- **Agentes especializados**: `claude-sonnet-4-6` — balance calidad/costo

## Setup

```bash
# 1. Clonar e instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys

# 3. Ejecutar
python main.py                          # Modo interactivo
python main.py "dame el reporte de leads de hoy"
python main.py --agente contenido "crea un post para esta casa de 3 recámaras en Polanco"
```

## Arquitectura de dos capas

### Agentes Generales (cualquier negocio)
| Agente | Descripción | Herramientas |
|--------|------------|--------------|
| `investigador` | Investiga mercados, apps, tendencias globales | Búsqueda web, Drive |
| `estratega` | Desarrolla y valida ideas de negocio, planes | Búsqueda web, Drive |
| `desarrollador` | Programa webs, apps, APIs, automatizaciones | Archivos, Búsqueda, Drive |
| `marketing` | Estrategia y contenido para cualquier negocio | Búsqueda, Meta API, Drive |
| `analista` | Reportes, KPIs, análisis financiero | Airtable, Notion, Drive |
| `trader` | Análisis de mercados, estrategias de trading | Búsqueda, APIs de mercado |

### Agentes Especializados — Inmobiliaria
| Agente | Descripción | Herramientas |
|--------|------------|--------------|
| `inmobiliaria_leads` | CRM de clientes/prospectos | Airtable, Notion |
| `inmobiliaria_contenido` | Posts y marketing de propiedades | Airtable, Meta API, Drive |
| `inmobiliaria_clientes` | Atención al cliente | Airtable, Notion |

## Variables de entorno requeridas

```
ANTHROPIC_API_KEY      # API key de Anthropic (obligatoria)
TAVILY_API_KEY         # Búsqueda web para el Agente Investigador (tavily.com)
AIRTABLE_API_KEY       # Personal Access Token de Airtable
AIRTABLE_BASE_ID       # ID de la base (appXXXX)
NOTION_API_KEY         # Integration token de Notion
NOTION_PROPIEDADES_DB_ID  # ID de la DB de propiedades
NOTION_TAREAS_DB_ID    # ID de la DB de tareas
META_ACCESS_TOKEN      # Token de la App de Meta
META_PAGE_ID           # ID de la página de Facebook
META_IG_ACCOUNT_ID     # ID de la cuenta de Instagram
GOOGLE_CREDENTIALS_FILE   # Ruta al JSON de credenciales OAuth2
GOOGLE_DRIVE_FOLDER_ID    # ID de la carpeta en Drive
```

## Ejemplos de uso

```bash
# Leads
python main.py "muéstrame todos los leads nuevos de esta semana"
python main.py "registra nuevo lead: Juan Pérez, tel 5512345678, busca casa en CDMX hasta 3MDP"
python main.py --agente leads "actualiza el lead recXXXX a estado Calificado"

# Contenido
python main.py "crea un post de Instagram para una casa de 4 recámaras en Lomas de Chapultepec, precio $8.5MDP"
python main.py --agente contenido "publica en Facebook: anuncio de nueva propiedad en Polanco"

# Reportes
python main.py "dame el reporte semanal del negocio"
python main.py --agente reportes "¿cuántos leads tenemos por origen este mes?"

# Clientes
python main.py "un cliente busca departamento de 2 recámaras en renta en la Narvarte, ¿qué tenemos?"
```

## Cómo agregar un nuevo agente

1. Crear `src/agents/mi_agente.py` heredando de `AgenteBase`
2. Definir `INSTRUCCIONES` y `HERRAMIENTAS`
3. Implementar `ejecutar_herramienta()`
4. Registrar en `orchestrator.py` dentro de `self._agentes`
5. Agregar la descripción de enrutamiento en `INSTRUCCIONES_ROUTER`

## Cómo agregar una nueva herramienta

1. Crear o editar en `src/tools/`
2. Definir la herramienta en `TOOLS_*` siguiendo el schema JSON de Claude
3. Implementar la función ejecutora
4. Agregar `ejecutar_herramienta()` al dispatcher
5. Importar y agregar `TOOLS_*` en los agentes que la usarán
