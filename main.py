#!/usr/bin/env python3
"""
Equipo de Agentes IA — Futura Bienes Raíces
============================================
Punto de entrada principal para interactuar con el equipo de agentes.

Uso:
    python main.py                          # Modo interactivo
    python main.py "texto de la tarea"      # Ejecutar tarea directamente
    python main.py --agente leads "tarea"   # Usar agente específico
"""
from __future__ import annotations
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

AGENTES_DISPONIBLES = {
    "leads": "Gestión de prospectos y CRM",
    "contenido": "Marketing y publicaciones en redes",
    "reportes": "Reportes y análisis del negocio",
    "clientes": "Atención al cliente y consultas",
    "auto": "Enrutamiento automático (por defecto)",
}

BANNER = """
╔══════════════════════════════════════════════════════╗
║        FUTURA BIENES RAÍCES — EQUIPO IA              ║
║  Leads · Contenido · Reportes · Atención al Cliente  ║
╚══════════════════════════════════════════════════════╝
"""


def ejecutar_tarea(tarea: str, agente: str = "auto") -> None:
    from src.agents.orchestrator import Orquestador

    orquestador = Orquestador()

    with console.status("[bold cyan]Procesando...[/bold cyan]", spinner="dots"):
        if agente == "auto":
            respuesta = orquestador.ejecutar(tarea, verbose=False)
        else:
            respuesta = orquestador.ejecutar_con_agente(agente, tarea)

    console.print(Panel(respuesta, title="[bold green]Respuesta del Agente[/bold green]", expand=False))


def modo_interactivo() -> None:
    console.print(BANNER, style="bold cyan")
    console.print("Escribe tu solicitud y el agente correcto la atenderá automáticamente.")
    console.print("Escribe [bold]'salir'[/bold] o presiona Ctrl+C para terminar.\n")

    while True:
        try:
            tarea = console.input("[bold yellow]Tú:[/bold yellow] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n¡Hasta luego!")
            break

        if not tarea:
            continue
        if tarea.lower() in ("salir", "exit", "quit"):
            console.print("¡Hasta luego!")
            break

        try:
            ejecutar_tarea(tarea)
        except Exception as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Equipo de Agentes IA — Futura Bienes Raíces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(
            [f"  {k:10} → {v}" for k, v in AGENTES_DISPONIBLES.items()]
        ),
    )
    parser.add_argument(
        "tarea",
        nargs="?",
        help="Tarea a ejecutar (opcional — si no se proporciona, modo interactivo)",
    )
    parser.add_argument(
        "--agente",
        "-a",
        choices=list(AGENTES_DISPONIBLES.keys()),
        default="auto",
        help="Agente a usar (por defecto: auto)",
    )
    args = parser.parse_args()

    if args.tarea:
        try:
            ejecutar_tarea(args.tarea, agente=args.agente)
        except Exception as exc:
            console.print(f"[bold red]Error:[/bold red] {exc}")
            sys.exit(1)
    else:
        modo_interactivo()


if __name__ == "__main__":
    main()
