"""
Design Tools — Generador de flyers y carousels visuales usando Pillow.
Colores oficiales:
  Futura Bienes Raíces (FBR): #2C5F2E (verde) | blanco | dorado #C9A84C
  Futura Cleaning    (FC):  #0077B6 (azul)  | blanco | cian  #00B4D8

Fuentes disponibles en Linux/macOS sin instalar nada:
  - Liberation Sans → Bold, Regular  (equivalente a Arial)
  - DejaVu Sans     → Bold, Regular
  En macOS se buscan automáticamente en /Library/Fonts y /System/Library/Fonts.

Incluyé helper de CTA/WhatsApp para insertar links dinámicos en copies.
"""

from __future__ import annotations

import os
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Pillow (instalado con pip install Pillow) ─────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# ── Rutas de salida ───────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUT = _ROOT / "media" / "output"

# ── Paletas de marca ──────────────────────────────────────────────
MARCA: dict[str, dict] = {
    "fbr": {
        "nombre":    "Futura Bienes Raíces",
        "primario":  "#2C5F2E",   # verde bosque
        "secundario":"#1A3D1B",   # verde oscuro
        "acento":    "#C9A84C",   # dorado
        "fondo":     "#FAFAF5",   # blanco cálido
        "texto":     "#1A1A1A",
        "tag":       "#E8F5E9",
        "carpeta":   "futura_bienes_raices",
    },
    "fc": {
        "nombre":    "Futura Cleaning",
        "primario":  "#0077B6",   # azul profundo
        "secundario":"#023E8A",   # azul marino
        "acento":    "#00B4D8",   # cian brillante
        "fondo":     "#F0F8FF",   # blanco azulado
        "texto":     "#1A1A1A",
        "tag":       "#E0F4FF",
        "carpeta":   "futura_cleaning",
    },
}


# ══════════════════════════════════════════════════════════════════
# UTILIDADES INTERNAS
# ══════════════════════════════════════════════════════════════════

def _hex(color: str) -> tuple:
    """Convierte '#RRGGBB' → (R, G, B)."""
    c = color.lstrip("#")
    return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))


def _hex_a(color: str, alpha: int = 255) -> tuple:
    r, g, b = _hex(color)
    return (r, g, b, alpha)


def _buscar_fuente(nombres: list[str], tamaño: int) -> Optional["ImageFont.FreeTypeFont"]:
    """Busca la primera fuente disponible del sistema."""
    rutas_base = [
        "/System/Library/Fonts/",          # macOS nativas (primera prioridad)
        "/Library/Fonts/",                 # macOS instaladas por el usuario
        str(Path.home() / "Library" / "Fonts"),
        "/usr/share/fonts/truetype/liberation/",
        "/usr/share/fonts/truetype/dejavu/",
        "/usr/share/fonts/",
    ]
    for nombre in nombres:
        for base in rutas_base:
            candidato = Path(base) / nombre
            if candidato.exists():
                try:
                    return ImageFont.truetype(str(candidato), tamaño)
                except Exception:
                    pass
    return ImageFont.load_default()


def _fuente_bold(tamaño: int) -> "ImageFont.FreeTypeFont":
    return _buscar_fuente([
        "HelveticaNeue.ttc",          # macOS
        "Avenir Next.ttc",            # macOS
        "Arial Unicode.ttf",          # macOS /Library/Fonts
        "LiberationSans-Bold.ttf",    # Linux
        "DejaVuSans-Bold.ttf",        # Linux
    ], tamaño)


def _fuente_regular(tamaño: int) -> "ImageFont.FreeTypeFont":
    return _buscar_fuente([
        "HelveticaNeue.ttc",          # macOS
        "Avenir Next.ttc",            # macOS
        "Arial Unicode.ttf",          # macOS /Library/Fonts
        "LiberationSans-Regular.ttf", # Linux
        "DejaVuSans.ttf",             # Linux
    ], tamaño)


_EMOJI_MAP = {
    "✔": "->",  "✅": "[OK]",  "❌": "[X]",  "📱": "",  "📲": "",
    "🏠": "",   "🏡": "",      "💰": "$",    "📊": "",  "🔑": "",
    "⭐": "*",  "✨": "*",     "🌟": "*",    "📣": "",  "💡": "",
    "🎯": ">",  "🔥": "!",    "👉": "->",   "👇": "v", "📞": "Tel.",
}

