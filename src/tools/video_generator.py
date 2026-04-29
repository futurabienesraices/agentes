"""
Video Generator — Futura Bienes Raíces & Futura Cleaning
=========================================================
Genera videos para Reels/TikTok/Stories usando MoviePy + Pillow.

Tipos de video soportados:
  - slideshow:   Slides de texto con transición fade (sin imágenes externas)
  - propiedad:   Video de propiedad con fotos locales

Uso de APIs gratuitas:
  - Pexels API (https://www.pexels.com/api/) — imágenes de stock gratis
    → Requiere PEXELS_API_KEY en .env (registro gratuito)
  - Pixabay API — alternativa gratuita, no requiere OAuth
"""
from __future__ import annotations

import os
import textwrap
import urllib.request
import urllib.parse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── MoviePy ───────────────────────────────────────────────────────
try:
    from moviepy import ImageClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip, ColorClip
    MOVIEPY_OK = True
except ImportError:
    MOVIEPY_OK = False

# ── Pillow ────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# ── Rutas ─────────────────────────────────────────────────────────
_ROOT   = Path(__file__).resolve().parent.parent.parent
_OUTPUT = _ROOT / "media" / "output"
_TEMP   = _ROOT / "media" / ".tmp"
_TEMP.mkdir(parents=True, exist_ok=True)

