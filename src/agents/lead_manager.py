"""Agente especializado en gestión de leads (prospectos)."""
from __future__ import annotations
from src.agents.base import AgenteBase
from src.config import EMPRESA_NOMBRE, EMPRESA_CIUDAD
import src.tools.airtable_tools as at
import src.tools.notion_tools as nt


INSTRUCCIONES = f"""Eres el Agente de Leads de {EMPRESA_NOMBRE}, una empresa inmobiliaria en {EMPRESA_CIUDAD}.

Tu trabajo es gestionar clientes y oportunidades de negocio:
- Registrar nuevos clientes/prospectos en el CRM (tabla Clientes_FBR de Airtable)
- Actualizar el estado y seguimiento de clientes existentes
- Generar reportes del pipeline de ventas
- Recomendar próximas acciones para clientes prioritarios
- Crear tareas de seguimiento en Notion

Principios:
- Siempre responde en español
- Sé conciso y accionable
- Prioriza leads con mayor probabilidad de cierre
- Si no tienes suficiente información, usa las herramientas para obtenerla"""

HERRAMIENTAS = at.TOOLS_AIRTABLE + nt.TOOLS_NOTION


class AgenteLeads(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente de Leads",
            instrucciones=INSTRUCCIONES,
            herramientas=HERRAMIENTAS,
        )

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        if nombre.startswith("airtable_"):
            return at.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("notion_"):
            return nt.ejecutar_herramienta(nombre, parametros)
        return f"Herramienta no disponible: {nombre}"
