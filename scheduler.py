#!/usr/bin/env python3
"""
Programador de tareas automáticas — Futura Bienes Raíces + Futura Cleaning
Corre en segundo plano y ejecuta publicaciones diarias a la hora configurada.

Uso:
  python scheduler.py              # Inicia el scheduler (corre en segundo plano)
  python scheduler.py --ahora      # Ejecuta la tarea inmediatamente (para probar)

Para que corra siempre, ejecuta con nohup:
  nohup python scheduler.py > logs/scheduler.log 2>&1 &
"""
from __future__ import annotations
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

import schedule

# ── Configuración ─────────────────────────────────────────────
HORA_PUBLICACION = "08:00"   # Hora local del servidor
HORA_CONTENIDO   = "07:00"   # Generación de carousel + video (1h antes)
PYTHON = sys.executable
PROYECTO = Path(__file__).parent

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scheduler.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def tarea_contenido_diario() -> None:
    """Genera carousel + video Reel para las redes sociales del día."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info(f"Generando contenido diario — {fecha}")

    for empresa in ["fbr", "fc"]:
        resultado = subprocess.run(
            [PYTHON, "content_daily.py", "--empresa", empresa, "--tipo", "ambos"],
            cwd=str(PROYECTO),
            capture_output=True,
            text=True,
            timeout=600,   # 10 minutos máximo (los videos tardan más)
        )
        if resultado.returncode == 0:
            log.info(f"✅ Contenido generado OK — {empresa.upper()} — {fecha}")
        else:
            log.error(f"❌ Error contenido {empresa.upper()} — {fecha}")
            log.error(resultado.stderr[-500:] if resultado.stderr else "(sin stderr)")


def tarea_diaria() -> None:
    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info(f"Iniciando publicación automática — {fecha}")

    resultado = subprocess.run(
        [PYTHON, "reporte_diario.py", "--publicar"],
        cwd=str(PROYECTO),
        capture_output=True,
        text=True,
        timeout=300,   # 5 minutos máximo
    )

    if resultado.returncode == 0:
        log.info(f"Publicación completada OK — {fecha}")
    else:
        log.error(f"Error en publicación — {fecha}")
        log.error(resultado.stderr[-500:] if resultado.stderr else "(sin stderr)")


def main() -> None:
    if "--ahora" in sys.argv:
        log.info("Ejecutando tareas ahora (modo prueba)...")
        tarea_contenido_diario()
        tarea_diaria()
        return

    log.info(f"Scheduler iniciado")
    log.info(f"  → Contenido diario (carousel + video): {HORA_CONTENIDO}")
    log.info(f"  → Publicación automática: {HORA_PUBLICACION}")

    schedule.every().day.at(HORA_CONTENIDO).do(tarea_contenido_diario)
    schedule.every().day.at(HORA_PUBLICACION).do(tarea_diaria)

    # Mostrar próxima ejecución
    proxima = schedule.next_run()
    if proxima:
        log.info(f"Próxima ejecución: {proxima.strftime('%Y-%m-%d %H:%M')}")

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