# ── Paletas ───────────────────────────────────────────────────────
PALETA = {
    "fbr": {
        "nombre":    "Futura Bienes Raíces",
        "primario":  (44, 95, 46),     # #2C5F2E verde
        "secundario":(26, 61, 27),     # #1A3D1B verde oscuro
        "acento":    (201, 168, 76),   # #C9A84C dorado
        "fondo":     (26, 61, 27),
        "carpeta":   "futura_bienes_raices",
    },
    "fc": {
        "nombre":    "Futura Cleaning",
        "primario":  (0, 119, 182),    # #0077B6 azul
        "secundario":(2, 62, 138),     # #023E8A azul marino
        "acento":    (0, 180, 216),    # #00B4D8 cian
        "fondo":     (2, 62, 138),
        "carpeta":   "futura_cleaning",
    },
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _carpeta(empresa: str, tipo: str) -> Path:
    p = _OUTPUT / PALETA[empresa]["carpeta"] / tipo
    p.mkdir(parents=True, exist_ok=True)
    return p


def _buscar_fuente(tamaño: int) -> Optional["ImageFont.FreeTypeFont"]:
    """Busca fuente del sistema disponible."""
    candidatos = [
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in candidatos:
        if Path(c).exists():
            try:
                return ImageFont.truetype(c, tamaño)
            except Exception:
                pass
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════════
# PEXELS API — Imágenes de stock gratuitas
# ══════════════════════════════════════════════════════════════════

def _buscar_imagen_pexels(query: str, api_key: str) -> Optional[str]:
    """
    Busca una imagen en Pexels y la descarga a /tmp.
    Requiere PEXELS_API_KEY en .env (registro gratis en pexels.com/api).
    Retorna ruta local del archivo descargado, o None si falla.
    """
    if not api_key:
        return None
    try:
        q = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=3&orientation=landscape"
        req = urllib.request.Request(url, headers={"Authorization": api_key})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        fotos = data.get("photos", [])
        if not fotos:
            return None

        img_url = fotos[0]["src"]["landscape"]
        dest = _TEMP / f"pexels_{_timestamp()}.jpg"
        urllib.request.urlretrieve(img_url, dest)
        return str(dest)
    except Exception:
        return None


def _buscar_imagen_pixabay(query: str, api_key: str) -> Optional[str]:
    """
    Alternativa gratuita a Pexels usando Pixabay API.
    Requiere PIXABAY_API_KEY en .env (gratis en pixabay.com/api/docs).
    """
    if not api_key:
        return None
    try:
        q = urllib.parse.quote(query)
        url = f"https://pixabay.com/api/?key={api_key}&q={q}&image_type=photo&orientation=horizontal&per_page=3"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())

        hits = data.get("hits", [])
        if not hits:
            return None

        img_url = hits[0]["largeImageURL"]
        dest = _TEMP / f"pixabay_{_timestamp()}.jpg"
        urllib.request.urlretrieve(img_url, dest)
        return str(dest)
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
# GENERADOR DE FRAME PNG (slide individual para el video)
# ══════════════════════════════════════════════════════════════════

def _crear_frame_png(
    empresa: str,
    titulo: str,
    subtitulo: str = "",
    imagen_fondo: Optional[str] = None,
    ancho: int = 1080,
    alto: int = 1920,
) -> str:
    """Crea un frame PNG individual para usar en el video."""
    if not PILLOW_OK:
        raise RuntimeError("Pillow no instalado")

    m = PALETA[empresa]
    img = Image.new("RGB", (ancho, alto), m["fondo"])
    draw = ImageDraw.Draw(img, "RGBA")

    # Fondo degradado
    r1, g1, b1 = m["primario"]
    r2, g2, b2 = m["secundario"]
    for y in range(alto):
        t = y / alto
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        draw.line([(0, y), (ancho, y)], fill=(r, g, b))

    # Imagen de fondo con overlay si existe
    if imagen_fondo and Path(imagen_fondo).exists():
        try:
            bg = Image.open(imagen_fondo).convert("RGB")
            bg = bg.resize((ancho, alto), Image.LANCZOS)
            img.paste(bg, (0, 0))
            draw = ImageDraw.Draw(img, "RGBA")
            overlay = Image.new("RGBA", (ancho, alto), (*m["secundario"], 160))
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img, "RGBA")
        except Exception:
            pass

    # Barra marca superior
    draw.rectangle([(0, 0), (ancho, 120)], fill=(*m["secundario"], 220))
    f_marca = _buscar_fuente(36)
    draw.text((50, 42), m["nombre"].upper(), font=f_marca, fill=(255, 255, 255))

    # Barra acento
    draw.rectangle([(0, 120), (ancho, 128)], fill=m["acento"])

    # Título centrado
    f_titulo = _buscar_fuente(80)
    y_cursor = alto // 3
    palabras = titulo.upper().split()
    linea_actual = ""
    lineas = []
    for p in palabras:
        prueba = f"{linea_actual} {p}".strip()
        bbox = draw.textbbox((0, 0), prueba, font=f_titulo)
        if bbox[2] <= ancho - 100:
            linea_actual = prueba
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = p
    if linea_actual:
        lineas.append(linea_actual)

    for linea in lineas:
        bbox = draw.textbbox((0, 0), linea, font=f_titulo)
        x = (ancho - (bbox[2] - bbox[0])) // 2
        draw.text((x + 3, y_cursor + 3), linea, font=f_titulo, fill=(0, 0, 0, 100))
        draw.text((x, y_cursor), linea, font=f_titulo, fill=(255, 255, 255))
        y_cursor += bbox[3] - bbox[1] + 16

    # Separador dorado
    y_cursor += 30
    draw.rectangle([(80, y_cursor), (ancho - 80, y_cursor + 5)], fill=m["acento"])
    y_cursor += 40

    # Subtítulo
    if subtitulo:
        f_sub = _buscar_fuente(48)
        for parrafo in subtitulo.split("\n"):
            if not parrafo.strip():
                y_cursor += 20
                continue
            # Wrap manual
            palabras_s = parrafo.split()
            lin = ""
            lins = []
            for p in palabras_s:
                prueba = f"{lin} {p}".strip()
                bbox = draw.textbbox((0, 0), prueba, font=f_sub)
                if bbox[2] <= ancho - 120:
                    lin = prueba
                else:
                    if lin:
                        lins.append(lin)
                    lin = p
            if lin:
                lins.append(lin)
            for l in lins:
                bbox = draw.textbbox((0, 0), l, font=f_sub)
                x = (ancho - (bbox[2] - bbox[0])) // 2
                draw.text((x, y_cursor), l, font=f_sub, fill=(220, 220, 220))
                y_cursor += bbox[3] - bbox[1] + 12

    # Logo empresa y CTA abajo
    draw.rectangle([(0, alto - 160), (ancho, alto)], fill=(*m["secundario"], 230))
    f_cta = _buscar_fuente(38)
    cta_txt = "Futura Bienes Raises  |  Tel: 6027-2418"
    bbox_cta = draw.textbbox((0, 0), cta_txt, font=f_cta)
    x_cta = (ancho - (bbox_cta[2] - bbox_cta[0])) // 2
    draw.text((x_cta, alto - 120), cta_txt, font=f_cta, fill=m["acento"])

    # Guardar frame temporal
    ruta = str(_TEMP / f"frame_{_timestamp()}.png")
    img.save(ruta, "PNG")
    return ruta


