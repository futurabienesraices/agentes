"""Herramientas para interactuar con Airtable."""
from __future__ import annotations
import json
from typing import Any
from src.config import (
    AIRTABLE_API_KEY, AIRTABLE_BASE_ID,
    AIRTABLE_LEADS_TABLE, AIRTABLE_PROPIEDADES_TABLE, AIRTABLE_CLIENTES_TABLE,
)


def _get_table(nombre_tabla: str):
    from pyairtable import Api
    api = Api(AIRTABLE_API_KEY)
    return api.table(AIRTABLE_BASE_ID, nombre_tabla)


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_AIRTABLE: list[dict] = [
    {
        "name": "airtable_listar_leads",
        "description": (
            "Lista los leads (prospectos) del CRM en Airtable. "
            "Puedes filtrar por estado: Nuevo, Contactado, Calificado, Propuesta, Cerrado, Perdido."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado del lead (opcional)",
                    "enum": ["Nuevo", "Contactado", "Calificado", "Propuesta", "Cerrado", "Perdido"],
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad máxima de registros a devolver (por defecto 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "airtable_crear_lead",
        "description": "Crea un nuevo lead (prospecto) en el CRM de Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre completo del prospecto"},
                "telefono": {"type": "string", "description": "Teléfono de contacto"},
                "email": {"type": "string", "description": "Correo electrónico"},
                "interes": {"type": "string", "description": "Qué tipo de propiedad busca o le interesa"},
                "presupuesto": {"type": "string", "description": "Presupuesto aproximado"},
                "origen": {
                    "type": "string",
                    "description": "Cómo llegó el lead",
                    "enum": ["Instagram", "Facebook", "WhatsApp", "Referido", "Portal", "Otro"],
                },
                "notas": {"type": "string", "description": "Notas adicionales sobre el lead"},
            },
            "required": ["nombre"],
        },
    },
    {
        "name": "airtable_actualizar_lead",
        "description": "Actualiza el estado o información de un lead existente en Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "ID del registro en Airtable (rec...)"},
                "estado": {
                    "type": "string",
                    "description": "Nuevo estado del lead",
                    "enum": ["Nuevo", "Contactado", "Calificado", "Propuesta", "Cerrado", "Perdido"],
                },
                "notas": {"type": "string", "description": "Notas adicionales a agregar"},
                "siguiente_accion": {"type": "string", "description": "Próxima acción a realizar"},
            },
            "required": ["record_id"],
        },
    },
    {
        "name": "airtable_listar_propiedades",
        "description": "Lista las propiedades disponibles en el inventario de Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "description": "Tipo de propiedad (opcional)",
                    "enum": ["Casa", "Departamento", "Terreno", "Local", "Oficina", "Bodega"],
                },
                "operacion": {
                    "type": "string",
                    "description": "Tipo de operación (opcional)",
                    "enum": ["Venta", "Renta"],
                },
                "precio_max": {"type": "number", "description": "Precio máximo en pesos (opcional)"},
                "limite": {"type": "integer", "description": "Límite de resultados", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_reporte_leads",
        "description": "Genera un resumen estadístico de los leads: total por estado, origen, conversión.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    """Ejecuta una herramienta de Airtable y devuelve el resultado como string."""
    handlers = {
        "airtable_listar_leads": _listar_leads,
        "airtable_crear_lead": _crear_lead,
        "airtable_actualizar_lead": _actualizar_lead,
        "airtable_listar_propiedades": _listar_propiedades,
        "airtable_reporte_leads": _reporte_leads,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _listar_leads(estado: str | None = None, limite: int = 20) -> str:
    tabla = _get_table(AIRTABLE_LEADS_TABLE)
    formula = f"{{Estado}}='{estado}'" if estado else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron leads con esos criterios."
    resultado = []
    for r in registros:
        f = r["fields"]
        resultado.append(
            f"• [{r['id']}] {f.get('Nombre', '—')} | "
            f"Tel: {f.get('Telefono', '—')} | "
            f"Estado: {f.get('Estado', '—')} | "
            f"Origen: {f.get('Origen', '—')}"
        )
    return f"Leads encontrados ({len(resultado)}):\n" + "\n".join(resultado)


def _crear_lead(
    nombre: str,
    telefono: str = "",
    email: str = "",
    interes: str = "",
    presupuesto: str = "",
    origen: str = "Otro",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_LEADS_TABLE)
    campos: dict[str, Any] = {
        "Nombre": nombre,
        "Estado": "Nuevo",
        "Origen": origen,
    }
    if telefono:
        campos["Telefono"] = telefono
    if email:
        campos["Email"] = email
    if interes:
        campos["Interes"] = interes
    if presupuesto:
        campos["Presupuesto"] = presupuesto
    if notas:
        campos["Notas"] = notas
    registro = tabla.create(campos)
    return f"Lead creado exitosamente. ID: {registro['id']} | Nombre: {nombre}"


def _actualizar_lead(
    record_id: str,
    estado: str | None = None,
    notas: str | None = None,
    siguiente_accion: str | None = None,
) -> str:
    tabla = _get_table(AIRTABLE_LEADS_TABLE)
    campos: dict[str, Any] = {}
    if estado:
        campos["Estado"] = estado
    if notas:
        campos["Notas"] = notas
    if siguiente_accion:
        campos["SiguienteAccion"] = siguiente_accion
    if not campos:
        return "No se proporcionaron campos para actualizar."
    tabla.update(record_id, campos)
    return f"Lead {record_id} actualizado correctamente."


def _listar_propiedades(
    tipo: str | None = None,
    operacion: str | None = None,
    precio_max: float | None = None,
    limite: int = 10,
) -> str:
    tabla = _get_table(AIRTABLE_PROPIEDADES_TABLE)
    partes_formula = []
    if tipo:
        partes_formula.append(f"{{Tipo}}='{tipo}'")
    if operacion:
        partes_formula.append(f"{{Operacion}}='{operacion}'")
    if precio_max:
        partes_formula.append(f"{{Precio}}<={precio_max}")
    formula = f"AND({', '.join(partes_formula)})" if partes_formula else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron propiedades con esos criterios."
    resultado = []
    for r in registros:
        f = r["fields"]
        resultado.append(
            f"• {f.get('Titulo', '—')} | "
            f"Tipo: {f.get('Tipo', '—')} | "
            f"Op: {f.get('Operacion', '—')} | "
            f"Precio: ${f.get('Precio', 0):,.0f} | "
            f"Zona: {f.get('Zona', '—')}"
        )
    return f"Propiedades ({len(resultado)}):\n" + "\n".join(resultado)


def _reporte_leads() -> str:
    tabla = _get_table(AIRTABLE_LEADS_TABLE)
    todos = tabla.all()
    if not todos:
        return "No hay leads en el sistema."
    conteos: dict[str, int] = {}
    origenes: dict[str, int] = {}
    for r in todos:
        estado = r["fields"].get("Estado", "Sin estado")
        origen = r["fields"].get("Origen", "Sin origen")
        conteos[estado] = conteos.get(estado, 0) + 1
        origenes[origen] = origenes.get(origen, 0) + 1
    total = len(todos)
    cerrados = conteos.get("Cerrado", 0)
    conversion = f"{(cerrados/total*100):.1f}%" if total > 0 else "0%"
    lineas = [
        f"Total leads: {total}",
        f"Tasa de conversión: {conversion}",
        "\nPor estado:",
    ]
    for est, n in sorted(conteos.items(), key=lambda x: -x[1]):
        lineas.append(f"  {est}: {n}")
    lineas.append("\nPor origen:")
    for orig, n in sorted(origenes.items(), key=lambda x: -x[1]):
        lineas.append(f"  {orig}: {n}")
    return "\n".join(lineas)
