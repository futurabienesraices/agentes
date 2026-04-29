#!/usr/bin/env python3
"""
Generador de Contenido Diario Automático — Futura Bienes Raíces
================================================================
Ejecuta cada día y genera automáticamente material para redes sociales:
  → Carousel de Instagram (PNG x 6 slides)
  → Reel / TikTok (MP4 ~20 segundos)
  → Copy listo para publicar en Facebook e Instagram

Modos de uso:
  python content_daily.py                   # Genera contenido para hoy (FBR)
  python content_daily.py --empresa fc      # Para Futura Cleaning
  python content_daily.py --tipo carousel   # Solo carousel
  python content_daily.py --tipo video      # Solo video
  python content_daily.py --tipo ambos      # Carousel + Video (default)
  python content_daily.py --preview         # Muestra plan sin generar archivos
"""
from __future__ import annotations
import sys
import json
import random
import argparse
import logging
from datetime import datetime
from pathlib import Path

# ── Configuración ──────────────────────────────────────────────────
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv()

from src.agents.orchestrator import Orquestador
from src.tools.design_tools import carousel_crear, flyer_crear
from src.tools.video_generator import video_slideshow_crear

Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/content_daily.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# TEMAS ROTATIVOS — Cambian cada día de la semana
# ══════════════════════════════════════════════════════════════════

TEMAS_FBR = [
    # Lunes
    {
        "tema": "Consejos para comprar tu primera casa en El Salvador",
        "tipo_contenido": "educativo",
        "hashtags": "#PrimeraCasa #BienesRaices #ElSalvador #FuturaBienesRaices #InvierteEnTuFuturo",
    },
    # Martes
    {
        "tema": "¿Cuánto vale una casa en Santa Ana, El Salvador? Guía 2025",
        "tipo_contenido": "informativo",
        "hashtags": "#SantaAna #CasasEnVenta #MercadoInmobiliario #ElSalvador",
    },
    # Miércoles
    {
        "tema": "5 errores que debes evitar al invertir en bienes raíces",
        "tipo_contenido": "educativo",
        "hashtags": "#InversionInmobiliaria #Errores #ConsejosInmobiliarios #BienesRaices",
    },
    # Jueves
    {
        "tema": "¿Renta o compra? Te ayudamos a decidir en El Salvador",
        "tipo_contenido": "decisión",
        "hashtags": "#RentarOComprar #ElSalvador #Propiedades #DecisiónFinanciera",
    },
    # Viernes
    {
        "tema": "Propiedades disponibles esta semana en Futura Bienes Raíces",
        "tipo_contenido": "catálogo",
        "hashtags": "#CasasDisponibles #SantaAna #ElSalvador #PropiedadesEnVenta",
    },
    # Sábado
    {
        "tema": "Tips para hacer crecer tu patrimonio con bienes raíces",
        "tipo_contenido": "motivacional",
        "hashtags": "#Patrimonio #LibertadFinanciera #BienesRaices #Inversión",
    },
    # Domingo
    {
        "tema": "¿Listo para tu nuevo hogar? Agenda una cita con nosotros",
        "tipo_contenido": "cta",
        "hashtags": "#NuevoHogar #AgendaTuVisita #FuturaBienesRaices #Contacto",
    },
]

