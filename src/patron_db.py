"""
Base de datos de patrones aprendidos por los agentes.
Almacena prohibiciones (nunca hacer X) y reglas (cuando X, hacer Y).
Se inyecta automáticamente en el system prompt de cada agente.
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

_PATRON_DIR = Path(__file__).parent.parent / "memoria"
_PATRON_FILE = _PATRON_DIR / "patrones.json"


def _leer() -> dict:
    if not _PATRON_FILE.exists():
        return {"prohibiciones": [], "reglas": []}
    try:
        return json.loads(_PATRON_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"prohibiciones": [], "reglas": []}


def _escribir(data: dict) -> None:
    _PATRON_DIR.mkdir(exist_ok=True)
    _PATRON_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def prohibir(accion: str, razon: str, agente: str = "general") -> None:
    """Registra: nunca hacer X porque causa Y. Evita duplicados."""
    data = _leer()
    data.setdefault("prohibiciones", [])
    existentes = [p["accion"][:80] for p in data["prohibiciones"]]
    if accion[:80] not in existentes:
        data["prohibiciones"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "agente": agente,
            "accion": accion.strip()[:200],
            "razon": razon.strip()[:300],
        })
        data["prohibiciones"] = data["prohibiciones"][-50:]
    _escribir(data)


def aprender(situacion: str, accion: str, agente: str = "general") -> None:
    """Registra: cuando se da X, la acción correcta es Y. Evita duplicados."""
    data = _leer()
    data.setdefault("reglas", [])
    existentes = [r["situacion"][:80] for r in data["reglas"]]
    if situacion[:80] not in existentes:
        data["reglas"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "agente": agente,
            "situacion": situacion.strip()[:200],
            "accion": accion.strip()[:300],
        })
        data["reglas"] = data["reglas"][-50:]
    _escribir(data)


def cargar_para_agente(agente: str) -> str:
    """Devuelve patrones relevantes como texto listo para inyectar en el system prompt."""
    data = _leer()
    partes = []

    prohibiciones = [
        p for p in data.get("prohibiciones", [])
        if p.get("agente") in (agente, "general")
    ]
    if prohibiciones:
        partes.append("=== PROHIBICIONES (nunca hacer esto) ===")
        for p in prohibiciones[-6:]:
            partes.append(f"✗ NUNCA: {p['accion']} — PORQUE: {p['razon']}")

    reglas = [
        r for r in data.get("reglas", [])
        if r.get("agente") in (agente, "general")
    ]
    if reglas:
        partes.append("=== PATRONES APRENDIDOS ===")
        for r in reglas[-6:]:
            partes.append(f"↳ Cuando {r['situacion']} → {r['accion']}")

    return "\n".join(partes)


def listar_todos() -> dict:
    return _leer()
