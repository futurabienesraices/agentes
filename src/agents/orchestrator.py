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
from src.agents.trader import AgenteTrader
from src.agents.media import AgenteMedia

# ── Agentes especializados — Inmobiliaria ─────────────────────────
from src.agents.lead_manager import AgenteLeads
from src.agents.content_creator import AgenteContenido
from src.agents.client_service import AgenteClientes


INSTRUCCIONES_ROUTER = f"""Eres el orquestador del equipo de IA de un emprendedor serial con múltiples negocios.
Clasifica la solicitud con una sola palabra. Sé preciso — elige el agente más específico para la tarea.

=== AGENTES GENERALES ===
investigador  → Investigar: mercados, apps, tendencias globales, competidores, tecnologías, cualquier tema de investigación
estratega     → Ideas de negocio, validar oportunidades, modelos de ingreso, planes, estrategia empresarial, nuevos negocios
desarrollador → Código, webs, apps, APIs, automatizaciones, scripts, bases de datos, bots
marketing     → Estrategia de marketing, copies, contenido, embudos, anuncios, redes sociales para cualquier negocio
analista      → Reportes, KPIs, métricas, análisis financiero, dashboards, datos de cualquier negocio
trader        → Trading de acciones, criptomonedas, ETFs, análisis técnico, señales de compra/venta, portafolio, inversiones
media         → Editar video, cortar clips, crear reels, transcribir, extraer audio, podcast, ebooks, fotografía, contenido para redes

=== AGENTES ESPECIALIZADOS — INMOBILIARIA ===
inmobiliaria_leads     → CRM: registrar, actualizar o consultar clientes/prospectos inmobiliarios
inmobiliaria_contenido → Crear posts, copies o publicar contenido específico de propiedades en redes
inmobiliaria_clientes  → Atención a clientes: consultas, propiedades disponibles, visitas, información

REGLAS DE ENRUTAMIENTO:
- Trading/inversiones/mercados financieros → SIEMPRE trader
- Inmobiliaria → especializados si es CRM/contenido/atención; analista si son reportes del negocio
- Dudas entre estratega e investigador → investigador si busca datos, estratega si elabora un plan
- Una sola palabra, sin explicación."""


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
            "trader": AgenteTrader,
            "media": AgenteMedia,
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
            "trader": "Trader",
            "media": "Editor de Media",
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

    def ejecutar_pipeline(self, pipeline: str, tarea: str, verbose: bool = True) -> str:
        """Encadena agentes: la salida de uno es el contexto del siguiente."""
        PIPELINES = {
            "content-cleaning": {
                "pasos": [
                    ("investigador", (
                        "Investiga en TikTok, Instagram y Reels qué tipo de videos de "
                        "limpieza de muebles (sofás, colchones) están viralizando AHORA en "
                        "Latinoamérica. Necesito: "
                        "1) Duración ideal del video, "
                        "2) Estructura del hook (primeros 3 segundos), "
                        "3) Tipo de música, "
                        "4) Uso de texto/subtítulos en pantalla, "
                        "5) Tipo de voz en off si aplica, "
                        "6) Hashtags ganadores, "
                        "7) Ejemplos de captions virales. "
                        "Responde con criterios concretos y accionables para un editor de video."
                    )),
                    ("media", tarea),
                ],
                "nombre": "Investigador → Editor (Futura Cleaning)",
            },
            "content-inmobiliaria": {
                "pasos": [
                    ("investigador", (
                        "Investiga en TikTok, Instagram y Facebook qué tipo de videos "
                        "inmobiliarios están funcionando mejor AHORA en Latinoamérica y El Salvador. "
                        "Necesito: "
                        "1) Duración ideal por plataforma, "
                        "2) Estructura del video (orden de tomas), "
                        "3) Texto y subtítulos en pantalla, "
                        "4) Voz en off: ¿sí o no? ¿qué estilo?, "
                        "5) Música recomendada, "
                        "6) Hashtags ganadores para El Salvador, "
                        "7) Qué información del precio mostrar y cómo. "
                        "Criterios concretos para editor de video."
                    )),
                    ("media", tarea),
                ],
                "nombre": "Investigador → Editor (Bienes Raíces)",
            },
        }

        if pipeline not in PIPELINES:
            opciones = ", ".join(PIPELINES.keys())
            raise ValueError(f"Pipeline '{pipeline}' no existe. Opciones: {opciones}")

        config = PIPELINES[pipeline]
        contexto = ""
        resultado = ""

        for i, (tipo_agente, tarea_paso) in enumerate(config["pasos"]):
            nombre_agente = self._nombres.get(tipo_agente, tipo_agente)
            if verbose:
                print(f"\n[Paso {i+1}/{len(config['pasos'])} — {nombre_agente}]\n")

            if contexto:
                tarea_completa = (
                    f"CRITERIOS DEL INVESTIGADOR:\n{contexto}\n\n"
                    f"TU TAREA (aplica los criterios anteriores):\n{tarea_paso}"
                )
            else:
                tarea_completa = tarea_paso

            resultado = self._agentes[tipo_agente]().ejecutar(tarea_completa)
            contexto = resultado

        return resultado

    def listar_agentes(self) -> str:
        generales = [k for k in self._agentes if not k.startswith("inmobiliaria_")]
        especializados = [k for k in self._agentes if k.startswith("inmobiliaria_")]
        lineas = ["Agentes generales:", *[f"  {a}" for a in generales],
                  "", "Agentes inmobiliaria:", *[f"  {a}" for a in especializados]]
        return "\n".join(lineas)
