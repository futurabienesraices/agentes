"""Memoria persistente para los agentes — guarda contexto, errores y aprendizajes."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

_MEMORIA_DIR = Path(__file__).parent.parent / "memoria"


def _archivo(agente: str, tipo: str = "sesiones") -> Path:
    _MEMORIA_DIR.mkdir(exist_ok=True)
    nombre = agente.lower().replace(" ", "_")
    return _MEMORIA_DIR / f"{nombre}_{tipo}.json"


def _leer(ruta: Path) -> dict:
    if not ruta.exists():
        return {}
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _escribir(ruta: Path, data: dict) -> None:
    ruta.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Notas curadas (controladas manualmente por el usuario) ────

def agregar_nota(agente: str, titulo: str, contenido: str) -> None:
    """Agrega una nota curada con título. El usuario decide qué guardar aquí."""
    ruta = _archivo(agente, "notas")
    data = _leer(ruta)
    data.setdefault("notas", [])
    data["notas"].append({
        "id": len(data["notas"]) + 1,
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "titulo": titulo.strip()[:60],
        "contenido": contenido.strip()[:500],
    })
    _escribir(ruta, data)


def listar_notas(agente: str) -> list[dict]:
    return _leer(_archivo(agente, "notas")).get("notas", [])


def borrar_nota(agente: str, nota_id: int) -> bool:
    ruta = _archivo(agente, "notas")
    data = _leer(ruta)
    notas = data.get("notas", [])
    nuevas = [n for n in notas if n.get("id") != nota_id]
    if len(nuevas) == len(notas):
        return False
    data["notas"] = nuevas
    _escribir(ruta, data)
    return True


# ── Sesiones (contexto general) ───────────────────────────────

def cargar(agente: str) -> str:
    """Inyecta en el system prompt: notas curadas + sesiones recientes + errores + aprendizajes."""
    partes = []

    # Notas curadas (máxima prioridad — el usuario las controla)
    notas = _leer(_archivo(agente, "notas")).get("notas", [])
    if notas:
        partes.append("=== NOTAS IMPORTANTES ===")
        for n in notas:
            partes.append(f"• [{n['titulo']}] {n['contenido']}")

    # Últimas 2 sesiones (reducido para ahorrar tokens)
    sesiones = _leer(_archivo(agente, "sesiones")).get("entradas", [])
    if sesiones:
        partes.append("\n=== SESIONES RECIENTES ===")
        for e in sesiones[-2:]:
            partes.append(f"[{e['fecha']}] {e['resumen']}")

    # Errores conocidos (máx 3)
    errores = _leer(_archivo(agente, "errores")).get("errores", [])
    if errores:
        partes.append("\n=== ERRORES CONOCIDOS — NO REPETIR ===")
        for e in errores[-3:]:
            partes.append(f"• ERROR: {e['error']} → SOLUCIÓN: {e['solucion']}")

    # Aprendizajes (máx 3)
    aprendizajes = _leer(_archivo(agente, "aprendizajes")).get("aprendizajes", [])
    if aprendizajes:
        partes.append("\n=== MEJORES PRÁCTICAS ===")
        for a in aprendizajes[-3:]:
            partes.append(f"• {a['aprendizaje']}")

    if not partes:
        return ""
    partes.append("=====================================")
    return "\n".join(partes)


def guardar(agente: str, resumen: str) -> None:
    """Guarda resumen de sesión."""
    ruta = _archivo(agente, "sesiones")
    data = _leer(ruta)
    data.setdefault("entradas", [])
    data["entradas"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "resumen": resumen.strip()[:400],
    })
    data["entradas"] = data["entradas"][-20:]
    _escribir(ruta, data)


def registrar_error(agente: str, error: str, solucion: str) -> None:
    """Registra un error y su solución para no repetirlo."""
    ruta = _archivo(agente, "errores")
    data = _leer(ruta)
    data.setdefault("errores", [])
    # No duplicar errores iguales
    errores_existentes = [e["error"] for e in data["errores"]]
    if error[:100] not in [e[:100] for e in errores_existentes]:
        data["errores"].append({
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "error": error.strip()[:300],
            "solucion": solucion.strip()[:300],
        })
        data["errores"] = data["errores"][-50:]
        _escribir(ruta, data)


def registrar_aprendizaje(agente: str, aprendizaje: str) -> None:
    """Registra una mejora o buena práctica descubierta."""
    ruta = _archivo(agente, "aprendizajes")
    data = _leer(ruta)
    data.setdefault("aprendizajes", [])
    data["aprendizajes"].append({
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "aprendizaje": aprendizaje.strip()[:400],
    })
    data["aprendizajes"] = data["aprendizajes"][-30:]
    _escribir(ruta, data)
