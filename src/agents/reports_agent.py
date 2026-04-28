"""Agente especializado en reportes y análisis del negocio."""
from __future__ import annotations
from src.agents.base import AgenteBase
from src.config import EMPRESA_NOMBRE, EMPRESA_CIUDAD
import src.tools.airtable_tools as at
import src.tools.drive_tools as dr


INSTRUCCIONES = f"""Eres el Agente de Reportes y Análisis de {EMPRESA_NOMBRE}, inmobiliaria en {EMPRESA_CIUDAD}.

Tu trabajo es convertir datos en información útil para la toma de decisiones:
- Generar reportes de leads: cuántos, de dónde vienen, tasa de conversión
- Analizar el inventario de propiedades disponibles
- Identificar cuellos de botella en el proceso de ventas
- Generar resúmenes ejecutivos semanales/mensuales
- Guardar reportes en Google Drive

Formato de reportes:
- Usa encabezados claros
- Incluye números concretos
- Añade observaciones y recomendaciones
- Siempre en español
- Destaca las métricas más importantes al inicio (resumen ejecutivo)"""

HERRAMIENTAS = at.TOOLS_AIRTABLE + dr.TOOLS_DRIVE


class AgenteReportes(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente de Reportes",
            instrucciones=INSTRUCCIONES,
            herramientas=HERRAMIENTAS,
        )

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        if nombre.startswith("airtable_"):
            return at.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("drive_"):
            return dr.ejecutar_herramienta(nombre, parametros)
        return f"Herramienta no disponible: {nombre}"
