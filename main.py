#!/usr/bin/env python3
"""
Equipo de Agentes IA — Futura Bienes Raíces
============================================
Punto de entrada principal para interactuar con el equipo de agentes.

Uso:
    python main.py                                    # Modo interactivo
    python main.py "texto de la tarea"               # Ejecutar tarea directamente
    python main.py --agente trader "analiza AAPL"    # Usar agente específico
"""
from __future__ import annotations
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

AGENTES_DISPONIBLES = {
    # Generales
    "investigador":           "Investiga mercados, apps y tendencias",
    "estratega":              "Ideas de negocio, planes, estrategia empresarial",
    "desarrollador":          "Código, webs, apps, APIs y automatizaciones",
    "marketing":              "Estrategia de marketing para cualquier negocio",
    "analista":               "Reportes, KPIs y análisis financiero",
    "trader":                 "Trading: acciones, cripto, análisis técnico",
    "media":                  "Editor de video, audio, reels, ebooks",
    # Inmobiliaria
    "inmobiliaria_leads":     "CRM: registrar y consultar clientes/prospectos",
    "inmobiliaria_contenido": "Posts y marketing de propiedades en redes",
    "inmobiliaria_clientes":  "Atención al cliente y propiedades disponibles",
    # Auto
    "auto":                   "Enrutamiento automático (por defecto)",
}

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         FUTURA BIENES RAÍCES — EQUIPO IA                     ║
║  Investigador · Estratega · Trader · Media · Inmobiliaria    ║
╚══════════════════════════════════════════════════════════════╝
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
            [f"  {k:25} → {v}" for k, v in AGENTES_DISPONIBLES.items()]
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
        metavar="AGENTE",
        help=f"Agente a usar (por defecto: auto). Opciones: {', '.join(AGENTES_DISPONIBLES.keys())}",
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
