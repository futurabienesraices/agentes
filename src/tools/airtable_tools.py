"""Herramientas para interactuar con Airtable — Futura Bienes Raíces."""
from __future__ import annotations
from typing import Any
from src.config import (
    AIRTABLE_API_KEY, AIRTABLE_BASE_ID,
    AIRTABLE_PROPIEDADES_TABLE,
    AIRTABLE_MARKETING_TABLE,
    AIRTABLE_CLIENTES_TABLE,
)


def _get_table(nombre_tabla: str):
    from pyairtable import Api
    return Api(AIRTABLE_API_KEY).table(AIRTABLE_BASE_ID, nombre_tabla)


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_AIRTABLE: list[dict] = [
    {
        "name": "airtable_listar_clientes",
        "description": (
            "Lista los clientes/prospectos del CRM en Airtable (tabla Clientes_FBR). "
            "Filtra por estado si se indica."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {
                    "type": "string",
                    "description": "Filtrar por estado (opcional), ej: Nuevo, Contactado, Calificado, Cerrado",
                },
                "limite": {"type": "integer", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_crear_cliente",
        "description": "Registra un nuevo cliente o prospecto en Airtable (tabla Clientes_FBR).",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre completo"},
                "telefono": {"type": "string"},
                "email": {"type": "string"},
                "interes": {"type": "string", "description": "Qué tipo de propiedad busca"},
                "presupuesto": {"type": "string"},
                "origen": {
                    "type": "string",
                    "enum": ["Instagram", "Facebook", "WhatsApp", "Referido", "Portal", "Otro"],
                },
                "notas": {"type": "string"},
            },
            "required": ["nombre"],
        },
    },
    {
        "name": "airtable_actualizar_cliente",
        "description": "Actualiza datos o estado de un cliente existente en Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "string", "description": "ID del registro (rec...)"},
                "estado": {"type": "string"},
                "notas": {"type": "string"},
                "siguiente_accion": {"type": "string"},
            },
            "required": ["record_id"],
        },
    },
    {
        "name": "airtable_listar_propiedades",
        "description": "Lista propiedades del inventario en Airtable (tabla Propiedades_FBR).",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["Casa", "Departamento", "Terreno", "Local", "Oficina", "Bodega"],
                },
                "operacion": {"type": "string", "enum": ["Venta", "Renta"]},
                "precio_max": {"type": "number"},
                "limite": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_crear_propiedad",
        "description": "Registra una nueva propiedad en el inventario de Airtable (tabla Propiedades_FBR).",
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Nombre o título de la propiedad"},
                "tipo": {
                    "type": "string",
                    "enum": ["Casa", "Departamento", "Terreno", "Local", "Oficina", "Bodega"],
                },
                "operacion": {"type": "string", "enum": ["Venta", "Renta"]},
                "precio": {"type": "number"},
                "zona": {"type": "string"},
                "recamaras": {"type": "integer"},
                "banos": {"type": "number"},
                "m2": {"type": "number"},
                "descripcion": {"type": "string"},
            },
            "required": ["titulo", "tipo", "operacion", "precio"],
        },
    },
    {
        "name": "airtable_listar_marketing",
        "description": (
            "Lista registros de la tabla Marketing_FBR: campañas, publicaciones, "
            "acciones de marketing y sus resultados."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limite": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_registrar_accion_marketing",
        "description": "Registra una acción o campaña de marketing en la tabla Marketing_FBR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Nombre de la campaña o acción"},
                "canal": {
                    "type": "string",
                    "description": "Canal de marketing",
                    "enum": ["Instagram", "Facebook", "WhatsApp", "Portal", "Email", "Otro"],
                },
                "tipo": {
                    "type": "string",
                    "description": "Tipo de acción",
                    "enum": ["Post", "Story", "Anuncio", "Email", "Llamada", "Evento"],
                },
                "propiedad_relacionada": {"type": "string", "description": "Título o ID de la propiedad"},
                "notas": {"type": "string"},
            },
            "required": ["titulo", "canal"],
        },
    },
    {
        "name": "airtable_reporte_clientes",
        "description": "Resumen estadístico de clientes: total por estado, origen y conversión.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "airtable_listar_clientes": _listar_clientes,
        "airtable_crear_cliente": _crear_cliente,
        "airtable_actualizar_cliente": _actualizar_cliente,
        "airtable_listar_propiedades": _listar_propiedades,
        "airtable_crear_propiedad": _crear_propiedad,
        "airtable_listar_marketing": _listar_marketing,
        "airtable_registrar_accion_marketing": _registrar_accion_marketing,
        "airtable_reporte_clientes": _reporte_clientes,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _listar_clientes(estado: str | None = None, limite: int = 20) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    formula = f"{{Estado}}='{estado}'" if estado else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron clientes con esos criterios."
    lineas = [f"Clientes ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(
            f"• [{r['id']}] {f.get('Nombre', '—')} | "
            f"Tel: {f.get('Telefono', '—')} | "
            f"Estado: {f.get('Estado', '—')} | "
            f"Origen: {f.get('Origen', '—')}"
        )
    return "\n".join(lineas)


def _crear_cliente(
    nombre: str,
    telefono: str = "",
    email: str = "",
    interes: str = "",
    presupuesto: str = "",
    origen: str = "Otro",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    campos: dict[str, Any] = {"Nombre": nombre, "Estado": "Nuevo", "Origen": origen}
    if telefono: campos["Telefono"] = telefono
    if email: campos["Email"] = email
    if interes: campos["Interes"] = interes
    if presupuesto: campos["Presupuesto"] = presupuesto
    if notas: campos["Notas"] = notas
    r = tabla.create(campos)
    return f"Cliente registrado. ID: {r['id']} | {nombre}"


def _actualizar_cliente(
    record_id: str,
    estado: str | None = None,
    notas: str | None = None,
    siguiente_accion: str | None = None,
) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    campos: dict[str, Any] = {}
    if estado: campos["Estado"] = estado
    if notas: campos["Notas"] = notas
    if siguiente_accion: campos["SiguienteAccion"] = siguiente_accion
    if not campos:
        return "No se proporcionaron campos para actualizar."
    tabla.update(record_id, campos)
    return f"Cliente {record_id} actualizado."


def _listar_propiedades(
    tipo: str | None = None,
    operacion: str | None = None,
    precio_max: float | None = None,
    limite: int = 10,
) -> str:
    tabla = _get_table(AIRTABLE_PROPIEDADES_TABLE)
    partes: list[str] = []
    if tipo: partes.append(f"{{Tipo}}='{tipo}'")
    if operacion: partes.append(f"{{Operacion}}='{operacion}'")
    if precio_max: partes.append(f"{{Precio}}<={precio_max}")
    formula = f"AND({', '.join(partes)})" if partes else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron propiedades con esos criterios."
    lineas = [f"Propiedades ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(
            f"• {f.get('Titulo', '—')} | {f.get('Tipo', '—')} | "
            f"{f.get('Operacion', '—')} | ${f.get('Precio', 0):,.0f} | "
            f"Zona: {f.get('Zona', '—')}"
        )
    return "\n".join(lineas)


def _crear_propiedad(
    titulo: str,
    tipo: str,
    operacion: str,
    precio: float,
    zona: str = "",
    recamaras: int = 0,
    banos: float = 0,
    m2: float = 0,
    descripcion: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_PROPIEDADES_TABLE)
    campos: dict[str, Any] = {
        "Titulo": titulo, "Tipo": tipo, "Operacion": operacion,
        "Precio": precio, "Estado": "Disponible",
    }
    if zona: campos["Zona"] = zona
    if recamaras: campos["Recamaras"] = recamaras
    if banos: campos["Banos"] = banos
    if m2: campos["M2"] = m2
    if descripcion: campos["Descripcion"] = descripcion
    r = tabla.create(campos)
    return f"Propiedad '{titulo}' registrada. ID: {r['id']}"


def _listar_marketing(limite: int = 10) -> str:
    tabla = _get_table(AIRTABLE_MARKETING_TABLE)
    registros = tabla.all(max_records=limite)
    if not registros:
        return "No hay registros de marketing."
    lineas = [f"Marketing ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(
            f"• {f.get('Titulo', '—')} | Canal: {f.get('Canal', '—')} | "
            f"Tipo: {f.get('Tipo', '—')}"
        )
    return "\n".join(lineas)


def _registrar_accion_marketing(
    titulo: str,
    canal: str,
    tipo: str = "Post",
    propiedad_relacionada: str = "",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_MARKETING_TABLE)
    campos: dict[str, Any] = {"Titulo": titulo, "Canal": canal, "Tipo": tipo}
    if propiedad_relacionada: campos["PropiedadRelacionada"] = propiedad_relacionada
    if notas: campos["Notas"] = notas
    r = tabla.create(campos)
    return f"Acción de marketing '{titulo}' registrada. ID: {r['id']}"


def _reporte_clientes() -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    todos = tabla.all()
    if not todos:
        return "No hay clientes en el sistema."
    estados: dict[str, int] = {}
    origenes: dict[str, int] = {}
    for r in todos:
        est = r["fields"].get("Estado", "Sin estado")
        ori = r["fields"].get("Origen", "Sin origen")
        estados[est] = estados.get(est, 0) + 1
        origenes[ori] = origenes.get(ori, 0) + 1
    total = len(todos)
    cerrados = estados.get("Cerrado", 0)
    lineas = [
        f"Total clientes: {total}",
        f"Tasa de conversión: {cerrados/total*100:.1f}%",
        "\nPor estado:",
    ]
    for k, v in sorted(estados.items(), key=lambda x: -x[1]):
        lineas.append(f"  {k}: {v}")
    lineas.append("\nPor origen:")
    for k, v in sorted(origenes.items(), key=lambda x: -x[1]):
        lineas.append(f"  {k}: {v}")
    return "\n".join(lineas)
