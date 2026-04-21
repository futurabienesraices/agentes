#!/usr/bin/env python3
"""
Reporte y publicación diaria — Futura Bienes Raíces + Futura Cleaning

Uso:
  python reporte_diario.py                 # Solo genera el reporte
  python reporte_diario.py --publicar      # Genera el reporte Y publica en Facebook
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
    publicar = "--publicar" in sys.argv
    fecha = datetime.now().strftime("%Y-%m-%d")
    hora = datetime.now().strftime("%H:%M")

    console.print()
    console.print(Rule(f"[bold cyan]{'Publicación' if publicar else 'Reporte'} Diaria — {fecha}  {hora}[/bold cyan]"))
    if publicar:
        console.print("[dim]Investigando tendencias, generando contenido y publicando en redes...[/dim]\n")
    else:
        console.print("[dim]Investigando tendencias y revisando métricas de redes sociales...[/dim]\n")

    from src.agents.orchestrator import Orquestador

    if publicar:
        pipeline = "publicar-diario"
        tarea = (
            f"HOY es {fecha}. Haz lo siguiente en orden:\n"
            "1. Usa social_insights_posts_fb para ver los últimos posts de Facebook y su rendimiento\n"
            "2. Usa social_insights_posts_ig para ver los últimos posts de Instagram\n"
            "3. Usa social_insights_cuenta_ig para ver el total de seguidores actual\n"
            "4. Con las tendencias del Investigador + las métricas obtenidas, crea DOS posts:\n"
            "   POST A — FUTURA BIENES RAÍCES: caption profesional + hashtags para El Salvador\n"
            "   POST B — FUTURA CLEANING: caption llamativo + hashtags para El Salvador\n"
            "5. Publica el POST A en Facebook usando social_publicar_facebook\n"
            "6. Devuelve un resumen con: métricas actuales, los dos posts creados, "
            "   y confirma qué se publicó. Incluye los captions completos listos para copiar en Instagram/TikTok."
        )
    else:
        pipeline = "daily-brief"
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
            "[bold cyan]Procesando...[/bold cyan]", spinner="dots"
        ):
            resultado = orq.ejecutar_pipeline(pipeline, tarea, verbose=False)
    except Exception as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        sys.exit(1)

    titulo = f"[bold green]{'Publicación' if publicar else 'Reporte'} {fecha}[/bold green]"
    console.print(Panel(resultado, title=titulo, expand=False))

    # Guardar en archivo
    carpeta = Path("reportes")
    carpeta.mkdir(exist_ok=True)
    prefijo = "publicacion" if publicar else "reporte"
    archivo = carpeta / f"{fecha}_{prefijo}.md"
    encabezado = f"# {'Publicación' if publicar else 'Reporte'} Diario — {fecha}\n\n"
    archivo.write_text(encabezado + resultado, encoding="utf-8")
    console.print(f"\n[dim]Guardado en: reportes/{archivo.name}[/dim]")


if __name__ == "__main__":
    main()
