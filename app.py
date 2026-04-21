"""
Interfaz web para el equipo de agentes IA — Futura Bienes Raíces + Futura Cleaning.
Ejecutar: python app.py  →  abrir http://localhost:5000
"""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ── Historial por agente ──────────────────────────────────────────
_HIST_DIR = Path(__file__).parent / "memoria" / "historial"
_HIST_DIR.mkdir(parents=True, exist_ok=True)


def _cargar_hist(agente: str) -> list:
    ruta = _HIST_DIR / f"{agente}.json"
    if ruta.exists():
        try:
            return json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _guardar_hist(agente: str, msgs: list) -> None:
    ruta = _HIST_DIR / f"{agente}.json"
    ruta.write_text(
        json.dumps(msgs[-200:], ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ── Metadatos de los agentes ──────────────────────────────────────
AGENTES_INFO: dict[str, dict] = {
    "auto":                   {"emoji": "🔀", "nombre": "Auto",        "desc": "El orquestador elige el agente correcto"},
    "investigador":           {"emoji": "🔍", "nombre": "Investigador","desc": "Mercados, tendencias, datos, competidores"},
    "estratega":              {"emoji": "💡", "nombre": "Estratega",   "desc": "Planes de negocio, ideas, oportunidades"},
    "desarrollador":          {"emoji": "💻", "nombre": "Desarrollador","desc": "Código, apps, APIs, automatizaciones"},
    "marketing":              {"emoji": "📣", "nombre": "Marketing",   "desc": "Copies, redes sociales, anuncios"},
    "analista":               {"emoji": "📊", "nombre": "Analista",    "desc": "Reportes, KPIs, métricas, finanzas"},
    "trader":                 {"emoji": "📈", "nombre": "Trader",      "desc": "Acciones, cripto, análisis técnico"},
    "media":                  {"emoji": "🎬", "nombre": "Media",       "desc": "Videos, reels, edición, ebooks"},
    "inmobiliaria_leads":     {"emoji": "👥", "nombre": "Leads",       "desc": "CRM de prospectos inmobiliarios"},
    "inmobiliaria_contenido": {"emoji": "📱", "nombre": "Contenido",   "desc": "Posts y marketing de propiedades"},
    "inmobiliaria_clientes":  {"emoji": "🤝", "nombre": "Clientes",    "desc": "Atención al cliente inmobiliaria"},
}


# ── Rutas ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", agentes=AGENTES_INFO)


@app.route("/api/agentes")
def api_agentes():
    resultado = {}
    for key, info in AGENTES_INFO.items():
        hist = _cargar_hist(key)
        msgs_agente = [m for m in hist if m["rol"] == "agente"]
        ultimo_txt = msgs_agente[-1]["texto"][:55] + "…" if msgs_agente else info["desc"]
        ultima_hora = msgs_agente[-1].get("hora", "") if msgs_agente else ""
        resultado[key] = {
            **info,
            "ultimo": ultimo_txt,
            "hora": ultima_hora,
            "total": len([m for m in hist if m["rol"] == "usuario"]),
        }
    return jsonify(resultado)


@app.route("/api/historial/<agente>")
def api_historial(agente: str):
    return jsonify(_cargar_hist(agente))


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json or {}
    agente = data.get("agente", "auto")
    tarea  = (data.get("tarea") or "").strip()
    if not tarea:
        return jsonify({"error": "Tarea vacía"}), 400

    hora = datetime.now().strftime("%H:%M")
    hist = _cargar_hist(agente)
    hist.append({"rol": "usuario", "texto": tarea, "hora": hora})

    try:
        from src.agents.orchestrator import Orquestador
        orq = Orquestador()
        if agente == "auto":
            resultado = orq.ejecutar(tarea, verbose=False)
        else:
            resultado = orq.ejecutar_con_agente(agente, tarea)
    except Exception as exc:
        resultado = f"Error: {exc}"

    hora_resp = datetime.now().strftime("%H:%M")
    hist.append({"rol": "agente", "agente": agente, "texto": resultado, "hora": hora_resp})
    _guardar_hist(agente, hist)

    return jsonify({"respuesta": resultado, "hora": hora_resp})


@app.route("/api/historial/<agente>", methods=["DELETE"])
def api_borrar_historial(agente: str):
    ruta = _HIST_DIR / f"{agente}.json"
    if ruta.exists():
        ruta.unlink()
    return jsonify({"ok": True})


@app.route("/api/pipeline/<nombre>", methods=["POST"])
def api_pipeline(nombre: str):
    tarea = (request.json or {}).get("tarea", "")
    try:
        from src.agents.orchestrator import Orquestador
        resultado = Orquestador().ejecutar_pipeline(nombre, tarea)
        return jsonify({"respuesta": resultado})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


if __name__ == "__main__":
    print("🤖 Iniciando interfaz web de agentes en http://localhost:5000")
    app.run(debug=False, port=5000, threaded=True)
