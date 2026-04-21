#!/usr/bin/env python3
"""
Reporte diario de redes sociales — Futura Bienes Raíces + Futura Cleaning
Ejecutar cada mañana: python reporte_diario.py
"""
from __future__ import annotations
import sys
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()


def main() -> None:
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")

    console.print()
    console.print(Rule(f"[bold cyan]Reporte Diario — {fecha}  {hora}[/bold cyan]"))
    console.print("[dim]Investigando tendencias y revisando métricas de redes sociales...[/dim]\n")

    from src.agents.orchestrator import Orquestador

    tarea = (
        f"HOY es {fecha}. Genera el reporte diario completo de redes sociales para ambos negocios.\n"
        "1. Consulta los últimos posts de Facebook e Instagram con sus métricas\n"
        "2. Analiza qué tipo de contenido está funcionando mejor\n"
        "3. Con las tendencias del Investigador, crea el plan de contenido de HOY y MAÑANA\n"
        "4. Incluye captions listos para copiar/pegar para cada post sugerido\n"
        "Separa siempre FUTURA CLEANING de FUTURA BIENES RAÍCES en el reporte."
    )

    orq = Orquestador()

    try:
        with console.status(
            "[bold cyan]Analizando tendencias y métricas...[/bold cyan]", spinner="dots"
        ):
            resultado = orq.ejecutar_pipeline("daily-brief", tarea, verbose=False)
    except Exception as exc:
        console.print(f"[bold red]Error al generar el reporte:[/bold red] {exc}")
        sys.exit(1)

    console.print(
        Panel(resultado, title=f"[bold green]Reporte {fecha}[/bold green]", expand=False)
    )

    # Guardar en archivo
    carpeta = Path("reportes")
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"{fecha}.md"
    archivo.write_text(f"# Reporte Diario — {fecha}\n\n{resultado}", encoding="utf-8")
    console.print(f"\n[dim]Reporte guardado en: reportes/{fecha}.md[/dim]")


if __name__ == "__main__":
    main()