TEMAS_FC = [
    # Lunes
    {
        "tema": "¿Cada cuánto lavar tu sofá? La guía completa",
        "tipo_contenido": "educativo",
        "hashtags": "#LimpiezaSofa #FuturaCleaning #LimpiezaProfesional #ElSalvador",
    },
    # Martes
    {
        "tema": "Antes y después: resultados reales de limpieza de colchón",
        "tipo_contenido": "resultado",
        "hashtags": "#AntesYDespues #Colchon #LimpiezaColchon #FuturaCleaning",
    },
    # Miércoles
    {
        "tema": "5 señales de que tu sofá necesita limpieza profesional ya",
        "tipo_contenido": "educativo",
        "hashtags": "#Sofa #LimpiezaHogar #Higiene #FuturaCleaning",
    },
    # Jueves
    {
        "tema": "¿Por qué elegir Futura Cleaning? Nuestro proceso de limpieza",
        "tipo_contenido": "proceso",
        "hashtags": "#LimpiezaProfesional #CalidadGarantizada #FuturaCleaning",
    },
    # Viernes
    {
        "tema": "Oferta de fin de semana: limpieza de sofá + colchón",
        "tipo_contenido": "oferta",
        "hashtags": "#Oferta #LimpiezaHogar #FuturaCleaning #ElSalvador",
    },
    # Sábado
    {
        "tema": "Cómo mantener tu hogar limpio toda la semana: tips rápidos",
        "tipo_contenido": "tips",
        "hashtags": "#TipsLimpieza #HogarLimpio #FuturaCleaning",
    },
    # Domingo
    {
        "tema": "¡Agenda tu limpieza profesional hoy! Respondemos en minutos",
        "tipo_contenido": "cta",
        "hashtags": "#AgendaAhora #LimpiezaProfesional #FuturaCleaning #Contacto",
    },
]


def _get_tema_hoy(empresa: str) -> dict:
    """Selecciona el tema según el día de la semana (0=Lunes, 6=Domingo)."""
    dia = datetime.now().weekday()
    temas = TEMAS_FBR if empresa == "fbr" else TEMAS_FC
    return temas[dia % len(temas)]


# ══════════════════════════════════════════════════════════════════
# GENERACIÓN CON IA — El agente de marketing crea el contenido
# ══════════════════════════════════════════════════════════════════

def _generar_contenido_ia(tema_info: dict, empresa: str) -> dict:
    """
    Usa el Agente de Marketing para generar el contenido estructurado del día.
    Retorna dict con: slides_carousel, slides_video, copy_instagram, copy_facebook
    """
    nombre_empresa = "Futura Bienes Raíces" if empresa == "fbr" else "Futura Cleaning"
    tema = tema_info["tema"]
    tipo = tema_info["tipo_contenido"]

    prompt = f"""Eres el agente de marketing de {nombre_empresa}.
Hoy es {datetime.now().strftime('%A %d de %B de %Y')}.

Genera contenido para redes sociales sobre este tema:
TEMA: {tema}
TIPO: {tipo}

Devuelve EXACTAMENTE este JSON (sin texto extra, solo el JSON):
{{
  "slides_carousel": [
    {{"titulo": "...", "texto": "...", "subtexto": "..."}},
    {{"titulo": "...", "texto": "...", "subtexto": "..."}},
    {{"titulo": "...", "texto": "...", "subtexto": "..."}},
    {{"titulo": "...", "texto": "...", "subtexto": "..."}},
    {{"titulo": "...", "texto": "...", "subtexto": "..."}},
    {{"titulo": "Contáctanos", "texto": "Estamos aquí para ayudarte.", "subtexto": "Tel: 6027-2418"}}
  ],
  "slides_video": [
    {{"titulo": "...", "subtitulo": "..."}},
    {{"titulo": "...", "subtitulo": "..."}},
    {{"titulo": "...", "subtitulo": "..."}},
    {{"titulo": "...", "subtitulo": "..."}},
    {{"titulo": "...", "subtitulo": "..."}}
  ],
  "copy_instagram": "Post completo para Instagram con emojis y hashtags...",
  "copy_facebook": "Post completo para Facebook..."
}}

Reglas:
- Slides carousel: máx 40 palabras por slide, copy impactante
- Slides video: títulos cortos (máx 6 palabras), subtítulos informativos
- Copy: tono profesional pero cercano, en español latinoamericano
- Incluye siempre CTA con Tel: 6027-2418"""

    try:
        orq = Orquestador()
        respuesta = orq.ejecutar_con_agente("marketing", prompt)

        # Extraer JSON de la respuesta
        inicio = respuesta.find("{")
        fin = respuesta.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            json_str = respuesta[inicio:fin]
            return json.loads(json_str)
    except Exception as e:
        log.warning(f"IA falló: {e}. Usando contenido de respaldo.")

    # Contenido de respaldo si la IA falla
    return _contenido_respaldo(tema, empresa)


