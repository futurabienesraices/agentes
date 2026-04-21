"""Herramientas de edición y análisis de video/audio/ebooks."""
from __future__ import annotations
import base64
import json
import os
import subprocess
import tempfile
from pathlib import Path
from src import video_db

CARPETA_MEDIA = os.path.join(os.getcwd(), "media")
CARPETA_OUTPUT = os.path.join(CARPETA_MEDIA, "output")
CARPETA_INPUT = os.path.join(CARPETA_MEDIA, "input")


def _init_carpetas():
    for c in [CARPETA_INPUT, CARPETA_OUTPUT]:
        os.makedirs(c, exist_ok=True)


def _ruta_input(nombre: str) -> str:
    _init_carpetas()
    return os.path.join(CARPETA_INPUT, nombre)


def _ruta_output(nombre: str, subcarpeta: str = "") -> str:
    """Devuelve la ruta de salida, creando la subcarpeta si se indica."""
    base = Path(CARPETA_OUTPUT) / subcarpeta if subcarpeta else Path(CARPETA_OUTPUT)
    base.mkdir(parents=True, exist_ok=True)
    return str(base / nombre)


def _subcarpeta_por_nombre(nombre: str, plataforma: str = "") -> str:
    """Detecta la subcarpeta correcta según el nombre del archivo y la plataforma."""
    n = nombre.lower()
    es_cleaning = any(p in n for p in ("cleaning", "limpieza", "sofa", "colchon", "mueble"))
    es_fbr = any(p in n for p in ("fbr", "bienes", "casa", "terreno", "propiedad"))
    es_reel = any(p in n + plataforma for p in ("reel", "tiktok", "instagram", "vertical", "9x16"))
    es_fb = any(p in n + plataforma for p in ("facebook", "fb", "horizontal"))

    if es_cleaning:
        return "futura_cleaning/reels" if es_reel else ("futura_cleaning/facebook" if es_fb else "futura_cleaning")
    if es_fbr:
        return "futura_bienes_raices/reels" if es_reel else ("futura_bienes_raices/facebook" if es_fb else "futura_bienes_raices")
    return ""


def _ffmpeg(*args, timeout: int = 120) -> tuple[str, str]:
    """Ejecuta FFmpeg con timeout de seguridad (default 2 min)."""
    cmd = ["ffmpeg", "-y"] + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f"FFmpeg error:\n{r.stderr[-1000:]}")
    return r.stdout, r.stderr


