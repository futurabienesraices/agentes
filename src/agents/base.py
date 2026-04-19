"""Clase base para todos los agentes del equipo."""
from __future__ import annotations
from typing import Any
import anthropic
from src.config import ANTHROPIC_API_KEY, MODELO_PRINCIPAL


class AgenteBase:
    """
    Agente base que implementa el loop de herramientas (tool-use loop) de Claude.
    Cada agente especializado hereda de esta clase y define sus propias herramientas.
    """

    def __init__(self, nombre: str, instrucciones: str, herramientas: list[dict]):
        self.nombre = nombre
        self.instrucciones = instrucciones
        self.herramientas = herramientas
        self.cliente = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.modelo = MODELO_PRINCIPAL
        self.max_iteraciones = 10

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        """Ejecuta una herramienta por nombre. Debe implementarse en cada agente."""
        raise NotImplementedError

    def ejecutar(self, tarea: str, contexto: str = "") -> str:
        """
        Ejecuta una tarea con el agente usando el loop de tool-use de Claude.
        Devuelve el texto final de la respuesta.
        """
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

            # Si el modelo terminó sin llamar herramientas, devolver texto
            if respuesta.stop_reason == "end_turn":
                return self._extraer_texto(respuesta.content)

            # Si hay tool_use, ejecutar las herramientas y continuar
            if respuesta.stop_reason == "tool_use":
                # Agregar respuesta del asistente al historial
                mensajes.append({"role": "assistant", "content": respuesta.content})

                # Ejecutar cada herramienta solicitada
                resultados_herramientas = []
                for bloque in respuesta.content:
                    if bloque.type == "tool_use":
                        resultado = self.ejecutar_herramienta(bloque.name, bloque.input)
                        resultados_herramientas.append({
                            "type": "tool_result",
                            "tool_use_id": bloque.id,
                            "content": resultado,
                        })

                # Agregar resultados al historial
                mensajes.append({"role": "user", "content": resultados_herramientas})
            else:
                # stop_reason inesperado
                break

        return self._extraer_texto(respuesta.content)

    @staticmethod
    def _extraer_texto(contenido: list) -> str:
        partes = []
        for bloque in contenido:
            if hasattr(bloque, "text"):
                partes.append(bloque.text)
        return "\n".join(partes)