def _contenido_respaldo(tema: str, empresa: str) -> dict:
    """Contenido de respaldo si la IA no está disponible."""
    nombre = "Futura Bienes Raíces" if empresa == "fbr" else "Futura Cleaning"
    return {
        "slides_carousel": [
            {"titulo": tema[:40], "texto": f"En {nombre} te ayudamos con todo.", "subtexto": ""},
            {"titulo": "Expertos a tu servicio", "texto": "Años de experiencia respaldándonos.", "subtexto": ""},
            {"titulo": "Calidad garantizada", "texto": "Tu satisfacción es nuestra prioridad.", "subtexto": ""},
            {"titulo": "Resultados reales", "texto": "Miles de clientes satisfechos en El Salvador.", "subtexto": ""},
            {"titulo": "¿Listo para empezar?", "texto": "Contáctanos y te asesoramos sin costo.", "subtexto": ""},
            {"titulo": "Contáctanos HOY", "texto": "Respuesta inmediata garantizada.", "subtexto": "Tel: 6027-2418"},
        ],
        "slides_video": [
            {"titulo": nombre, "subtitulo": "El mejor servicio en El Salvador"},
            {"titulo": tema[:35], "subtitulo": ""},
            {"titulo": "Expertos en lo que hacemos", "subtitulo": "Resultados garantizados"},
            {"titulo": "¡Contáctanos!", "subtitulo": "Tel: 6027-2418"},
            {"titulo": nombre, "subtitulo": "Santa Ana, El Salvador"},
        ],
        "copy_instagram": f"✨ {tema}\n\nEn {nombre} estamos aquí para ayudarte.\n\nContáctanos: 6027-2418\n\n#ElSalvador #{nombre.replace(' ', '')}",
        "copy_facebook": f"{tema}\n\n{nombre} — Tu aliado de confianza en El Salvador.\n\nEscríbenos al 6027-2418 para más información.",
    }


# ══════════════════════════════════════════════════════════════════
# PIPELINE PRINCIPAL
# ══════════════════════════════════════════════════════════════════