def _ffprobe(ruta: str) -> dict:
    """Obtiene metadata del video/audio."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_streams", "-show_format", ruta],
        capture_output=True, text=True, timeout=30,
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
                "max_frames": {
                    "type": "integer",
                    "description": "Máximo de frames a extraer (default: 4, máx: 8). Más frames = más tokens.",
                    "default": 4,
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
        "name": "media_indexados",
        "description": (
            "Lista los videos que ya fueron analizados y están en el índice permanente. "
            "Úsala ANTES de video_analizar para saber si ya tienes el análisis guardado "
            "y evitar gastar tokens re-analizando."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "media_limpiar_output",
        "description": (
            "Limpia y organiza media/output/: "
            "elimina archivos corruptos (<500KB) y los indicados en 'eliminar', "
            "y mueve los buenos a subcarpetas por negocio y tipo "
            "(futura_cleaning/reels/, futura_bienes_raices/facebook/, etc.). "
            "Llama SIEMPRE al final de cada tarea de edición."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "eliminar": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Nombres de archivos intermedios o defectuosos a borrar",
                    "default": [],
                },
                "organizar": {
                    "type": "boolean",
                    "description": "Mover archivos buenos a subcarpetas organizadas (default: true)",
                    "default": True,
                },
            },
            "required": [],
        },
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
    {
        "name": "video_crear_profesional",
        "description": (
            "Crea un video profesional completo estilo redes sociales: "
            "une múltiples clips con transiciones suaves, agrega voz en off automática (TTS neural), "
            "y quema subtítulos estilizados. Úsalo en vez de video_crear_reel cuando quieras "
            "resultado de alta calidad con narración. Duración recomendada: 45-90 segundos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "clips": {
                    "type": "array",
                    "description": "Lista de clips a usar, con archivo, inicio y duración en segundos",
                    "items": {
                        "type": "object",
                        "properties": {
                            "archivo":  {"type": "string", "description": "Nombre del archivo de video"},
                            "inicio":   {"type": "string", "description": "Tiempo de inicio, ej: '00:05' o '1:20'"},
                            "duracion": {"type": "number",  "description": "Duración del clip en segundos"},
                        },
                        "required": ["archivo", "inicio", "duracion"],
                    },
                },
                "script_voz": {
                    "type": "string",
                    "description": "Texto completo para la voz en off. Escribe en español natural, coloquial, directo. Máx 150 palabras para 60s.",
                },
                "nombre_salida": {
                    "type": "string",
                    "description": "Nombre del archivo final, ej: cleaning_reel_tiktok o fbr_casa_trebol_reel",
                },
                "plataforma": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "facebook", "youtube"],
                    "default": "tiktok",
                    "description": "tiktok/instagram = vertical 9:16 | facebook/youtube = horizontal 16:9",
                },
                "transicion": {
                    "type": "string",
                    "enum": ["fade", "wiperight", "wipeleft", "slideleft", "slideright", "circleopen", "dissolve"],
                    "default": "fade",
                    "description": "Tipo de transición entre clips",
                },
                "voz": {
                    "type": "string",
                    "default": "es-MX-DaliaNeural",
                    "description": "Voz TTS. Opciones: es-MX-DaliaNeural (mujer), es-MX-JorgeNeural (hombre), es-ES-ElviraNeural",
                },
            },
            "required": ["clips", "script_voz", "nombre_salida"],
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
        "media_indexados": lambda: video_db.listar_indexados(),
        "media_limpiar_output": _media_limpiar_output,
        "video_crear_profesional": _video_crear_profesional,
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


def _resolver_ruta(nombre_archivo: str) -> str:
    """Resuelve la ruta completa buscando en input/ recursivamente y luego en output/."""
    # Ruta directa
    for base in [CARPETA_INPUT, CARPETA_OUTPUT]:
        ruta = os.path.join(base, nombre_archivo)
        if os.path.exists(ruta):
            return ruta
    # Búsqueda recursiva en input/
    for f in Path(CARPETA_INPUT).rglob("*"):
        if f.name == nombre_archivo or str(f.relative_to(CARPETA_INPUT)) == nombre_archivo:
            return str(f)
    return os.path.join(CARPETA_INPUT, nombre_archivo)  # fallback


def _video_info(nombre_archivo: str) -> str:
    ruta = _resolver_ruta(nombre_archivo)

    # Revisar índice permanente primero
    guardado = video_db.obtener_info(ruta)
    if guardado:
        return f"[índice] {guardado}"

    meta = _ffprobe(ruta)
    fmt = meta.get("format", {})
    duracion = float(fmt.get("duration", 0))
    size_mb = int(fmt.get("size", 0)) / (1024 * 1024)
    info_video = next(
        (s for s in meta.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    resultado = (
        f"Archivo: {nombre_archivo}\n"
        f"Duración: {int(duracion//60)}:{int(duracion%60):02d}\n"
        f"Resolución: {info_video.get('width','?')}x{info_video.get('height','?')}\n"
        f"FPS: {info_video.get('r_frame_rate','?')}\n"
        f"Tamaño: {size_mb:.1f} MB\n"
        f"Codec video: {info_video.get('codec_name','?')}"
    )
    video_db.guardar_info(ruta, resultado)
    return resultado


def _video_analizar(
    nombre_archivo: str,
    max_frames: int = 2,
    tipo_analisis: str = "general",
) -> str:
    """Analiza un video extrayendo MÁXIMO max_frames frames distribuidos uniformemente.
    Default 4 frames = ~800 tokens. Nunca más de 8 frames para controlar costos.
    El resultado se guarda permanentemente en media/video_index.json."""
    import anthropic as ant
    ruta = _resolver_ruta(nombre_archivo)

    # Revisar índice permanente antes de hacer cualquier trabajo
    guardado = video_db.obtener_analisis(ruta, tipo_analisis)
    if guardado:
        return f"[índice — analizado anteriormente]\n{guardado}"

    tmp_dir = tempfile.mkdtemp()

    # Obtener duración primero
    try:
        meta = _ffprobe(ruta)
        duracion = float(meta.get("format", {}).get("duration", 60))
    except Exception:
        duracion = 60

    # Limitar a máximo 8 frames siempre, distribuidos uniformemente
    max_frames = min(max_frames, 8)
    intervalo = max(duracion / max_frames, 1)

    # Extraer solo max_frames frames
    patron = os.path.join(tmp_dir, "frame_%03d.jpg")
    _ffmpeg(
        "-i", ruta,
        "-vf", f"fps=1/{intervalo},scale=640:-1",  # escala reducida para menor peso
        "-vframes", str(max_frames),
        "-q:v", "5",
        patron,
    )
    frames = sorted(Path(tmp_dir).glob("frame_*.jpg"))
    if not frames:
        return "No se pudieron extraer frames del video."

    prompts = {
        "propiedad": (
            "Analiza estos frames de un video inmobiliario. "
            "Para cada frame: tipo de toma (exterior/sala/cocina/recámara/baño/otro), "
            "descripción breve y calidad (buena/regular/mala). "
            "¿Vale la pena editar este video para redes? ¿Qué tipo de contenido sería?"
        ),
        "cleaning": (
            "Analiza estos frames de un video de limpieza de muebles. "
            "Identifica: qué mueble es (sofá/colchón/sillón), el proceso mostrado, "
            "si se ve el antes/después. ¿Sirve para reel de TikTok/Instagram?"
        ),
        "reel": (
            "Analiza estos frames. Identifica los momentos más atractivos visualmente. "
            "¿Cuál sería el mejor hook (primeros 3 segundos)? ¿Sirve para reel viral?"
        ),
        "general": (
            "Describe brevemente qué hay en cada frame. "
            "Identifica de qué negocio es (limpieza de muebles o propiedad inmobiliaria) "
            "y qué tipo de contenido es."
        ),
    }
    prompt = prompts.get(tipo_analisis, prompts["general"])

    # Enviar frames a Claude Vision
    client = ant.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    content = [{"type": "text", "text": prompt}]
    for i, frame_path in enumerate(frames[:8]):  # máx 8 frames
        with open(frame_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode()
        ts = int(i * intervalo)
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

    resultado = respuesta.content[0].text
    # Guardar en índice permanente
    video_db.guardar_analisis(ruta, tipo_analisis, resultado)
    return resultado


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
    entrada = _resolver_ruta(nombre_archivo)  # busca en input/ Y output/
    salida = _ruta_output(nombre_salida if nombre_salida.endswith(".mp4") else nombre_salida + ".mp4")
    _ffmpeg(
        "-ss", inicio,          # seek rápido antes del -i
        "-i", entrada,
        "-to", fin,
        "-c:v", "libx264",      # recodificar para que sea válido desde cualquier punto
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",  # moov al inicio = reproducción inmediata
        salida,
        timeout=180,
    )
    size = os.path.getsize(salida) / (1024 * 1024)
    return f"Clip creado: {os.path.basename(salida)} ({size:.1f} MB)\nGuardado en: media/output/"


def _video_extraer_audio(
    nombre_archivo: str, nombre_salida: str, formato: str = "mp3"
) -> str:
    entrada = _resolver_ruta(nombre_archivo)
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
    entrada = _resolver_ruta(nombre_archivo)
    nombre_mp4 = nombre_salida if nombre_salida.endswith(".mp4") else nombre_salida + ".mp4"
    sub = _subcarpeta_por_nombre(nombre_mp4, "tiktok")
    salida = _ruta_output(nombre_mp4, sub)
    filtros = (
        "scale=1080:1920:force_original_aspect_ratio=decrease,"
        "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    if caption:
        texto = caption.replace("'", "\\'").replace(":", "\\:").replace(",", "\\,")
        filtros += (
            f",drawtext=text='{texto}':fontsize=52:fontcolor=white:font=Arial:"
            f"box=1:boxcolor=black@0.6:boxborderw=12:"
            f"x=(w-text_w)/2:y=h-text_h-100"
        )
    _ffmpeg(
        "-ss", inicio,          # seek rápido antes del -i
        "-i", entrada,
        "-t", str(min(duracion_segundos, 60)),
        "-vf", filtros,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        salida,
        timeout=300,
    )
    size = os.path.getsize(salida) / (1024 * 1024)
    return (
        f"Reel creado: {os.path.basename(salida)}\n"
        f"Formato: 1080x1920 vertical 9:16\n"
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
    EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v",
            ".jpg", ".jpeg", ".png", ".heic", ".gif", ".mp3", ".wav", ".m4a"}

    def listar_recursivo(carpeta: Path, prefijo: str) -> list[str]:
        lineas = []
        try:
            items = sorted(carpeta.iterdir())
        except PermissionError:
            return []
        for item in items:
            if item.is_dir():
                lineas.append(f"  📂 {item.name}/")
                for sub in listar_recursivo(item, prefijo + "  "):
                    lineas.append("  " + sub)
            elif item.suffix.lower() in EXTS:
                size = item.stat().st_size / (1024 * 1024)
                # ruta relativa desde CARPETA_INPUT para usarla como argumento
                rel = str(item.relative_to(Path(CARPETA_INPUT)))
                lineas.append(f"  • {rel} ({size:.1f} MB)")
        return lineas

    lineas = ["📁 media/input/:"]
    sub = listar_recursivo(Path(CARPETA_INPUT), "")
    lineas += sub if sub else ["  (vacío — coloca tus videos aquí)"]

    lineas.append("\n📁 media/output/:")
    outputs = sorted(Path(CARPETA_OUTPUT).rglob("*"))
    outputs = [f for f in outputs if f.is_file() and f.suffix.lower() in EXTS]
    if outputs:
        for f in outputs:
            size = f.stat().st_size / (1024 * 1024)
            lineas.append(f"  • {f.name} ({size:.1f} MB)")
    else:
        lineas.append("  (vacío)")
    return "\n".join(lineas)


def _media_limpiar_output(
    eliminar: list[str] | None = None,
    organizar: bool = True,
) -> str:
    """Limpia y organiza media/output/.
    - Elimina archivos corruptos (<500KB) y los indicados en 'eliminar'
    - Organiza los buenos en subcarpetas por negocio y tipo
    Estructura final:
      output/futura_cleaning/reels/   output/futura_cleaning/facebook/
      output/futura_bienes_raices/reels/  output/futura_bienes_raices/facebook/
    """
    MIN_BYTES = 500 * 1024  # 500 KB
    EXTS_VIDEO = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}
    output = Path(CARPETA_OUTPUT)
    output.mkdir(exist_ok=True)

    borrados, movidos, errores = [], [], []

    # 1. Borrar archivos corruptos (< 500KB)
    for f in list(output.rglob("*")):
        if f.is_file() and f.suffix.lower() in EXTS_VIDEO:
            if f.stat().st_size < MIN_BYTES:
                try:
                    size = f.stat().st_size
                    f.unlink()
                    borrados.append(f"{f.name} ({size}B — corrupto)")
                except Exception:
                    pass

    # 2. Borrar archivos específicos indicados
    for nombre in (eliminar or []):
        candidatos = [output / nombre] + list(output.rglob(nombre))
        for ruta in candidatos:
            if ruta.exists():
                try:
                    ruta.unlink()
                    borrados.append(nombre)
                except Exception as e:
                    errores.append(f"{nombre}: {e}")
                break

    # 3. Organizar archivos buenos en subcarpetas
    if organizar:
        CARPETAS = {
            # (palabras clave en nombre) → subcarpeta destino
            ("cleaning", "limpieza", "sofa", "colchon", "mueble"): {
                ("reel", "tiktok", "instagram", "vertical"): "futura_cleaning/reels",
                ("facebook", "fb", "horizontal"):               "futura_cleaning/facebook",
                ():                                             "futura_cleaning",
            },
            ("fbr", "bienes", "casa", "terreno", "propiedad", "inmobiliaria"): {
                ("reel", "tiktok", "instagram", "vertical"): "futura_bienes_raices/reels",
                ("facebook", "fb", "horizontal", "tour"):    "futura_bienes_raices/facebook",
                ():                                          "futura_bienes_raices",
            },
        }

        for f in list(output.glob("*")):
            if not f.is_file() or f.suffix.lower() not in EXTS_VIDEO:
                continue
            nombre_lower = f.name.lower()
            destino_rel = None

            for palabras_negocio, tipos in CARPETAS.items():
                if any(p in nombre_lower for p in palabras_negocio):
                    for palabras_tipo, carpeta in tipos.items():
                        if not palabras_tipo or any(p in nombre_lower for p in palabras_tipo):
                            destino_rel = carpeta
                            break
                    break

            if destino_rel:
                destino = output / destino_rel
                destino.mkdir(parents=True, exist_ok=True)
                nuevo = destino / f.name
                if not nuevo.exists():
                    f.rename(nuevo)
                    movidos.append(f"{f.name} → output/{destino_rel}/")

    lineas = ["=== Limpieza y organización de output/ ==="]
    if borrados:
        lineas.append(f"\nEliminados ({len(borrados)}):")
        for b in borrados:
            lineas.append(f"  ✗ {b}")
    if movidos:
        lineas.append(f"\nOrganizados ({len(movidos)}):")
        for m in movidos:
            lineas.append(f"  → {m}")
    if not borrados and not movidos:
        lineas.append("Todo en orden, no se requirió ningún cambio.")
    if errores:
        lineas.append(f"\nErrores: {', '.join(errores)}")
    return "\n".join(lineas)


# ── TTS + Subtítulos + Editor profesional ────────────────────────

def _ass_ts(s: float) -> str:
    """Segundos → H:MM:SS.cc para formato ASS."""
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{sec:05.2f}"


def _generar_ass(script: str, dur_total: float, ruta: str, w: int, h: int) -> None:
    """Genera archivo ASS con subtítulos auto-temporalizados y estilo profesional."""
    palabras = script.split()
    PPL = 6  # palabras por línea
    grupos = [" ".join(palabras[i:i+PPL]) for i in range(0, len(palabras), PPL)]
    if not grupos:
        grupos = [" "]
    tpg = dur_total / len(grupos)
    fs = 72 if h >= 1920 else 52
    mv = max(60, int(h * 0.07))
    ass = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 1\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, "
        "BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,Arial Black,{fs},&H00FFFFFF,&H000000FF,&H00000000,&HAA000000,"
        f"-1,0,0,0,100,100,1,0,1,4,2,2,30,30,{mv},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    for i, g in enumerate(grupos):
        ass += f"Dialogue: 0,{_ass_ts(i*tpg)},{_ass_ts((i+1)*tpg)},Default,,0,0,0,,{g}\n"
    Path(ruta).write_text(ass, encoding="utf-8")


def _generar_voz(texto: str, salida: str, voz: str = "es-MX-DaliaNeural") -> None:
    """Genera voz en off con edge-tts (neural, gratis). Fallback a gTTS."""
    try:
        import edge_tts, asyncio

        async def _run():
            await edge_tts.Communicate(texto, voz).save(salida)

        try:
            asyncio.run(_run())
        except RuntimeError:
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.run(_run())
    except Exception:
        from gtts import gTTS
        gTTS(text=texto, lang="es", slow=False).save(salida)


def _parse_tiempo(t: str) -> float:
    """Convierte '1:20', '00:05' o '80' a segundos."""
    t = str(t).strip()
    if ":" in t:
        p = t.split(":")
        return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2]) if len(p) == 3 else int(p[0]) * 60 + float(p[1])
    return float(t)


def _video_crear_profesional(
    clips: list[dict],
    script_voz: str,
    nombre_salida: str,
    plataforma: str = "tiktok",
    transicion: str = "fade",
    voz: str = "es-MX-DaliaNeural",
) -> str:
    """Editor profesional con MoviePy: clips + crossfade + TTS + subtítulos."""
    try:
        from moviepy import (
            VideoFileClip, AudioFileClip,
            concatenate_videoclips, CompositeVideoClip, TextClip,
        )
    except ImportError:
        return "Falta moviepy. Ejecuta: pip install moviepy"

    import shutil as sh

    RESOLUCIONES = {"tiktok": (1080, 1920), "instagram": (1080, 1920),
                    "facebook": (1920, 1080), "youtube": (1920, 1080)}
    w, h = RESOLUCIONES.get(plataforma, (1080, 1920))
    tmp = Path(tempfile.mkdtemp(prefix="futura_"))

    try:
        # ── 1. Cargar clips ───────────────────────────────────────
        video_clips = []
        for c in clips[:6]:
            entrada = _resolver_ruta(c["archivo"])
            inicio  = _parse_tiempo(c.get("inicio", "0"))
            dur     = float(c.get("duracion", 5))
            clip = VideoFileClip(entrada, audio=False).subclipped(inicio, inicio + dur)
            # Escalar y recortar al formato objetivo
            if clip.w / clip.h > w / h:
                clip = clip.resized(height=h).cropped(x_center=clip.w / 2, width=w)
            else:
                clip = clip.resized(width=w).cropped(y_center=clip.h / 2, height=h)
            video_clips.append(clip)

        if not video_clips:
            return "Error: no se cargó ningún clip."

        # ── 2. Concatenar con crossfade ───────────────────────────
        video_final = concatenate_videoclips(video_clips, padding=-0.3, method="compose")
        dur_total   = video_final.duration

        # ── 3. Voz en off ─────────────────────────────────────────
        voz_path = str(tmp / "voz.mp3")
        print("  ⚙ Generando voz en off...", flush=True)
        _generar_voz(script_voz, voz_path, voz)
        audio_voz = AudioFileClip(voz_path)

        # Alargar video si la voz es más larga
        if audio_voz.duration > dur_total:
            extra = audio_voz.duration - dur_total + 0.5
            video_clips[-1] = video_clips[-1].with_duration(video_clips[-1].duration + extra)
            video_final = concatenate_videoclips(video_clips, padding=-0.3, method="compose")
            dur_total = video_final.duration

        video_final = video_final.with_audio(audio_voz.with_duration(dur_total))

        # ── 4. Subtítulos ─────────────────────────────────────────
        palabras = script_voz.split()
        PPL      = 6
        grupos   = [" ".join(palabras[i:i+PPL]) for i in range(0, len(palabras), PPL)]
        tpg      = dur_total / max(len(grupos), 1)
        fs       = max(42, int(h * 0.038))

        capas = [video_final]
        for i, grupo in enumerate(grupos):
            try:
                txt = (
                    TextClip(text=grupo, font_size=fs, color="white",
                             stroke_color="black", stroke_width=3,
                             font="Arial-Bold", method="label", size=(w - 80, None))
                    .with_start(i * tpg).with_duration(tpg)
                    .with_position(("center", int(h * 0.82)))
                )
                capas.append(txt)
            except Exception:
                pass

        video_con_subs = CompositeVideoClip(capas, size=(w, h))

        # ── 5. Exportar ───────────────────────────────────────────
        nombre_mp4  = nombre_salida if nombre_salida.endswith(".mp4") else nombre_salida + ".mp4"
        sub_carpeta = _subcarpeta_por_nombre(nombre_mp4, plataforma)
        salida      = _ruta_output(nombre_mp4, sub_carpeta)

        print("  ⚙ Renderizando...", flush=True)
        video_con_subs.write_videofile(
            salida, fps=30, codec="libx264", audio_codec="aac",
            preset="ultrafast", threads=4, logger=None,
        )

        for c in video_clips:
            c.close()
        audio_voz.close()

        size   = os.path.getsize(salida) / (1024 * 1024)
        dm, ds = int(dur_total // 60), int(dur_total % 60)
        return (
            f"Video profesional creado: {nombre_mp4}\n"
            f"Duración: {dm}:{ds:02d} | Tamaño: {size:.1f} MB\n"
            f"Plataforma: {plataforma} ({w}x{h}) | Clips: {len(video_clips)}\n"
            f"Guardado en: media/output/{sub_carpeta + '/' if sub_carpeta else ''}{nombre_mp4}"
        )

    except Exception as exc:
        return f"Error al crear el video: {exc}"

    finally:
        sh.rmtree(str(tmp), ignore_errors=True)


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
