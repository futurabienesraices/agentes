"""Memoria persistente para los agentes — guarda contexto entre sesiones."""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path

_MEMORIA_DIR = Path(__file__).parent.parent / "memoria"


def _archivo(agente: str) -> Path:
    _MEMORIA_DIR.mkdir(exist_ok=True)
    return _MEMORIA_DIR / f"{agente.lower().replace(' ', '_')}.json"


def cargar(agente: str) -> str:
    """Devuelve el contexto guardado como string para inyectar en el system prompt."""
    ruta = _archivo(agente)
    if not ruta.exists():
        return ""
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        entradas = data.get("entradas", [])
        if not entradas:
            return ""
        # Solo las últimas 5 entradas para no inflar el prompt
        recientes = entradas[-5:]
        lineas = ["=== MEMORIA DE SESIONES ANTERIORES ==="]
        for e in recientes:
            lineas.append(f"[{e['fecha']}] {e['resumen']}")
        lineas.append("======================================")
        return "\n".join(lineas)
    except Exception:
        return ""


def guardar(agente: str, resumen: str) -> None:
    """Guarda un resumen de la sesión actual."""
    ruta = _archivo(agente)
    data: dict = {"entradas": []}
    if ruta.exists():
        try:
            data = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            pass
    data.setdefault("entradas", [])
    data["entradas"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resumen": resumen.strip()[:500],  # máx 500 chars por entrada
    })
    # Mantener solo las últimas 20 entradas
    data["entradas"] = data["entradas"][-20:]
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