def _sanitizar(texto: str) -> str:
    """Reemplaza emojis y caracteres no-Latin-1 por equivalentes imprimibles."""
    for emoji, reemplazo in _EMOJI_MAP.items():
        texto = texto.replace(emoji, reemplazo)
    # Eliminar cualquier carácter fuera del rango imprimible básico
    return "".join(c if ord(c) < 8000 else "?" for c in texto)


def _wrap_text(draw: "ImageDraw.ImageDraw", texto: str, fuente, ancho_max: int) -> list[str]:
    """Divide texto para que quepa en ancho_max píxeles."""
    palabras = texto.split()
    lineas, linea_actual = [], ""
    for p in palabras:
        prueba = f"{linea_actual} {p}".strip()
        bbox = draw.textbbox((0, 0), prueba, font=fuente)
        if bbox[2] <= ancho_max:
            linea_actual = prueba
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = p
    if linea_actual:
        lineas.append(linea_actual)
    return lineas


def _carpeta_salida(empresa: str, tipo: str) -> Path:
    p = _OUTPUT / MARCA[empresa]["carpeta"] / tipo
    p.mkdir(parents=True, exist_ok=True)
    return p


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _degradado_vertical(draw: "ImageDraw.ImageDraw", ancho: int, alto: int,
                        color_top: str, color_bot: str) -> None:
    """Pinta un degradado vertical sobre el canvas."""
    r1, g1, b1 = _hex(color_top)
    r2, g2, b2 = _hex(color_bot)
    for y in range(alto):
        t = y / alto
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (ancho, y)], fill=(r, g, b))


def _barra_acento(draw: "ImageDraw.ImageDraw", ancho: int, y: int,
                  grosor: int, color: str) -> None:
    draw.rectangle([(0, y), (ancho, y + grosor)], fill=_hex(color))


# ══════════════════════════════════════════════════════════════════
# FUNCIÓN 1 — FLYER GENERATOR
# ══════════════════════════════════════════════════════════════════

