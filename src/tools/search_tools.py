"""Herramientas de búsqueda web para el agente investigador."""
from __future__ import annotations
import httpx
import os

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")


TOOLS_SEARCH: list[dict] = [
    {
        "name": "web_buscar",
        "description": (
            "Busca en internet información sobre apps, plataformas o tendencias "
            "de bienes raíces en cualquier país. Devuelve resultados con título, "
            "URL y resumen de cada resultado."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Términos de búsqueda, ej: 'real estate search app Spain features'",
                },
                "pais": {
                    "type": "string",
                    "description": "País de enfoque opcional, ej: Spain, USA, Colombia",
                },
                "limite": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_obtener_pagina",
        "description": (
            "Descarga y extrae el contenido de texto de una URL. "
            "Útil para leer en detalle las características de una app o plataforma."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL a leer"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "web_generar_codigo",
        "description": (
            "Genera el código fuente completo de una página web o componente "
            "basado en una descripción de funcionalidades. "
            "Devuelve HTML/CSS/JS listo para usar o componente React/Next.js."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "descripcion": {
                    "type": "string",
                    "description": "Descripción detallada de lo que debe hacer la página o app",
                },
                "tecnologia": {
                    "type": "string",
                    "description": "Tecnología a usar",
                    "enum": ["html-css-js", "react", "nextjs"],
                    "default": "html-css-js",
                },
                "nombre_archivo": {
                    "type": "string",
                    "description": "Nombre del archivo a generar, ej: buscador.html, PropertyCard.jsx",
                },
            },
            "required": ["descripcion", "nombre_archivo"],
        },
    },
]


def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "web_buscar": _buscar,
        "web_obtener_pagina": _obtener_pagina,
        "web_generar_codigo": _generar_codigo,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _buscar(query: str, pais: str = "", limite: int = 5) -> str:
    q = f"{query} {pais} site:.com OR site:.io OR site:.app" if pais else query

    # Intentar Tavily primero (diseñado para agentes IA)
    if TAVILY_API_KEY:
        return _buscar_tavily(q, limite)

    # Fallback: Brave Search
    if BRAVE_API_KEY:
        return _buscar_brave(q, limite)

    return (
        "No hay API de búsqueda configurada. "
        "Agrega TAVILY_API_KEY o BRAVE_API_KEY en tu .env. "
        f"Consulta pendiente: {q}"
    )


def _buscar_tavily(query: str, limite: int) -> str:
    resp = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": limite,
            "search_depth": "advanced",
            "include_answer": True,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    lineas = []
    if data.get("answer"):
        lineas.append(f"Resumen: {data['answer']}\n")
    for r in data.get("results", []):
        lineas.append(f"• {r['title']}\n  {r['url']}\n  {r.get('content', '')[:200]}")
    return "\n".join(lineas) if lineas else "Sin resultados."


def _buscar_brave(query: str, limite: int) -> str:
    resp = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": limite},
        headers={"Accept": "application/json", "X-Subscription-Token": BRAVE_API_KEY},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    resultados = data.get("web", {}).get("results", [])
    if not resultados:
        return "Sin resultados."
    lineas = []
    for r in resultados:
        lineas.append(f"• {r['title']}\n  {r['url']}\n  {r.get('description', '')[:200]}")
    return "\n".join(lineas)


def _obtener_pagina(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    resp = httpx.get(url, headers=headers, timeout=20, follow_redirects=True)
    resp.raise_for_status()
    # Extracción básica de texto eliminando HTML
    import re
    texto = re.sub(r"<style[^>]*>.*?</style>", " ", resp.text, flags=re.DOTALL)
    texto = re.sub(r"<script[^>]*>.*?</script>", " ", texto, flags=re.DOTALL)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto[:3000] + ("..." if len(texto) > 3000 else "")


def _generar_codigo(
    descripcion: str, nombre_archivo: str, tecnologia: str = "html-css-js"
) -> str:
    # Esta herramienta es un marcador — el agente Claude genera el código directamente.
    # Devolvemos la instrucción para que el agente la use en su respuesta.
    return (
        f"[GENERAR_CODIGO]\n"
        f"Descripción: {descripcion}\n"
        f"Tecnología: {tecnologia}\n"
        f"Archivo: {nombre_archivo}\n"
        f"Instrucción: Genera el código completo en tu respuesta. "
        f"Devuelve SOLO el código sin explicación adicional."
    )