def generar_contenido_diario(
    empresa: str = "fbr",
    tipo: str = "ambos",
    preview: bool = False,
) -> dict:
    """
    Pipeline completo de generación diaria.

    Args:
        empresa: 'fbr' o 'fc'
        tipo:    'carousel' | 'video' | 'ambos'
        preview: Si True, solo muestra el plan sin generar archivos

    Returns:
        Dict con rutas generadas y copys listos.
    """
    fecha = datetime.now().strftime("%Y-%m-%d")
    dia_nombre = datetime.now().strftime("%A")
    tema_hoy = _get_tema_hoy(empresa)

    log.info(f"{'='*60}")
    log.info(f"CONTENIDO DIARIO — {fecha} ({dia_nombre})")
    log.info(f"Empresa: {'Futura Bienes Raíces' if empresa == 'fbr' else 'Futura Cleaning'}")
    log.info(f"Tema: {tema_hoy['tema']}")
    log.info(f"{'='*60}")

    resultado = {
        "fecha": fecha,
        "tema": tema_hoy["tema"],
        "hashtags": tema_hoy["hashtags"],
        "archivos": [],
        "copy_instagram": "",
        "copy_facebook": "",
        "copy_completo": "",
    }

    if preview:
        log.info("MODO PREVIEW — No se generarán archivos")
        log.info(f"Tema del día: {tema_hoy['tema']}")
        log.info(f"Tipo de contenido: {tema_hoy['tipo_contenido']}")
        return resultado

    # Generar contenido con IA
    log.info("Generando contenido con IA...")
    contenido = _generar_contenido_ia(tema_hoy, empresa)

    # ── CAROUSEL ────────────────────────────────────────────────────
    if tipo in ("carousel", "ambos"):
        log.info("Generando carousel...")
        try:
            rutas_carousel = carousel_crear(
                empresa=empresa,
                diapositivas=contenido["slides_carousel"],
            )
            if rutas_carousel and not rutas_carousel[0].startswith("ERROR"):
                resultado["archivos"].extend(rutas_carousel)
                log.info(f"✅ Carousel: {len(rutas_carousel)} slides generadas")
                for r in rutas_carousel:
                    log.info(f"   → {Path(r).name}")
            else:
                log.error(f"❌ Error carousel: {rutas_carousel}")
        except Exception as e:
            log.error(f"❌ Carousel falló: {e}")

    # ── VIDEO REEL ──────────────────────────────────────────────────
    if tipo in ("video", "ambos"):
        log.info("Generando video Reel...")
        try:
            ruta_video = video_slideshow_crear(
                empresa=empresa,
                slides=contenido["slides_video"],
                duracion_slide=3.5,
            )
            if not ruta_video.startswith("ERROR"):
                resultado["archivos"].append(ruta_video)
                log.info(f"✅ Video: {Path(ruta_video).name}")
            else:
                log.error(f"❌ Error video: {ruta_video}")
        except Exception as e:
            log.error(f"❌ Video falló: {e}")

    # ── GUARDAR COPYS ───────────────────────────────────────────────
    resultado["copy_instagram"] = contenido.get("copy_instagram", "")
    resultado["copy_facebook"]  = contenido.get("copy_facebook", "")

    # Copy completo con hashtags
    resultado["copy_completo"] = (
        f"📅 CONTENIDO DEL DÍA — {fecha}\n"
        f"{'='*50}\n\n"
        f"📸 INSTAGRAM:\n{resultado['copy_instagram']}\n\n"
        f"{'='*50}\n\n"
        f"📘 FACEBOOK:\n{resultado['copy_facebook']}\n\n"
        f"{'='*50}\n\n"
        f"#️⃣ HASHTAGS:\n{tema_hoy['hashtags']}\n\n"
        f"📁 ARCHIVOS GENERADOS ({len(resultado['archivos'])}):\n"
        + "\n".join(f"  → {Path(a).name}" for a in resultado["archivos"])
    )

    # Guardar copy en archivo
    carpeta_copys = _ROOT / "media" / "output" / (
        "futura_bienes_raices" if empresa == "fbr" else "futura_cleaning"
    ) / "copys"
    carpeta_copys.mkdir(parents=True, exist_ok=True)
    archivo_copy = carpeta_copys / f"copy_{fecha}.txt"
    archivo_copy.write_text(resultado["copy_completo"], encoding="utf-8")
    log.info(f"✅ Copy guardado: {archivo_copy.name}")

    log.info(f"\n{'='*60}")
    log.info(f"COMPLETADO — {len(resultado['archivos'])} archivos generados")
    log.info(f"{'='*60}\n")
    log.info(resultado["copy_completo"])

    return resultado


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generador de contenido diario")
    parser.add_argument("--empresa",  default="fbr", choices=["fbr", "fc"],
                        help="'fbr' = Bienes Raíces | 'fc' = Futura Cleaning")
    parser.add_argument("--tipo",     default="ambos", choices=["carousel", "video", "ambos"],
                        help="Tipo de contenido a generar")
    parser.add_argument("--preview",  action="store_true",
                        help="Solo muestra el plan sin generar archivos")
    args = parser.parse_args()

    resultado = generar_contenido_diario(
        empresa=args.empresa,
        tipo=args.tipo,
        preview=args.preview,
    )

    if not args.preview:
        print(f"\n✅ {len(resultado['archivos'])} archivos generados")
        print(f"📅 Tema del día: {resultado['tema']}")


if __name__ == "__main__":
    main()
