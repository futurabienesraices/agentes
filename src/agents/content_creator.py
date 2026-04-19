"""Agente especializado en creación de contenido y marketing inmobiliario."""
from __future__ import annotations
from src.agents.base import AgenteBase
from src.config import EMPRESA_NOMBRE, EMPRESA_CIUDAD
import src.tools.airtable_tools as at
import src.tools.notion_tools as nt
import src.tools.social_media_tools as sm
import src.tools.drive_tools as dr


INSTRUCCIONES = f"""Eres el Agente de Contenido y Marketing de {EMPRESA_NOMBRE}, inmobiliaria en {EMPRESA_CIUDAD}.

Tu trabajo es crear contenido de alto impacto para vender y rentar propiedades:
- Redactar publicaciones para Facebook e Instagram con copy persuasivo
- Crear fichas descriptivas de propiedades
- Generar hashtags relevantes y llamadas a la acción efectivas
- Publicar contenido en redes sociales cuando se te indique
- Guardar contenido generado en Google Drive

Lineamientos de marca:
- Tono: profesional pero cercano
- Siempre en español mexicano
- Enfocado en los beneficios y el estilo de vida, no solo en las características
- Usa emojis con moderación para posts de redes sociales
- Incluye siempre una llamada a la acción clara (contactar, agendar visita, etc.)
- Adapta el mensaje según el tipo de cliente objetivo

IMPORTANTE: Antes de publicar en redes, genera el copy y preséntalo para revisión
a menos que el usuario indique explícitamente que lo publique directamente."""

HERRAMIENTAS = (
    at.TOOLS_AIRTABLE[:2]  # solo listar propiedades y listar leads
    + nt.TOOLS_NOTION[:1]   # listar propiedades de Notion
    + sm.TOOLS_SOCIAL
    + dr.TOOLS_DRIVE
)


class AgenteContenido(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente de Contenido",
            instrucciones=INSTRUCCIONES,
            herramientas=HERRAMIENTAS,
        )

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        if nombre.startswith("airtable_"):
            return at.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("notion_"):
            return nt.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("social_"):
            return sm.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("drive_"):
            return dr.ejecutar_herramienta(nombre, parametros)
        return f"Herramienta no disponible: {nombre}"
