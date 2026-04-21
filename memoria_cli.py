#!/usr/bin/env python3
"""
Gestor de memoria de agentes — agrega, lista y borra notas curadas y patrones.

Uso:
  python memoria_cli.py listar [agente]                          # Ver notas y sesiones
  python memoria_cli.py nota <agente> <titulo> <contenido>       # Agregar nota curada
  python memoria_cli.py borrar <agente> <id>                     # Borrar nota por ID
  python memoria_cli.py limpiar <agente>                         # Borrar sesiones antiguas
  python memoria_cli.py todos                                    # Listar todos los agentes
  python memoria_cli.py patrones                                 # Ver todos los patrones
  python memoria_cli.py prohibir <agente> <accion> <razon>       # Registrar prohibición
  python memoria_cli.py aprender <agente> <situacion> <accion>   # Registrar patrón

Ejemplos:
  python memoria_cli.py listar marketing
  python memoria_cli.py nota marketing "Casa Trébol" "Casa en venta $100,000 USD, 3hab, 2baños"
  python memoria_cli.py borrar marketing 2
  python memoria_cli.py patrones
  python memoria_cli.py prohibir media "llamar video_cortar antes de video_crear_profesional" "duplica trabajo"
  python memoria_cli.py aprender media "videos iPhone HEVC fallan en MoviePy" "usar previews .mp4 de output/ o transcodificar primero"
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
_MEMORIA_DIR = Path(__file__).parent / "memoria"


def cmd_listar(agente: str) -> None:
    from src import memory

    console.print(f"\n[bold cyan]Memoria del agente:[/bold cyan] {agente}\n")

    # Notas curadas
    notas = memory.listar_notas(agente)
    if notas:
        tabla = Table(title="Notas curadas", box=box.ROUNDED, show_lines=True)
        tabla.add_column("ID", style="dim", width=4)
        tabla.add_column("Título", style="bold")
        tabla.add_column("Contenido")
        tabla.add_column("Fecha", style="dim", width=12)
        for n in notas:
            tabla.add_row(str(n["id"]), n["titulo"], n["contenido"][:80], n.get("fecha", ""))
        console.print(tabla)
    else:
        console.print("[dim]Sin notas curadas.[/dim]")

    # Últimas sesiones automáticas
    ruta_sesiones = _MEMORIA_DIR / f"{agente.lower().replace(' ', '_')}_sesiones.json"
    if ruta_sesiones.exists():
        data = json.loads(ruta_sesiones.read_text(encoding="utf-8"))
        sesiones = data.get("entradas", [])
        if sesiones:
            console.print(f"\n[bold]Sesiones automáticas:[/bold] {len(sesiones)} registradas (últimas 3):")
            for e in sesiones[-3:]:
                console.print(f"  [{e['fecha']}] {e['resumen'][:120]}")
    console.print()


def cmd_todos() -> None:
    if not _MEMORIA_DIR.exists():
        console.print("[dim]No hay memoria guardada todavía.[/dim]")
        return

    agentes: set[str] = set()
    for f in _MEMORIA_DIR.iterdir():
        if f.suffix == ".json":
            partes = f.stem.rsplit("_", 1)
            if len(partes) == 2:
                agentes.add(partes[0])

    if not agentes:
        console.print("[dim]No hay memoria guardada todavía.[/dim]")
        return

    console.print("\n[bold cyan]Agentes con memoria guardada:[/bold cyan]\n")
    for a in sorted(agentes):
        archivos = list(_MEMORIA_DIR.glob(f"{a}_*.json"))
        tipos = [f.stem.split("_")[-1] for f in archivos]
        console.print(f"  [bold]{a}[/bold] — {', '.join(tipos)}")
    console.print()


def cmd_nota(agente: str, titulo: str, contenido: str) -> None:
    from src import memory
    memory.agregar_nota(agente, titulo, contenido)
    console.print(f"[green]✓[/green] Nota guardada para [bold]{agente}[/bold]: [{titulo}]")


def cmd_borrar(agente: str, nota_id: int) -> None:
    from src import memory
    ok = memory.borrar_nota(agente, nota_id)
    if ok:
        console.print(f"[green]✓[/green] Nota #{nota_id} borrada de [bold]{agente}[/bold].")
    else:
        console.print(f"[red]No se encontró nota #{nota_id} para {agente}.[/red]")


def cmd_limpiar(agente: str) -> None:
    ruta = _MEMORIA_DIR / f"{agente.lower().replace(' ', '_')}_sesiones.json"
    if ruta.exists():
        ruta.write_text('{"entradas": []}', encoding="utf-8")
        console.print(f"[green]✓[/green] Sesiones automáticas de [bold]{agente}[/bold] eliminadas.")
    else:
        console.print(f"[dim]No hay sesiones guardadas para {agente}.[/dim]")


def cmd_patrones() -> None:
    from src import patron_db
    data = patron_db.listar_todos()

    prohibiciones = data.get("prohibiciones", [])
    reglas = data.get("reglas", [])

    if not prohibiciones and not reglas:
        console.print("[dim]No hay patrones registrados todavía.[/dim]")
        return

    if prohibiciones:
        tabla = Table(title="Prohibiciones (nunca hacer esto)", box=box.ROUNDED, show_lines=True)
        tabla.add_column("Agente", style="dim", width=10)
        tabla.add_column("Nunca hacer", style="bold red")
        tabla.add_column("Porque", style="yellow")
        tabla.add_column("Fecha", style="dim", width=12)
        for p in prohibiciones:
            tabla.add_row(p.get("agente","?"), p["accion"][:60], p["razon"][:60], p.get("fecha",""))
        console.print(tabla)

    if reglas:
        tabla = Table(title="Patrones aprendidos", box=box.ROUNDED, show_lines=True)
        tabla.add_column("Agente", style="dim", width=10)
        tabla.add_column("Cuando", style="bold cyan")
        tabla.add_column("Hacer", style="green")
        tabla.add_column("Fecha", style="dim", width=12)
        for r in reglas:
            tabla.add_row(r.get("agente","?"), r["situacion"][:60], r["accion"][:60], r.get("fecha",""))
        console.print(tabla)


def cmd_prohibir(agente: str, accion: str, razon: str) -> None:
    from src import patron_db
    patron_db.prohibir(accion, razon, agente)
    console.print(f"[green]✓[/green] Prohibición registrada para [bold]{agente}[/bold].")


def cmd_aprender(agente: str, situacion: str, accion: str) -> None:
    from src import patron_db
    patron_db.aprender(situacion, accion, agente)
    console.print(f"[green]✓[/green] Patrón registrado para [bold]{agente}[/bold].")


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        console.print(__doc__)
        return

    comando = args[0]

    if comando == "todos":
        cmd_todos()

    elif comando == "listar":
        agente = args[1] if len(args) > 1 else None
        if not agente:
            cmd_todos()
        else:
            cmd_listar(agente)

    elif comando == "nota":
        if len(args) < 4:
            console.print("[red]Uso: python memoria_cli.py nota <agente> <titulo> <contenido>[/red]")
            sys.exit(1)
        cmd_nota(args[1], args[2], args[3])

    elif comando == "borrar":
        if len(args) < 3:
            console.print("[red]Uso: python memoria_cli.py borrar <agente> <id>[/red]")
            sys.exit(1)
        try:
            cmd_borrar(args[1], int(args[2]))
        except ValueError:
            console.print("[red]El ID debe ser un número entero.[/red]")
            sys.exit(1)

    elif comando == "limpiar":
        if len(args) < 2:
            console.print("[red]Uso: python memoria_cli.py limpiar <agente>[/red]")
            sys.exit(1)
        cmd_limpiar(args[1])

    elif comando == "patrones":
        cmd_patrones()

    elif comando == "prohibir":
        if len(args) < 4:
            console.print("[red]Uso: python memoria_cli.py prohibir <agente> <accion> <razon>[/red]")
            sys.exit(1)
        cmd_prohibir(args[1], args[2], args[3])

    elif comando == "aprender":
        if len(args) < 4:
            console.print("[red]Uso: python memoria_cli.py aprender <agente> <situacion> <accion>[/red]")
            sys.exit(1)
        cmd_aprender(args[1], args[2], args[3])

    else:
        console.print(f"[red]Comando desconocido: {comando}[/red]")
        console.print("Comandos: listar, nota, borrar, limpiar, todos, patrones, prohibir, aprender")
        sys.exit(1)


if __name__ == "__main__":
    main()