def flyer_crear(
    empresa: str,
    titulo: str,
    subtitulo: str = "",
    precio: str = "",
    detalles: list[str] | None = None,
    cta: str = "Contáctanos ahora",
    telefono: str = "6027-2418",
    imagen_fondo: str = "",
    ancho: int = 1080,
    alto: int = 1350,
) -> str:
    """
    Genera un flyer de alta calidad en formato 4:5 (1080×1350px — ideal Instagram).

    Args:
        empresa:       'fbr' (Bienes Raíces) o 'fc' (Futura Cleaning)
        titulo:        Título principal del flyer (ej. "Casa en Venta")
        subtitulo:     Texto secundario (ej. "Colonia Escalón, Santa Ana")
        precio:        Si aplica (ej. "$85,000")
        detalles:      Lista de bullets (ej. ["3 habitaciones", "2 baños"])
        cta:           Call to action
        telefono:      Número de contacto
        imagen_fondo:  Ruta a imagen de fondo opcional
        ancho/alto:    Dimensiones en píxeles

    Returns:
        Ruta del archivo PNG generado.
    """
    if not PILLOW_OK:
        return "ERROR: Pillow no instalado. Ejecuta: pip install Pillow"

    m = MARCA.get(empresa)
    if not m:
        return f"ERROR: empresa debe ser 'fbr' o 'fc', recibido: '{empresa}'"

    detalles = detalles or []

    # ── Sanitizar entradas ────────────────────────────────────────
    titulo    = _sanitizar(titulo)
    subtitulo = _sanitizar(subtitulo)
    precio    = _sanitizar(precio)
    cta       = _sanitizar(cta)
    telefono  = _sanitizar(telefono)
    detalles  = [_sanitizar(d) for d in detalles]

    # ── Canvas base ───────────────────────────────────────────────
    img = Image.new("RGB", (ancho, alto), _hex(m["fondo"]))
    draw = ImageDraw.Draw(img, "RGBA")

    # ── Degradado de fondo ────────────────────────────────────────
    _degradado_vertical(draw, ancho, alto, m["primario"], m["secundario"])

    # ── Imagen de fondo opcional (con overlay semiopaco) ──────────
    if imagen_fondo and Path(imagen_fondo).exists():
        try:
            bg = Image.open(imagen_fondo).convert("RGB").resize((ancho, alto))
            img.paste(bg, (0, 0))
            draw = ImageDraw.Draw(img, "RGBA")
            overlay = Image.new("RGBA", (ancho, alto), (*_hex(m["secundario"]), 185))
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img, "RGBA")
        except Exception:
            pass

    # ── Franja superior con nombre de empresa ─────────────────────
    franja_h = 90
    draw.rectangle([(0, 0), (ancho, franja_h)], fill=(*_hex(m["secundario"]), 230))

    f_marca = _fuente_bold(32)
    draw.text((40, 28), m["nombre"].upper(), font=f_marca, fill="#FFFFFF")

    # Teléfono arriba derecha
    f_tel = _fuente_regular(26)
    bbox_tel = draw.textbbox((0, 0), telefono, font=f_tel)
    draw.text((ancho - bbox_tel[2] - 40, 32), telefono, font=f_tel, fill=_hex(m["acento"]))

    # ── Barra acento bajo la franja ───────────────────────────────
    _barra_acento(draw, ancho, franja_h, 6, m["acento"])

    # ── Precio (badge destacado) ──────────────────────────────────
    y_cursor = franja_h + 60
    if precio:
        f_precio = _fuente_bold(72)
        bbox_p = draw.textbbox((0, 0), precio, font=f_precio)
        pw = bbox_p[2] - bbox_p[0]
        px = (ancho - pw) // 2
        # Sombra
        draw.text((px + 3, y_cursor + 3), precio, font=f_precio, fill=(0, 0, 0, 120))
        draw.text((px, y_cursor), precio, font=f_precio, fill=_hex(m["acento"]))
        y_cursor += bbox_p[3] - bbox_p[1] + 30

    # ── Título ────────────────────────────────────────────────────
    f_titulo = _fuente_bold(58)
    lineas_titulo = _wrap_text(draw, titulo.upper(), f_titulo, ancho - 80)
    for linea in lineas_titulo:
        bbox_l = draw.textbbox((0, 0), linea, font=f_titulo)
        x = (ancho - (bbox_l[2] - bbox_l[0])) // 2
        draw.text((x + 2, y_cursor + 2), linea, font=f_titulo, fill=(0, 0, 0, 100))
        draw.text((x, y_cursor), linea, font=f_titulo, fill="#FFFFFF")
        y_cursor += bbox_l[3] - bbox_l[1] + 12

    # ── Barra separador ───────────────────────────────────────────
    y_cursor += 20
    _barra_acento(draw, ancho, y_cursor, 4, m["acento"])
    y_cursor += 30

    # ── Subtítulo ─────────────────────────────────────────────────
    if subtitulo:
        f_sub = _fuente_regular(38)
        lineas_sub = _wrap_text(draw, subtitulo, f_sub, ancho - 100)
        for linea in lineas_sub:
            bbox_s = draw.textbbox((0, 0), linea, font=f_sub)
            x = (ancho - (bbox_s[2] - bbox_s[0])) // 2
            draw.text((x, y_cursor), linea, font=f_sub, fill="#E0E0E0")
            y_cursor += bbox_s[3] - bbox_s[1] + 10
        y_cursor += 40

    # ── Bullets de detalles ──────────────────────────────────────
    if detalles:
        f_det = _fuente_regular(34)
        for item in detalles[:6]:
            txt = f"✔  {item}"
            bbox_d = draw.textbbox((0, 0), txt, font=f_det)
            x_det = (ancho - (bbox_d[2] - bbox_d[0])) // 2
            draw.text((x_det, y_cursor), txt, font=f_det, fill="#FFFFFF")
            y_cursor += bbox_d[3] - bbox_d[1] + 14
        y_cursor += 30

    # ── CTA (call to action) ──────────────────────────────────────
    f_cta = _fuente_bold(42)
    bbox_cta = draw.textbbox((0, 0), cta.upper(), font=f_cta)
    cw = bbox_cta[2] - bbox_cta[0]
    ch = bbox_cta[3] - bbox_cta[1]
    pad_x, pad_y = 50, 20
    btn_x = (ancho - cw - pad_x * 2) // 2
    btn_y = alto - 200
    draw.rounded_rectangle(
        [(btn_x, btn_y), (btn_x + cw + pad_x * 2, btn_y + ch + pad_y * 2)],
        radius=16,
        fill=_hex(m["acento"]),
    )
    draw.text((btn_x + pad_x, btn_y + pad_y), cta.upper(), font=f_cta, fill=_hex(m["secundario"]))

    # ── Pie de página ─────────────────────────────────────────────
    f_pie = _fuente_regular(26)
    pie_txt = f"{m['nombre']}  |  {telefono}"
    bbox_pie = draw.textbbox((0, 0), pie_txt, font=f_pie)
    draw.rectangle([(0, alto - 70), (ancho, alto)], fill=(*_hex(m["secundario"]), 230))
    x_pie = (ancho - (bbox_pie[2] - bbox_pie[0])) // 2
    draw.text((x_pie, alto - 52), pie_txt, font=f_pie, fill="#AAAAAA")

    # ── Guardar ───────────────────────────────────────────────────
    carpeta = _carpeta_salida(empresa, "flyers")
    nombre_archivo = f"flyer_{empresa}_{_timestamp()}.png"
    ruta_salida = str(carpeta / nombre_archivo)
    img.save(ruta_salida, "PNG", optimize=True)

    return ruta_salida