# ══════════════════════════════════════════════════════════════════
# VIDEO TIPO 1 — SLIDESHOW (Reel/TikTok de texto)
# ══════════════════════════════════════════════════════════════════

def video_slideshow_crear(
    empresa: str,
    slides: list[dict],
    duracion_slide: float = 3.5,
    fps: int = 24,
    musica: Optional[str] = None,
) -> str:
    """
    Genera un video estilo Reel/TikTok con slides de texto.

    Args:
        empresa:         'fbr' o 'fc'
        slides:          Lista de dicts: [{"titulo": str, "subtitulo": str}, ...]
        duracion_slide:  Segundos por slide (default 3.5s)
        fps:             Frames por segundo (default 24)
        musica:          Ruta a archivo de audio MP3/WAV (opcional)

    Returns:
        Ruta del archivo MP4 generado.
    """
    if not MOVIEPY_OK:
        return "ERROR: MoviePy no instalado. Ejecuta: pip install moviepy"
    if not PILLOW_OK:
        return "ERROR: Pillow no instalado. Ejecuta: pip install Pillow"
    if empresa not in PALETA:
        return f"ERROR: empresa debe ser 'fbr' o 'fc'"

    clips = []
    frames_tmp = []

    for slide in slides:
        titulo    = slide.get("titulo", "")
        subtitulo = slide.get("subtitulo", "")
        imagen    = slide.get("imagen_fondo", None)

        # Crear frame PNG
        frame_path = _crear_frame_png(
            empresa=empresa,
            titulo=titulo,
            subtitulo=subtitulo,
            imagen_fondo=imagen,
        )
        frames_tmp.append(frame_path)

        clip = ImageClip(frame_path, duration=duracion_slide)
        clip = clip.with_fps(fps)
        clips.append(clip)

    if not clips:
        return "ERROR: No se generaron clips"

    # Concatenar slides
    video = concatenate_videoclips(clips, method="compose")

    # Agregar música si existe
    if musica and Path(musica).exists():
        try:
            audio = AudioFileClip(musica).subclipped(0, video.duration)
            video = video.with_audio(audio)
        except Exception:
            pass

    # Guardar
    carpeta = _carpeta(empresa, "videos")
    nombre  = f"reel_{empresa}_{_timestamp()}.mp4"
    salida  = str(carpeta / nombre)

    video.write_videofile(
        salida,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    # Limpiar temporales
    for f in frames_tmp:
        try:
            Path(f).unlink()
        except Exception:
            pass

    return salida


# ══════════════════════════════════════════════════════════════════
# VIDEO TIPO 2 — VIDEO DE PROPIEDAD con fotos locales
# ══════════════════════════════════════════════════════════════════

def video_propiedad_crear(
    empresa: str,
    fotos: list[str],
    titulo_propiedad: str,
    precio: str = "",
    caracteristicas: list[str] | None = None,
    cta: str = "¡Agenda tu visita hoy!",
    duracion_foto: float = 3.0,
    fps: int = 24,
) -> str:
    """
    Genera un video de presentación de propiedad usando fotos locales.

    Args:
        empresa:           'fbr' o 'fc'
        fotos:             Lista de rutas a fotos de la propiedad
        titulo_propiedad:  Nombre/descripción de la propiedad
        precio:            Precio formateado (ej. "$85,000")
        caracteristicas:   Lista de bullets (ej. ["3 hab.", "2 baños"])
        cta:               Call to action para el slide final
        duracion_foto:     Segundos por foto
        fps:               Frames por segundo

    Returns:
        Ruta del MP4 generado.
    """
    if not MOVIEPY_OK:
        return "ERROR: MoviePy no instalado"

    caracteristicas = caracteristicas or []
    clips = []
    frames_tmp = []

    # Slide de introducción
    intro_subtitulo = precio if precio else ""
    if caracteristicas:
        intro_subtitulo += "\n" + " | ".join(caracteristicas[:3])
    frame_intro = _crear_frame_png(
        empresa=empresa,
        titulo=titulo_propiedad,
        subtitulo=intro_subtitulo.strip(),
    )
    frames_tmp.append(frame_intro)
    clips.append(ImageClip(frame_intro, duration=3.0).with_fps(fps))

    # Slides de fotos de la propiedad
    for foto_path in fotos[:8]:  # máx 8 fotos
        if not Path(foto_path).exists():
            continue
        try:
            clip = ImageClip(foto_path, duration=duracion_foto).with_fps(fps)
            clips.append(clip)
        except Exception:
            pass

    # Slide final CTA
    frame_cta = _crear_frame_png(
        empresa=empresa,
        titulo=cta,
        subtitulo=f"{titulo_propiedad}\nTel: 6027-2418",
    )
    frames_tmp.append(frame_cta)
    clips.append(ImageClip(frame_cta, duration=3.5).with_fps(fps))

    if not clips:
        return "ERROR: No se pudieron cargar las fotos"

    video = concatenate_videoclips(clips, method="compose")

    carpeta = _carpeta(empresa, "videos")
    nombre  = f"propiedad_{empresa}_{_timestamp()}.mp4"
    salida  = str(carpeta / nombre)

    video.write_videofile(
        salida,
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    for f in frames_tmp:
        try:
            Path(f).unlink()
        except Exception:
            pass

    return salida


# ══════════════════════════════════════════════════════════════════
# HERRAMIENTAS (formato anthropic tool-use)
# ══════════════════════════════════════════════════════════════════

VIDEO_TOOLS: list[dict] = [
    {
        "name": "video_slideshow",
        "description": (
            "Genera un video corto tipo Reel/TikTok/Stories (formato vertical 1080x1920) "
            "con slides de texto animadas para Futura Bienes Raíces o Futura Cleaning. "
            "Ideal para tips, consejos, listas y contenido educativo de redes sociales."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "empresa": {
                    "type": "string",
                    "enum": ["fbr", "fc"],
                    "description": "'fbr' = Bienes Raíces | 'fc' = Futura Cleaning",
                },
                "slides": {
                    "type": "array",
                    "description": "Lista de slides. Cada slide: {titulo: str, subtitulo: str}",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo":    {"type": "string"},
                            "subtitulo": {"type": "string", "default": ""},
                        },
                        "required": ["titulo"],
                    },
                },
                "duracion_slide": {
                    "type": "number",
                    "description": "Segundos por slide (default: 3.5)",
                    "default": 3.5,
                },
            },
            "required": ["empresa", "slides"],
        },
    },
    {
        "name": "video_propiedad",
        "description": (
            "Genera un video de presentación de propiedad inmobiliaria usando fotos locales. "
            "Crea una secuencia: slide intro → fotos → slide CTA."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "empresa": {"type": "string", "enum": ["fbr", "fc"]},
                "fotos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de rutas absolutas a fotos JPG/PNG de la propiedad",
                },
                "titulo_propiedad": {"type": "string"},
                "precio": {"type": "string", "default": ""},
                "caracteristicas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de características (ej. ['3 hab.', '2 baños', 'Garaje'])",
                    "default": [],
                },
                "cta": {
                    "type": "string",
                    "default": "¡Agenda tu visita hoy!",
                },
            },
            "required": ["empresa", "fotos", "titulo_propiedad"],
        },
    },
]


def ejecutar_video_tool(nombre: str, params: dict) -> str:
    """Dispatcher para herramientas de video."""
    if nombre == "video_slideshow":
        salida = video_slideshow_crear(
            empresa        = params["empresa"],
            slides         = params["slides"],
            duracion_slide = params.get("duracion_slide", 3.5),
        )
        if salida.startswith("ERROR"):
            return salida
        return f"✅ Video Reel generado:\n{salida}"

    elif nombre == "video_propiedad":
        salida = video_propiedad_crear(
            empresa            = params["empresa"],
            fotos              = params["fotos"],
            titulo_propiedad   = params["titulo_propiedad"],
            precio             = params.get("precio", ""),
            caracteristicas    = params.get("caracteristicas", []),
            cta                = params.get("cta", "¡Agenda tu visita hoy!"),
        )
        if salida.startswith("ERROR"):
            return salida
        return f"✅ Video de propiedad generado:\n{salida}"

    return f"ERROR: Herramienta de video desconocida: '{nombre}'"
