"""
Caché de resultados de herramientas — evita repetir llamadas costosas a APIs.
Cada resultado se guarda con un TTL (tiempo de vida). Pasado ese tiempo, se repite la llamada.

TTLs por herramienta:
  - media_listar, drive_listar: 1 hora (los archivos no cambian en segundos)
  - airtable_listar_*: 15 min (datos del negocio cambian poco)
  - web_buscar: 6 horas (las tendencias no cambian cada minuto)
  - social_insights_*: 30 min
"""
from __future__ import annotations
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

_CACHE_DIR = Path(__file__).parent.parent / ".cache_herramientas"

# TTL en minutos por prefijo de herramienta
_TTL: dict[str, int] = {
    "video_analizar":       1440,  # 24h — el análisis es permanente (video_db)
    "video_info":           1440,  # 24h — metadata del archivo no cambia
    "media_indexados":      1440,  # 24h — refleja video_db
    "media_listar":         60,
    "drive_listar":         60,
    "airtable_listar":      15,
    "airtable_buscar":      15,
    "web_buscar":           360,
    "web_noticias":         120,
    "social_insights":      30,
    "social_estadisticas":  30,
}

_TTL_DEFAULT = 10  # minutos para todo lo demás


def _ttl_para(nombre_herramienta: str) -> int:
    for prefijo, minutos in _TTL.items():
        if nombre_herramienta.startswith(prefijo):
            return minutos
    return _TTL_DEFAULT


def _clave(nombre: str, params: dict) -> str:
    contenido = nombre + json.dumps(params, sort_keys=True)
    return hashlib.md5(contenido.encode()).hexdigest()


def _ruta(clave: str) -> Path:
    _CACHE_DIR.mkdir(exist_ok=True)
    return _CACHE_DIR / f"{clave}.json"


def obtener(nombre: str, params: dict) -> str | None:
    """Devuelve el resultado cacheado si está vigente, None si expiró o no existe."""
    ruta = _ruta(_clave(nombre, params))
    if not ruta.exists():
        return None
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        guardado = datetime.fromisoformat(data["fecha"])
        ttl = timedelta(minutes=_ttl_para(nombre))
        if datetime.now() - guardado > ttl:
            ruta.unlink(missing_ok=True)
            return None
        return data["resultado"]
    except Exception:
        return None


def guardar(nombre: str, params: dict, resultado: str) -> None:
    """Guarda el resultado en caché."""
    ruta = _ruta(_clave(nombre, params))
    try:
        ruta.write_text(
            json.dumps(
                {"herramienta": nombre, "params": params, "resultado": resultado,
                 "fecha": datetime.now().isoformat()},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def limpiar(patron: str = "*") -> int:
    """Borra entradas de caché. patron='media_*' borra solo las de media."""
    _CACHE_DIR.mkdir(exist_ok=True)
    borrados = 0
    for f in _CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            nombre = data.get("herramienta", "")
            if patron == "*" or nombre.startswith(patron.rstrip("*")):
                f.unlink()
                borrados += 1
        except Exception:
            pass
    return borrados
