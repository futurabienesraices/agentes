"""Orquestador principal — enruta tareas entre agentes generales y especializados."""
from __future__ import annotations
import anthropic
from src.config import ANTHROPIC_API_KEY, MODELO_RAPIDO, EMPRESA_NOMBRE

# ── Agentes generales (cualquier negocio) ─────────────────────────
from src.agents.investigador import AgenteInvestigador
from src.agents.estratega import AgenteEstrategra
from src.agents.desarrollador import AgenteDesarrollador
from src.agents.marketing import AgenteMarketing
from src.agents.analista import AgenteAnalista

# ── Agentes especializados — Inmobiliaria ─────────────────────────
from src.agents.lead_manager import AgenteLeads
from src.agents.content_creator import AgenteContenido
from src.agents.client_service import AgenteClientes


INSTRUCCIONES_ROUTER = f"""Eres el orquestador del equipo de IA de un emprendedor serial.
El equipo tiene agentes generales y agentes especializados en inmobiliaria.

Clasifica la solicitud y responde ÚNICAMENTE con una de estas palabras:

=== AGENTES GENERALES (cualquier negocio o industria) ===
- investigador  → Investigar mercados, competidores, tendencias, apps globales, cualquier tema
- estratega     → Desarrollar ideas de negocio, validar oportunidades, planes de negocio, modelos de ingreso
- desarrollador → Programar webs, apps, APIs, automatizaciones, scripts, cualquier código
- marketing     → Estrategia de marketing, contenido, copies, embudos, lanzamientos para cualquier negocio
- analista      → Reportes, KPIs, análisis financiero, métricas, forecasting para cualquier negocio

=== AGENTES ESPECIALIZADOS — INMOBILIARIA ===
- inmobiliaria_leads     → CRM de clientes/prospectos inmobiliarios, seguimiento, pipeline de ventas
- inmobiliaria_contenido → Posts y marketing específico de propiedades en redes sociales
- inmobiliaria_clientes  → Atención a clientes sobre propiedades, consultas, visitas

REGLA: Si la tarea es general o para un negocio diferente a inmobiliaria → usa agentes generales.
Si es específicamente sobre propiedades, leads o clientes de la inmobiliaria → usa los especializados.

SOLO responde con una de esas palabras exactas."""


class Orquestador:
    def __init__(self):
        self.cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self._agentes = {
            # Generales
            "investigador": AgenteInvestigador,
            "estratega": AgenteEstrategra,
            "desarrollador": AgenteDesarrollador,
            "marketing": AgenteMarketing,
            "analista": AgenteAnalista,
            # Inmobiliaria
            "inmobiliaria_leads": AgenteLeads,
            "inmobiliaria_contenido": AgenteContenido,
            "inmobiliaria_clientes": AgenteClientes,
        }
        self._nombres = {
            "investigador": "Investigador",
            "estratega": "Estratega de Negocios",
            "desarrollador": "Desarrollador",
            "marketing": "Marketing",
            "analista": "Analista",
            "inmobiliaria_leads": "Inmobiliaria — Leads",
            "inmobiliaria_contenido": "Inmobiliaria — Contenido",
            "inmobiliaria_clientes": "Inmobiliaria — Clientes",
        }

    def _enrutar(self, tarea: str) -> str:
        respuesta = self.cliente.messages.create(
            model=MODELO_RAPIDO,
            max_tokens=30,
            system=INSTRUCCIONES_ROUTER,
            messages=[{"role": "user", "content": tarea}],
        )
        agente = respuesta.content[0].text.strip().lower()
        return agente if agente in self._agentes else "estratega"

    def ejecutar(self, tarea: str, verbose: bool = True) -> str:
        tipo_agente = self._enrutar(tarea)
        if verbose:
            print(f"\n[{self._nombres.get(tipo_agente, tipo_agente)}]\n")
        return self._agentes[tipo_agente]().ejecutar(tarea)

    def ejecutar_con_agente(self, tipo_agente: str, tarea: str) -> str:
        if tipo_agente not in self._agentes:
            opciones = ", ".join(self._agentes.keys())
            raise ValueError(f"Agente '{tipo_agente}' no existe. Opciones: {opciones}")
        return self._agentes[tipo_agente]().ejecutar(tarea)

    def listar_agentes(self) -> str:
        generales = [k for k in self._agentes if not k.startswith("inmobiliaria_")]
        especializados = [k for k in self._agentes if k.startswith("inmobiliaria_")]
        lineas = ["Agentes generales:", *[f"  {a}" for a in generales],
                  "", "Agentes inmobiliaria:", *[f"  {a}" for a in especializados]]
        return "\n".join(lineas)