# ══════════════════════════════════════════════════════════════════
# FUNCIÓN 2 — CAROUSEL GENERATOR
# ══════════════════════════════════════════════════════════════════

def carousel_crear(
    empresa: str,
    diapositivas: list[dict],
    ancho: int = 1080,
    alto: int = 1080,
) -> list[str]:
    """
    Genera un carousel de Instagram (N diapositivas cuadradas 1080×1080px).

    Cada diapositiva es un dict con las claves (todas opcionales excepto 'texto'):
        {
          "texto":    str   — Contenido principal de la diapositiva  ← REQUERIDO
          "titulo":   str   — Encabezado grande (opcional)
          "subtexto": str   — Texto pequeño o datos (opcional)
          "numero":   int   — Si se omite se auto-numera
        }

    Args:
        empresa:      'fbr' o 'fc'
        diapositivas: Lista de dicts (ver arriba). Máximo 10.
        ancho/alto:   Dimensiones en píxeles (cuadrado recomendado)

    Returns:
        Lista de rutas PNG generadas (una por diapositiva).
    """
    if not PILLOW_OK:
        return ["ERROR: Pillow no instalado. Ejecuta: pip install Pillow"]

    m = MARCA.get(empresa)
    if not m:
        return [f"ERROR: empresa debe ser 'fbr' o 'fc'"]

    if not diapositivas:
        return ["ERROR: 'diapositivas' no puede estar vacío"]

    diapositivas = diapositivas[:10]
    total = len(diapositivas)
    rutas: list[str] = []
    carpeta = _carpeta_salida(empresa, "carousel")
    ts = _timestamp()

    for idx, slide in enumerate(diapositivas):
        numero = slide.get("numero", idx + 1)
        titulo   = _sanitizar(slide.get("titulo", ""))
        texto    = _sanitizar(slide.get("texto", ""))
        subtexto = _sanitizar(slide.get("subtexto", ""))
        es_ultima = (idx == total - 1)

        # ── Canvas ────────────────────────────────────────────────
        img = Image.new("RGB", (ancho, alto), _hex(m["fondo"]))
        draw = ImageDraw.Draw(img, "RGBA")

        # ── Fondo: degradado + rectángulo decorativo ──────────────
        if idx == 0:
            # Primera slide: degradado completo
            _degradado_vertical(draw, ancho, alto, m["primario"], m["secundario"])
        elif es_ultima:
            # Última slide: CTA — fondo oscuro
            _degradado_vertical(draw, ancho, alto, m["secundario"], "#0A0A0A")
        else:
            # Slides intermedias: fondo claro con acento
            draw.rectangle([(0, 0), (ancho, alto)], fill=_hex(m["fondo"]))
            draw.rectangle([(0, 0), (12, alto)], fill=_hex(m["primario"]))

        # ── Número de slide ────────────────────────────────────────
        f_num = _fuente_bold(22)
        num_txt = f"{numero} / {total}"
        draw.text((ancho - 80, 30), num_txt, font=f_num,
                  fill=_hex(m["acento"]) if idx == 0 else _hex(m["primario"]))

        # ── Logo / nombre empresa (esquina superior izq) ──────────
        f_marca = _fuente_bold(26)
        color_marca = "#FFFFFF" if (idx == 0 or es_ultima) else _hex(m["primario"])
        draw.text((30, 30), m["nombre"].upper(), font=f_marca, fill=color_marca)

        # ── Barra separador bajo encabezado ───────────────────────
        _barra_acento(draw, ancho, 80, 3, m["acento"])

        # ── Título de la diapositiva ───────────────────────────────
        y_cursor = 130
        if titulo:
            f_tit = _fuente_bold(52 if idx == 0 else 44)
            color_tit = "#FFFFFF" if (idx == 0 or es_ultima) else _hex(m["secundario"])
            lineas_tit = _wrap_text(draw, titulo, f_tit, ancho - 80)
            for linea in lineas_tit:
                draw.text((40, y_cursor), linea, font=f_tit, fill=color_tit)
                bbox = draw.textbbox((0, 0), linea, font=f_tit)
                y_cursor += bbox[3] - bbox[1] + 10
            y_cursor += 25

        # ── Cuerpo de texto ────────────────────────────────────────
        f_txt = _fuente_regular(34)
        color_txt = "#E8E8E8" if (idx == 0 or es_ultima) else _hex(m["texto"])
        parrafos = texto.split("\n")
        for parrafo in parrafos:
            if not parrafo.strip():
                y_cursor += 20
                continue
            lineas_p = _wrap_text(draw, parrafo, f_txt, ancho - 80)
            for linea in lineas_p:
                draw.text((40, y_cursor), linea, font=f_txt, fill=color_txt)
                bbox = draw.textbbox((0, 0), linea, font=f_txt)
                y_cursor += bbox[3] - bbox[1] + 8
            y_cursor += 16

        # ── Subtexto ───────────────────────────────────────────────
        if subtexto:
            y_cursor += 20
            f_subt = _fuente_regular(28)
            color_sub = _hex(m["acento"]) if (idx == 0 or es_ultima) else _hex(m["primario"])
            lineas_s = _wrap_text(draw, subtexto, f_subt, ancho - 80)
            for linea in lineas_s:
                draw.text((40, y_cursor), linea, font=f_subt, fill=color_sub)
                bbox = draw.textbbox((0, 0), linea, font=f_subt)
                y_cursor += bbox[3] - bbox[1] + 8

        # ── En la última slide: CTA visible ───────────────────────
        if es_ultima:
            f_cta = _fuente_bold(38)
            cta_txt = "¡Contáctanos ahora!  📲 6027-2418"
            bbox_cta = draw.textbbox((0, 0), cta_txt, font=f_cta)
            cw = bbox_cta[2] - bbox_cta[0]
            ch = bbox_cta[3] - bbox_cta[1]
            btn_x = (ancho - cw - 60) // 2
            btn_y = alto - 180
            draw.rounded_rectangle(
                [(btn_x, btn_y), (btn_x + cw + 60, btn_y + ch + 30)],
                radius=14, fill=_hex(m["acento"]),
            )
            draw.text((btn_x + 30, btn_y + 15), cta_txt, font=f_cta, fill=_hex(m["secundario"]))

        # ── Pie ────────────────────────────────────────────────────
        f_pie = _fuente_regular(22)
        draw.rectangle([(0, alto - 50), (ancho, alto)], fill=(*_hex(m["secundario"]), 200))
        pie_txt = f"{m['nombre']}  |  6027-2418"
        draw.text((30, alto - 36), pie_txt, font=f_pie, fill="#888888")

        # ── Guardar diapositiva ────────────────────────────────────
        nombre_archivo = f"carousel_{empresa}_{ts}_slide{numero:02d}.png"
        ruta = str(carpeta / nombre_archivo)
        img.save(ruta, "PNG", optimize=True)
        rutas.append(ruta)

    return rutas


