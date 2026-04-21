"""Clase base para todos los agentes del equipo."""
from __future__ import annotations
from typing import Any
import anthropic
from src.config import ANTHROPIC_API_KEY, MODELO_PRINCIPAL
from src import memory


class AgenteBase:
    def __init__(self, nombre: str, instrucciones: str, herramientas: list[dict]):
        self.nombre = nombre
        self.herramientas = herramientas
        self.cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.modelo = MODELO_PRINCIPAL
        self.max_iteraciones = 10

        # Inyectar memoria de sesiones anteriores en el system prompt
        memoria_previa = memory.cargar(nombre)
        self.instrucciones = (
            f"{instrucciones}\n\n{memoria_previa}" if memoria_previa else instrucciones
        )

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        raise NotImplementedError

    def ejecutar(self, tarea: str, contexto: str = "") -> str:
        mensaje_usuario = tarea
        if contexto:
            mensaje_usuario = f"Contexto adicional:\n{contexto}\n\nTarea:\n{tarea}"

        mensajes: list[dict[str, Any]] = [
            {"role": "user", "content": mensaje_usuario}
        ]

        for _ in range(self.max_iteraciones):
            respuesta = self.cliente.messages.create(
                model=self.modelo,
                max_tokens=4096,
                system=self.instrucciones,
                tools=self.herramientas,
                messages=mensajes,
            )

            if respuesta.stop_reason == "end_turn":
                texto_final = self._extraer_texto(respuesta.content)
                self._guardar_memoria(tarea, texto_final)
                return texto_final

            if respuesta.stop_reason == "tool_use":
                mensajes.append({"role": "assistant", "content": respuesta.content})

                resultados_herramientas = []
                for bloque in respuesta.content:
                    if bloque.type == "tool_use":
                        resultado = self.ejecutar_herramienta(bloque.name, bloque.input)
                        resultados_herramientas.append({
                            "type": "tool_result",
                            "tool_use_id": bloque.id,
                            "content": resultado,
                        })

                mensajes.append({"role": "user", "content": resultados_herramientas})
            else:
                break

        texto_final = self._extraer_texto(respuesta.content)
        self._guardar_memoria(tarea, texto_final)
        return texto_final

    def _guardar_memoria(self, tarea: str, respuesta: str) -> None:
        resumen = f"Tarea: {tarea[:150]} | Respuesta: {respuesta[:200]}"
        memory.guardar(self.nombre, resumen)
        # Auto-detectar errores en la respuesta y registrarlos
        resp_lower = respuesta.lower()
        if any(w in resp_lower for w in ["error:", "no se pudo", "falló", "unknown field", "http error"]):
            memory.registrar_error(self.nombre, tarea[:200], respuesta[:300])
        # Auto-detectar aprendizajes cuando la respuesta menciona mejoras
        if any(w in resp_lower for w in ["aprendí", "mejor forma", "optimizado", "próxima vez", "recomiendo"]):
            memory.registrar_aprendizaje(self.nombre, respuesta[:300])

    @staticmethod
    def _extraer_texto(contenido: list) -> str:
        return "\n".join(b.text for b in contenido if hasattr(b, "text"))

    @staticmethod
    def _extraer_texto(contenido: list) -> str:
        partes = []
        for bloque in contenido:
            if hasattr(bloque, "text"):
                partes.append(bloque.text)
        return "\n".join(partes)
