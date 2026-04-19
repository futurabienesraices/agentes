"""Herramientas de edición y análisis de video/audio/ebooks."""
from __future__ import annotations
import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path

CARPETA_MEDIA = os.path.join(os.getcwd(), "media")
CARPETA_OUTPUT = os.path.join(CARPETA_MEDIA, "output")
CARPETA_INPUT = os.path.join(CARPETA_MEDIA, "input")


def _init_carpetas():
    for c in [CARPETA_INPUT, CARPETA_OUTPUT]:
        os.makedirs(c, exist_ok=True)


def _ruta_input(nombre: str) -> str:
    _init_carpetas()
    return os.path.join(CARPETA_INPUT, nombre)


def _ruta_output(nombre: str) -> str:
    _init_carpetas()
    return os.path.join(CARPETA_OUTPUT, nombre)


def _ffmpeg(*args) -> tuple[str, str]:
    """Ejecuta FFmpeg y devuelve (stdout, stderr)."""
    cmd = ["ffmpeg", "-y"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{r.stderr[-1000:]}")
    return r.stdout, r.stderr


def _ffprobe(ruta: str) -> dict:
    """Obtiene metadata del video/audio."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", ruta],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        raise RuntimeError(f"ffprobe error: {r.stderr}")
    return json.loads(r.stdout)


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_MEDIA: list[dict] = [
    {
        "name": "video_analizar",
        "description": (
            "Analiza el contenido de un video extrayendo frames clave y describiéndolos. "
            "Identifica tipos de tomas, personas, espacios, objetos. "
            "Para propiedades: clasifica cada toma (exterior, sala, cocina, recámara, etc.). "
            "Devuelve un análisis detallado con timestamps de cada escena."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {
                    "type": "string",
                    "description": "Nombre del video en la carpeta media/input/",
                },
                "intervalo_segundos": {
                    "type": "number",
                    "description": "Extraer un frame cada N segundos (default: 5)",
                    "default": 5,
                },
                "tipo_analisis": {
                    "type": "string",
                    "description": "Qué tipo de análisis necesitas",
                    "enum": ["propiedad", "podcast", "reel", "general"],
                    "default": "general",
                },
            },
            "required": ["nombre_archivo"],
        },
    },
    {
        "name": "video_transcribir",
        "description": (
            "Transcribe el audio de un video o archivo de audio a texto usando Whisper. "
            "Devuelve la transcripción completa con timestamps por segmento. "
            "Ideal para podcasts, entrevistas, testimoniales de clientes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string"},
                "idioma": {
                    "type": "string",
                    "description": "Código de idioma, ej: es, en",
                    "default": "es",
                },
            },
            "required": ["nombre_archivo"],
        },
    },
    {
        "name": "video_cortar",
        "description": (
            "Corta un segmento específico de un video. "
            "Especifica el tiempo de inicio y fin en formato MM:SS o segundos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string"},
                "inicio": {
                    "type": "string",
                    "description": "Tiempo de inicio, ej: '00:30' o '90' (segundos)",
                },
                "fin": {
                    "type": "string",
                    "description": "Tiempo de fin, ej: '01:45' o '105' (segundos)",
                },
                "nombre_salida": {
                    "type": "string",
                    "description": "Nombre del archivo resultado, ej: clip_01.mp4",
                },
            },
            "required": ["nombre_archivo", "inicio", "fin", "nombre_salida"],
        },
    },
    {
        "name": "video_extraer_audio",
        "description": (
            "Extrae el audio de un video como archivo MP3 o WAV. "
            "Útil para crear episodios de podcast desde una grabación de video."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string"},
                "formato": {
                    "type": "string",
                    "enum": ["mp3", "wav"],
                    "default": "mp3",
                },
                "nombre_salida": {"type": "string"},
            },
            "required": ["nombre_archivo", "nombre_salida"],
        },
    },
    {
        "name": "video_crear_reel",
        "description": (
            "Crea un reel optimizado para redes sociales (vertical 9:16, máx 60s). "
            "Recorta el mejor segmento del video original. "
            "Opcionalmente agrega texto de caption superpuesto."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string"},
                "inicio": {"type": "string", "description": "Tiempo de inicio del clip"},
                "duracion_segundos": {
                    "type": "number",
                    "description": "Duración del reel en segundos (max 60)",
                    "default": 30,
                },
                "caption": {
                    "type": "string",
                    "description": "Texto a superponer en el video (opcional)",
                },
                "nombre_salida": {"type": "string"},
            },
            "required": ["nombre_archivo", "nombre_salida"],
        },
    },
    {
        "name": "video_unir_clips",
        "description": (
            "Une múltiples clips de video en uno solo, en el orden indicado. "
            "Para propiedades: ordena las tomas de forma lógica antes de unirlas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "archivos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Lista de nombres de archivos en el orden deseado",
                },
                "nombre_salida": {"type": "string"},
            },
            "required": ["archivos", "nombre_salida"],
        },
    },
    {
        "name": "video_info",
        "description": "Obtiene información técnica de un video: duración, resolución, FPS, tamaño.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string"},
            },
            "required": ["nombre_archivo"],
        },
    },
    {
        "name": "media_listar",
        "description": "Lista los archivos disponibles en las carpetas media/input y media/output.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "ebook_crear",
        "description": (
            "Crea un ebook profesional en PDF con portada, índice y capítulos. "
            "Ideal para monetizar conocimiento: guías inmobiliarias, estrategias de negocio, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string"},
                "subtitulo": {"type": "string", "default": ""},
                "autor": {"type": "string"},
                "capitulos": {
                    "type": "array",
                    "description": "Lista de capítulos con título y contenido",
                    "items": {
                        "type": "object",
                        "properties": {
                            "titulo": {"type": "string"},
                            "contenido": {"type": "string"},
                        },
                    },
                },
                "nombre_salida": {
                    "type": "string",
                    "description": "Nombre del PDF resultante, ej: guia-inversion.pdf",
                },
            },
            "required": ["titulo", "autor", "capitulos", "nombre_salida"],
        },
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "video_analizar": _video_analizar,
        "video_transcribir": _video_transcribir,
        "video_cortar": _video_cortar,
        "video_extraer_audio": _video_extraer_audio,
        "video_crear_reel": _video_crear_reel,
        "video_unir_clips": _video_unir_clips,
        "video_info": _video_info,
        "media_listar": _media_listar,
        "ebook_crear": _ebook_crear,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except FileNotFoundError as exc:
        return f"No se encontró el archivo: {exc}"
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _video_info(nombre_archivo: str) -> str:
    ruta = _ruta_input(nombre_archivo)
    if not os.path.exists(ruta):
        ruta = _ruta_output(nombre_archivo)
    meta = _ffprobe(ruta)
    fmt = meta.get("format", {})
    duracion = float(fmt.get("duration", 0))
    size_mb = int(fmt.get("size", 0)) / (1024 * 1024)
    info_video = next(
        (s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    return (
        f"Archivo: {nombre_archivo}\n"
        f"Duración: {int(duracion//60)}:{int(duracion%60):02d}\n"
        f"Resolución: {info_video.get('width','?')}x{info_video.get('height','?')}\n"
        f"FPS: {info_video.get('r_frame_rate','?')}\n"
        f"Tamaño: {size_mb:.1f} MB\n"
        f"Codec video: {info_video.get('codec_name','?')}"
    )


def _video_analizar(
    nombre_archivo: str,
    intervalo_segundos: float = 5,
    tipo_analisis: str = "general",
) -> str:
    import anthropic as ant
    ruta = _ruta_input(nombre_archivo)
    tmp_dir = tempfile.mkdtemp()

    # Extraer frames con FFmpeg
    patron = os.path.join(tmp_dir, "frame_%03d.jpg")
    _ffmpeg(
        "-i", ruta,
        "-vf", f"fps=1/{intervalo_segundos}",
        "-q:v", "3",
        patron,
    )
    frames = sorted(Path(tmp_dir).glob("frame_*.jpg"))
    if not frames:
        return "No se pudieron extraer frames del video."

    # Construir prompt según tipo
    prompts = {
        "propiedad": (
            "Analiza estos frames de un video de propiedad inmobiliaria. "
            "Para cada frame indica: número de frame, timestamp aproximado, "
            "tipo de toma (exterior, sala, cocina, comedor, recámara, baño, jardín, garage, otro), "
            "descripción breve de lo que se ve, y calidad visual (buena/regular/mala). "
            "Al final sugiere el orden óptimo para presentar la propiedad (exterior → áreas sociales → recámaras → baños → extras) "
            "y qué frames descartar por baja calidad."
        ),
        "podcast": (
            "Analiza estos frames de una grabación de podcast o entrevista. "
            "Identifica: cuándo hay personas hablando, cambios de escena o corte, "
            "momentos donde podría cortarse para crear clips virales. "
            "Sugiere los mejores segmentos para clips cortos (30-60 segundos)."
        ),
        "reel": (
            "Analiza estos frames para identificar los momentos más atractivos visualmente. "
            "Identifica: tomas dinámicas, expresiones emotivas, momentos de acción, "
            "texto visible, cambios de ritmo. "
            "Sugiere los mejores 30 segundos para un reel viral, con justificación."
        ),
        "general": (
            "Describe en detalle qué hay en cada frame del video. "
            "Identifica personas, lugares, objetos, acciones, texto visible. "
            "Crea un índice de contenido con timestamps aproximados."
        ),
    }
    prompt = prompts.get(tipo_analisis, prompts["general"])

    # Enviar frames a Claude Vision
    client = ant.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    content = [{"type": "text", "text": prompt}]
    for i, frame_path in enumerate(frames[:20]):  # máx 20 frames
        with open(frame_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()
        ts = int(i * intervalo_segundos)
        content.append({
            "type": "text",
            "text": f"\n--- Frame {i+1} (≈{ts//60}:{ts%60:02d}) ---"
        })
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": data},
        })

    respuesta = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": content}],
    )
    # Limpiar frames temporales
    for f in frames:
        f.unlink()
    os.rmdir(tmp_dir)
    return respuesta.content[0].text


def _video_transcribir(nombre_archivo: str, idioma: str = "es") -> str:
    try:
        import whisper
    except ImportError:
        return (
            "Whisper no instalado. Ejecuta:\n"
            "pip install openai-whisper\n"
            "pip install ffmpeg-python"
        )
    ruta = _ruta_input(nombre_archivo)
    model = whisper.load_model("base")
    resultado = model.transcribe(ruta, language=idioma, verbose=False)
    lineas = [f"TRANSCRIPCIÓN — {nombre_archivo}\n"]
    for seg in resultado["segments"]:
        t_ini = int(seg["start"])
        t_fin = int(seg["end"])
        lineas.append(
            f"[{t_ini//60}:{t_ini%60:02d} → {t_fin//60}:{t_fin%60:02d}] {seg['text'].strip()}"
        )
    return "\n".join(lineas)


def _video_cortar(
    nombre_archivo: str, inicio: str, fin: str, nombre_salida: str
) -> str:
    entrada = _ruta_input(nombre_archivo)
    salida = _ruta_output(nombre_salida)
    _ffmpeg(
        "-i", entrada,
        "-ss", inicio,
        "-to", fin,
        "-c", "copy",
        salida,
    )
    size = os.path.getsize(salida) / (1024 * 1024)
    return f"Clip creado: {nombre_salida} ({size:.1f} MB)\nGuardado en: media/output/"


def _video_extraer_audio(
    nombre_archivo: str, nombre_salida: str, formato: str = "mp3"
) -> str:
    entrada = _ruta_input(nombre_archivo)
    salida = _ruta_output(nombre_salida if nombre_salida.endswith(f".{formato}") else f"{nombre_salida}.{formato}")
    _ffmpeg(
        "-i", entrada,
        "-vn",
        "-acodec", "libmp3lame" if formato == "mp3" else "pcm_s16le",
        "-ab", "192k",
        salida,
    )
    size = os.path.getsize(salida) / (1024 * 1024)
    return f"Audio extraído: {os.path.basename(salida)} ({size:.1f} MB)\nGuardado en: media/output/"


def _video_crear_reel(
    nombre_archivo: str,
    nombre_salida: str,
    inicio: str = "00:00",
    duracion_segundos: float = 30,
    caption: str | None = None,
) -> str:
    entrada = _ruta_input(nombre_archivo)
    salida = _ruta_output(nombre_salida)
    filtros = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2"
    if caption:
        # Escapar caracteres especiales para FFmpeg drawtext
        texto = caption.replace("'", "\\'").replace(":", "\\:")
        filtros += (
            f",drawtext=text='{texto}':fontsize=48:fontcolor=white:"
            f"box=1:boxcolor=black@0.5:boxborderw=10:"
            f"x=(w-text_w)/2:y=h-text_h-80"
        )
    _ffmpeg(
        "-i", entrada,
        "-ss", inicio,
        "-t", str(duracion_segundos),
        "-vf", filtros,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-b:a", "192k",
        salida,
    )
    size = os.path.getsize(salida) / (1024 * 1024)
    return (
        f"Reel creado: {nombre_salida}\n"
        f"Formato: 1080x1920 (vertical 9:16)\n"
        f"Duración: {duracion_segundos}s | Tamaño: {size:.1f} MB\n"
        f"Guardado en: media/output/"
    )


def _video_unir_clips(archivos: list[str], nombre_salida: str) -> str:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for a in archivos:
        ruta = _ruta_output(a) if os.path.exists(_ruta_output(a)) else _ruta_input(a)
        tmp.write(f"file '{ruta}'\n")
    tmp.close()
    salida = _ruta_output(nombre_salida)
    _ffmpeg(
        "-f", "concat",
        "-safe", "0",
        "-i", tmp.name,
        "-c", "copy",
        salida,
    )
    os.unlink(tmp.name)
    size = os.path.getsize(salida) / (1024 * 1024)
    return (
        f"Video unido: {nombre_salida} ({len(archivos)} clips → {size:.1f} MB)\n"
        f"Guardado en: media/output/"
    )


def _media_listar() -> str:
    _init_carpetas()
    lineas = ["📁 media/input/ (videos originales):"]
    inputs = list(Path(CARPETA_INPUT).iterdir())
    if inputs:
        for f in sorted(inputs):
            size = f.stat().st_size / (1024 * 1024)
            lineas.append(f"  • {f.name} ({size:.1f} MB)")
    else:
        lineas.append("  (vacío — coloca tus videos aquí)")
    lineas.append("\n📁 media/output/ (resultados editados):")
    outputs = list(Path(CARPETA_OUTPUT).iterdir())
    if outputs:
        for f in sorted(outputs):
            size = f.stat().st_size / (1024 * 1024)
            lineas.append(f"  • {f.name} ({size:.1f} MB)")
    else:
        lineas.append("  (vacío)")
    return "\n".join(lineas)


def _ebook_crear(
    titulo: str,
    autor: str,
    capitulos: list[dict],
    nombre_salida: str,
    subtitulo: str = "",
) -> str:
    try:
        from fpdf import FPDF
    except ImportError:
        return "fpdf2 no instalado. Ejecuta: pip install fpdf2"

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ── Portada ──────────────────────────────────────────────
    pdf.add_page()
    pdf.set_fill_color(20, 20, 40)
    pdf.rect(0, 0, 210, 297, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 32)
    pdf.ln(60)
    pdf.multi_cell(0, 12, titulo, align="C")
    if subtitulo:
        pdf.set_font("Helvetica", "", 16)
        pdf.ln(5)
        pdf.multi_cell(0, 8, subtitulo, align="C")
    pdf.set_font("Helvetica", "", 14)
    pdf.ln(15)
    pdf.cell(0, 8, f"Por {autor}", align="C")
    pdf.set_text_color(0, 0, 0)

    # ── Tabla de contenidos ───────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.ln(10)
    pdf.cell(0, 12, "Índice de contenido", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    for i, cap in enumerate(capitulos, 1):
        pdf.cell(0, 8, f"{i}. {cap['titulo']}", ln=True)

    # ── Capítulos ─────────────────────────────────────────────
    for i, cap in enumerate(capitulos, 1):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.ln(5)
        pdf.cell(0, 10, f"Capítulo {i}", ln=True)
        pdf.set_font("Helvetica", "B", 14)
        pdf.multi_cell(0, 8, cap["titulo"])
        pdf.ln(5)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, cap["contenido"])

    salida = _ruta_output(nombre_salida if nombre_salida.endswith(".pdf") else f"{nombre_salida}.pdf")
    pdf.output(salida)
    size = os.path.getsize(salida) / (1024 * 1024)
    return (
        f"Ebook creado: {os.path.basename(salida)}\n"
        f"Capítulos: {len(capitulos)} | Tamaño: {size:.2f} MB\n"
        f"Guardado en: media/output/"
    )