# ════════════════════════════════════════════════════════════════
# CTA / WHATSAPP HELPERS
# ════════════════════════════════════════════════════════════════

import urllib.parse
from src.config import EMPRESA_TELEFONO


def generar_link_whatsapp(
    propiedad_ref: str,
    telefono: str | None = None,
    mensaje_extra: str = "",
) -> str:
    """
    Genera un link wa.me listo para usar en copies y CTAs.

    Args:
        propiedad_ref: Identificador o nombre corto de la propiedad
                       (ej. 'Casa-001', 'Terreno Santa Ana').
        telefono:      Número en formato internacional sin '+' ni espacios
                       (ej. '50360272418'). Si None, usa EMPRESA_TELEFONO del .env.
        mensaje_extra: Texto adicional a agregar al mensaje precargado.

    Returns:
        URL completa de WhatsApp con mensaje precargado, ej:
        https://wa.me/50360272418?text=Hola%2C%20vi%20la%20propiedad%20Casa-001...
    """
    tel = (telefono or EMPRESA_TELEFONO).replace("+", "").replace(" ", "").replace("-", "")
    # Si el número no empieza con código de país, agregar El Salvador (+503)
    if not tel.startswith("503") and len(tel) == 8:
        tel = f"503{tel}"
    texto = f"Hola, vi la propiedad {propiedad_ref} y me interesa más información."
    if mensaje_extra:
        texto += f" {mensaje_extra.strip()}"
    return f"https://wa.me/{tel}?text={urllib.parse.quote(texto)}"


