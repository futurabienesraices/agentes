"""
Índice permanente de videos analizados.
Guarda el resultado del análisis usando una huella del contenido del archivo
(primeros 64KB en MD5) como clave — así el índice sobrevive renombrados.
"""
from __future__ import annotations
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

_INDICE = Path(__file__).parent.parent / "media" / "video_index.json"


def _leer() -> dict:
    if not _INDICE.exists():
        return {}
    try:
        return json.loads(_INDICE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _escribir(data: dict) -> None:
    _INDICE.parent.mkdir(parents=True, exist_ok=True)
    _INDICE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _clave(ruta_archivo: str) -> str:
    """Huella del contenido: MD5 de los primeros 64KB + tamaño total.
    Sobrevive renombrados. Si el archivo cambia, la clave cambia."""
    try:
        size = os.path.getsize(ruta_archivo)
        with open(ruta_archivo, "rb") as f:
            muestra = f.read(65536)  # primeros 64KB
        h = hashlib.md5(muestra).hexdigest()[:12]
        return f"{h}:{size}"
    except Exception:
        return Path(ruta_archivo).name


def obtener_analisis(ruta_archivo: str, tipo_analisis: str = "general") -> str | None:
    """Devuelve el análisis guardado para este video, o None si no existe."""
    data = _leer()
    clave = _clave(ruta_archivo)
    entrada = data.get(clave, {})
    return entrada.get(f"analisis_{tipo_analisis}")


def guardar_analisis(ruta_archivo: str, tipo_analisis: str, resultado: str) -> None:
    """Guarda el análisis de un video permanentemente."""
    data = _leer()
    clave = _clave(ruta_archivo)
    if clave not in data:
        data[clave] = {
            "nombre": Path(ruta_archivo).name,
            "primera_vez": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        try:
            data[clave]["tamaño_mb"] = round(os.path.getsize(ruta_archivo) / 1024 / 1024, 1)
        except Exception:
            pass
    # Actualizar nombre siempre (puede haber sido renombrado)
    data[clave]["nombre"] = Path(ruta_archivo).name
    data[clave][f"analisis_{tipo_analisis}"] = resultado
    data[clave]["ultima_vez"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _escribir(data)


def obtener_info(ruta_archivo: str) -> str | None:
    """Devuelve la info técnica guardada (duración, resolución, etc.)."""
    data = _leer()
    return data.get(_clave(ruta_archivo), {}).get("info_tecnica")


def guardar_info(ruta_archivo: str, info: str) -> None:
    """Guarda la info técnica de un video permanentemente."""
    data = _leer()
    clave = _clave(ruta_archivo)
    if clave not in data:
        data[clave] = {
            "nombre": Path(ruta_archivo).name,
            "primera_vez": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
    data[clave]["nombre"] = Path(ruta_archivo).name
    data[clave]["info_tecnica"] = info
    data[clave]["ultima_vez"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _escribir(data)


def listar_indexados() -> str:
    """Lista todos los videos que ya están en el índice."""
    data = _leer()
    if not data:
        return "No hay videos indexados todavía."
    lineas = [f"Videos indexados: {len(data)}\n"]
    for entrada in data.values():
        nombre = entrada.get("nombre", "?")
        mb = entrada.get("tamaño_mb", "?")
        tipos = [k.replace("analisis_", "") for k in entrada if k.startswith("analisis_")]
        tiene_info = "✓" if entrada.get("info_tecnica") else "—"
        lineas.append(
            f"  {nombre} ({mb} MB) | info:{tiene_info} | análisis:{','.join(tipos) or '—'}"
        )
    return "\n".join(lineas)
