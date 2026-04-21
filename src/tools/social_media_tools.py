"""Herramientas para publicar en redes sociales (Meta: Facebook e Instagram)."""
from __future__ import annotations
import httpx
from src.config import META_ACCESS_TOKEN, META_PAGE_ID, META_IG_ACCOUNT_ID

GRAPH_URL = "https://graph.facebook.com/v21.0"


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_SOCIAL: list[dict] = [
    {
        "name": "social_publicar_facebook",
        "description": (
            "Publica un mensaje en la página de Facebook del negocio. "
            "Ideal para anunciar propiedades, novedades o consejos inmobiliarios."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "mensaje": {"type": "string", "description": "Texto de la publicación"},
                "url_imagen": {
                    "type": "string",
                    "description": "URL pública de la imagen a adjuntar (opcional)",
                },
                "enlace": {
                    "type": "string",
                    "description": "URL de enlace a incluir en la publicación (opcional)",
                },
            },
            "required": ["mensaje"],
        },
    },
    {
        "name": "social_publicar_instagram",
        "description": (
            "Publica una imagen con caption en la cuenta de Instagram del negocio. "
            "Requiere URL pública de imagen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "caption": {"type": "string", "description": "Texto del caption con hashtags"},
                "url_imagen": {
                    "type": "string",
                    "description": "URL pública de la imagen (JPEG, mín 320px)",
                },
            },
            "required": ["caption", "url_imagen"],
        },
    },
    {
        "name": "social_generar_copy",
        "description": (
            "Genera el texto (copy) para una publicación de propiedad en redes sociales. "
            "NO publica, solo devuelve el texto listo para revisar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo_propiedad": {
                    "type": "string",
                    "description": "Casa, Departamento, Terreno, etc.",
                },
                "operacion": {"type": "string", "enum": ["Venta", "Renta"]},
                "precio": {"type": "string", "description": "Precio con formato, ej: $2,500,000"},
                "caracteristicas": {
                    "type": "string",
                    "description": "Recámaras, baños, metros, zona, amenidades, etc.",
                },
                "tono": {
                    "type": "string",
                    "description": "Tono del copy",
                    "enum": ["profesional", "cercano", "urgente", "lujoso"],
                    "default": "profesional",
                },
            },
            "required": ["tipo_propiedad", "operacion", "precio", "caracteristicas"],
        },
    },
    {
        "name": "social_estadisticas_pagina",
        "description": "Obtiene estadísticas básicas de la página de Facebook (fans, alcance, interacciones).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "social_insights_posts_fb",
        "description": (
            "Obtiene las últimas publicaciones de Facebook con métricas de rendimiento "
            "(likes, comentarios, compartidos). Útil para el reporte diario."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de posts a obtener (default 5, máx 10)",
                    "default": 5,
                }
            },
            "required": [],
        },
    },
    {
        "name": "social_insights_posts_ig",
        "description": (
            "Obtiene las últimas publicaciones de Instagram con métricas "
            "(likes, comentarios, tipo de media). Útil para el reporte diario."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de posts a obtener (default 5, máx 10)",
                    "default": 5,
                }
            },
            "required": [],
        },
    },
    {
        "name": "social_insights_cuenta_ig",
        "description": "Obtiene estadísticas de la cuenta de Instagram: seguidores, total de posts, bio.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "social_publicar_facebook": _publicar_facebook,
        "social_publicar_instagram": _publicar_instagram,
        "social_generar_copy": _generar_copy,
        "social_estadisticas_pagina": _estadisticas_pagina,
        "social_insights_posts_fb": _insights_posts_fb,
        "social_insights_posts_ig": _insights_posts_ig,
        "social_insights_cuenta_ig": _insights_cuenta_ig,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _publicar_facebook(
    mensaje: str, url_imagen: str | None = None, enlace: str | None = None
) -> str:
    payload: dict = {
        "message": mensaje,
        "access_token": META_ACCESS_TOKEN,
    }
    if enlace:
        payload["link"] = enlace
    if url_imagen:
        # Publicar con foto
        endpoint = f"{GRAPH_URL}/{META_PAGE_ID}/photos"
        payload["url"] = url_imagen
    else:
        endpoint = f"{GRAPH_URL}/{META_PAGE_ID}/feed"
    resp = httpx.post(endpoint, data=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    post_id = data.get("id") or data.get("post_id", "—")
    return f"Publicado en Facebook. ID del post: {post_id}"


def _publicar_instagram(caption: str, url_imagen: str) -> str:
    # Paso 1: Crear contenedor de media
    resp1 = httpx.post(
        f"{GRAPH_URL}/{META_IG_ACCOUNT_ID}/media",
        data={
            "image_url": url_imagen,
            "caption": caption,
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp1.raise_for_status()
    creation_id = resp1.json()["id"]
    # Paso 2: Publicar el contenedor
    resp2 = httpx.post(
        f"{GRAPH_URL}/{META_IG_ACCOUNT_ID}/media_publish",
        data={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN},
        timeout=30,
    )
    resp2.raise_for_status()
    media_id = resp2.json().get("id", "—")
    return f"Publicado en Instagram. ID del post: {media_id}"


def _generar_copy(
    tipo_propiedad: str,
    operacion: str,
    precio: str,
    caracteristicas: str,
    tono: str = "profesional",
) -> str:
    """Genera copy sin llamar al API — el agente de contenido usará Claude para esto."""
    plantillas = {
        "profesional": (
            f"🏠 {tipo_propiedad} en {operacion}\n\n"
            f"{caracteristicas}\n\n"
            f"Precio: {precio}\n\n"
            f"¿Te interesa? Contáctanos para más información y visita. "
            f"#BienesRaices #Inmobiliaria #{tipo_propiedad.replace(' ', '')} #{operacion}"
        ),
        "cercano": (
            f"¡Tenemos lo que buscabas! 🏡\n\n"
            f"{tipo_propiedad} en {operacion} por {precio}\n\n"
            f"{caracteristicas}\n\n"
            f"Escríbenos y te damos todos los detalles 😊 "
            f"#BienesRaices #{tipo_propiedad.replace(' ', '')} #{operacion}"
        ),
        "urgente": (
            f"⚡ OPORTUNIDAD — {tipo_propiedad} en {operacion}\n\n"
            f"{caracteristicas}\n\n"
            f"Solo {precio} • Disponibilidad limitada\n\n"
            f"¡Contáctanos HOY! #BienesRaices #Oportunidad #{tipo_propiedad.replace(' ', '')}"
        ),
        "lujoso": (
            f"✨ {tipo_propiedad} Premium en {operacion}\n\n"
            f"{caracteristicas}\n\n"
            f"Precio desde {precio}\n\n"
            f"Exclusividad y confort en cada detalle. "
            f"#LuxuryRealEstate #BienesRaices #Premium"
        ),
    }
    return plantillas.get(tono, plantillas["profesional"])


def _estadisticas_pagina() -> str:
    resp = httpx.get(
        f"{GRAPH_URL}/{META_PAGE_ID}",
        params={
            "fields": "name,fan_count,followers_count",
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    d = resp.json()
    return (
        f"Página: {d.get('name', '—')}\n"
        f"Fans: {d.get('fan_count', 0):,}\n"
        f"Seguidores: {d.get('followers_count', 0):,}"
    )


def _insights_posts_fb(limite: int = 5) -> str:
    limite = min(int(limite), 10)
    resp = httpx.get(
        f"{GRAPH_URL}/{META_PAGE_ID}/posts",
        params={
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": limite,
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json().get("data", [])
    if not posts:
        return "No hay publicaciones recientes en Facebook."

    lineas = ["=== ÚLTIMAS PUBLICACIONES FACEBOOK ==="]
    for p in posts:
        likes = p.get("likes", {}).get("summary", {}).get("total_count", 0)
        comentarios = p.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = p.get("shares", {}).get("count", 0)
        fecha = (p.get("created_time") or "")[:10]
        texto = p.get("message") or ""
        resumen = (texto[:100] + "...") if len(texto) > 100 else texto
        lineas.append(f"\n[{fecha}] ❤️ {likes} | 💬 {comentarios} | 🔄 {shares}")
        if resumen:
            lineas.append(f"  \"{resumen}\"")
    return "\n".join(lineas)


def _insights_posts_ig(limite: int = 5) -> str:
    limite = min(int(limite), 10)
    resp = httpx.get(
        f"{GRAPH_URL}/{META_IG_ACCOUNT_ID}/media",
        params={
            "fields": "id,caption,media_type,timestamp,like_count,comments_count",
            "limit": limite,
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json().get("data", [])
    if not posts:
        return "No hay publicaciones recientes en Instagram."

    lineas = ["=== ÚLTIMAS PUBLICACIONES INSTAGRAM ==="]
    for p in posts:
        likes = p.get("like_count", 0)
        comentarios = p.get("comments_count", 0)
        tipo = p.get("media_type", "IMAGE")
        fecha = (p.get("timestamp") or "")[:10]
        caption = p.get("caption") or ""
        resumen = (caption[:100] + "...") if len(caption) > 100 else caption
        lineas.append(f"\n[{fecha}] {tipo} | ❤️ {likes} | 💬 {comentarios}")
        if resumen:
            lineas.append(f"  \"{resumen}\"")
    return "\n".join(lineas)


def _insights_cuenta_ig() -> str:
    resp = httpx.get(
        f"{GRAPH_URL}/{META_IG_ACCOUNT_ID}",
        params={
            "fields": "name,biography,followers_count,follows_count,media_count,website",
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=30,
    )
    resp.raise_for_status()
    d = resp.json()
    return (
        f"Cuenta IG: @{d.get('name', '—')}\n"
        f"Seguidores: {d.get('followers_count', 0):,}\n"
        f"Siguiendo: {d.get('follows_count', 0):,}\n"
        f"Posts totales: {d.get('media_count', 0)}\n"
        f"Bio: {d.get('biography', '—')}"
    )