def generar_cta_completo(
    propiedad_ref: str,
    telefono: str | None = None,
    canal: str = "instagram",
) -> str:
    """
    Devuelve un bloque de CTA formateado según el canal.

    canal: 'instagram' | 'facebook' | 'whatsapp' | 'portal'

    Returns:
        Texto de CTA listo para pegar en el copy del canal indicado.
    """
    link = generar_link_whatsapp(propiedad_ref, telefono)
    tel_display = (telefono or EMPRESA_TELEFONO)

    ctas = {
        "instagram": (
            f"✉️ ¿Te interesa? Escríbeme directo por WhatsApp:\n"
            f"{link}\n"
            f"📞 {tel_display} | Respondo en minutos"
        ),
        "facebook": (
            f"💬 Éscríbenos por WhatsApp para agendar tu visita sin compromiso:\n"
            f"{link}\n"
            f"Tel: {tel_display} — Atención inmediata"
        ),
        "whatsapp": (
            f"Hola, vi tu propiedad {propiedad_ref} y me gustaría más información. "
            f"¿Cuándo podemos hablar?"
        ),
        "portal": (
            f"Contactar al agente: {tel_display}\n"
            f"WhatsApp directo: {link}"
        ),
    }
    return ctas.get(canal, ctas["instagram"])


# ════════════════════════════════════════════════════════════════
# HERRAMIENTAS DE CTA (formato anthropic tool-use)
# ════════════════════════════════════════════════════════════════

CTA_TOOLS: list[dict] = [
    {
        "name": "generar_cta_whatsapp",
        "description": (
            "Genera un link de WhatsApp dinámico con el nombre/ID de la propiedad precargado "
            "y el texto de CTA correspondiente al canal (instagram, facebook, whatsapp, portal). "
            "Usar siempre al final de cada copy generado para una propiedad."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "propiedad_ref": {
                    "type": "string",
                    "description": "ID o nombre corto de la propiedad (ej. 'Casa Colonia Escalon')",
                },
                "canal": {
                    "type": "string",
                    "enum": ["instagram", "facebook", "whatsapp", "portal"],
                    "description": "Canal donde se va a publicar el copy",
                    "default": "instagram",
                },
                "telefono": {
                    "type": "string",
                    "description": "Número opcional (si es diferente al teléfono principal del negocio)",
                    "default": "",
                },
            },
            "required": ["propiedad_ref"],
        },
    },
]


# ══════════════════════════════════════════════════════════════════
# DEFINICIONES DE HERRAMIENTAS (formato anthropic tool-use)
# ══════════════════════════════════════════════════════════════════

