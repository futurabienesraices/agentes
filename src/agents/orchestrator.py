"""Orquestador principal — enruta tareas al agente correcto."""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY, MODELO_RAPIDO, EMPRESA_NOMBRE
from src.agents.lead_manager import AgenteLeads
from src.agents.content_creator import AgenteContenido
from src.agents.reports_agent import AgenteReportes
from src.agents.client_service import AgenteClientes


INSTRUCCIONES_ROUTER = f"""Eres el orquestador del equipo de agentes de IA de {EMPRESA_NOMBRE}.

Tu única tarea es clasificar la solicitud del usuario y responder con el nombre del agente apropiado.
Responde ÚNICAMENTE con uno de estos valores exactos (sin explicación adicional):

- leads       → Gestión de prospectos, CRM, seguimiento, pipeline de ventas
- contenido   → Publicaciones en redes sociales, copy de propiedades, marketing
- reportes    → Análisis, estadísticas, reportes del negocio, KPIs
- clientes    → Atención a clientes, consultas sobre propiedades, información general
- general     → Cualquier solicitud que no encaje en las anteriores

SOLO responde con una de esas palabras."""


class Orquestador:
    """
    Orquestador que determina qué agente especializado debe manejar cada tarea
    y lo ejecuta, devolviendo la respuesta final.
    """

    def __init__(self):
        self.cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self._agentes = {
            "leads": AgenteLeads,
            "contenido": AgenteContenido,
            "reportes": AgenteReportes,
            "clientes": AgenteClientes,
        }

    def _enrutar(self, tarea: str) -> str:
        """Determina qué agente debe manejar la tarea."""
        respuesta = self.cliente.messages.create(
            model=MODELO_RAPIDO,
            max_tokens=20,
            system=INSTRUCCIONES_ROUTER,
            messages=[{"role": "user", "content": tarea}],
        )
        agente = respuesta.content[0].text.strip().lower()
        return agente if agente in self._agentes else "clientes"

    def ejecutar(self, tarea: str, verbose: bool = True) -> str:
        """
        Enruta la tarea al agente correcto y devuelve la respuesta.

        Args:
            tarea: La solicitud del usuario en lenguaje natural
            verbose: Si True, imprime qué agente está manejando la tarea
        Returns:
            Respuesta del agente especializado
        """
        tipo_agente = self._enrutar(tarea)

        if verbose:
            nombres = {
                "leads": "Agente de Leads",
                "contenido": "Agente de Contenido",
                "reportes": "Agente de Reportes",
                "clientes": "Agente de Clientes",
            }
            print(f"\n[Orquestador] → {nombres.get(tipo_agente, tipo_agente)}\n")

        AgenteCls = self._agentes[tipo_agente]
        agente = AgenteCls()
        return agente.ejecutar(tarea)

    def ejecutar_con_agente(self, tipo_agente: str, tarea: str) -> str:
        """Ejecuta directamente en un agente específico sin enrutamiento."""
        if tipo_agente not in self._agentes:
            tipos = ", ".join(self._agentes.keys())
            raise ValueError(f"Agente desconocido: {tipo_agente}. Opciones: {tipos}")
        AgenteCls = self._agentes[tipo_agente]
        return AgenteCls().ejecutar(tarea)
