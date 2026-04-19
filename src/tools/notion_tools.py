"""Herramientas para interactuar con Notion."""
from __future__ import annotations
from src.config import NOTION_API_KEY, NOTION_PROPIEDADES_DB_ID, NOTION_TAREAS_DB_ID


def _get_client():
    from notion_client import Client
    return Client(auth=NOTION_API_KEY)


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_NOTION: list[dict] = [
    {
        "name": "notion_listar_propiedades",
        "description": (
            "Lista las propiedades registradas en la base de datos de Notion. "
            "Útil para obtener fichas técnicas detalladas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado de la propiedad",
                    "enum": ["Disponible", "Reservada", "Vendida", "Rentada"],
                },
                "limite": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "notion_crear_tarea",
        "description": "Crea una tarea o recordatorio en la base de datos de tareas de Notion.",
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Título de la tarea"},
                "descripcion": {"type": "string", "description": "Descripción detallada"},
                "responsable": {"type": "string", "description": "Nombre del responsable"},
                "fecha_limite": {
                    "type": "string",
                    "description": "Fecha límite en formato YYYY-MM-DD",
                },
                "prioridad": {
                    "type": "string",
                    "enum": ["Alta", "Media", "Baja"],
                    "default": "Media",
                },
            },
            "required": ["titulo"],
        },
    },
    {
        "name": "notion_buscar_propiedad",
        "description": "Busca una propiedad específica en Notion por nombre o dirección.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto a buscar (nombre, dirección, zona)"},
            },
            "required": ["query"],
        },
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "notion_listar_propiedades": _listar_propiedades,
        "notion_crear_tarea": _crear_tarea,
        "notion_buscar_propiedad": _buscar_propiedad,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _listar_propiedades(estado: str | None = None, limite: int = 10) -> str:
    client = _get_client()
    filtros: dict = {}
    if estado:
        filtros = {
            "filter": {
                "property": "Estado",
                "select": {"equals": estado},
            }
        }
    respuesta = client.databases.query(
        database_id=NOTION_PROPIEDADES_DB_ID,
        page_size=limite,
        **filtros,
    )
    resultados = respuesta.get("results", [])
    if not resultados:
        return "No se encontraron propiedades en Notion con esos criterios."
    lineas = []
    for p in resultados:
        props = p["properties"]
        titulo = _texto_propiedad(props, "Nombre") or _texto_propiedad(props, "Titulo") or "Sin título"
        estado_p = _select_propiedad(props, "Estado") or "—"
        precio = _numero_propiedad(props, "Precio")
        lineas.append(f"• {titulo} | Estado: {estado_p} | Precio: ${precio:,.0f}")
    return f"Propiedades en Notion ({len(lineas)}):\n" + "\n".join(lineas)


def _crear_tarea(
    titulo: str,
    descripcion: str = "",
    responsable: str = "",
    fecha_limite: str | None = None,
    prioridad: str = "Media",
) -> str:
    client = _get_client()
    props: dict = {
        "Titulo": {"title": [{"text": {"content": titulo}}]},
        "Prioridad": {"select": {"name": prioridad}},
        "Estado": {"select": {"name": "Pendiente"}},
    }
    if descripcion:
        props["Descripcion"] = {"rich_text": [{"text": {"content": descripcion}}]}
    if responsable:
        props["Responsable"] = {"rich_text": [{"text": {"content": responsable}}]}
    if fecha_limite:
        props["FechaLimite"] = {"date": {"start": fecha_limite}}
    client.pages.create(
        parent={"database_id": NOTION_TAREAS_DB_ID},
        properties=props,
    )
    return f"Tarea '{titulo}' creada en Notion con prioridad {prioridad}."


def _buscar_propiedad(query: str) -> str:
    client = _get_client()
    respuesta = client.search(
        query=query,
        filter={"value": "page", "property": "object"},
    )
    resultados = respuesta.get("results", [])[:5]
    if not resultados:
        return f"No se encontraron resultados para '{query}' en Notion."
    lineas = [f"Resultados para '{query}':"]
    for p in resultados:
        titulo = "Sin título"
        if p.get("properties"):
            for key in ("Nombre", "Titulo", "Name", "Title"):
                val = _texto_propiedad(p["properties"], key)
                if val:
                    titulo = val
                    break
        lineas.append(f"• {titulo} — ID: {p['id']}")
    return "\n".join(lineas)


# ── Helpers ───────────────────────────────────────────────────────

def _texto_propiedad(props: dict, nombre: str) -> str:
    prop = props.get(nombre, {})
    items = prop.get("title") or prop.get("rich_text") or []
    return "".join(i.get("plain_text", "") for i in items)


def _select_propiedad(props: dict, nombre: str) -> str:
    return (props.get(nombre, {}).get("select") or {}).get("name", "")


def _numero_propiedad(props: dict, nombre: str) -> float:
    return props.get(nombre, {}).get("number") or 0.0