DESIGN_TOOLS: list[dict] = [
    {
        "name": "design_flyer",
        "description": (
            "Genera un flyer visual profesional en PNG (1080×1350px, formato Instagram 4:5) "
            "para Futura Bienes Raíces o Futura Cleaning, listo para publicar en redes sociales."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "empresa": {
                    "type": "string",
                    "enum": ["fbr", "fc"],
                    "description": "'fbr' = Futura Bienes Raíces | 'fc' = Futura Cleaning",
                },
                "titulo": {
                    "type": "string",
                    "description": "Título principal del flyer (ej. 'Casa en Venta', 'Oferta de Limpieza')",
                },
                "subtitulo": {
                    "type": "string",
                    "description": "Texto secundario descriptivo (ej. 'Colonia Escalón, Santa Ana')",
                    "default": "",
                },
                "precio": {
                    "type": "string",
                    "description": "Precio formateado (ej. '$85,000 USD') — omitir si no aplica",
                    "default": "",
                },
                "detalles": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de bullets destacados (máx 6). Ej: ['3 habitaciones', '2 baños', 'Piscina']",
                    "default": [],
                },
                "cta": {
                    "type": "string",
                    "description": "Texto del botón de call to action",
                    "default": "Contáctanos ahora",
                },
                "telefono": {
                    "type": "string",
                    "description": "Teléfono de contacto a mostrar",
                    "default": "6027-2418",
                },
                "imagen_fondo": {
                    "type": "string",
                    "description": "Ruta absoluta a imagen de fondo (opcional). Si no existe, se usa degradado de color.",
                    "default": "",
                },
            },
            "required": ["empresa", "titulo"],
        },
    },
    {
        "name": "design_carousel",
        "description": (
            "Genera un carousel de Instagram (N imágenes cuadradas 1080×1080px) "
            "con diseño coherente de marca para Futura Bienes Raíces o Futura Cleaning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "empresa": {
                    "type": "string",
                    "enum": ["fbr", "fc"],
                    "description": "'fbr' = Futura Bienes Raíces | 'fc' = Futura Cleaning",
                },
                "diapositivas": {
                    "type": "array",
                    "description": "Lista de diapositivas (máx 10). Cada una es un objeto con campos: titulo (str), texto (str), subtexto (str).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo":    {"type": "string", "description": "Encabezado grande de la diapositiva"},
                            "texto":     {"type": "string", "description": "Cuerpo principal de texto"},
                            "subtexto":  {"type": "string", "description": "Dato adicional, acento de color"},
                        },
                        "required": ["texto"],
                    },
                },
            },
            "required": ["empresa", "diapositivas"],
        },
    },
]


# ══════════════════════════════════════════════════════════════════
# DISPATCHER — llamado desde AgenteBase.ejecutar_herramienta
# ══════════════════════════════════════════════════════════════════

def ejecutar_design_tool(nombre: str, params: dict) -> str:
    """
    Punto de entrada para el agente de diseño.
    Recibe el nombre de la herramienta y sus parámetros, devuelve string.
    """
    if nombre == "design_flyer":
        ruta = flyer_crear(
            empresa       = params["empresa"],
            titulo        = params["titulo"],
            subtitulo     = params.get("subtitulo", ""),
            precio        = params.get("precio", ""),
            detalles      = params.get("detalles", []),
            cta           = params.get("cta", "Contáctanos ahora"),
            telefono      = params.get("telefono", "6027-2418"),
            imagen_fondo  = params.get("imagen_fondo", ""),
        )
        if ruta.startswith("ERROR"):
            return ruta
        return f"✅ Flyer generado exitosamente:\n{ruta}"

    elif nombre == "design_carousel":
        rutas = carousel_crear(
            empresa       = params["empresa"],
            diapositivas  = params["diapositivas"],
        )
        if rutas and rutas[0].startswith("ERROR"):
            return rutas[0]
        resultado = f"✅ Carousel generado — {len(rutas)} diapositivas:\n"
        resultado += "\n".join(f"  [{i+1}] {r}" for i, r in enumerate(rutas))
        return resultado

    return f"ERROR: Herramienta de diseño desconocida: '{nombre}'"
